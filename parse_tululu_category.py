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
from parse_tululu_ids import get_soup
from parse_tululu_ids import download_txt
from parse_tululu_ids import download_image
from parse_tululu_ids import get_comments
from parse_tululu_ids import get_genres
from parse_tululu_ids import get_image
from parse_tululu_ids import get_title_and_author


def get_book(book, book_url, txt_url_template, dest_folder, skip_txt, skip_imgs):
    book_id = book.select_one('a')['href'].strip('/').strip('b')
    params = {
        "id": book_id,
    }
    url = f"{book_url}{book_id}"
    soup = get_soup(url, )
    book = parse_book_page(soup, url)

    title, author = book["title"], book["author"]
    image = book["image"]
    book_path = None
    if not skip_txt:
        book_path = download_txt(txt_url_template, title, params, dest_folder)
    img_path = None
    if not skip_imgs:
        img_path = download_image(image, book_id, dest_folder)
    return {
        "title": title,
        "author": author,
        "img_src": img_path,
        "book_path": book_path,
        "comments": book["comments"],
        "genres": book["genres"],
    }

def prepare_parser():
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
    return parser


def main():
    args = prepare_parser().parse_args()

    book_url = "https://tululu.org/b"
    all_books_url_template = "https://tululu.org/l55/"
    txt_url_template = "https://tululu.org/txt.php"

    books = []
    first_reconnection = True
    dest_folder = args.dest_folder
    skip_imgs = args.skip_imgs
    skip_txt = args.skip_txt
    start_page = args.start_page
    last_page = args.end_page
    for page in range(start_page, last_page + 1):
        try:
            soup = get_soup(urljoin(all_books_url_template, str(page)))
            books_on_page = soup.select("table.d_book")
            if not books_on_page:
                print(f"Ran out of pages")
                break

            for count, book in enumerate(books_on_page):
                try:
                    books.append(
                        get_book(
                            book,
                            book_url,
                            txt_url_template,
                            dest_folder,
                            skip_txt,
                            skip_imgs
                        )
                    )
                except requests.HTTPError:
                    print(f"Book {book.select_one('a')['href'].strip('/').strip('b')} not found")

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

    with open(os.path.join(dest_folder, "books.json"), "w+", encoding='utf8') as f:
        json.dump(books, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
