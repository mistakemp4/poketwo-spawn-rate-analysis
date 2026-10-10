"""Export the executed notebook, its charts, the lookup data and the sprites into the neocities site repo."""
import base64
import io
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import mistune
import nbformat
from PIL import Image

HERE = Path(__file__).parent
SITE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / 'src' / 'neocities'

NOTEBOOK = HERE / 'poketwo_spawn_rate_analysis.ipynb'
LOOKUP = HERE / 'data' / 'spawn_lookup.json'

PUBLIC_DIR = SITE / 'public' / 'projects' / 'poketwo'
PUBLIC_URL = '/projects/poketwo'
SPRITE_DIR = PUBLIC_DIR / 'sprites'
SPRITE_SOURCE = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{dex}.png'


def save_webp(png_bytes, target):
    # lossless, so charts and pixel sprites stay sharp
    image = Image.open(io.BytesIO(png_bytes))
    if image.mode == 'P':
        image = image.convert('RGBA')
    image.save(target, 'WEBP', lossless=True, method=6)
    return image.size


def as_lines(text):
    # lists of lines keep the json readable and its diffs small
    return text.rstrip().split('\n')


def convert_output(out, figure_number):
    if out.output_type == 'stream':
        return {'kind': 'text', 'text': as_lines(out.text)}

    data = out.get('data', {})
    if 'image/png' in data:
        name = f'fig-{figure_number:02d}.webp'
        width, height = save_webp(base64.b64decode(data['image/png']), PUBLIC_DIR / name)
        return {'kind': 'image', 'src': f'{PUBLIC_URL}/{name}', 'width': width, 'height': height}
    if 'text/html' in data:
        # pandas ships its own table styles, the site has its own
        html = re.sub(r'<style scoped>.*?</style>', '', data['text/html'], flags=re.S)
        return {'kind': 'html', 'html': as_lines(html.strip())}
    return {'kind': 'text', 'text': as_lines(data['text/plain'])}


def export_notebook():
    nb = nbformat.read(NOTEBOOK, as_version=4)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    for old in PUBLIC_DIR.glob('fig-*'):
        old.unlink()

    cells = []
    figures = 0
    for cell in nb.cells:
        source = cell.source.strip()
        if not source:
            continue
        if cell.cell_type == 'markdown':
            cells.append({'type': 'markdown', 'html': as_lines(mistune.html(source))})
            continue

        outputs = []
        for out in cell.get('outputs', []):
            if 'image/png' in out.get('data', {}):
                figures += 1
            outputs.append(convert_output(out, figures))
        cells.append({'type': 'code', 'source': as_lines(source), 'outputs': outputs})

    target = SITE / 'src' / 'data' / 'poketwo-notebook.json'
    target.write_text(json.dumps(cells, ensure_ascii=False, indent='\t') + '\n', encoding='utf-8')
    print(f'notebook: {len(cells)} cells, {figures} figures -> {target}')


def export_lookup():
    src = json.loads(LOOKUP.read_text(encoding='utf-8'))
    rows = [
        {
            'dex': p['dex_number'],
            'name': p['name'],
            'region': p['region'],
            'types': ' / '.join(t for t in (p['type_1'], p['type_2']) if t),
            'class': p['class'],
            'weight': p['weight'],
        }
        for p in src['pokemon']
    ]

    # one pokemon per line
    lines = ',\n'.join('\t\t' + json.dumps(row, ensure_ascii=False) for row in rows)
    text = (
        '{\n'
        f'\t"total": {src["total_weight"]},\n'
        f'\t"perSpawn": {src["messages_per_spawn"]},\n'
        f'\t"pokemon": [\n{lines}\n\t]\n'
        '}\n'
    )

    target = SITE / 'public' / 'data' / 'poketwo-spawns.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')
    print(f'lookup: {len(rows)} species -> {target}')


def fetch_sprite(dex):
    target = SPRITE_DIR / f'{dex}.webp'
    if target.exists():
        return 'kept'
    try:
        with urllib.request.urlopen(SPRITE_SOURCE.format(dex=dex), timeout=30) as res:
            data = res.read()
    except OSError:
        return 'missing'
    if not data.startswith(b'\x89PNG'):
        return 'missing'
    save_webp(data, target)
    return 'new'


def export_sprites():
    # local copies, so the lookup tool does not depend on GitHub staying up
    src = json.loads(LOOKUP.read_text(encoding='utf-8'))
    dex_numbers = sorted({p['dex_number'] for p in src['pokemon']})
    SPRITE_DIR.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(fetch_sprite, dex_numbers))

    missing = [dex for dex, result in zip(dex_numbers, results) if result == 'missing']
    print(f"sprites: {results.count('new')} new, {results.count('kept')} kept, {len(missing)} missing {missing[:10]}")


export_notebook()
export_lookup()
export_sprites()
