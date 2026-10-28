const {text,box,notes,repo}=require("./common");
const slideConfig={index:1,type:"cover",title:"UPI Fraud Stress Lab"};
function createSlide(p,t) {
  const s=p.addSlide();s.background={color:t.primary};
  text(s,"UPI Fraud\nStress Lab",.6,.7,4.5,1.65,46,"FFFFFF",{bold:true});
  text(s,"Can an attack campaign\nreach its target before a\ndetector stops it?",.65,2.65,4.35,1.2,23,t.light);
  text(s,"A synthetic campaign-level research laboratory",.65,4.05,4.35,.45,15,"FFFFFF");
  text(s,"PROJECT GUIDE",5.35,.8,4,.25,12,t.light,{bold:true});
  text(s,"Dr S. KALYANI",5.35,1.16,4,.4,22,"FFFFFF",{bold:true});
  text(s,"STUDENTS",5.35,1.9,4,.25,12,t.light,{bold:true});
  [
    "24BCA7401 - SHAURYA SINGH",
    "24BCA7167 - K.H.A.Revanth",
    "24BCA7171 - K Yuva Karthik",
    "24BCE7026 - Likith R",
    "24BCA7040 - Hima Tejaswi"
  ].forEach((name,i)=>text(s,name,5.35,2.35+i*.43,4.05,.32,16,"FFFFFF"));
  text(s,"Final project branch: prototype/rl-academic-complete",.65,4.65,8.7,.3,14,t.light,{bold:true});
  text(s,"Offline simulation only. No real payments. Gate C remains HOLD.",.65,5.08,8.7,.25,12,t.light);
  notes(s,"Lecturer pitch: The project is a Python laboratory, not a deployed fraud-prevention service. It connects attacker decisions, detector responses and simulated account transfers in inspectable campaigns. The user selected prototype/rl-academic-complete as the final project branch for this presentation; final selection is not scientific certification. Guide and student names/IDs were supplied by the user. No phone numbers or pasted-chat timestamps are included. The later dashboard and matched pilot live on the separate review branch.\nRepository: "+repo);
  return s;
}
module.exports={createSlide,slideConfig};
