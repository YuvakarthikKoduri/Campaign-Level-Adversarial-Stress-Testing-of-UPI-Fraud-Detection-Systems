"""Check current documentation links, metric-to-paper anchors and evidence structure."""
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
BASE="92a12966ec49fd6dcd147fd4d7411382715bc729"
HISTORICAL={p for p in subprocess.check_output(
    ["git","ls-tree","-r","--name-only",BASE],cwd=ROOT,text=True).splitlines()
    if p.endswith(".md") and p!="README.md"}

def main():
    errors=[];count=0
    paths=[ROOT/"README.md",ROOT/"CONTRIBUTING.md"]
    paths += [p for p in (ROOT/"docs").rglob("*.md")
              if p.relative_to(ROOT/"docs").parts[0] not in ("history","verification")]
    paths+=list((ROOT/"research").rglob("*.md"))
    for path in paths:
        if path.relative_to(ROOT).as_posix() in HISTORICAL:continue
        for href in re.findall(r"\[[^\]]*\]\(([^)]+)\)",path.read_text()):
            href=href.split("#",1)[0]
            if not href or re.match(r"[A-Za-z]+:",href):continue
            count+=1
            if not (path.parent/href).exists():errors.append([path.relative_to(ROOT).as_posix(),href])
    for p in (ROOT/"docs/verification").glob("*.xml"):ET.parse(p)
    final=ROOT/"docs/verification/post-race-tests.xml"
    suite=ET.parse(final if final.exists() else ROOT/"docs/verification/final-integrated-tests.xml").getroot()
    cases=suite.findall(".//testcase")
    assert len(cases)==478
    assert not suite.findall(".//failure") and not suite.findall(".//error") and not suite.findall(".//skipped")
    rows=list(csv.DictReader((ROOT/"results/results_summary.csv").open()))
    assert sum(int(r["campaigns"]) for r in rows)==7200
    assert sum(int(r["completed"]) for r in rows)==3539
    text=subprocess.check_output(["pdftotext",str(ROOT/"research/paper/main.pdf"),"-"],text=True)
    for token in ("3,539","28,895","24,634","3,661","192,300,996.32","48.278","12.806","30,985"):
        assert token in text,token
    paper=ROOT/"research/paper/main.tex"
    bib=(paper.parent/"references.bib").read_text()
    cited={k.strip() for part in re.findall(r"\\cite\{([^}]+)\}",paper.read_text()) for k in part.split(",")}
    defined=set(re.findall(r"@\w+\{([^,]+),",bib))
    assert not cited-defined,cited-defined
    ET.parse(ROOT/"docs/images/architecture.svg")
    result=dict(current_relative_links=count,broken=errors,distinct_tests=len(cases),
                citation_keys=len(cited),defined_bib_entries=len(defined),
                paper_sha256=hashlib.sha256((paper.parent/"main.pdf").read_bytes()).hexdigest(),
                note="Historical bodies are explicitly scoped and excluded from current-link authority. External URLs were primary-source researched, not all refetched by this local checker.")
    (ROOT/"docs/verification/PACKAGE_CHECK.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))
    assert not errors,errors

if __name__=="__main__":main()
