import json,csv
R=json.load(open('pass1.json')); st=json.load(open('status.json'))
# Pass 2: codebook applied strictly to the extracted evidence quotes only (first-pass codes not consulted).
P2={'I01':('include','','T'),'I02':('include','','T'),'I03':('exclude','E5',''),'I04':('include','','T'),
    'I05':('exclude','E3',''),'I06':('include','','A;T'),'I07':('include','','T;O'),'I08':('include','','T'),
    'I09':('include','','T'),'I10':('include','','T'),'I11':('include','','T'),'X03':('exclude','E4','')}
P2NOTE={'I03':'Retry and self-disqualification are both steps of one membership-renewal routine (independence fails).',
 'I05':'Session buffering is not in the codebook mechanism class; only one class mechanism (reconnect) remains.',
 'I07':'Quotes support retries->load->scale-out->DB load as the primary path; signal inflation secondary.',
 'I11':'Observation path (autoscaler blind to sidecar limiter) is inferred from a remediation item, not stated; dropped under strict reading.',
 'X03':'Retry loop in reporting agent caused memory exhaustion via a leak (code defect), so E4 rather than E3.'}
rows=[]
for r in R:
    d2,e2,c2=P2.get(r['id'],(r['dec'],r['ex'],r['ch']))
    final='include' if (r['dec']=='include' and d2=='include') else ('borderline' if r['dec']!=d2 else 'exclude')
    rows.append({'id':r['id'],'org':r['org'],'incident_date':r['date'],'title':r['title'],'url':r['url'],'http_status':st[r['id']],'access_date':'2026-10-15',
      'source_type':r['src'],'mechanisms':r['mech'],'channels_pass1':r['ch'],'primary_pass1':r['ch'].split(';')[0] if r['ch'] else '',
      'confidence':r['conf'],'decision_pass1':r['dec'],'exclusion_pass1':r['ex'],'channels_pass2':c2,'primary_pass2':c2.split(';')[0] if c2 else '',
      'decision_pass2':d2,'exclusion_pass2':e2,'final_status':final,'evidence_quote_1':r['q1'],'evidence_quote_2':r['q2'],'notes':r['notes'],'pass2_note':P2NOTE.get(r['id'],'')})
with open('/workspace/concerto/CONCERTO/audit/incidents.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
n=len(rows); a=sum(x['decision_pass1']==x['decision_pass2'] for x in rows)
p1=sum(x['decision_pass1']=='include' for x in rows)/n; p2=sum(x['decision_pass2']=='include' for x in rows)/n
pe=p1*p2+(1-p1)*(1-p2); po=a/n; k=(po-pe)/(1-pe)
both=[x for x in rows if x['decision_pass1']=='include' and x['decision_pass2']=='include']
prim=sum(x['primary_pass1']==x['primary_pass2'] for x in both); sets=sum(set(x['channels_pass1'].split(';'))==set(x['channels_pass2'].split(';')) for x in both)
exc_agree=sum(x['exclusion_pass1']==x['exclusion_pass2'] for x in rows if x['decision_pass1']=='exclude' and x['decision_pass2']=='exclude')
nexc=sum(1 for x in rows if x['decision_pass1']=='exclude' and x['decision_pass2']=='exclude')
print(f'n={n} agree={a} po={po:.3f} pe={pe:.3f} kappa={k:.2f}; pass1 inc={round(p1*n)} pass2 inc={round(p2*n)} both={len(both)} primary agree={prim}/{len(both)} set agree={sets}/{len(both)} exclcode agree={exc_agree}/{nexc}')
from collections import Counter
print('final',Counter(x['final_status'] for x in rows))
print('excl codes (pass1, final excluded)',Counter(x['exclusion_pass1'] for x in rows if x['final_status']=='exclude'))
print('channels any (both)',Counter(c for x in both for c in set(x['channels_pass1'].split(';'))&set(x['channels_pass2'].split(';'))))
print('primary p1 (both)',Counter(x['primary_pass1'] for x in both),'p2',Counter(x['primary_pass2'] for x in both))
print('orgs',Counter(x['org'] for x in rows))
