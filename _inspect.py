import json, re

for name in ['ANN_V1','Security','CNN']:
    with open(f'_summary_{name}.json', encoding='utf-8') as f:
        data = json.load(f)
    print('='*70)
    print(f'COURSE: {name}')
    print('='*70)
    summary = data.get('summary', {})
    chapters = summary.get('chapters', []) if isinstance(summary, dict) else []
    if not chapters:
        chapters = data.get('chapters', [])
    
    # Scan for residual ligature artifacts and watermarks
    full_text = json.dumps(data, ensure_ascii=False)
    suspicious_ligatures = re.findall(r'\b\w*\s+(cation|nition|érent|icile|isant|icace|ux|ltres?|chier)\w*\b', full_text)
    print(f'Suspicious ligature gaps: {len(suspicious_ligatures)} {suspicious_ligatures[:8]}')
    
    # Show first 2 chapters
    for ch in chapters[:3]:
        print(f"\n--- Chapter: {ch.get('title','?')[:80]} ---")
        print(f"Pages: {ch.get('pages','?')}")
        print(f"Concepts: {ch.get('key_concepts',[])}")
        bullets = ch.get('summary','')
        if isinstance(bullets, list):
            for b in bullets[:5]:
                print(f"  • {b[:200]}")
        else:
            print(bullets[:800])
    print()
