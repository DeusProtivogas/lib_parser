import os
import json

from http.server import HTTPServer, SimpleHTTPRequestHandler
from livereload import Server, shell
from more_itertools import chunked
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

def on_reload():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    dest_folder = "temp_folder"
    with open(os.path.join(dest_folder, "books.json"), "r", encoding='utf8') as file:
        # print(file)
        books_json = file.read()

    books = json.loads(books_json)

    for book in books:
        replace_slash(book)

    books = list( chunked(list(chunked(books, 2)), 10 ) )
    # print(books)

    template = env.get_template('index_template.html')

    for counter, books_portion in enumerate(books):
        rendered_page = template.render(
            books=books_portion,
        )

        Path(os.path.join("pages")).mkdir(parents=True, exist_ok=True)
        with open(os.path.join("pages", f'index{counter}.html'), 'w', encoding="utf8") as file:
            file.write(rendered_page)


def replace_slash(book):
    book["img_src"] = book["img_src"].replace("\\", "/")
    book["book_path"] = book["book_path"].replace("\\", "/")


def main():

    on_reload()

    server = Server()
    server.watch('index_template.html', on_reload)
    server.serve(root='.')


if __name__ == "__main__":
    main()