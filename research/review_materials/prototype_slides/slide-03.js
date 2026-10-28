const {slide,text,box,notes}=require("./common");
const slideConfig={index:3,type:"content",title:"How the prototype works"};
function createSlide(p,t) {
  const s=slide(p,t,3,slideConfig.title);
  ["Campaign\nworkload","Attacker\nactions","Ledger +\ndetector","Recorded\noutcomes"].forEach((v,i)=>{
    box(s,p,v,.5+i*2.35,1.65,1.95,.95);
    if(i<3) text(s,"→",2.5+i*2.35,1.92,.3,.4,23,t.primary);
  });
  text(s,"Feedback: detector → adaptive attacker (public decisions only).",.5,2.75,9,.4,16,t.accent);
  text(s,"Two saved detectors",.5,3.35,4.2,.35,20,t.primary,{bold:true});
  text(s,"XGBoost and Random Forest\nReused artifacts; no retraining required for the demo.",.5,3.84,4.1,.65,15);
  text(s,"Four workload families",5,3.35,4.5,.35,20,t.primary,{bold:true});
  text(s,"High-value burst · Slow drain\nGradual escalation · Beneficiary hopping",5,3.84,4.5,.65,15);
  notes(s,"Implementation source: src/campaigns/generator.py, src/campaigns/executor.py, src/attackers/, src/detectors/baseline.py and src/experiments/prototype.py. The legacy family labels describe workload generation and pacing; the RL action trajectory need not preserve each family's original shape. This branch does not contain run_dashboard.py or the later mechanism_pilot module.");
  return s;
}
module.exports={createSlide,slideConfig};
