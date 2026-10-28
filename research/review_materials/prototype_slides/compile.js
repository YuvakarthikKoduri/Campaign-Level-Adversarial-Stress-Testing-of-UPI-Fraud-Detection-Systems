const pptxgen=require("pptxgenjs");
const path=require("path");
async function main() {
  const p=new pptxgen();p.layout="LAYOUT_16x9";
  p.author="AI-assisted draft for researcher review";
  p.subject="Faculty review of prototype/rl-academic-complete";
  p.title="UPI Fraud Stress Lab: Prototype Faculty Review";
  p.company="Researcher authorship details pending approval";
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
