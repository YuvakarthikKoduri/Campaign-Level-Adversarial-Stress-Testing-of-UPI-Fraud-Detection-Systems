const {slide,text,box,notes,snapshot}=require("./common");
const slideConfig={index:2,type:"content",title:"Why measure a whole campaign?"};
function createSlide(p,t) {
  const s=slide(p,t,2,slideConfig.title);
  text(s,"A transaction label is not the same as an intervention outcome.",.5,1.5,9,.45,20,t.accent,{bold:true});
  [["ALLOW","Transfer can proceed."],["FLAG","Alert raised; transfer may proceed."],["BLOCK","Simulator stops the campaign."]].forEach((a,i)=>{
    const x=.5+i*3.1;
    box(s,p,"",x,2.25,2.8,1.4);
    text(s,a[0],x+.17,2.44,2.46,.35,22,t.primary,{bold:true});
    text(s,a[1],x+.17,2.93,2.46,.55,15);
    if(i<2) text(s,"→",x+2.84,2.7,.23,.35,17,t.primary);
  });
  text(s,"Measure target completion, first alert, first block and gross simulated debit.",.5,3.95,9,.6,19);
  notes(s,"This is a semantic explanation of the simulator, not an observed three-transaction trajectory. FLAG is not treated as a prevented transfer. Gross debit is internal simulated money flow, not actual victim loss or proven money saved. Source: src/environment/simulator.py and src/campaigns/executor.py.");
  return s;
}
module.exports={createSlide,slideConfig};
