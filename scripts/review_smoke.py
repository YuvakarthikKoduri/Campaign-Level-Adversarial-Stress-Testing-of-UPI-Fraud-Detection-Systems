"""Reproduce short real legacy/pilot main-repeat-reload workflows, without a full study."""
from pathlib import Path
import json,os,subprocess,sys,time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/".local/review-demo"
def main():
    if OUT.exists():raise SystemExit("Refusing existing review-demo output. Preserve it; select a fresh checkout for another run.")
    OUT.mkdir(parents=True)
    records=[]
    def run(label,args):
        command=[sys.executable,"-B","-s",*args]
        t=time.monotonic()
        with (OUT/(label+".log")).open("x") as log:
            result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",PYTHONHASHSEED="17"),timeout=600)
        records.append(dict(label=label,argv=command,exit_code=result.returncode,elapsed_seconds=time.monotonic()-t))
        (OUT/"journal.json").write_text(json.dumps(records,indent=2)+"\n")
        print(label,result.returncode,flush=True)
        if result.returncode:raise SystemExit(result.returncode)
    for kind in ("legacy","pilot"):
        a=OUT/(kind+"-main");b=OUT/(kind+"-repeat");c=OUT/(kind+"-reload")
        base=(["run_prototype.py","--detector","both","--attacker","all","--seeds","101",
               "--episodes","6","--campaigns","2"] if kind=="legacy" else
              ["-m","src.experiments.mechanism_pilot","--blocks","1","--episodes","2","--contexts","2","--seed-base","71000"])
        for mode,p in (("main",a),("repeat",b),("reload",c)):
            args=[*base,"--output",str(p)]
            if mode=="reload":args.extend(["--policy-dir" if kind=="legacy" else "--reload-from",str(a)])
            run(kind+"-"+mode,args)
        run(kind+"-check",["verify_prototype_outputs.py" if kind=="legacy" else "verify_mechanism_pilot.py",
            "--reference",str(a),"--repeat",str(b),"--reload",str(c),"--output",str(OUT/(kind+"-verification.json"))])
    print("Short demonstration only. Retained full results were not regenerated.")
if __name__=="__main__":main()
