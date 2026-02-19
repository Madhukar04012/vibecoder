"""Deep validation of generated SSS-class frontend code."""
import re
from backend.templates.sss_class_frontend import get_sss_class_frontend_templates

test_cases = [
    ('SaaS', 'myapp', ['auth', 'payments'], 'SaaS platform with billing and auth'),
    ('Ecommerce', 'shop', ['products', 'cart', 'orders'], 'ecommerce store with cart and product catalog'),
    ('Chat', 'chatapp', ['chat', 'notifications'], 'realtime chat application with notifications'),
    ('Dashboard', 'admin', ['users', 'analytics'], 'admin dashboard with user management'),
    ('CMS', 'blog', ['posts', 'comments'], 'blog CMS with posts and comments'),
]

total_errors = 0

def extract_top_level_keys(content, block_name):
    """Extract top-level keys from a TS const object."""
    keys = set()
    pattern = re.compile(rf'export const {block_name}\s*=\s*\{{')
    m = pattern.search(content)
    if not m:
        return keys
    start = m.end()
    depth = 1
    i = start
    current_key = ''
    while i < len(content) and depth > 0:
        ch = content[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        elif depth == 1 and ch == ':' and current_key.strip():
            keys.add(current_key.strip())
            current_key = ''
            i += 1
            continue
        elif depth == 1 and ch in (',', '\n'):
            current_key = ''
            i += 1
            continue
        elif depth == 1:
            current_key += ch
        i += 1
    return keys

aliases = {
    '@app/': 'src/app/',
    '@core/': 'src/core/',
    '@infra/': 'src/infrastructure/',
    '@features/': 'src/features/',
    '@shared/': 'src/shared/',
}
npm_prefixes = ['@tanstack/', '@vitejs/', '@testing-library/', 'react', 'sonner', 'lucide', 'next-themes', 'clsx', 'tailwind']
import_pattern = re.compile(r'''from\s+["'](@[^"'/]+/[^"' ]+)["']''')

for label, name, feats, idea in test_cases:
    print(f'\n{"="*60}')
    print(f'TEST: {label} ({idea})')
    print(f'{"="*60}')
    
    t = get_sss_class_frontend_templates(name, feats, idea)
    all_paths = {k[len('frontend/'):] for k in t if k.startswith('frontend/')}
    errors = []
    
    # 1. Aliased imports
    for fp, content in t.items():
        if not fp.endswith(('.ts', '.tsx')): continue
        for i, line in enumerate(content.split('\n'), 1):
            for imp in import_pattern.findall(line):
                if any(imp.startswith(p) for p in npm_prefixes): continue
                resolved = imp
                for alias, target in aliases.items():
                    if imp.startswith(alias):
                        resolved = target + imp[len(alias):]
                        break
                if resolved == imp: continue
                cands = [resolved + x for x in ('.ts', '.tsx', '/index.ts', '/index.tsx')]
                if not any(c in all_paths for c in cands):
                    errors.append(f'IMPORT: {fp}:{i} -> {imp}')
    
    # 2. ROUTES
    cc = t.get('frontend/src/core/constants/index.ts', '')
    ac = t.get('frontend/src/app/App.tsx', '')
    dr = extract_top_level_keys(cc, 'ROUTES')
    for r in set(re.findall(r'ROUTES\.(\w+)', ac)):
        if r not in dr:
            errors.append(f'ROUTES: ROUTES.{r} missing from constants')
    
    # 3. API_ENDPOINTS
    de = extract_top_level_keys(cc, 'API_ENDPOINTS')
    for fp, content in t.items():
        if 'api/' in fp and fp.endswith('.ts'):
            for ep in set(re.findall(r'API_ENDPOINTS\.(\w+)\.', content)):
                if ep not in de:
                    errors.append(f'API_ENDPOINTS: {fp} uses .{ep} not defined')
    
    # 4. QUERY_KEYS
    dq = extract_top_level_keys(cc, 'QUERY_KEYS')
    for fp, content in t.items():
        if 'hooks/' in fp and fp.endswith('.ts'):
            for qk in set(re.findall(r'QUERY_KEYS\.(\w+)\.', content)):
                if qk not in dq:
                    errors.append(f'QUERY_KEYS: {fp} uses .{qk} not defined')
    
    # 5. Lazy imports
    for match in re.findall(r'lazy\(\(\)\s*=>\s*import\("([^"]+)"\)\)', ac):
        resolved = match
        for alias, target in aliases.items():
            if match.startswith(alias):
                resolved = target + match[len(alias):]
                break
        cands = [resolved + x for x in ('.ts', '.tsx', '/index.ts', '/index.tsx')]
        if not any(c in all_paths for c in cands):
            errors.append(f'LAZY: {match} unresolved')
    
    # 6. Syntax
    for fp, content in t.items():
        if '{{{{' in content:
            errors.append(f'SYNTAX: {fp} quadruple braces')
    
    if errors:
        total_errors += len(errors)
        for e in errors:
            print(f'  ERROR: {e}')
    else:
        print(f'  ALL CHECKS PASSED ({len(t)} files)')

print(f'\n{"="*60}')
print(f'TOTAL ERRORS: {total_errors}')
if total_errors == 0:
    print('ALL TESTS PASSED')
else:
    print(f'FIX {total_errors} ERRORS')
