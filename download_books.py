import argparse
import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlsplit

import requests as requests
from bs4 import BeautifulSoup
from loguru import logger
from pathvalidate import sanitize_filename


def check_redirect(response: requests.Response) -> None:
    """Проверяет ссылки на редирект"""
    if response.history:
        raise requests.HTTPError()


def retry_request(func):
    def wrapper(*args, **kwargs):
        reconnect_time = 0.1
        while True:
            try:
                return func(*args, **kwargs)
            except requests.exceptions.ConnectionError:
                time.sleep(reconnect_time)
                reconnect_time *= 2
                logger.warning(f'Потеря соединения. Повторный запрос через {reconnect_time} секунд')

    return wrapper


@retry_request
def get_response(url: str) -> requests.Response:
    response: requests.Response = requests.get(url)
    response.raise_for_status()
    check_redirect(response)
    return response


def download_txt(book_id: str, file_name: str, url: str, dir_name: str = 'books/') -> str:
    """Скачивает текст"""
    response = get_response(url)
    clear_file_name = sanitize_filename(file_name)
    book_path = f'{dir_name}{book_id}. {clear_file_name}.txt'

    with open(book_path, 'wb') as file:
        file.write(response.content)

    return f'{dir_name}{clear_file_name}.txt'


def download_image(url: str, dir_name: str = 'images/') -> str:
    """Скачивает картинку книги"""
    response = get_response(url)

    file_name = urlparse(url).path.split('/')[-1]
    img_src = f'{dir_name}{file_name}'

    with open(img_src, 'wb') as file:
        file.write(response.content)

    return img_src


def parse_book_page(response: requests.Response) -> dict:
    """Парсит html страницу и возвращает данные о книге"""
    page_html = BeautifulSoup(response.text, 'lxml')

    book_title = page_html.select_one('h1')
    title, author = [book.strip() for book in book_title.text.split('::')]

    image_path = page_html.select_one('.bookimage img')['src']
    image_url = urljoin(f'https://{urlsplit(response.url).netloc}', image_path)

    comments_html = page_html.select('.texts .black')
    comments = [comment.text for comment in comments_html] if comments_html else None

    genres_html = page_html.select('span.d_book a')
    genres = [genre.text for genre in genres_html] if comments else None

    return {
        'title': title,
        'author': author,
        'image_url': image_url,
        'comments': comments,
        'genres': genres,
    }


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(""" \
    Программа предназначена для скачивания книг с сайта 'https://tululu.org'
    """)
    parser.add_argument('first', type=int, default=1, help='id первой книги')
    parser.add_argument('last', type=int, default=10, help='id последней книги')

    return parser


def main() -> None:
    logger.add('information.log', format='{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}')
    logger.level('BOOK', no=38, color='<yellow>')

    parser = create_parser()
    args = parser.parse_args()
    category_page_num_from = args.first
    category_page_num_to = args.last

    category_url_param = 'l55/'
    category_name = 'Научная фантастика.json'
    url_path = 'https://tululu.org/'
    category_url = urljoin(url_path, category_url_param)

    Path('books').mkdir(parents=True, exist_ok=True)
    Path('images').mkdir(parents=True, exist_ok=True)

    books_content = []
    for num_page in range(category_page_num_from, category_page_num_to + 1):
        logger.info(f'{num_page} страница категории')
        category_page_url = urljoin(category_url, str(num_page))
        response_category_page: requests.Response = get_response(category_page_url)

        category_html = BeautifulSoup(response_category_page.text, 'lxml')
        book_params = category_html.find_all(class_='d_book')
        books_url = [urljoin(url_path, book.find('a').get('href')) for book in book_params]

        for book_url in books_url:
            print(book_url)
            book_id = urlparse(book_url).path.strip('/').strip('b')

            try:
                response = get_response(book_url)
                book_content = parse_book_page(response)
                logger.info(f'Информация о книге собрана с адреса {book_url}')
            except requests.HTTPError or ValueError:
                logger.warning(f'На странице {book_url} отсутствует книга. Переходим к следующей.')
                continue

            try:
                book_path = download_txt(book_id, book_content['title'], book_url)
                book_content['book_path'] = book_path
                logger.info(f'Книга скачена')
            except requests.HTTPError:
                logger.info(f'Книга на странице {book_url} на скачена. Текст отсутствует по данному адресу.')
                continue

            try:
                img_src = download_image(book_content['image_url'])
                book_content['img_src'] = img_src
                logger.info(f'Изображение скачено')
            except requests.HTTPError:
                logger.info(f'Обложка на странице {book_url} на скачена. Картинка отсутствует по данному адресу.')

            books_content.append(book_content)

    books_content_json = json.dumps(books_content, ensure_ascii=False, indent=4)
    with open(category_name, 'w', encoding='utf-8') as file:
        file.write(books_content_json)
    logger.info(f'Данные о книгах записаны в файл: "{category_name}"')


if __name__ == '__main__':
    main()
