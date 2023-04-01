from pathlib import PurePosixPath
from urllib.parse import urlparse, quote

import requests
from pathvalidate import sanitize_filename

from web_requests import get_response


def download_txt(book_id: str, file_name: str, url: str, books_dir: str, ) -> str:
    """Скачивает текст"""
    response: requests.Response = get_response(url)
    clear_file_name = sanitize_filename(file_name)
    book_path = f'{PurePosixPath(books_dir, book_id)}. {clear_file_name}.txt'
    quote_book_path = quote(book_path, encoding='utf-8')

    with open(quote_book_path, 'wb') as file:
        file.write(response.content)

    return quote_book_path

def download_image(url: str, dir_name: str) -> str:
    """Скачивает картинку книги"""
    response = get_response(url)
    file_name = urlparse(url).path.split('/')[-1]
    img_src = str(PurePosixPath(dir_name, file_name))
    with open(img_src, 'wb') as file:
        file.write(response.content)

    return img_src


# parsing-online-library/dest_folder/books/18973.%20%D0%90%20%D0%B2%D0%B4%D1%80%D1%83%D0%B3.txt
# parsing-online-library\dest_folder\books\18973.%20%D0%90%20%D0%B2%D0%B4%D1%80%D1%83%D0%B3.txt
