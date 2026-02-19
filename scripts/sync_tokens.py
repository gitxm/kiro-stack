#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path('/data/appdata/kiro-stack')
GO_CONFIG = ROOT / 'kiro-go' / 'data' / 'config.json'
GW_ENV = ROOT / 'kiro-gateway' / '.env'


def load_env(path: Path):
    out = {}
    lines = []
    if path.exists():
        lines = path.read_text(encoding='utf-8').splitlines()
        for line in lines:
            s = line.strip()
            if not s or s.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            out[k.strip()] = v.strip().strip('"')
    return out, lines


def quote(v: str) -> str:
    return '"' + v.replace('"', '\\"') + '"'


def main():
    data = json.loads(GO_CONFIG.read_text(encoding='utf-8'))
    accounts = data.get('accounts', [])

    env_map, lines = load_env(GW_ENV)
    primary = env_map.get('REFRESH_TOKEN', '')

    tokens = []
    seen = set()
    for a in accounts:
        if not a.get('enabled', False):
            continue
        token = (a.get('refreshToken') or '').strip()
        if not token:
            continue
        if token == primary:
            continue
        if token in seen:
            continue
        seen.add(token)
        tokens.append(token)

    joined = ','.join(tokens)
    kv = f'KIRO_REFRESH_TOKENS={quote(joined)}'

    replaced = False
    new_lines = []
    for line in lines:
        if line.startswith('KIRO_REFRESH_TOKENS='):
            new_lines.append(kv)
            replaced = True
        else:
            new_lines.append(line)

    if not replaced:
        if new_lines and new_lines[-1].strip() != '':
            new_lines.append('')
        new_lines.append(kv)

    GW_ENV.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
    print(f'synced_tokens={len(tokens)}')


if __name__ == '__main__':
    main()
