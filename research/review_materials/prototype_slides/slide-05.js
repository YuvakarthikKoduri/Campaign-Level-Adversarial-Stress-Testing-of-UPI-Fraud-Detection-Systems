const {slide,text,notes,snapshot}=require("./common");
const slideConfig={index:5,type:"content",title:"What the retained records show"};
function createSlide(p,t) {
  const s=slide(p,t,5,slideConfig.title);
  [["1,152","attack campaigns"],["4,189","evaluated transactions"],["3","evaluation seeds"]].forEach((r,i)=>{
    text(s,r[0],.5+i*3.05,1.45,2.85,.55,34,t.accent,{bold:true});
    text(s,r[1],.5+i*3.05,2.05,2.85,.25,13);
  });
  const keys=["static","adaptive","rl","untrained_rl"];
  const series=["xgboost","random_forest"].map(d=>({
    name:d==="xgboost"?"XGBoost":"Random Forest",
    labels:["Static","Rule-adaptive","Trained RL","Zero Q"],
    values:keys.map(a=>100*Number(snapshot.summary.find(r=>r.detector===d&&r.kind==="known"&&r.attacker===a).success_mean))
  }));
  text(s,"High-value-burst subset: campaign completion",.5,2.38,5.9,.28,13,t.primary,{bold:true});
  s.addChart(p.ChartType.bar,series,{
    x:.5,y:2.72,w:5.85,h:1.7,barDir:"col",catAxisLabelFontSize:11,valAxisLabelFontSize:11,
    catAxisLabelColor:t.primary,valAxisLabelColor:t.primary,chartColors:[t.accent,"707F82"],
    valAxisMinVal:0,valAxisMaxVal:100,valAxisMajorUnit:25,showLegend:true,
    legendPos:"b",legendFontSize:11,legendColor:t.primary,showTitle:false,
    showValue:true,dataLabelPosition:"inEnd",dataLabelColor:"FFFFFF",dataLabelFormatCode:"0",
    dataLabelFontSize:10,showCatName:false,catAxisTitle:"Attacker strategy",
    showValAxisTitle:true,valAxisTitle:"Completion (%)",valAxisTitleFontSize:10,
    catGridLine:{style:"none"},valGridLine:{color:"E4EAE8",size:.5},
    chartArea:{fill:{color:"FFFFFF"},border:{color:"FFFFFF",pt:0}},
    plotArea:{fill:{color:"FFFFFF"},border:{color:"FFFFFF",pt:0}}
  });
  text(s,"All campaigns (pooled)\n1,077 / 1,152 = 93.490%\nreached their target.",6.65,2.5,2.85,.82,14,t.primary,{bold:true,paraSpaceAfterPt:0});
  text(s,"Not detector accuracy\nor proof of RL superiority.",6.65,3.45,2.85,.55,13,t.secondary);
  text(s,"Chart: high-value burst only.\n72 per arm / detector; 3 seeds.\nSeed SDs in notes; confounded.",6.65,4.03,2.85,.5,11,t.secondary,{paraSpaceAfterPt:0});
  const sd=series.map((r,i)=>r.name+": "+keys.map(a=>{
    const row=snapshot.summary.find(z=>z.detector===["xgboost","random_forest"][i]&&z.kind==="known"&&z.attacker===a);
    return (100*Number(row.success_seed_sd)).toFixed(3);
  }).join(", ")).join("\n");
  notes(s,"Exact source: prototype_evidence/comparison-final/{campaigns.json,transactions.csv,summary.csv,config.json} at code baseline 92a1296. New read-only arithmetic checked the historical records, not a new full run. Completion is target-reaching campaigns / attempted campaigns. Bar labels are rounded to whole percentages to separate adjacent values; the underlying native-chart series retain unrounded values. The counts are not the corrected legacy 4,161 transactions or matched pilot 7,200 campaigns. No error bars are plotted; sample seed SD in percentage points in category order Static, Rule, RL, Zero Q:\n"+sd+"\nRaw pooled completions: "+snapshot.completed+". Pooling is descriptive, not a common strategy effect.");
  return s;
}
module.exports={createSlide,slideConfig};
