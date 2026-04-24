import requests, time, json
ids = ['69e6ab9fe8eaf33994528fae','69e77d733affbb258fce99d1','69e8ab5bcc7caaec228d6848']
names = {'69e6ab9fe8eaf33994528fae':'ANN_V1','69e77d733affbb258fce99d1':'Security','69e8ab5bcc7caaec228d6848':'CNN'}

base = 'http://localhost:8000/api/summary/'

for cid in ids:
    try:
        r = requests.get(base + cid, timeout=5)
        print(f'{names[cid]:10s} trigger: {r.status_code} {r.json().get("status","?")}')
    except Exception as e:
        print(f'{names[cid]:10s} trigger ERROR: {e}')

done = set()
for i in range(40):
    if len(done) == len(ids):
        break
    time.sleep(8)
    for cid in ids:
        if cid in done:
            continue
        try:
            r = requests.get(base + cid, timeout=5).json()
            status = r.get('status','?')
            print(f'  [{(i+1)*8:3d}s] {names[cid]:10s} {status}')
            if status == 'ready':
                done.add(cid)
        except Exception as e:
            print(f'  poll {cid}: {e}')

for cid in ids:
    try:
        r = requests.get(base + cid, timeout=10).json()
        out = f'_summary_{names[cid]}.json'
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(r, f, ensure_ascii=False, indent=2)
        chapters = r.get('summary',{}).get('chapters',[]) if isinstance(r.get('summary'), dict) else r.get('chapters',[])
        print(f'Saved {out}: status={r.get("status")} chapters={len(chapters)}')
    except Exception as e:
        print(f'save {cid}: {e}')
