import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from loguru import logger

from download_books import (download_image, download_txt, get_response,
                            parse_book_page)


def main():
    url_path = 'https://tululu.org/'
    category_url_param = 'l55/'
    category_name = 'Научная фантастика.txt'
    category_url = urljoin(url_path, category_url_param)
    Path('books').mkdir(parents=True, exist_ok=True)
    Path('images').mkdir(parents=True, exist_ok=True)

    books_content = []
    for num_page in range(1, 2):
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


if __name__ == '__main__':
    main()
