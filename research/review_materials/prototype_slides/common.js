const repo = "https://github.com/YuvakarthikKoduri/Campaign-Level-Adversarial-Stress-Testing-of-UPI-Fraud-Detection-Systems";
const snapshot = require("../prototype_snapshot.json");
function text(s, value, x, y, w, h, size=16, color="202B2D", extra={}) {
  s.addText(value, {x,y,w,h,fontFace:"Arial",fontSize:size,color,margin:0,
    breakLine:false,paraSpaceAfterPt:8,valign:"top",...extra});
}
function box(s,p,t,x,y,w,h,fill="F0F4F3") {
  s.addShape(p.ShapeType.rect,{x,y,w,h,line:{color:"D7E0DE",width:.6},fill:{color:fill}});
  text(s,t,x+.16,y+.16,w-.32,h-.32,16);
}
function slide(p,t,n,title,type="content") {
  const s=p.addSlide();s.background={color:t.bg};
  text(s,title,.5,.38,9,.95,34,t.primary,{bold:true,breakLine:false});
  if(n>1) {
    s.addShape(p.ShapeType.ellipse,{x:9.3,y:5.1,w:.32,h:.32,
      line:{color:t.accent,transparency:100},fill:{color:t.accent}});
    text(s,String(n),9.3,5.135,.32,.2,10,"FFFFFF",{align:"center",bold:true});
  }
  text(s,"SYNTHETIC RESEARCH  |  GATE C HOLD",.5,5.1,4.6,.22,10,t.secondary);
  s.addText([{text:"Source: ",options:{color:t.secondary}},
    {text:"prototype source and retained records",options:{color:t.accent,hyperlink:{url:repo+"/tree/prototype/rl-academic-complete"}}}],
    {x:.5,y:4.78,w:8.75,h:.22,fontFace:"Arial",fontSize:10,margin:0});
  s._reviewType=type;
  return s;
}
function notes(s,body) {s.addNotes(body+"\nCode baseline: 92a12966ec49fd6dcd147fd4d7411382715bc729. Not the later corrected legacy or matched-pilot study.");}
module.exports={text,box,slide,notes,snapshot,repo};
