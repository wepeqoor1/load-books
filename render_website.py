import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import more_itertools
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader('.'),
    autoescape=select_autoescape(['html', 'xml'])
)
template = env.get_template('template.html')

with open('dest_folder/Научная фантастика.json', 'r', encoding='utf-8') as read_file:
    books_content = list(more_itertools.chunked(json.load(read_file), 2))
    books_content = {'books_content': books_content}

rendered_page = template.render(books_content)

with open('index.html', 'w', encoding='utf8') as file:
    file.write(rendered_page)

server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
server.serve_forever()
