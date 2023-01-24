import requests as requests

from pathlib import Path


def check_for_redirect(response: requests.Response) -> None:
    response_url = response.url
    print(response_url)
    if response_url == 'https://tululu.org/' or response.history:
        raise requests.HTTPError()


def download_book(book_name: str, dir_name: str,  url: str) -> None:
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    with open(f'{dir_name}/{book_name}.txt', 'wb') as file:
        file.write(response.content)


def create_directory(name: str) -> None:
    Path(name).mkdir(parents=True, exist_ok=True)


def main():
    dir_name = 'books'
    create_directory(dir_name)

    for book_id in range(1, 10):
        url = f'https://tululu.org/txt.php?id={book_id}/'
        try:
            download_book(str(book_id), dir_name, url)
        except requests.HTTPError:
            continue


if __name__ == '__main__':
    main()
