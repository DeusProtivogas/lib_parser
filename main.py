import os
import time
import requests
import argparse
from bs4 import BeautifulSoup
from pathlib import Path
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
from urllib.parse import urlparse


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def get_soup(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    soup = BeautifulSoup(response.text, 'lxml')
    return soup


def get_title_and_author(soup):
    tag = soup.find('body').find('h1')
    title, author = map(str.strip, tag.text.split("::"))
    return title, author


def get_comments(soup):
    tags = soup.find_all('div', class_='texts')
    return [tag.find('span', class_="black").text for tag in tags]


def get_genres(soup):
    tags = soup.find('span', class_='d_book').find_all('a')
    return [tag.text for tag in tags]


def get_image(soup, base_url):
    tag = soup.find('div', class_='bookimage')
    if tag:
        return urljoin(base_url, tag.find("img")['src'])


def download_txt(url, filename, params, folder='books/'):
    response = requests.get(url, params)
    response.raise_for_status()
    check_for_redirect(response)

    Path(f"./{folder}").mkdir(parents=True, exist_ok=True)
    name = f'{params["id"]}. {sanitize_filename(filename)}.txt'
    path = os.path.join(folder, name)
    with open(path, 'wb') as file:
        file.write(response.content)
    return path


def download_image(url, filename, folder='covers/'):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    Path(f"./{folder}").mkdir(parents=True, exist_ok=True)
    name = f'{filename}.{urlparse(url).path.split(".")[-1]}'
    path = os.path.join(folder, name)
    with open(path, 'wb') as file:
        file.write(response.content)
    return path


def parse_book_page(soup, url):
    title, author = get_title_and_author(soup)
    return {
        "title": title,
        "author": author,
        "comments": get_comments(soup),
        "genres": get_genres(soup),
        "image": get_image(soup, url),
    }


def main():
    parser = argparse.ArgumentParser(description="Скачать книги и обложки")
    parser.add_argument(
        '--start_id',
        help='Начальный индекс (по умолчанию = 1)',
        default=1
    )
    parser.add_argument(
        '--end_id',
        help='Конечный индекс (по умолчанию = 10)',
        default=10
    )
    args = parser.parse_args()

    url_txt_template = "https://tululu.org/txt.php"
    url_template = "https://tululu.org/b"

    first_reconnection = True
    book_id = int(args.start_id)
    last_id = int(args.end_id)
    while book_id <= last_id:
        try:
            params = {
                "id": book_id,
            }
            url = f"{url_template}{book_id}/"
            soup = get_soup(url,)
            book = parse_book_page(soup, url)

            # {
            #     "title": title,
            #     "author": author,
            #     "comments": get_comments(soup),
            #     "genres": get_genres(soup),
            #     "image": get_image(soup, url),
            # }

            title, author = book["title"], book["author"] # get_title_and_author(soup)
            image = book["image"] # get_image(soup, url)
            download_txt(url_txt_template, title, params)
            download_image(image, book_id,)
            book_id += 1
        except requests.HTTPError:
            print(f"Book with id {book_id} not found")
            book_id += 1
        except (requests.ConnectionError, requests.Timeout):
            print("Connection has been interrupted, restarting...")
            if first_reconnection:
                first_reconnection = False
                time.sleep(1)
                continue
            time.sleep(3)


if __name__ == "__main__":
    main()
