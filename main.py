import requests
import requests_cache
from bs4 import BeautifulSoup
import subprocess
import json
import tempfile
import os

# Krok 1: Pobierz stronę
link = 'https://www.olx.pl/motoryzacja/q-samochody-osobowe/'
text = requests.get(link).text
soup = BeautifulSoup(text, 'html.parser')

# Krok 2: Znajdź skrypt zawierający "regionName"
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
    result = subprocess.run(['bun', js_filename], capture_output=True, text=True, check=True, encoding='UTF-8')
    json_output = result.stdout.strip()
    data = json.loads(json_output)
finally:
    os.remove(js_filename)

for key in data.keys():
    try:
        if isinstance(data[key], str):
            data[key] = json.loads(data[key])
    except:
        ...

with open('out.json', 'w', encoding='UTF-8') as plik:
    print(json.dumps(data['__PRERENDERED_STATE__']['listing']['listing']['ads'], indent=2), file=plik)
