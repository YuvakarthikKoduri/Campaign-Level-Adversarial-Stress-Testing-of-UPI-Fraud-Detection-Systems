const {slide,text,notes,repo}=require("./common");
const slideConfig={index:8,type:"summary",title:"From master to our final prototype"};
function createSlide(p,t) {
  const s=slide(p,t,8,slideConfig.title,"summary",{
    label:"verified master-to-prototype code comparison",
    url:repo+"/compare/1e2ca9e3db4a19bb72e0433f07f10425f74b82fa...25c28300ca738ee2d0a530b99683033668c312ca"
  });
  const rows=[
    [
      {text:"Area",options:{bold:true,color:"FFFFFF",fill:t.accent}},
      {text:"master: earlier baseline",options:{bold:true,color:"FFFFFF",fill:t.accent}},
      {text:"prototype: selected FINAL",options:{bold:true,color:"FFFFFF",fill:t.accent}}
    ],
    ["Learning","Static + rule policies","Adds Q-learning + zero-Q control"],
    ["Run / reload","Scenario runner","RL runner + saved-policy evaluation"],
    ["Evidence","Scenario summaries","Traces, checkpoints, manifests, plots"],
    ["Shared core","Two detectors + synthetic data","Same model/data bytes; architecture retained"]
  ];
  s.addTable(rows,{x:.5,y:1.4,w:9,colW:[1.45,3.15,4.4],rowH:.48,
    fontFace:"Arial",fontSize:14,color:t.primary,margin:.09,
    border:{type:"solid",color:"D7E0DE",pt:.5},fill:"FFFFFF",autoPage:false,
    paraSpaceAfterPt:0,valign:"ctr"});
  text(s,"Engineering contribution, not a controlled performance comparison.",.5,4.2,9,.3,15,t.accent,{bold:true});
  notes(s,"Final is the user's selected delivery branch, not production or scientific-validation certification. Verified comparison: master 1e2ca9e3db4a19bb72e0433f07f10425f74b82fa versus prototype documentation head 25c28300ca738ee2d0a530b99683033668c312ca; research-code baseline 92a12966ec49fd6dcd147fd4d7411382715bc729. Master already contains static/rule attackers, two saved detectors, campaign simulation and scenario JSON reports. Prototype adds src/attackers/q_learning.py, src/experiments/prototype.py, run_prototype.py, saved policies and prototype RL tests. The models/ and data/ trees have zero diff. This comparison is of implementation features, not a controlled performance experiment against master. The prototype branch has no local dashboard; later dashboard, matched pilot and repaired study are on the separate review branch. Historical detector-family exclusion remains unverified and policy comparisons are confounded. Later money, evaluation-state and schema repairs are not backported by this presentation revision. The later IEEE draft remains AI-assisted; human authorship review and university-approved AI-content/similarity checks remain pending. Do not promise a zero AI-content or unmeasured similarity score.\nPrior research already addresses fraud classification, sequential modelling, adversarial evasion and learning-based attackers; the implemented combination is campaign-ledger execution, inspectable tabular policies, checkpoints and traces. No first-ever algorithm or literature-wide novelty claim is made. Literature matrix: "+repo+"/blob/review/academic-dashboard-paper-v1/research/literature_review/comparison_matrix.csv . Examples: Carminati et al., RAID 2020, https://www.usenix.org/conference/raid2020/presentation/carminati ; Henderson et al., Deep Reinforcement Learning That Matters, https://arxiv.org/abs/1709.06560 .");
  return s;
}
module.exports={createSlide,slideConfig};
