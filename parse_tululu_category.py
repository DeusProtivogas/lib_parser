import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import urlparse
from pathlib import Path
from pathvalidate import sanitize_filename


def check_for_redirect(response):
    # if response.history:
    #     raise requests.HTTPError
    pass

def get_soup(url):
    # print("SOUP ", url)
    response = requests.get(url)
    response.raise_for_status()
    # print(response.history)
    check_for_redirect(response)
    # print("Soup", response)

    soup = BeautifulSoup(response.text, 'lxml')
    # print(soup)
    return soup


def get_title_and_author(soup):
    # print(soup)
    # print(soup.find(id= "content"))
    tag = soup.find('body').find('h1')
    # print("TAG ",tag)
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


def parse_book_page(soup, url):
    print(url)
    title, author = get_title_and_author(soup)
    return {
        "title": title,
        "author": author,
        "comments": get_comments(soup),
        "genres": get_genres(soup),
        "image": get_image(soup, url),
    }


def download_txt(url, filename, params, folder='books/'):
    response = requests.get(url, params)
    print(response)
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


# def get_comments(soup):
#     tags = soup.find_all('div', class_='texts')
#     return [tag.find('span', class_="black").text for tag in tags]
#
#
# def get_genres(soup):
#     tags = soup.find('span', class_='d_book').find_all('a')
#     return [tag.text for tag in tags]


def main():
    url_book = "https://tululu.org/b"
    url_all_books_template = "https://tululu.org/l55/"
    url_txt_template = "https://tululu.org/txt.php"
    # https://tululu.org/txt.php?id=b239
    # https: // tululu.org / txt.php?id = 239

    books = []
    books_short_info = []
    last_page = 1
    for page in range(1, last_page + 1):
        soup = get_soup(urljoin(url_all_books_template, str(page)))
        books.extend( soup.find_all('table', class_='d_book') )

    for count, book in enumerate(books):
        try:
            # print(book)
            book_id = book.find('a')['href'].strip('/').strip('b')
            params = {
                "id": book_id,
            }
            # url = f"{url_template}{book_id}/"
            url = f"{url_book}{book_id}"
            # print("NOT SOUP ", url_book)
            soup = get_soup(url,)
            # print(soup)
            print("TEST")
            book = parse_book_page(soup, url)

            title, author = book["title"], book["author"]
            image = book["image"]
            book_path = download_txt(url_txt_template, title, params)
            img_path = download_image(image, book_id,)
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
        if count >= 5:
            break
    print(books_short_info)

    # books_short_info_json = json.dump(books_short_info, ensure_ascii=False).encode('utf8')

    with open("books_short_info.json", "w", encoding='utf8') as my_file:
        json.dump(books_short_info, my_file, ensure_ascii=False)

    # print(len(books))


if __name__ == "__main__":
    main()
