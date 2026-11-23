"""Gerçek model ses/video testi. Ağ erişimi yalnızca model indirmesinde."""
import sys
import json
from pathlib import Path
from core import transcribe, render

def main():
    results = {}
    for device in ['cuda', 'cpu']:
        segments = []
        try:
            transcribe(sys.argv[1], 'tiny', 'en', device, False,
                       lambda s, p: segments.append(s), print, lambda: False)
            text = render(segments)
            assert segments and any(word in text.lower() for word in ['university', 'lecture', 'science', 'mathematics']), text
            results[device] = {'ok': True, 'text': text}
        except Exception as e:
            results[device] = {'ok': False, 'error': str(e)}
    Path(__file__).with_name('test-sonucu.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if not all(r['ok'] for r in results.values()):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
