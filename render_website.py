import os
import json
import argparse

from livereload import Server
from more_itertools import chunked
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def prepare_parser():
    parser = argparse.ArgumentParser(description="Запустить библиотеку")
    parser.add_argument(
        "--dest_folder",
        help="Путь к каталогу с библиотекой",
        default="library"
    )
    parser.add_argument(
        "--library_file",
        help="Путь к файлу с информацией о книгах",
        default="books.json"
    )
    return parser


def on_reload():
    env = Environment(
        loader=FileSystemLoader("."),
        autoescape=select_autoescape(["html", "xml"])
    )

    args = prepare_parser().parse_args()
    dest_folder = args.dest_folder
    library_file = args.library_file
    with open(
            os.path.join(dest_folder, library_file), "r", encoding="utf8"
    ) as file:
        # books = json.loads(file.read())
        books = json.load(file)

    for book in books:
        replace_slash(book)

    books_on_page = 10
    books_in_row = 2
    books = list(chunked(list(chunked(books, books_in_row)), books_on_page))

    template = env.get_template("index_template.html")
    pages_number = range(1, len(books) + 1)

    for counter, books_portion in enumerate(books, 1):
        rendered_page = template.render(
            books=books_portion,
            pages=pages_number,
            current_page=counter,
            dest_folder=dest_folder,
        )

        Path(os.path.join("pages")).mkdir(parents=True, exist_ok=True)
        with open(os.path.join(
                "pages", f"index{counter}.html"
        ), "w", encoding="utf8") as file:
            file.write(rendered_page)


def replace_slash(book):
    book["img_src"] = os.path.join(
        "..", book["img_src"]
    ).replace("\\", "/")
    book["book_path"] = os.path.join(
        "..", book["book_path"]
    ).replace("\\", "/")


def main():

    on_reload()

    server = Server()
    server.watch("index_template.html", on_reload)
    server.serve(root=".")


if __name__ == "__main__":
    main()
