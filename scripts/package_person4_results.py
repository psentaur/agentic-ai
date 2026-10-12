"""Refresh and verify the preliminary results archive; run from the project root."""
from pathlib import Path
import zipfile,json,hashlib
root=Path('.'); paths=[p for p in (root/'results/local-nf4-v1').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
extras=[*root.glob('configs/*.json'),*root.glob('docs/*.md'),root/'TEAM_PLAN.md',root/'STATUS.md',root/'README.md',root/'paper/main.tex',root/'paper/references.bib',root/'paper/literature-verification.md',root/'paper/claim-source-map.json',root/'output/pdf/preliminary-mgsm-study.pdf']
with zipfile.ZipFile('dist/local-preliminary-results.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(paths):z.write(p,Path('local-nf4-v1')/p.relative_to(root/'results/local-nf4-v1'))
 for p in sorted(set(extras)):z.write(p,Path('extras')/p)
verification={}
for name in ['indic-study.zip','overleaf-paper.zip','local-preliminary-results.zip']:
 p=root/'dist'/name
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  assert len(z.namelist())==len(set(z.namelist()))
  assert not any('/.venv' in n or '__pycache__' in n or n.endswith('.safetensors') for n in z.namelist())
  if name=='overleaf-paper.zip':
   for file in z.namelist():assert z.read(file)==(root/'paper'/file).read_bytes(),file
  elif name=='indic-study.zip':
   for file in ['paper/main.tex','scripts/build_person4_packet.py','docs/MANUAL_TASKS.md','output/pdf/preliminary-mgsm-study.pdf','results/local-nf4-v1/person4-review/evidence.json']:
    assert z.read('indic-study/'+file)==(root/file).read_bytes()
  else:
   for file in ['person4-review/evidence.json','person4-review/double_review.csv','person4-report/compilation.json','analysis/development_review.csv','raw/qwen3-4b.jsonl']:
    assert z.read('local-nf4-v1/'+file)==(root/'results/local-nf4-v1'/file).read_bytes()
  verification[name]={'files':len(z.namelist()),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'zip_integrity':'passed','sample_content_checks':'passed'}
(root/'dist/person4-package-verification.json').write_text(json.dumps(verification,indent=2)+'\n')
print(json.dumps(verification,indent=2))
