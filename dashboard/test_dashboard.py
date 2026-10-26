"""Dashboard tests: no research engine edits and no expensive experiment execution."""
import copy
from decimal import Decimal
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from http.server import ThreadingHTTPServer

import pytest

from dashboard.records import Catalog, aggregate, csv_export, load, normalize, select, totals
from dashboard.runner import Jobs, build, redact
from dashboard.server import Application, Handler

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent
RETAINED = REPO/".local/retained" if (REPO/".local/retained").exists() else ROOT/"retained"


def test_nested_local_state_is_approved_but_git_is_not(tmp_path):
    repo=tmp_path/"repo";state=repo/".local/dashboard-state"
    state.mkdir(parents=True)
    log=state/"jobs/demo.log";log.parent.mkdir();log.write_text("actual log")
    git=repo/".git/config";git.parent.mkdir();git.write_text("not an artifact")
    catalog=Catalog(repo/".local/retained",repo,state)
    assert catalog.register(log)["name"]=="demo.log"
    with pytest.raises(ValueError,match="Hidden"):catalog.register(git)


@pytest.fixture(scope="module")
def catalog(tmp_path_factory):
    return Catalog(RETAINED, REPO, tmp_path_factory.mktemp("catalog-state"))


@pytest.mark.parametrize("name", ["../escape", "/tmp/escape", "a;touch-x", "a&&x", "a b",
                                  "a/../b", "", "A", ".", "x"*49, "a\nb"])
def test_output_rejected(name, catalog, tmp_path):
    with pytest.raises(ValueError, match="Output name"):
        build(dict(type="legacy", name=name), REPO, tmp_path, catalog)


@pytest.mark.parametrize("extra", [dict(command="id"), dict(executable="/bin/sh"),
    dict(shell=True), dict(timeout=0), dict(env={"TOKEN":"secret"}), dict(budget=1),
    dict(family="slow_drain")])
def test_no_arbitrary_execution_fields(extra, catalog, tmp_path):
    with pytest.raises(ValueError, match="Unsupported"):
        build(dict(type="legacy", name="test", **extra), REPO, tmp_path, catalog)


@pytest.mark.parametrize("key,value", [("episodes",0), ("episodes",True), ("episodes",301),
    ("campaigns",float("nan")), ("max_steps",31), ("seeds",[101,101]), ("seeds","101"),
    ("seeds",[True]), ("attacker","blind_rl"), ("detector","other")])
def test_bad_legacy_options(key,value,catalog,tmp_path):
    with pytest.raises(ValueError):
        build(dict(type="legacy",name="test",**{key:value}),REPO,tmp_path,catalog)


def test_valid_fixed_argv(catalog,tmp_path):
    plan=build(dict(type="legacy",name="valid",detector="both",attacker="all",
                    seeds=[101],episodes=60,campaigns=6,max_steps=30),REPO,tmp_path,catalog)
    assert plan["argv"][:4] == [sys.executable,"-B","-s","-u"]
    assert plan["argv"][4] == "run_prototype.py"
    assert plan["workload"] == dict(evaluation_campaigns=96,training_episodes=120,
        note="Derived episode counts, not a runtime estimate; repeat is not independent replication.")
    assert not plan["expensive"]
    large=build(dict(type="pilot",name="larger",blocks=9,episodes=300,contexts=40),REPO,tmp_path,catalog)
    assert large["expensive"] and large["workload"]["evaluation_campaigns"] == 7200


@pytest.mark.parametrize("options", [dict(detector="xgboost"),dict(attacker="rl"),dict(seeds=[101]),
                                     dict(blocks=10),dict(train_episodes=3)])
def test_pilot_unsupported(options,catalog,tmp_path):
    with pytest.raises(ValueError):
        build(dict(type="pilot",name="pilot",**options),REPO,tmp_path,catalog)


def test_reference_inheritance(catalog,tmp_path):
    plan=build(dict(type="pilot",name="reload",mode="reload",reference="pilot-main"),REPO,tmp_path,catalog)
    assert "--reload-from" in plan["argv"] and plan["workload"]["training_episodes"] == 0
    assert plan["argv"][plan["argv"].index("--episodes")+1] == "300"
    with pytest.raises(ValueError,match="version"):
        build(dict(type="pilot",name="mismatch",mode="reload",reference="legacy-short"),REPO,tmp_path,catalog)
    with pytest.raises(ValueError,match="versions"):
        build(dict(type="verify",name="mixed",reference="pilot-main",repeat="legacy-repeat",
                   reload="pilot-reload"),REPO,tmp_path,catalog)


def test_self_reused_verification_rejected(catalog,tmp_path):
    with pytest.raises(ValueError,match="three distinct"):
        build(dict(type="verify",name="self",reference="pilot-main",repeat="pilot-main",
                   reload="pilot-main"),REPO,tmp_path,catalog)


def test_output_symlinks(catalog,tmp_path):
    (tmp_path/"runs").symlink_to(RETAINED,target_is_directory=True)
    with pytest.raises(ValueError,match="symlink"):
        build(dict(type="legacy",name="new"),REPO,tmp_path,catalog)


def test_real_record_totals_independent(catalog):
    records=[]
    for path in sorted((RETAINED/"pilot-main").glob("block-*/*/campaigns.jsonl")):
        records += [json.loads(x) for x in path.read_text().splitlines()]
    complete=sum(r["success"] for r in records)
    txs=[t for r in records for t in r["transactions"]]
    gross=sum((Decimal(str(t["amount_transferred"])) for t in txs),Decimal(0))
    view=catalog.view("pilot-main",{})
    assert view["totals"] == dict(campaigns=7200,completed=complete,transactions=len(txs),
        gross=float(gross),allow=sum(t["decision"]=="ALLOW" for t in txs),
        flag=sum(t["decision"]=="FLAG" for t in txs),block=sum(t["decision"]=="BLOCK" for t in txs))
    assert complete == 3539 and len(txs) == 28895 and gross == Decimal("192300996.32")
    group=next(g for g in view["groups"] if (g["detector"],g["family"],g["strategy"])==
               ("xgboost","gradual_escalation","rule"))
    assert group["campaigns"] == 360 and group["completed"] == 271
    rates={(b["detector"],b["stratum"]):b for b in view["benign"]}
    assert rates["xgboost","benign_mimic_test"]["blocked"] == 1738
    assert rates["random_forest","benign_mimic_test"]["blocked"] == 461


def test_filters_and_csv(catalog):
    view=catalog.view("pilot-main",dict(detector="xgboost",strategy="rule",
                                       family="gradual_escalation",block="0"))
    assert view["totals"]["campaigns"] == 40 and len(view["groups"]) == 1
    assert view["groups"][0]["block_sd"] is None
    assert len(csv_export(view["groups"]).splitlines()) == 2
    assert sum(g["campaigns"] for g in catalog.view("legacy-short",{})["groups"]) == 96
    assert catalog.view("pilot-main",dict(strategy="not-present"))["totals"]["campaigns"] == 0
    assert "'=SUM" in csv_export([dict(detector="=SUM(A1)",family="x",strategy="x")])


def test_inventory_hashes_and_policies(catalog):
    models=catalog.models("pilot-main")
    assert len(models)==18 and sum(len(m["policies"]) for m in models)==36
    assert all(len(m["sha256"])==64 and m["fitting"]==1000 for m in models)
    files=catalog.datasets("pilot-main")
    assert len(files)==27 and {f["role"] for f in files}=={"Fit","Validation","Registered membership"}
    assert {m["detector"] for m in catalog.models("legacy-short")}=={"xgboost","random_forest"}


def test_expensive_submission_requires_confirmation(catalog,tmp_path):
    jobs=Jobs(REPO,tmp_path,catalog)
    with pytest.raises(ValueError,match="explicit confirmation"):
        jobs.submit(dict(type="pilot",name="large",blocks=9,episodes=300,contexts=40))
    assert not jobs.jobs and not list((tmp_path/"runs").iterdir())


def test_nan_json_rejected(tmp_path):
    path=tmp_path/"malformed.json";path.write_text('{"amount": NaN}')
    with pytest.raises(ValueError):load(path)


@pytest.mark.parametrize("mutator,diagnostic",[
    (lambda r:r.update(gross_paise=1),"gross"),
    (lambda r:r.update(success="yes"),"success"),
    (lambda r:r.update(transactions={}),"transactions"),
    (lambda r:r["transactions"][0].update(amount=float("inf")),"finite"),
    (lambda r:r["transactions"][0].update(decision="MAYBE"),"decision"),
    (lambda r:r["transactions"][0].update(timestamp="2026-01-05"),"timestamp"),
    (lambda r:r["transactions"][0]["rl_transition"].update(terminal=True),"after terminal"),
])
def test_malformed_records(mutator,diagnostic):
    path=RETAINED/"pilot-main/block-00/xgboost/campaigns.jsonl"
    raw=json.loads(path.read_text().splitlines()[0]);mutator(raw)
    with pytest.raises(ValueError,match=diagnostic):
        normalize(raw,"pilot",{},1,0)


def wait_job(jobs,identifier):
    end=time.monotonic()+10
    while jobs.active and time.monotonic()<end:
        time.sleep(.03)
    assert jobs.active is None
    return jobs.jobs[identifier]


def process_plan(tmp_path,code,timeout=3,kind="legacy"):
    return dict(kind=kind,output=str(tmp_path/"runs"/"process"),name="process",mode="main",
        workload=None,expensive=False,timeout=timeout,
        argv=[sys.executable,"-B","-u","-c",code],command="trusted process-control fixture",cwd=str(REPO))


def test_actual_process_streams_redaction_and_clean_env(monkeypatch,tmp_path,catalog):
    monkeypatch.setenv("DASHBOARD_INHERITED_SECRET","do-not-inherit")
    plan=process_plan(tmp_path,"import os,sys;print('hello');print('password=hidden',file=sys.stderr);print(os.getenv('DASHBOARD_INHERITED_SECRET'))")
    monkeypatch.setattr("dashboard.runner.build",lambda *a:plan)
    jobs=Jobs(REPO,tmp_path,catalog); job=jobs.submit({})
    final=wait_job(jobs,job["id"])
    logs=jobs.logs(job["id"],0)["lines"]
    assert final["exit_code"] == 0 and final["status"] == "completed"
    assert {r["channel"] for r in logs} == {"stdout","stderr"}
    text="\n".join(r["text"] for r in logs)
    assert "hello" in text and "None" in text and "hidden" not in text and "[REDACTED]" in text


def test_large_log_retention_is_explicit(monkeypatch,tmp_path,catalog):
    plan=process_plan(tmp_path,"for i in range(12000): print('x'*1000)",timeout=8)
    monkeypatch.setattr("dashboard.runner.build",lambda *a:plan)
    jobs=Jobs(REPO,tmp_path,catalog);job=jobs.submit({})
    final=wait_job(jobs,job["id"])
    log=tmp_path/"jobs"/(job["id"]+".jsonl")
    assert final["log_truncated"] is True and log.stat().st_size < 10_100_000
    assert "retention limit" in json.loads(log.read_text().splitlines()[-1])["text"]


def test_cancel_kills_term_ignoring_descendant(monkeypatch,tmp_path,catalog):
    child="import os,signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print('child-ready:'+str(os.getpid()),flush=True);time.sleep(30)"
    code=f"import subprocess,sys,time;subprocess.Popen([sys.executable,'-u','-c',{child!r}]);time.sleep(30)"
    plan=process_plan(tmp_path,code,timeout=8)
    monkeypatch.setattr("dashboard.runner.build",lambda *a:plan)
    jobs=Jobs(REPO,tmp_path,catalog);job=jobs.submit({})
    deadline=time.monotonic()+3
    pid=None
    while time.monotonic()<deadline:
        lines=jobs.logs(job["id"],0)["lines"]
        found=[r["text"] for r in lines if r["text"].startswith("child-ready:")]
        if found:
            pid=int(found[0].split(":")[1]);break
        time.sleep(.03)
    assert pid is not None
    jobs.cancel(job["id"]);assert wait_job(jobs,job["id"])["status"]=="cancelled"
    status=Path(f"/proc/{pid}/stat")
    assert not status.exists() or status.read_text().split()[2]=="Z"


@pytest.mark.parametrize("mode",["failure","timeout","cancel","malformed-junit"])
def test_failure_timeout_cancel_cleanup(mode,monkeypatch,tmp_path,catalog):
    output=tmp_path/"runs"/"process"
    if mode=="malformed-junit":
        output.mkdir(parents=True);(output/"tests.xml").write_text("<testsuites>")
    code="import time; print('started',flush=True); time.sleep(30)" if mode in ("cancel","timeout") else "raise SystemExit(3)" if mode=="failure" else "print('partial xml')"
    plan=process_plan(tmp_path,code,timeout=.2 if mode=="timeout" else 3)
    monkeypatch.setattr("dashboard.runner.build",lambda *a:plan)
    jobs=Jobs(REPO,tmp_path,catalog);job=jobs.submit({})
    with pytest.raises(ValueError,match="active"):jobs.submit({})
    if mode=="cancel":jobs.cancel(job["id"])
    final=wait_job(jobs,job["id"])
    assert final["status"] == {"failure":"failed","timeout":"timed_out","cancel":"cancelled","malformed-junit":"completed"}[mode]
    if mode=="malformed-junit":
        assert final["counts"] is None and "JUnit" in final["note"]


def test_http_origin_token_and_exports(tmp_path,catalog):
    app=Application(REPO,RETAINED,tmp_path)
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler);server.app=app
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    port=server.server_port;host=f"127.0.0.1:{port}"
    def request(method,path,payload=None,headers=None):
        conn=http.client.HTTPConnection("127.0.0.1",port,timeout=10)
        body=None if payload is None else json.dumps(payload)
        conn.request(method,path,body=body,headers=headers or {})
        r=conn.getresponse();data=r.read();status=r.status;conn.close();return status,data
    try:
        status,body=request("GET","/api/bootstrap");assert status==200
        token=json.loads(body)["csrf"]
        assert request("GET","/api/bootstrap",headers={"Host":"evil.invalid"})[0] == 400
        assert request("POST","/api/preview",dict(type="legacy",name="new"))[0] == 400
        headers={"Content-Type":"application/json","Origin":"http://"+host,"X-Research-Token":token}
        assert request("POST","/api/preview",dict(type="legacy",name="new"),headers)[0] == 200
        assert request("POST","/api/jobs",dict(type="legacy",name="../bad"),headers)[0] == 400
        assert request("POST","/api/preview",dict(type="pilot",name="new"),
                       {**headers,"Origin":"https://evil.invalid"})[0] == 400
        status,body=request("GET","/api/export?run=pilot-main&detector=xgboost&strategy=rule&family=gradual_escalation")
        assert status==200 and len(body.decode().splitlines())==2 and "271" in body.decode()
        assert request("GET","/api/files/../../etc/passwd")[0] == 400
        assert request("GET","/api/summary?run=does-not-exist")[0] == 400
    finally:
        server.shutdown();server.server_close()
