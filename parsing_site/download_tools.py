from pathlib import PurePosixPath
from urllib.parse import urlparse

import requests
from pathvalidate import sanitize_filename
from transliterate import slugify

from web_requests import get_response


def download_txt(book_id: str, file_name: str, url: str, books_dir: str, ) -> str:
    """Скачивает текст"""
    response: requests.Response = get_response(url)
    clear_file_name = slugify(sanitize_filename(file_name))
    book_path = f'{PurePosixPath(books_dir, book_id)}.{clear_file_name}.txt'

    with open(book_path, 'wb') as file:
        file.write(response.content)

    return book_path


def download_image(url: str, dir_name: str) -> str:
    """Скачивает картинку книги"""
    response = get_response(url)
    file_name = urlparse(url).path.split('/')[-1]
    img_src = str(PurePosixPath(dir_name, file_name))
    with open(img_src, 'wb') as file:
        file.write(response.content)

    return img_src
