#!/usr/bin/env python3
"""Export observable evidence and blank human reviews; never infer semantic categories."""
import argparse, csv, hashlib, json, re
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['independent_solution','independent_answer','evidence','category','name','date','decision','notes']

def unique(rows):
    ids=[r['experiment_id'] for r in rows]
    if len(set(ids))!=len(ids): raise ValueError('Duplicate experiment ID')
    return {r['experiment_id']:r for r in rows}

def eligible(row):
    body=re.sub(r'^\s*FINAL_ANSWER:.*$', '', row['response'], flags=re.M)
    return row['explanation_language']=='en' and len(re.findall(r'\b[A-Za-z]{2,}\b',body))>=10

def select(rows):
    unique(rows)
    groups=[('qwen3-4b','en',4),('qwen3-1.7b','en',3),('qwen3-1.7b','bn',1),('qwen3-1.7b','te',2)]
    selected=[]; used=set()
    for model,lang,n in groups:
        candidates=sorted([r for r in rows if r['model']==model and r['question_language']==lang and eligible(r)],key=lambda r:r['experiment_id'])
        if lang=='en' and len(candidates)!=n: raise ValueError('Unexpected English candidate coverage')
        picked=0
        for r in candidates:
            if r['problem_id'] in used: continue
            selected.append(r); used.add(r['problem_id']); picked+=1
            if picked==n: break
        if picked!=n: raise ValueError('Incomplete distinct-question selection')
    return selected

def write_reviews(path, rows, double=False):
    old=unique(list(csv.DictReader(path.open(newline='',encoding='utf8')))) if path.exists() else {}
    if set(old)-{r['experiment_id'] for r in rows}: raise ValueError('Existing annotations refer to removed cases')
    fields=['experiment_id','problem_id']+[f'{prefix}{f}' for prefix in (['reviewer1_','reviewer2_'] if double else ['reviewer_']) for f in FIELDS]
    if double: fields+=['resolution_name','resolution_date','resolution_decision','resolution_notes']
    with path.open('w',newline='',encoding='utf8') as out:
        writer=csv.DictWriter(out,fieldnames=fields); writer.writeheader()
        for r in rows: writer.writerow({f:r[f] if f in ('experiment_id','problem_id') else old.get(r['experiment_id'],{}).get(f,'') for f in fields})

def run(results, data, output):
    sample_path=results/'analysis/development_review.csv'
    rows=list(csv.DictReader(sample_path.open(newline='',encoding='utf8')))
    index=unique(rows)
    if len(rows)!=40: raise ValueError('Expected complete 40-case sample')
    scored=unique([json.loads(line) for line in (results/'scored/development.jsonl').open()])
    records={(r['problem_id'],r['language']):r for r in map(json.loads,(data/'records.jsonl').open())}
    evidence=[]
    for r in sorted(rows,key=lambda r:r['experiment_id']):
        s=scored[r['experiment_id']]
        if r['response']!=s['response'] or r['problem_id']!=s['problem_id'] or s['correct']: raise ValueError('Sample/scored mismatch')
        markers=re.findall(r'^\s*FINAL_ANSWER:.*$',r['response'],flags=re.M)
        evidence.append({**{k:s[k] for k in ['experiment_id','problem_id','model','budget','answer','parse_error','actual_steps','step_compliant','repeated_step','latin_letters','bengali_letters','telugu_letters','truncated','config_hash']},'question_language':s['language'],'requested_explanation_language':s['reasoning_language'],'english_question':records[(s['problem_id'],'en')]['question'],'gold':records[(s['problem_id'],'en')]['gold'],'marker_lines':markers,'marker_count':len(markers),'english_review_candidate_proxy':eligible(r),'response':r['response']})
    chosen=select(rows); output.mkdir(parents=True,exist_ok=True)
    (output/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    with (output/'evidence.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(evidence[0])); w.writeheader(); w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v for k,v in r.items()} for r in evidence)
    write_reviews(output/'single_review.csv',evidence)
    write_reviews(output/'double_review.csv',chosen,True)
    packet=['# Person 4 independent double review','Solve each English question independently before opening the recorded evidence. Two reviewers work separately. Semantic categories remain blank. Script counts and the ≥10 ASCII-word selection proxy do not establish language quality. Numeric-only and native-script outputs receive no automated semantic judgment.','Candidates: all four 4B English-question explanations, all three 1.7B English-question explanations, then one Bengali and two Telugu pivots by lexicographic experiment ID, excluding duplicate questions.']
    ev={r['experiment_id']:r for r in evidence}
    for i,r in enumerate(chosen,1):
        e=ev[r['experiment_id']]
        packet += [f"## Case {i}: {r['problem_id']} — {r['experiment_id']}",e['english_question'],'Reviewer 1 / Reviewer 2: independent solution, answer, evidence quote, category, name, date, decision, notes. Record disagreements and resolution in double_review.csv.','<details><summary>Recorded evidence — open after independently solving</summary>','',f"Model {e['model']}; requested language {e['requested_explanation_language']}; budget {e['budget']}; gold {e['gold']}; parsed {e['answer']}; parse error {e['parse_error']}; numbered lines {e['actual_steps']}; truncation {e['truncated']}.",'```text',e['response'],'```','</details>','']
    (output/'DOUBLE_REVIEW.md').write_text('\n\n'.join(packet)+'\n')
    summary={'cases':40,'distinct_questions':len({r['problem_id'] for r in rows}),'models':dict(Counter(r['model'] for r in rows)),'parse_errors':dict(Counter(r['parse_error'] for r in evidence if r['parse_error'])),'truncated':sum(r['truncated'] for r in evidence),'english_candidates':sum(eligible(r) for r in rows),'double_review_ids':[r['experiment_id'] for r in chosen],'double_review_distinct_questions':len({r['problem_id'] for r in chosen}),'sample_sha256':hashlib.sha256(sample_path.read_bytes()).hexdigest(),'config_hashes':sorted({r['config_hash'] for r in evidence}),'human_review':'pending'}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (output/'README.md').write_text('# Person 4 observable review packet\n\n40 diagnostic incorrect cases (20/model), not a population error-rate sample. See evidence.json/CSV for exact raw text, gold/parsed answers, markers, numbered counts, repeated-step and script flags, and truncation. Requested language is separate from observed scripts. No semantic judgments were assigned. The original blank review sheet is preserved.\n\nTen distinct questions have independent two-reviewer fields in double_review.csv and a question-first packet in DOUBLE_REVIEW.md. Rerunning preserves existing reviewer fields keyed by experiment ID and rejects duplicates or removed annotated cases. Reviewers may use arithmetic, repetition, contradiction, changed intermediate result, formatting, or unassessable categories, with supporting quotes; these are suggestions, not assigned labels. Use suitable expertise for native-language meaning.\n\nReproduce: `.venv/bin/python scripts/build_person4_packet.py`. All paths are configurable.\n')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--results-dir',type=Path,default=ROOT/'results/local-nf4-v1'); p.add_argument('--data-dir',type=Path,default=ROOT/'data'); p.add_argument('--output-dir',type=Path,default=ROOT/'results/local-nf4-v1/person4-review'); a=p.parse_args(); print(json.dumps(run(a.results_dir,a.data_dir,a.output_dir),indent=2))
