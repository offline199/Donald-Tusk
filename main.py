import requests
from bs4 import BeautifulSoup

link = 'https://www.olx.pl/motoryzacja/q-samochody-osobowe/'

text = requests.get(link).text

soup = BeautifulSoup(text, 'html.parser')

print(soup)
