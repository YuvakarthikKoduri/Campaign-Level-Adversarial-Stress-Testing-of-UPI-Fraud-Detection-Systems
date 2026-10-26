"""Independent assertions against the unchanged candidate patch."""
import copy
from dataclasses import replace
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from src.attackers.q_learning import QLearningAttacker
from src.environment.entities import Account
from src.experiments.config import RunConfig, build_workload
from src.experiments.prototype import PrototypeConfig, compare, episode
from verify_prototype_outputs import verify

ROOT=Path(__file__).resolve().parents[1]

class Detector:
    def __init__(self, value=.1):
        self.value=value
    def predict(self,features):
        return self.value


@pytest.mark.parametrize("target",[23460.31,15000.,15000.01,.01,25868.13,29777.31])
def test_f1_exact_target_and_td_replay(target):
    cfg=RunConfig(campaigns=1,max_steps=3)
    spec=replace(build_workload(cfg)["known"][0],target_amount=target)
    a=QLearningAttacker(alpha=.25,gamma=.95,training=True)
    a.select=lambda _:12
    c=episode(Detector(),a,spec,cfg)
    assert c.status.value=="SUCCESS"
    assert Decimal(str(c.total_amount_moved))==Decimal(str(target))
    assert len(c.transactions)<=2
    if target==23460.31:
        assert [t["amount"] for t in c.transactions]==[15000,8460.31]
        assert len(a.rewards)==2 and a.updates==2
    q={}
    moved=Decimal(0)
    for i,t in enumerate(c.transactions):
        tr=t["rl_transition"]
        moved+=Decimal(str(t["amount_transferred"]))
        completed=moved>=Decimal(str(target))
        assert tr["terminal"]==completed
        assert not tr["terminal"] or i==len(c.transactions)-1
        expected=3*float(Decimal(str(t["amount_transferred"]))/Decimal(str(target)))+2*completed-.02
        assert tr["reward"]==pytest.approx(expected)
        state=tuple(tr["state"]); nxt=tuple(tr["next_state"])
        values=q.setdefault(state,[0.]*16)
        future=0 if tr["terminal"] else max(q.setdefault(nxt,[0.]*16))
        values[tr["action"]]+=.25*(expected+.95*future-values[tr["action"]])
    assert sum(t["rl_transition"]["terminal"] for t in c.transactions)==1
    assert set(a.q)==set(q)
    assert all(a.q[k]==pytest.approx(v) for k,v in q.items())


@pytest.mark.parametrize("start,debits",[(23460.31,[15000,8460.31]),(.3,[.1,.2]),(1.005,[.001,.004,1.])])
def test_f1_ledger_fractional_contract(start,debits):
    a=Account("independent",start)
    for i,amount in enumerate(debits):
        assert a.debit(amount,str(i))
    assert a.balance==0
    for i,amount in enumerate(reversed(debits)):
        assert a.credit(amount,"credit"+str(i))
    assert a.balance==start


@pytest.mark.parametrize("change,reason",[({"budget":1},"budget_exhausted"),
                                        ({"max_duration_seconds":1},"time_horizon")])
def test_f2_helper_propagation(change,reason):
    cfg=RunConfig(campaigns=1,max_steps=2,**change)
    a=QLearningAttacker()
    a.select=lambda _:0
    c=episode(Detector(),a,build_workload(cfg)["known"][0],cfg)
    assert c.budget==cfg.budget and c.max_duration_seconds==cfg.max_duration_seconds
    assert c.termination_reason==reason
    if reason=="budget_exhausted":
        assert not c.transactions and c.total_amount_moved==0


@pytest.mark.parametrize("kwargs",[{"budget":0},{"budget":float("nan")},
    {"max_duration_seconds":0},{"max_duration_seconds":float("inf")},{"max_steps":0}])
def test_f2_invalid_limits(kwargs):
    with pytest.raises(ValueError):
        RunConfig(**kwargs)


def test_f2_conflicting_feedback():
    cfg=RunConfig(campaigns=1,feedback="score")
    with pytest.raises(ValueError,match="label_only"):
        episode(Detector(),QLearningAttacker(),build_workload(cfg)["known"][0],cfg)


@pytest.fixture(scope="session")
def valid(tmp_path_factory):
    p=tmp_path_factory.mktemp("independent-valid")
    cfg=PrototypeConfig(seeds=(101,),episodes=5,campaigns=2,max_steps=3)
    compare(p/"main",cfg)
    compare(p/"repeat",cfg)
    compare(p/"reload",cfg,policy_dir=p/"main")
    return p


@pytest.mark.parametrize("field,value",[("training_families",["slow_drain"]),
    ("training_seed",999),("detector","random_forest"),("training_seed",True),
    ("training_families",None),("training_episodes","5")])
def test_f3_incompatible_metadata(valid,tmp_path,field,value):
    payload=json.loads((valid/"main/q_xgboost_101.json").read_text())
    payload["metadata"][field]=value
    (tmp_path/"q_xgboost_101.json").write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        compare(tmp_path/"out",PrototypeConfig(seeds=(101,),episodes=5,campaigns=2,
            max_steps=3,detector="xgboost",attacker="rl"),policy_dir=tmp_path)


@pytest.mark.parametrize("mutation",["missing_top","metadata_list","q_string"])
def test_f3_malformed_schema(valid,tmp_path,mutation):
    payload=json.loads((valid/"main/q_xgboost_101.json").read_text())
    if mutation=="missing_top":
        del payload["updates"]
    elif mutation=="metadata_list":
        payload["metadata"]=[]
    else:
        payload["q"]="not-a-table"
    path=tmp_path/"malformed.json"; path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        QLearningAttacker.load(path)


def test_f3_manifest_binding(valid):
    manifest=json.loads((valid/"reload/manifest.json").read_text())
    for r in manifest["runs"]:
        policy=valid/"main"/f"q_{r['detector']}_{r['seed']}.json"
        assert r["policy_sha256"]==hashlib.sha256(policy.read_bytes()).hexdigest()
        assert r["verified_provenance"]==json.loads(policy.read_text())["metadata"]


def test_f4_complete_policy_and_unseen_state():
    a=QLearningAttacker(training=False)
    a.metadata={"declared":"independent"}
    before=copy.deepcopy(a.policy_payload())
    a.select((0,3,0))
    assert a.policy_payload()==before and a.q=={}
    cfg=RunConfig(campaigns=1,max_steps=3)
    episode(Detector(),a,build_workload(cfg)["known"][0],cfg)
    assert a.policy_payload()==before and a.updates==0
    assert a.training is False


def test_f4_loaded_full_episode(valid):
    a=QLearningAttacker.load(valid/"main/q_xgboost_101.json")
    before=copy.deepcopy(a.policy_payload())
    cfg=RunConfig(campaigns=1,max_steps=3)
    episode(Detector(),a,build_workload(cfg)["known"][0],cfg)
    assert a.policy_payload()==before and not a.training


def test_f5_valid(valid):
    r=verify(valid/"main",valid/"repeat",valid/"reload")
    assert r["passed"] and r["byte_equal"] and r["evidence_complete"]
    assert r["scientific_validity"] is False


@pytest.mark.parametrize("case",["missing_policy","empty_sources","incomplete_sources",
    "missing_file","malformed_campaign","wrong_policy","wrong_run_count"])
def test_f5_required_negatives(valid,tmp_path,case):
    for d in ("main","repeat","reload"):
        shutil.copytree(valid/d,tmp_path/d)
    root=tmp_path/"main"
    if case=="missing_policy":
        (root/"q_xgboost_101.json").unlink()
    elif case in ("empty_sources","incomplete_sources","wrong_run_count"):
        p=root/"manifest.json"; obj=json.loads(p.read_text())
        if case=="empty_sources":obj["source_sha256"]={}
        elif case=="incomplete_sources":obj["source_sha256"].pop("run_prototype.py")
        else:obj["runs"]=obj["runs"][:1]
        p.write_text(json.dumps(obj))
    elif case=="missing_file":
        (root/"summary.json").unlink()
    elif case=="malformed_campaign":
        p=root/"campaigns.json"; obj=json.loads(p.read_text());obj[0]={}
        p.write_text(json.dumps(obj))
    else:
        p=root/"q_xgboost_101.json"; obj=json.loads(p.read_text())
        obj["metadata"]["detector"]="not-xgboost"
        p.write_text(json.dumps(obj))
    with pytest.raises((ValueError,OSError)):
        verify(tmp_path/"main",tmp_path/"repeat",tmp_path/"reload")


@pytest.mark.parametrize("case",["missing_target_schema","nonnumeric_summary","nonnumeric_per_seed"])
def test_f5_deeper_malformed_evidence_rejected(valid,tmp_path,case):
    """Changing all copies must not turn structurally malformed evidence into complete evidence."""
    for d in ("main","repeat","reload"):
        shutil.copytree(valid/d,tmp_path/d)
        root=tmp_path/d
        if case=="missing_target_schema":
            p=root/"campaigns.json"; obj=json.loads(p.read_text())
            obj[0]["spec"]={}
            p.write_text(json.dumps(obj,sort_keys=True))
        elif case=="nonnumeric_summary":
            p=root/"summary.json"; obj=json.loads(p.read_text())
            obj[0]["success_mean"]="not-a-number"
            p.write_text(json.dumps(obj,sort_keys=True))
        else:
            import csv
            p=root/"per_seed.csv"
            with p.open() as f:
                reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
            rows[0]["success"]="not-a-number"
            with p.open("w") as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    try:
        result=verify(tmp_path/"main",tmp_path/"repeat",tmp_path/"reload")
    except (ValueError,OSError):
        return
    print(json.dumps(result))
    assert result["passed"] is False or result["evidence_complete"] is False, \
        f"Checker certified malformed {case} as complete, equal evidence"
