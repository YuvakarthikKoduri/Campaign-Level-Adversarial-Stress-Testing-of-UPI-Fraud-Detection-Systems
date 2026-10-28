const {slide,text,box,notes}=require("./common");
const slideConfig={index:7,type:"content",title:"Run the prototype in a terminal"};
function createSlide(p,t) {
  const s=slide(p,t,7,slideConfig.title);
  text(s,"From a clone of prototype/rl-academic-complete; Linux / WSL2, Python 3.11.",.5,1.45,9,.45,15);
  s.addShape(p.ShapeType.rect,{x:.5,y:2.08,w:9,h:2.2,
    line:{color:t.primary,transparency:100},fill:{color:t.primary}});
  text(s,"python3.11 -m venv .venv\nsource .venv/bin/activate\npython -m pip install -r requirements-milestone1.lock\npython -B -s run_prototype.py \\\n  --detector both --attacker all --seeds 101 \\\n  --episodes 2 --campaigns 1 --output demo-faculty-01",
    .67,2.24,8.65,1.9,14,"FFFFFF",{fontFace:"Courier New",paraSpaceAfterPt:5});
  text(s,"Inspect campaigns.json, transactions.csv, summary.csv and comparison.svg.",.5,4.4,9,.3,14,t.accent);
  notes(s,"A small demonstration is not a reproduction of the retained 300-training-episode, 24-campaign-per-cell full study. Use a new output directory for every run; outputs are not overwritten. The exact small configuration was newly executed in an isolated workspace. The existing environment was reused, not clean-installed. Full clone/setup commands, reload and regression commands are in the revised README. Dashboard startup requires the later review branch, not this one.");
  return s;
}
module.exports={createSlide,slideConfig};
