from models.book import Book

class Fiction(Book):
    def __init__(self, book_id, title, author, isbn, published_date, genre):
        super().__init__(book_id, title, author, isbn, published_date)
        self.genre = genre

    def to_dict(self):
        data = super().to_dict()
        data["genre"] = self.genre
        data["type"] = "fiction"
        return data