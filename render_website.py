import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Iterator

import more_itertools
from jinja2 import Environment, FileSystemLoader, select_autoescape

PAGES_DIR = 'docs'

def get_nearby_pages(pages: list) -> Iterator:
    """
    Генерирует список страниц для пагинации
    """
    for idx, page in enumerate(pages):
        if idx == 0:
            yield None, page, pages[idx + 1]
        elif idx == len(pages) - 1:
            yield pages[idx - 1], page, None
        else:
            yield pages[idx - 1], page,  pages[idx + 1]


env = Environment(
    loader=FileSystemLoader('.'),
    autoescape=select_autoescape(['html', 'xml'])
)
template = env.get_template('template.html')

with open('dest_folder/Научная фантастика.json', 'r', encoding='utf-8') as read_file:
    books_content = list(more_itertools.chunked(json.load(read_file), 2))
    books_content_chunked = list(more_itertools.chunked(books_content, 10))

Path(PAGES_DIR).mkdir(parents=True, exist_ok=True)

pages_path = list(get_nearby_pages([f'index{idx_page + 1}.html' for idx_page, _ in enumerate(books_content_chunked)]))

for idx_page, (page_content, page_path) in enumerate(zip(books_content_chunked, pages_path)):
    current_page_file_name = f'index{idx_page + 1}.html'
    previous_page_path: str = page_path[0]
    current_page_path: str = page_path[1]
    next_page_path: str = page_path[2]

    rendered_page = template.render({
        'books_content': page_content,
        'pages_path': pages_path,
        'current_page_file_name': current_page_file_name,
        'previous_page_path': previous_page_path,
        'next_page_path': next_page_path
    })
    with open(Path(PAGES_DIR, current_page_path), 'w', encoding='utf8') as file:
        file.write(rendered_page)

server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
