import argparse
import json
import requests
from pathlib import Path
from typing import NamedTuple, TypedDict
from urllib.parse import urljoin, urlparse, urlsplit

from bs4 import BeautifulSoup, Tag
from loguru import logger

from download_tools import download_image, download_txt
from parsing_suite.custom_exceptions import NoFoundBookException
from web_requests import get_response


URL_PARAM = 'l55/'  # url параметр на книги с "научной фантастикой"
URL = 'https://tululu.org/'
CATEGORY_NAME = 'Научная фантастика.json'  # Название категории книг


class BookContent(TypedDict, total=False):
    title: str
    author: str
    image_url: str
    comments: list
    genres: list
    book_path: str
    img_src: str
    book_link: str


class ConsoleArgs(NamedTuple):
    start_page: int
    end_page: int
    dest_folder: str
    skip_imgs: bool
    skip_txt:  bool
    json_path: str


def parse_book_page(response: requests.Response) -> dict:
    """Парсит html страницу и возвращает данные о книге"""
    page_html = BeautifulSoup(response.text, 'lxml')
    url = f'https://{urlsplit(response.url).netloc}'

    book_title = page_html.select_one('h1')
    title, author = [book.strip() for book in book_title.text.split('::')]

    image_url_path = page_html.select_one('.bookimage img')['src']
    image_url = urljoin(url, image_url_path)

    tags = page_html.select('.d_book a')
    book_tag: list[Tag | None] = [tag for tag in tags if 'скачать txt' == tag.text]
    if book_tag:
        book_link = urljoin(url, book_tag[0]['href'])
        logger.debug(book_link, colorama='red')
    else:
        raise NoFoundBookException

    comments_html = page_html.select('.texts .black')
    comments = [comment.text for comment in comments_html] if comments_html else None

    genres_html = page_html.select('span.d_book a')
    genres = [genre.text for genre in genres_html] if comments else None

    return BookContent(
        title=title,
        author=author,
        image_url=image_url,
        comments=comments,
        genres=genres,
        book_link=book_link
    )


def get_book_urls(category_page_url: str, url_path: str) -> list:
    response: requests.Response = get_response(category_page_url)
    category_html = BeautifulSoup(response.text, 'lxml')
    book_params = category_html.select('.d_book')
    return [urljoin(url_path, book.find('a').get('href')) for book in book_params]


def get_console_args() -> ConsoleArgs:
    parser = argparse.ArgumentParser(""" \
    Программа предназначена для скачивания книг с сайта 'https://tululu.org'
    """)
    parser.add_argument('--first', type=int, default=1, help='Номер первой страницы')
    parser.add_argument('--last', type=int, default=1000, help='Номер последней страницы')
    parser.add_argument(
        '--dest_folder', type=str, default='dest_folder/',
        help='путь к каталогу с результатами парсинга: картинкам, книгам, JSON.'
    )
    parser.add_argument('--skip_imgs', action='store_true', help='не скачивать картинки')
    parser.add_argument('--skip_txt', action='store_true', help='не скачивать книги')
    parser.add_argument('--json_path', type=str, help='указать свой путь к *.json файлу с результатами')

    args = parser.parse_args()

    return ConsoleArgs(
        start_page=args.first,
        end_page=args.last,
        dest_folder=args.dest_folder,
        skip_imgs=args.skip_imgs,
        skip_txt=args.skip_txt,
        json_path=args.json_path
    )


def create_dirs(dest_folder: str, books_dir: str = 'books', images_dir: str = 'images') -> tuple:
    Path(dest_folder).mkdir(parents=True, exist_ok=True)
    books_dir = Path(dest_folder, books_dir)
    books_dir.mkdir(parents=True, exist_ok=True)
    images_dir = Path(dest_folder, images_dir)
    images_dir.mkdir(parents=True, exist_ok=True)

    return books_dir, images_dir


def init_logger() -> None:
    logger.add('information.log', format='{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}')
    logger.level('BOOK', no=38, color='<yellow>')


def get_books_content(args: ConsoleArgs, books_dir: str, images_dir: str) -> list:
    """Парсим сайт с книгами на одной странице"""
    for num_page in range(args.start_page, args.end_page):

        logger.info(f'---\n{num_page} страница категории \n --- \n')

        category_url = urljoin(URL, URL_PARAM)
        category_page_url = urljoin(category_url, str(num_page))
        try:
            books_urls: list = get_book_urls(category_page_url, URL)
        except requests.HTTPError:
            logger.warning('Не удалось получить ссылки на книги')

        for book_url in books_urls:
            book_id = urlparse(book_url).path.strip('/').strip('b')

            try:
                response = get_response(book_url)
                book_content: BookContent = parse_book_page(response)
                logger.info(f'Информация о книге собрана с адреса {book_url}')
            except requests.HTTPError or ValueError:
                logger.warning(f'На странице {book_url} отсутствует книга. Переходим к следующей.')
                continue
            except NoFoundBookException:
                logger.warning('Ссылка на книгу отсутствует. Переходим к следующей.')
                continue

            if not args.skip_txt:
                try:
                    book_path = download_txt(
                        book_id, book_content['title'], book_content['book_link'], books_dir
                    )
                    book_content['book_path'] = book_path
                    logger.info(f'Книга скачена')
                except requests.HTTPError:
                    logger.info(f'Книга на странице {book_url} на скачена. Текст отсутствует по данному адресу.')
                    continue

            if not args.skip_imgs:
                try:
                    img_src = download_image(book_content['image_url'], images_dir)
                    book_content['img_src'] = img_src
                    logger.info(f'Изображение скачено')
                except requests.HTTPError:
                    logger.info(f'Обложка на странице {book_url} не скачена. Картинка отсутствует по данному адресу.')

            yield book_content


def save_books_content(books_content: list[BookContent], dest_folder: str, json_path: str) -> str:
    category_path = json_path if json_path else Path(dest_folder, CATEGORY_NAME)

    with open(category_path, 'w', encoding='utf-8') as file:
        json.dump(books_content, file, ensure_ascii=False, indent=4)

    return category_path


def main() -> None:
    init_logger()
    args = get_console_args()
    books_dir, images_dir = create_dirs(args.dest_folder)
    books_content = list(get_books_content(args, books_dir, images_dir))
    save_books_content(books_content, args.dest_folder, args.json_path)
    logger.info(f'Данные о книгах записаны в файл')


if __name__ == '__main__':
    main()
