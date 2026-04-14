import json
from pathlib import Path
from urllib import request, error


def parse_api_txt(path: Path):
    providers = {
        'OPENAI': {'base_url': None, 'api_key': None},
        'ARK': {'base_url': None, 'api_key': None},
    }
    models = []
    current_provider = None

    for raw in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, val = line.split('=', 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")

        if key.endswith('_BASE_URL'):
            prefix = key.replace('_BASE_URL', '')
            if prefix in providers:
                providers[prefix]['base_url'] = val
                current_provider = prefix
            continue

        if key.endswith('_API_KEY'):
            prefix = key.replace('_API_KEY', '')
            if prefix in providers:
                providers[prefix]['api_key'] = val
                current_provider = prefix
            continue

        if key == 'model_name' and current_provider in providers:
            cfg = {
                'provider': current_provider,
                'model': val,
                'base_url': providers[current_provider]['base_url'],
                'api_key': providers[current_provider]['api_key'],
            }
            if cfg['base_url'] and cfg['api_key'] and cfg['model']:
                models.append(cfg)

    return models


def probe_chat(cfg):
    endpoint = cfg['base_url'].rstrip('/') + '/chat/completions'
    payload = {
        'model': cfg['model'],
        'messages': [
            {'role': 'user', 'content': 'Reply with OK only.'}
        ],
        'temperature': 0,
        'max_tokens': 8,
    }
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(endpoint, method='POST', data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f"Bearer {cfg['api_key']}")

    try:
        with request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode('utf-8', errors='ignore')
            obj = json.loads(body)
            content = obj['choices'][0]['message']['content']
            return True, f"HTTP {resp.status}, reply={content!r}"
    except error.HTTPError as e:
        try:
            detail = e.read().decode('utf-8', errors='ignore')
        except Exception:
            detail = ''
        return False, f"HTTPError {e.code}: {detail[:300]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    models = parse_api_txt(Path('api.txt'))
    print(f'model_count={len(models)}')
    for cfg in models:
        ok, msg = probe_chat(cfg)
        status = 'REACHABLE' if ok else 'UNREACHABLE'
        print(f"[{status}] provider={cfg['provider']} model={cfg['model']} -> {msg}")


if __name__ == '__main__':
    main()
