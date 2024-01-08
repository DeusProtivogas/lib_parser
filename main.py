import os
import requests
import argparse
from bs4 import BeautifulSoup
from pathlib import Path
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
from urllib.parse import urlparse


def check_for_redirect(r):
    if r.history:
        raise requests.HTTPError


def get_soup(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        check_for_redirect(response)
    except requests.HTTPError:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    return soup


def get_title_and_author(soup):
    tag = soup.find('body').find('h1')
    title, author = map(str.strip, tag.text.split("::"))
    return title, author


def get_comments(soup):
    tags = soup.find_all('div', class_='texts')
    return [tag.find('span', class_="black").text for tag in tags]


def get_genre(soup):
    tags = soup.find('span', class_='d_book').find_all('a')
    return [tag.text for tag in tags]


def get_image(soup, base_url="https://tululu.org/"):
    tag = soup.find('div', class_='bookimage')
    if tag:
        return urljoin(base_url, tag.find("img")['src'])


def download_txt(url, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """

    try:
        response = requests.get(url)
        response.raise_for_status()
        check_for_redirect(response)
    except requests.HTTPError:
        return

    Path(f"./{folder}").mkdir(parents=True, exist_ok=True)
    name = f'{sanitize_filename(filename)}.txt'
    path = os.path.join(folder, name)
    with open(path, 'wb') as file:
        file.write(response.content)
    return path


def download_image(url, filename, folder='covers/'):
    try:
        response = requests.get(url)
        response.raise_for_status()
        check_for_redirect(response)
    except requests.HTTPError:
        return

    Path(f"./{folder}").mkdir(parents=True, exist_ok=True)
    name = f'{filename}.{urlparse(url).path.split(".")[-1]}'
    path = os.path.join(folder, name)
    with open(path, 'wb') as file:
        file.write(response.content)
    return path


def parse_book_page(soup):
    title, author = get_title_and_author(soup)
    return {
        "title": title,
        "author": author,
        "comments": get_comments(soup),
        "genre": get_genre(soup),
        "image": get_image(soup),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_id', help='Начальный индекс')
    parser.add_argument('--end_id', help='Конечный индекс')
    args = parser.parse_args()

    url_txt_template = "https://tululu.org/txt.php?id="
    url_template = "https://tululu.org/b"
    url_image_source = "https://tululu.org/"

    for id in range(int(args.start_id), int(args.end_id) + 1):
        url = f"{url_template}{id}/"
        url_txt = f"{url_txt_template}{id}"
        soup = get_soup(url)
        if not soup:
            continue
        title, author = get_title_and_author(soup)
        image = get_image(soup, url_image_source)
        download_image(image, id,)
        download_txt(url_txt, title)


if __name__ == "__main__":
    main()
