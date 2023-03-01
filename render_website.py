import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import more_itertools
from jinja2 import Environment, FileSystemLoader, select_autoescape

PAGES_DIR = 'pages'

env = Environment(
    loader=FileSystemLoader('.'),
    autoescape=select_autoescape(['html', 'xml'])
)
template = env.get_template('template.html')

with open('dest_folder/Научная фантастика.json', 'r', encoding='utf-8') as read_file:
    books_content = list(more_itertools.chunked(json.load(read_file), 2))
    books_content_chunk = list(more_itertools.chunked(books_content, 10))

Path(PAGES_DIR).mkdir(parents=True, exist_ok=True)

for num, books_content in enumerate(books_content_chunk):
    html_page = f'index{num + 1}.html'
    rendered_page = template.render({'books_content': books_content})
    with open(Path(PAGES_DIR, html_page), 'w', encoding='utf8') as file:
        file.write(rendered_page)

server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
server.serve_forever()
