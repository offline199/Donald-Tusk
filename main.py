import requests
from bs4 import BeautifulSoup
import subprocess
import json
import tempfile
import os

page = 1

DATA = []

for page in range(1, 15):
    link = f'https://www.olx.pl/oferty/q-iphone/?page={page}'
    text = requests.get(link).text
    soup = BeautifulSoup(text, 'html.parser')

    script_content = None
    for t in soup.select('script'):
        if 'regionName' in repr(t):
            script_content = t.text
            break

    if not script_content:
        raise ValueError("Nie znaleziono odpowiedniego skryptu")

    js_code = f"""
    var window = {{}};
    {script_content}
    ;console.log(JSON.stringify(window));
    """

    with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.js', encoding='UTF-8') as js_file:
        js_file.write(js_code)
        js_filename = js_file.name

    try:
        result = subprocess.run(['bun', js_filename], capture_output=True, check=True)
        json_output = result.stdout.decode('utf-8', errors='replace').strip()
        data = json.loads(json_output)
    finally:
        os.remove(js_filename)

    for key in data.keys():
        try:
            if isinstance(data[key], str):
                data[key] = json.loads(data[key])
        except:
            ...

    DATA.extend(data['__PRERENDERED_STATE__']['listing']['listing']['ads'])
    print(f'{page=}')

with open('out.json', 'w', encoding='UTF-8') as plik:
    print(json.dumps(DATA, indent=2), file=plik)
