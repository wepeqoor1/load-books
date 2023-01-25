import requests as requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

from pathlib import Path


def check_for_redirect(response: requests.Response) -> None:
    """Проверяет ссылки на редирект"""
    response_url = response.url
    if response_url == 'https://tululu.org/' or response.history:
        raise requests.HTTPError()


def download_txt(book_id: int, file_name: str, url: str, dir_name: str = 'books/',) -> None:
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    clear_file_name = sanitize_filename(file_name)

    with open(f'{dir_name}/{book_id}. {clear_file_name}.txt', 'wb') as file:
        file.write(response.content)


def create_directory(name: str) -> None:
    Path(name).mkdir(parents=True, exist_ok=True)


def parsing_page(url: str):
    response = requests.get(url)
    response.raise_for_status()
    page_html = BeautifulSoup(response.text, 'lxml')
    if book_title := page_html.find('h1'):
        return [book.strip() for book in book_title.text.split('::')]
    raise ValueError


def main():
    dir_name = 'books'
    create_directory(dir_name)

    for book_id in range(1, 10):
        url = f'https://tululu.org/b{book_id}/'
        try:
            title, author = parsing_page(url)
        except ValueError:
            continue

        try:
            download_txt(book_id, title, url, dir_name)
        except requests.HTTPError:
            continue


if __name__ == '__main__':
    main()
