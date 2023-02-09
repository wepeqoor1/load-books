import time

import requests
from loguru import logger


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
