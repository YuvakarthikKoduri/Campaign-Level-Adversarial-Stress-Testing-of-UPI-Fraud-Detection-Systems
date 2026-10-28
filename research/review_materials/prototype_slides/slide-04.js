const {slide,text,box,notes}=require("./common");
const slideConfig={index:4,type:"content",title:"Compare four attacker controls"};
function createSlide(p,t) {
  const s=slide(p,t,4,slideConfig.title);
  const rows=[
    ["Static","Family rules that do not respond to detector feedback."],
    ["Rule-adaptive","Hand-written rules respond to observed decisions."],
    ["Trained RL","Tabular reinforcement learning (RL), trained before evaluation."],
    ["Zero-Q control","Same RL action vocabulary without learned Q values."]
  ];
  rows.forEach((r,i)=>{
    const y=1.55+i*.65;
    text(s,r[0],.5,y,2.55,.4,18,t.accent,{bold:true});
    text(s,r[1],3.15,y,6.35,.5,16);
  });
  text(s,"RL: at most 64 states and 16 amount / pacing / recipient actions.",.5,4.3,9,.3,15,t.primary,{bold:true});
  notes(s,"Source: docs/PROTOTYPE_GUIDE.md and src/attackers/q_learning.py. RL learns only on high-value-burst workloads. Other families are excluded from attacker training, not demonstrably excluded from historical detector training. Action spaces, pacing, clipping and offline costs differ across the legacy policies, so these are not fully matched comparisons. The newer label-blind arm belongs to the later pilot, not this branch.");
  return s;
}
module.exports={createSlide,slideConfig};
