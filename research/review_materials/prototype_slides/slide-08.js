const {slide,text,box,notes,repo}=require("./common");
const slideConfig={index:8,type:"summary",title:"What we can defend at review"};
function createSlide(p,t) {
  const s=slide(p,t,8,slideConfig.title);
  const entries=[
    ["Implemented","Campaign simulation, two detectors,\nfour attacker controls and raw outputs."],
    ["Still limited","Synthetic data; detector-family exclusion\nunverified; legacy policy comparisons confounded."],
    ["Submission pending","The later IEEE draft is AI-assisted.\nHuman authorship review and approved checks remain."]
  ];
  entries.forEach((r,i)=>{
    const y=1.5+i*.9;
    text(s,r[0],.5,y,2.5,.4,20,t.accent,{bold:true});
    text(s,r[1],3.1,y,6.4,.65,17);
  });
  s.addText([{text:"Later dashboard, matched pilot and IEEE paper: ",options:{color:t.primary}},
    {text:"review branch",options:{color:t.accent,hyperlink:{url:repo+"/tree/review/academic-dashboard-paper-v1"}}}],
    {x:.5,y:4.4,w:9,h:.3,fontFace:"Arial",fontSize:13,margin:0});
  notes(s,"Do not promise unseen-fraud detection, a causal adaptation paradox, universal RL superiority, real-world UPI effectiveness, actual victim-loss reduction, zero AI content or an unmeasured similarity threshold. Later audits repaired decimal-money handling, frozen evaluation state and evidence schema checks on the review branch; these repairs are not backported into this documentation-only prototype update. The existing IEEE paper covers that later corrected study and pilot, not this older snapshot alone. University-approved AI-content and similarity reports remain PENDING EXTERNAL VERIFICATION.");
  return s;
}
module.exports={createSlide,slideConfig};
