import os
import sys
import json
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import urlparse
from pathlib import Path
from pathvalidate import sanitize_filename


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError
    # pass

def get_soup(url):
    # print("SOUP ", url)
    response = requests.get(url)
    # print(response)
    response.raise_for_status()
    # print(url, response.history)
    # check_for_redirect(response)
    # print("Soup", response)

    soup = BeautifulSoup(response.text, 'lxml')
    # print(soup)
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

def parse_book_page(soup, url):
    # print(url)
    title, author = get_title_and_author(soup)
    return {
        "title": title,
        "author": author,
        "comments": get_comments(soup),
        "genres": get_genres(soup),
        "image": get_image(soup, url),
    }


def download_txt(url, filename, params, dest_folder, folder='books/'):
    response = requests.get(url, params)
    # print(url, params)
    # print(response.content)
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
        default=False
    )
    parser.add_argument(
        '--skip_txt',
        help='Не скачивать текста (по умолчанию = False)',
        default=False
    )
    parser.add_argument(
        '--dest_folder',
        help='Путь к каталогу с результатами (по умолчанию = 1)',
        default="./"
    )
    parser.add_argument(
        '--start_page',
        help='Начальная страница (по умолчанию = 1)',
        default=1
    )
    parser.add_argument(
        '--end_page',
        help='Конечная страница (по умолчанию - пока не закончатся страницы)',
        default=sys.maxsize
    )
    args = parser.parse_args()

    url_book = "https://tululu.org/b"
    url_all_books_template = "https://tululu.org/l55/"
    url_txt_template = "https://tululu.org/txt.php"
    # https://tululu.org/txt.php?id=b239
    # https: // tululu.org / txt.php?id = 239

    books_short_info = []
    # last_page = 1

    # last_page =

    first_reconnection = True
    dest_folder = args.dest_folder
    skip_imgs = bool(args.skip_imgs)
    skip_txt = bool(args.skip_txt)
    start_page = int(args.start_page)
    last_page = int(args.end_page)
    for page in range(start_page, last_page + 1):
        # print(page)
        try:
            # response =
            # print(urljoin(url_all_books_template, str(page)))
            soup = get_soup(urljoin(url_all_books_template, str(page)))
            # print(soup)
            books = soup.select("table.d_book")
            if not books:
                print(f"Ran out of pages")
                break

            for count, book in enumerate(books):
                # print(count)
                try:
                    # print(book)
                    book_id = book.select_one('a')['href'].strip('/').strip('b')
                    params = {
                        "id": book_id,
                    }
                    url = f"{url_book}{book_id}"
                    # print(url)
                    soup = get_soup(url,)
                    # print(soup)
                    book = parse_book_page(soup, url)

                    title, author = book["title"], book["author"]
                    image = book["image"]
                    book_path = None
                    if not skip_txt:
                        book_path = download_txt(url_txt_template, title, params, dest_folder)
                    img_path = None
                    if not skip_imgs:
                        img_path = download_image(image, book_id, dest_folder)
                    books_short_info.append({
                        "title": title,
                        "author": author,
                        "img_src": img_path,
                        "book_path": book_path,
                        "comments": get_comments(soup),
                        "genres": get_genres(soup),
                    })
                    # book_id += 1
                except requests.HTTPError:
                    print(f"Book with id {book_id} not found")
                    # book_id += 1
                # url = f"{url_template}{book_id}/"
                # print(url)
                if count >= 1:
                    break
        except requests.HTTPError:
            print(f"Ran out of pages")
            break

    # books_short_info_json = json.dump(books_short_info, ensure_ascii=False).encode('utf8')



    with open(os.path.join(dest_folder, "books_short_info.json"), "w", encoding='utf8') as my_file:
        json.dump(books_short_info, my_file, ensure_ascii=False)

    # print(len(books))


if __name__ == "__main__":
    main()
