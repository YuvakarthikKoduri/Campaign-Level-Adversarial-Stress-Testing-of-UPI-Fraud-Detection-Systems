const pptxgen=require("pptxgenjs");
const path=require("path");
async function main() {
  const p=new pptxgen();p.layout="LAYOUT_16x9";
  p.author="SHAURYA SINGH; K.H.A.Revanth; K Yuva Karthik; Likith R; Hima Tejaswi";
  p.subject="Faculty review of prototype/rl-academic-complete";
  p.title="UPI Fraud Stress Lab: Prototype Faculty Review";
  p.company="Student project presentation; guide: Dr S. KALYANI; AI-assisted slide preparation";
  p.lang="en-IN";
  const theme={primary:"172D30",secondary:"465E62",accent:"01696F",light:"BCE2E7",bg:"FFFFFF"};
  const plan=[];
  for(let i=1;i<=8;i++) {
    const mod=require("./slide-"+String(i).padStart(2,"0"));
    mod.createSlide(p,theme);plan.push(mod.slideConfig);
  }
  if(p._slides.length!==8)throw Error("Expected exactly eight slides");
  const output=path.join(__dirname,"../UPI_PROTOTYPE_FACULTY_8_SLIDES.pptx");
  await p.writeFile({fileName:output});
  console.log(JSON.stringify({output,slides:plan},null,2));
}
main().catch(e=>{console.error(e);process.exit(1)});
