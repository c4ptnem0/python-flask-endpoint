from models.book import Book

class NonFiction(Book):
    def __init__(self, book_id, title, author, isbn, published_date, subject):
        super().__init__(book_id, title, author, isbn, published_date)
        self.subject = subject

    def to_dict(self):
        data = super().to_dict()
        data["subject"] = self.subject
        data["type"] = "nonfiction"
        return data