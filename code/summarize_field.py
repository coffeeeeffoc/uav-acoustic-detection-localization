"""Descriptive results from saved field estimates; no model calls or audio generation."""
from field_data import *
import csv

def summarize(rows,candidates=None):
    out={}
    methods=sorted({r['method'] for r in rows})
    for m in methods:
        all_m=[r for r in rows if r['method']==m]
        r=[x for x in all_m if x['split']=='test']
        pos=[x for x in r if int(x['positive'])]
        neg=[x for x in r if not int(x['positive'])]
        errors=np.array([float(x['error_deg']) for x in pos])
        out[m]=dict(positive_blocks=len(pos),negative_blocks=len(neg),
            mean_deg=float(np.mean(errors)),median_deg=float(np.median(errors)),p95_deg=float(np.quantile(errors,.95)),
            within5=float(np.mean(errors<=5)),within10=float(np.mean(errors<=10)),
            detected_positive=sum(int(x['detected']) for x in pos),false_positive=sum(int(x['detected']) for x in neg),
            tpr=float(np.mean([int(x['detected']) for x in pos])),fpr=float(np.mean([int(x['detected']) for x in neg])),
            joint10=float(np.mean([int(x['detected']) and float(x['error_deg'])<=10 for x in pos])),
            compute_ms_median=float(np.median([float(x['compute_ms']) for x in r])),
            compute_ms_p95=float(np.quantile([float(x['compute_ms']) for x in r],.95)),
            recordings={})
        for rid in sorted({x['id'] for x in r}):
            rr=[x for x in r if x['id']==rid]
            a=dict(n=len(rr),detection_rate=float(np.mean([int(x['detected']) for x in rr])))
            if int(rr[0]['positive']):
                ee=[float(x['error_deg']) for x in rr]
                a.update(mean_deg=float(np.mean(ee)),median_deg=float(np.median(ee)),p95_deg=float(np.quantile(ee,.95)),
                         within10=float(np.mean(np.array(ee)<=10)))
            out[m]['recordings'][rid]=a
    # Paired comparisons include rejected positives and use the SAME ranker gate.
    pos={m:{(r['id'],r['start_s']):r for r in rows if r['method']==m and r['split']=='test' and int(r['positive'])} for m in methods}
    paired={}
    for base in [m for m in methods if m!='ranker']:
        keys=sorted(pos[base]);assert set(keys)==set(pos['ranker'])
        diff=np.array([float(pos[base][k]['error_deg'])-float(pos['ranker'][k]['error_deg']) for k in keys])
        paired[base]=dict(mean_improvement_deg=float(diff.mean()),median_improvement_deg=float(np.median(diff)),
            fraction_improved=float(np.mean(diff>1e-10)),
            same_ranker_gate_joint10=float(np.mean([int(pos['ranker'][k]['detected']) and float(pos[base][k]['error_deg'])<=10 for k in keys])),
            recording_improvement_deg={rid:float(np.mean([d for k,d in zip(keys,diff) if k[0]==rid])) for rid in sorted({k[0] for k in keys})})
    result=dict(methods=out,paired_against_ranker=paired,
                inference_scope='Descriptive held-out point results; 4 positive and 2 negative recordings from one aircraft and one day. No iid-window confidence intervals.',
                localization_reference='Nominal static directions from acquisition diagrams, not synchronized per-frame ground truth.')
    if candidates is not None:
        groups={}
        for r in candidates:
            if r['split']=='test' and r['error_deg']!='':
                groups.setdefault((r['id'],r['start_s']),[]).append(float(r['error_deg']))
        minimum=[min(v) for v in groups.values()]
        result['candidate_oracle']=dict(blocks=len(minimum),mean_deg=float(np.mean(minimum)),
            within10=float(np.mean(np.array(minimum)<=10)),note='Uses reference labels after inference; an oracle ceiling, not achievable inference performance.')
    return result

if __name__=='__main__':
    rows=list(csv.DictReader((OUT/'predictions.csv').open(encoding='utf-8')))
    candidates=list(csv.DictReader((OUT/'candidates.csv').open(encoding='utf-8')))
    result=summarize(rows,candidates)
    (OUT/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
