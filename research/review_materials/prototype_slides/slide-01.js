const {text,box,notes,repo}=require("./common");
const slideConfig={index:1,type:"cover",title:"UPI Fraud Stress Lab"};
function createSlide(p,t) {
  const s=p.addSlide();s.background={color:t.primary};
  text(s,"UPI Fraud\nStress Lab",.6,.7,8.8,1.65,52,"FFFFFF",{bold:true});
  text(s,"Can an attack campaign reach its target\nbefore a detector stops it?",.65,2.7,8.7,1,26,t.light);
  text(s,"A working, synthetic campaign-level research prototype",.65,4,8.6,.4,17,"FFFFFF");
  text(s,"prototype/rl-academic-complete  |  code baseline 92a1296",.65,4.65,8.7,.3,13,t.light);
  text(s,"Offline simulation only. No real payments. Gate C remains HOLD.",.65,5.08,8.7,.25,12,t.light);
  notes(s,"Lecturer pitch: The project is a Python laboratory, not a deployed fraud-prevention service. It connects attacker decisions, detector responses and simulated account transfers in inspectable campaigns. This presentation describes the requested prototype branch. The later dashboard and matched pilot live on the separate review branch.\nRepository: "+repo);
  return s;
}
module.exports={createSlide,slideConfig};
