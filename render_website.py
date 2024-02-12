import os
import json

from http.server import HTTPServer, SimpleHTTPRequestHandler
from livereload import Server, shell
from more_itertools import chunked

from jinja2 import Environment, FileSystemLoader, select_autoescape

def on_reload():
    dest_folder = "temp_folder"
    with open(os.path.join(dest_folder, "books.json"), "r", encoding='utf8') as file:
        # print(file)
        books_json = file.read()

    books = json.loads(books_json)

    for book in books:
        replace_slash(book)

    books = list(chunked(books, 2))
    # print(books)

    template = env.get_template('index_template.html')
    rendered_page = template.render(
        books=books,
    )

    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)

def replace_slash(book):
    book["img_src"] = book["img_src"].replace("\\", "/")
    book["book_path"] = book["book_path"].replace("\\", "/")

env = Environment(
    loader=FileSystemLoader('.'),
    autoescape=select_autoescape(['html', 'xml'])
)
#
# dest_folder = "temp_folder"
# with open(os.path.join(dest_folder, "books.json"), "r", encoding='utf8') as file:
#     # print(file)
#     books_json = file.read()
#
# books = json.loads(books_json)
#
# for book in books:
#     replace_slash(book)
#
# template = env.get_template('index_template.html')
# rendered_page = template.render(
#     books=books,
# )
#
# with open('index.html', 'w', encoding="utf8") as file:
#     file.write(rendered_page)

on_reload()

server = Server()
server.watch('index_template.html', on_reload)
server.serve(root='.')

