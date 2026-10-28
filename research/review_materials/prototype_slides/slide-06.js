const {slide,text,notes}=require("./common");
const terminal=require("../prototype_terminal_excerpt.json");
const slideConfig={index:6,type:"content",title:"Terminal results: what do they mean?"};
function createSlide(p,t) {
  const s=slide(p,t,6,slideConfig.title,"content",{
    label:"saved short-run stdout and interpretation",
    url:terminal.repository_record_url
  });
  text(s,"Recorded short demo: 16 campaigns, 4 training episodes; 1 campaign per cell.",.5,1.45,9,.35,15);
  s.addShape(p.ShapeType.rect,{x:.5,y:2.0,w:9,h:.95,
    line:{color:t.primary,transparency:100},fill:{color:t.primary}});
  text(s,terminal.selected_stdout_lines.join("\n"),.67,2.14,8.65,.7,12,"FFFFFF",
    {fontFace:"Courier New",paraSpaceAfterPt:3});
  const rows=[
    ["success=1.000","That configuration reached its target in 1 of 1 campaigns."],
    ["exposure","Gross simulated source debit in INR, not actual victim loss."],
    ["known","An attacker-training workload label, not proven detector holdout."],
    ["Interpretation","A tiny demo proves execution, not RL superiority or money saved."]
  ];
  rows.forEach((r,i)=>{
    const y=3.15+i*.37;
    text(s,r[0],.5,y,1.6,.3,13,t.accent,{bold:true});
    text(s,r[1],2.15,y,7.35,.3,14);
  });
  notes(s,"The three displayed lines are exact selected lines from previously executed short-main.stdout, not simulated terminal text and not a new experiment in this revision. The original 16-cell run used seed 101, two training episodes per detector and one campaign per detector/kind/attacker cell; all 16 cells completed. Recorded command exit code: 0. See prototype_terminal_excerpt.json for the full output hash, command, selected lines and record hashes. Exposure is the mean gross simulated debit within the cell; here its denominator is one campaign. Static and RL action/amount clipping differ, so the displayed exposure difference does not establish learned superiority or actual savings. The original stderr contains a model portability warning. The full-study counts on slide 5 are separate records.");
  return s;
}
module.exports={createSlide,slideConfig};
