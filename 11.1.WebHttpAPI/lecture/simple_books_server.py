from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4


class BookBase(BaseModel):
    title: str
    author: str
    year: int | None = None

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    year: int | None = None

class Book(BookBase):
    id: str = Field(default_factory=lambda: str(uuid4()))


books: dict[str, Book] = {}


def to_book(id_: str) -> Book:
    if id_ not in books:
        raise HTTPException(status_code=404, detail="Book not found")
    return books[id_]


app = FastAPI(title="Book API Demo")


@app.get("/books")
def list_books() -> list[Book]:
    return list(books.values())


@app.get("/books/{book_id}")
def get_book(book_id: str) -> Book:
    return to_book(book_id)


@app.post("/books", status_code=201)
def create_book(payload: BookCreate) -> Book:
    book = Book(**payload.model_dump())
    books[book.id] = book
    return book


@app.put("/books/{book_id}")
def replace_book(book_id: str, payload: BookCreate) -> Book:
    book = to_book(book_id)
    new_book = Book(id=book_id, **payload.model_dump())
    books[book.id] = new_book
    return new_book


@app.patch("/books/{book_id}")
def update_book(book_id: str, payload: BookUpdate) -> Book:
    book = to_book(book_id)
    update = payload.model_dump(exclude_unset=True)
    updated_book = Book(**(book.model_dump() | update))
    books[book_id] = updated_book
    return updated_book


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: str) -> None:
    book = to_book(book_id)
    del books[book.id]
    return None
