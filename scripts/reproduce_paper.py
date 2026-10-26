"""Independently reconstruct paper data from byte-verified retained records; no training."""
import argparse
from collections import Counter,defaultdict
import csv
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import random
import statistics

REPO=Path(__file__).resolve().parents[1]
ARMS=("static","rule","rl","blind_rl","zero_q")
def money(v):return int(Decimal(str(v))*100)
def read(p):return json.loads(p.read_text())
def write_csv(p,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def reconstruct():
    root=REPO/".local/retained"
    index=read(root/"index.json")
    checks=0;digests={}
    for run in ("pilot-main","legacy-full"):
        for name,expected in index[run]["files"].items():
            actual=hashlib.sha256((root/run/name).read_bytes()).hexdigest()
            assert actual==expected,(run,name);checks+=1;digests[run+"/"+name]=actual
    groups=defaultdict(list);totals=Counter();benign=defaultdict(Counter)
    for p in sorted((root/"pilot-main").glob("block-*/*/campaigns.jsonl")):
        for raw in p.read_text().splitlines():
            c=json.loads(raw);tx=c["transactions"]
            gross=sum(money(t["amount_transferred"]) for t in tx)
            assert gross==c["gross_paise"];checks+=1
            assert len(tx)==c["proposals"];checks+=1
            assert c["success"]==int(gross>=c["context"]["target_paise"]);checks+=1
            assert all(t["amount_transferred"]==0 for t in tx if t["decision"]=="BLOCK");checks+=1
            groups[(c["detector"],c["context"]["family"],c["arm"])].append(c)
            totals.update(campaigns=1,completed=c["success"],transactions=len(tx),gross_paise=gross)
            totals.update(t["decision"] for t in tx)
    table=[]
    for (det,fam,arm),rows in sorted(groups.items()):
        rates=[sum(c["success"] for c in rows if c["block"]==b)/40 for b in range(9)]
        successful=sum(c["success"] for c in rows)
        first_block=[];first_alert=[]
        for c in rows:
            begin=datetime.fromisoformat(c["context"]["start"])
            for event,decisions in ((first_block,("BLOCK",)),(first_alert,("FLAG","BLOCK"))):
                t=next((t for t in c["transactions"] if t["decision"] in decisions),None)
                if t:event.append((datetime.fromisoformat(t["timestamp"])-begin).total_seconds())
        table.append(dict(experiment="mechanism-pilot-v1",detector=det,family=fam,strategy=arm,
            campaigns=len(rows),completed=successful,completion_pct=100*successful/len(rows),
            independent_blocks=9,block_sd_pp=100*statistics.stdev(rates),
            allow=sum(t["decision"]=="ALLOW" for c in rows for t in c["transactions"]),
            flag=sum(t["decision"]=="FLAG" for c in rows for t in c["transactions"]),
            block=sum(t["decision"]=="BLOCK" for c in rows for t in c["transactions"]),
            gross_inr=sum(c["gross_paise"] for c in rows)/100,
            first_block_observed=len(first_block),
            first_block_seconds_conditional=statistics.mean(first_block) if first_block else "",
            first_alert_observed=len(first_alert),
            first_alert_seconds_conditional=statistics.mean(first_alert) if first_alert else ""))
        old=next(r for r in read(root/"pilot-main/summary.json")
            if r["detector"]==det and r["family"]==fam and r["arm"]==arm)
        assert abs(old["success"]-successful/len(rows))<1e-12;checks+=1
    manifest=read(root/"pilot-main/manifest.json")
    for b in manifest["blocks"]:
        for stratum,episodes in read(root/f"pilot-main/block-{b['block']:02d}/{b['detector']}/benign_scores.json").items():
            for e in episodes:
                assert e["peak"]==max(e["scores"]);checks+=1
                benign[(b["detector"],stratum)].update(n=1,blocked=int(e["peak"]>=b["block_threshold"]),
                                                     alerted=int(e["peak"]>=b["flag"]))
    benign_table=[dict(experiment="mechanism-pilot-v1",detector=d,stratum=s,**v,
        block_pct=100*v["blocked"]/v["n"],alert_pct=100*v["alerted"]/v["n"])
        for (d,s),v in sorted(benign.items())]
    contrasts=[]
    rng=random.Random(20261026)
    for det in ("xgboost","random_forest"):
        for a,b in (("rule","static"),("rl","blind_rl"),("rl","zero_q")):
            ra={c["context"]["id"]:c for c in groups[(det,"gradual_escalation",a)]}
            rb={c["context"]["id"]:c for c in groups[(det,"gradual_escalation",b)]}
            assert ra.keys()==rb.keys();checks+=1
            block=[statistics.mean(ra[k]["success"]-rb[k]["success"] for k in ra if ra[k]["block"]==i)
                   for i in range(9)]
            boot=sorted(100*statistics.mean(rng.choices(block,k=9)) for _ in range(10000))
            contrasts.append(dict(detector=det,contrast=a+" minus "+b,n_blocks=9,n_paired_contexts=360,
                difference_pp=100*statistics.mean(block),ci_low_pp=boot[249],ci_high_pp=boot[9749],
                method="Exploratory paired block percentile bootstrap; 10000 draws; seed 20261026; unadjusted"))
    legacy=read(root/"legacy-full/campaigns.json")
    legacygroups=defaultdict(list)
    for c in legacy:
        assert money(c["metrics"]["exposure"])==sum(money(t["amount_transferred"]) for t in c["transactions"]);checks+=1
        legacygroups[(c["detector"],c["kind"],c["attacker"])].append(c)
    legacytable=[dict(experiment="legacy-corrected",detector=d,workload=k,strategy=a,campaigns=len(rows),
        completed=sum(c["metrics"]["success"] for c in rows),
        completion_pct=100*sum(c["metrics"]["success"] for c in rows)/len(rows),
        seeds=3) for (d,k,a),rows in sorted(legacygroups.items())]
    assert dict(totals)==dict(campaigns=7200,completed=3539,transactions=28895,gross_paise=19230099632,
                             ALLOW=24634,FLAG=600,BLOCK=3661)
    expected={("xgboost","benign_mimic_test"):1738,("random_forest","benign_mimic_test"):461}
    for k,v in expected.items():assert benign[k]["blocked"]==v and benign[k]["n"]==3600;checks+=1
    out=REPO/"results";out.mkdir(exist_ok=True)
    write_csv(out/"results_summary.csv",table)
    write_csv(out/"comparison_tables/benign_controls.csv",benign_table)
    write_csv(out/"comparison_tables/paired_contrasts.csv",contrasts)
    write_csv(out/"comparison_tables/legacy_separate.csv",legacytable)
    result=dict(totals=totals,benign=benign_table,checks=checks,
        legacy_campaigns=len(legacy),legacy_transactions=sum(len(c["transactions"]) for c in legacy),
        source_hashes=digests,analysis_seed=20261026,bootstrap_draws=10000)
    (out/"independent_reconstruction.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    tables=REPO/"research/paper/tables";tables.mkdir(parents=True,exist_ok=True)
    lines=[r"\begin{tabular}{llrrrrr}\toprule",
           r"Detector&Family&Static&Rule&RL&Blind RL&Zero Q\\\midrule"]
    for det in ("xgboost","random_forest"):
        for fam in ("high_value_burst","gradual_escalation"):
            values=[next(r for r in table if r["detector"]==det and r["family"]==fam and r["strategy"]==a) for a in ARMS]
            lines.append(("XGB" if det=="xgboost" else "RF")+" & "+("HVB" if fam=="high_value_burst" else "GE")
                +" & "+" & ".join(f"{r['completion_pct']:.3f}" for r in values)+r" \\")
    lines.append(r"\bottomrule\end{tabular}")
    (tables/"completion.tex").write_text("\n".join(lines)+"\n")
    return table,benign_table,result

def figures(table,benign):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size":9,"pdf.fonttype":42,"svg.fonttype":"none","axes.spines.top":False,
                         "axes.spines.right":False})
    out=REPO/"research/paper/figures";out.mkdir(parents=True,exist_ok=True)
    fig,axs=plt.subplots(1,2,figsize=(7,2.7),sharey=True,layout="constrained")
    for ax,det,label in zip(axs,("xgboost","random_forest"),("XGBoost","Random Forest")):
        rows=[next(r for r in table if r["detector"]==det and r["family"]=="gradual_escalation" and r["strategy"]==a) for a in ARMS]
        ax.bar(range(5),[r["completion_pct"] for r in rows],color=["#687779","#20808d","#1b474d","#8da7aa","#b9c5c5"])
        ax.errorbar(range(5),[r["completion_pct"] for r in rows],yerr=[r["block_sd_pp"] for r in rows],
                    fmt="none",ecolor="#28251d",capsize=2)
        ax.set(xticks=range(5),xticklabels=["Static","Rule","RL","Blind RL","Zero Q"],
               title=label,ylim=(0,105),yticks=[0,25,50,75,100])
        ax.tick_params(axis="x",rotation=30)
    axs[0].set_ylabel("Campaign completion (%)")
    fig.suptitle("Held-out GE: 360 campaigns per arm, 9 blocks; bars ± block SD",fontsize=10)
    for ext in ("pdf","svg"):fig.savefig(out/f"completion.{ext}",metadata={"Creator":"Perplexity Computer",**({"Author":"Perplexity Computer"} if ext=="pdf" else {})})
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(3.5,2.2),layout="constrained")
    rows=[next(r for r in benign if r["detector"]==d and r["stratum"]=="benign_mimic_test")
          for d in ("xgboost","random_forest")]
    ax.barh(["XGBoost","Random Forest"],[r["block_pct"] for r in rows],color="#a84b2f")
    for y,r in enumerate(rows):ax.text(r["block_pct"]+1,y,f"{r['blocked']}/{r['n']} ({r['block_pct']:.3f}%)",va="center",fontsize=8)
    ax.set(xlim=(0,100),xlabel="Legitimate GE-mimic episodes\nblocked (%)",
           title="Benign mechanism shift\n3,600 episodes per detector")
    ax.set_title(ax.get_title(),fontsize=10)
    ax.xaxis.label.set_size(9)
    for ext in ("pdf","svg"):fig.savefig(out/f"benign_shift.{ext}",metadata={"Creator":"Perplexity Computer",**({"Author":"Perplexity Computer"} if ext=="pdf" else {})})
    plt.close(fig)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--figures",action="store_true");a=p.parse_args()
    table,benign,result=reconstruct()
    if a.figures:figures(table,benign)
    print(json.dumps({k:v for k,v in result.items() if k!="source_hashes"},indent=2))
