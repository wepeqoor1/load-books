import argparse
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlsplit

import requests as requests
from bs4 import BeautifulSoup
from loguru import logger
from pathvalidate import sanitize_filename
from tqdm import tqdm


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


def download_txt(book_id: int, file_name: str, url: str, dir_name: str = 'books/') -> None:
    """Скачивает текст"""
    response = get_response(url)
    clear_file_name = sanitize_filename(file_name)

    with open(f'{dir_name}/{book_id}. {clear_file_name}.txt', 'wb') as file:
        file.write(response.content)


def download_image(url: str, dir_name: str = 'images/') -> None:
    """Скачивает картинку книги"""
    response = get_response(url)

    file_name = urlparse(url).path.split('/')[-1]

    with open(f'{dir_name}/{file_name}', 'wb') as file:
        file.write(response.content)


def parse_book_page(response: requests.Response) -> dict:
    """Парсит html страницу и возвращает данные о книге"""
    page_html = BeautifulSoup(response.text, 'lxml')

    book_title = page_html.find('h1')
    title, author = [book.strip() for book in book_title.text.split('::')]

    image_path = page_html.find('div', class_='bookimage').find('img')['src']
    image_url = urljoin(f'https://{urlsplit(response.url).netloc}', image_path)

    comments_html = page_html.find_all('div', class_='texts')
    comments = [comment.find('span', class_='black').text for comment in comments_html] if comments_html else None

    genres_html = page_html.find('span', class_='d_book').find_all('a')
    genres = [genre.text for genre in genres_html] if comments else None

    return {
        'title': title,
        'author': author,
        'image_url': image_url,
        'comments': comments,
        'genre': genres,
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
    book_id_from = args.first
    book_id_last = args.last

    Path('books').mkdir(parents=True, exist_ok=True)
    Path('images').mkdir(parents=True, exist_ok=True)

    for book_id in tqdm(range(book_id_from, book_id_last + 1)):
        logger.log('BOOK', f'Книга с id {book_id}')

        url = f'https://tululu.org/b{book_id}/'
        try:
            response = get_response(url)
            book_content = parse_book_page(response)
            logger.info(f'Информация о книге собрана с адреса {url}')
        except requests.HTTPError or ValueError:
            logger.warning(f'На странице {url} отсутствует книга. Переходим к следующей.')
            continue

        try:
            download_txt(book_id, book_content['title'], url)
            logger.info(f'Книга скачена')
        except requests.HTTPError:
            logger.info(f'Книга на странице {url} на скачена. Текст отсутствует по данному адресу.')

        try:
            download_image(book_content['image_url'])
            logger.info(f'Изображение скачено')
        except requests.HTTPError:
            logger.info(f'Обложка на странице {url} на скачена. Картинка отсутствует по данному адресу.')


if __name__ == '__main__':
    main()
