import os
import sys
import time
import json
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import urlparse
from pathlib import Path
from pathvalidate import sanitize_filename

from parse_tululu_ids import check_for_redirect
from parse_tululu_ids import parse_book_page


def get_soup(url):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')
    return soup


def get_title_and_author(soup):
    selector = "body h1"
    tag = soup.select_one(selector)
    title, author = map(str.strip, tag.text.split("::"))
    return title, author


def get_comments(soup):
    selector = "div.texts span.black"
    return [tag.text for tag in soup.select(selector)]


def get_genres(soup):
    selector = "span.d_book a"
    return [tag.text for tag in soup.select(selector)]


def get_image(soup, base_url):
    selector = "div.bookimage"
    tag = soup.select_one(selector)
    if tag:
        return urljoin(base_url, tag.select_one("img")['src'])


def download_txt(url, filename, params, dest_folder, folder='books/'):
    response = requests.get(url, params)
    response.raise_for_status()
    check_for_redirect(response)

    Path(f"{dest_folder}/{folder}").mkdir(parents=True, exist_ok=True)
    name = f'{params["id"]}. {sanitize_filename(filename)}.txt'
    path = os.path.join(dest_folder, folder, name)
    with open(path, 'wb') as file:
        file.write(response.content)
    return path


def download_image(url, filename, dest_folder, folder='covers/'):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    Path(f"{dest_folder}/{folder}").mkdir(parents=True, exist_ok=True)
    name = f'{filename}.{urlparse(url).path.split(".")[-1]}'
    path = os.path.join(dest_folder, folder, name)
    with open(path, 'wb') as file:
        file.write(response.content)
    return path


def main():
    parser = argparse.ArgumentParser(description="Скачать книги и обложки")
    parser.add_argument(
        '--skip_imgs',
        help='Не скачивать картинки (по умолчанию = False)',
        action='store_true'
    )
    parser.add_argument(
        '--skip_txt',
        help='Не скачивать текста (по умолчанию = False)',
        action='store_true'
    )
    parser.add_argument(
        '--dest_folder',
        help='Путь к каталогу с результатами',
        default="./"
    )
    parser.add_argument(
        '--start_page',
        help='Начальная страница (по умолчанию = 1)',
        type=int,
        default=1
    )
    parser.add_argument(
        '--end_page',
        help='Конечная страница (по умолчанию - пока не закончатся страницы)',
        type=int,
        default=sys.maxsize
    )
    args = parser.parse_args()

    book_url = "https://tululu.org/b"
    all_books_url_template = "https://tululu.org/l55/"
    txt_url_template = "https://tululu.org/txt.php"

    information_about_books = []
    first_reconnection = True
    dest_folder = args.dest_folder
    skip_imgs = bool(args.skip_imgs)
    skip_txt = bool(args.skip_txt)
    print(skip_txt)
    print(skip_imgs)
    start_page = args.start_page
    last_page = args.end_page
    for page in range(start_page, last_page + 1):
        try:
            soup = get_soup(urljoin(all_books_url_template, str(page)))
            books = soup.select("table.d_book")
            if not books:
                print(f"Ran out of pages")
                break

            for count, book in enumerate(books):
                try:
                    book_id = book.select_one('a')['href'].strip('/').strip('b')
                    params = {
                        "id": book_id,
                    }
                    url = f"{book_url}{book_id}"
                    soup = get_soup(url,)
                    book = parse_book_page(soup, url)

                    title, author = book["title"], book["author"]
                    image = book["image"]
                    book_path = None
                    if not skip_txt:
                        book_path = download_txt(txt_url_template, title, params, dest_folder)
                    img_path = None
                    if not skip_imgs:
                        img_path = download_image(image, book_id, dest_folder)
                    information_about_books.append({
                        "title": title,
                        "author": author,
                        "img_src": img_path,
                        "book_path": book_path,
                        "comments": get_comments(soup),
                        "genres": get_genres(soup),
                    })
                except requests.HTTPError:
                    print(f"Book with id {book_id} not found")

                except (requests.ConnectionError, requests.Timeout):
                    print("Connection has been interrupted, restarting...")
                    if first_reconnection:
                        first_reconnection = False
                        time.sleep(1)
                        continue
                    time.sleep(3)
        except (requests.ConnectionError, requests.Timeout):
            print("Connection has been interrupted, restarting...")
            if first_reconnection:
                first_reconnection = False
                time.sleep(1)
                continue
            time.sleep(3)
        except requests.HTTPError:
            print(f"Ran out of pages")
            break

    with open(os.path.join(dest_folder, "information_about_books.json"), "w+", encoding='utf8') as f:
        json.dump(information_about_books, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
