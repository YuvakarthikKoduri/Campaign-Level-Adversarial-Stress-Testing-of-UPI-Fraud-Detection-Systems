const {slide,text,box,notes}=require("./common");
const slideConfig={index:6,type:"content",title:"A bounded engineering contribution"};
function createSlide(p,t) {
  const s=slide(p,t,6,slideConfig.title,"content",{
    label:"source-grounded literature matrix (review branch)",
    url:"https://github.com/YuvakarthikKoduri/Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems/blob/review/academic-dashboard-paper-v1/research/literature_review/comparison_matrix.csv"});
  text(s,"Existing methods",.5,1.5,4.2,.4,23,t.primary,{bold:true});
  text(s,"Fraud classification\nSequential modelling\nAdversarial evasion\nLearning-based attackers",.5,2.4,4.1,1.65,19);
  text(s,"Our implemented combination",5.05,1.5,4.45,.7,23,t.accent,{bold:true});
  text(s,"Campaign + ledger execution\nInspectable tabular policies\nSaved checkpoints and raw traces\nReproducible comparisons",5.05,2.4,4.45,1.65,19);
  text(s,"Useful research infrastructure, not a first-ever algorithm or superiority claim.",.5,4.35,9,.35,15);
  notes(s,"The prototype implements an engineering combination, not proven literature-wide novelty. The later source-grounded literature matrix is on review/academic-dashboard-paper-v1 at research/literature_review/comparison_matrix.csv. Published examples include Carminati et al. (RAID 2020), https://www.usenix.org/conference/raid2020/presentation/carminati and Henderson et al., Deep Reinforcement Learning That Matters, https://arxiv.org/abs/1709.06560. No published method is reimplemented on common data here. Inspectable means raw Q state and traces can be examined, not that their correctness is guaranteed.");
  return s;
}
module.exports={createSlide,slideConfig};
