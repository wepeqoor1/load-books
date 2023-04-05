import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Iterator, NamedTuple

import more_itertools
from jinja2 import Environment, FileSystemLoader, select_autoescape

PAGES_DIR = 'docs'


class PageName(NamedTuple):
    previous: str | None
    current: str
    next: str | None


def get_nearby_pages(pages: list) -> Iterator:
    """
    Генерирует список страниц для пагинации
    """
    for idx, page in enumerate(pages):
        if idx == 0:
            yield PageName(None, page, pages[idx + 1])
        elif idx == len(pages) - 1:
            yield PageName(pages[idx - 1], page, None)
        else:
            yield PageName(pages[idx - 1], page, pages[idx + 1])


env = Environment(
    loader=FileSystemLoader('.'),
    autoescape=select_autoescape(['html', 'xml'])
)
template = env.get_template('template.html')

with open('dest_folder/Научная фантастика.json', 'r', encoding='utf-8') as read_file:
    books_content = list(more_itertools.chunked(json.load(read_file), 2))
    books_content_chunked = list(more_itertools.chunked(books_content, 10))

Path(PAGES_DIR).mkdir(parents=True, exist_ok=True)

pagination_pages_name = list(
    get_nearby_pages(
        [
            'index.html' if idx_page == 0 else f'index{idx_page}.html'
            for idx_page, _ in enumerate(books_content_chunked)
        ]
    )
)

for page_content, PageName in zip(books_content_chunked, pagination_pages_name):
    rendered_page = template.render({
        'books_content': page_content,
        'pages_path': pagination_pages_name,
        'current_page_file_name': PageName.current,
        'previous_page_path': PageName.previous,
        'next_page_path': PageName.next
    })
    with open(Path(PAGES_DIR, PageName.current), 'w', encoding='utf8') as file:
        file.write(rendered_page)

server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
