import re
import os
import json
from flask import Flask, jsonify, request
from datetime import datetime
from models.book import Book
from models.fiction import Fiction
from models.non_fiction import NonFiction


app = Flask(__name__)

"""
Comment/revision:

# Class should be in separate file: /
# bulk deletion: /
# decorators for the url endpoint: /
# save it to a database or json file
"""

def read_file():
    FILE_PATH = "books.json"

    if not os.path.exists(FILE_PATH):
        return []
    try:
        with open(FILE_PATH, "r") as file:
            data = json.load(file)  # Load JSON as a list of dictionaries
            print(f"Data loaded from file: {data}")


            books = []
            for book_data in data:
                print(f"Processing book: {book_data}")
                book_type = book_data.pop("type", "book").lower()

                if book_type == "fiction":
                    books.append(Fiction(**book_data))
                elif book_type in ["nonfiction", "non-fiction"]:
                    books.append(NonFiction(**book_data))
                else:
                    books.append(Book(**book_data))
                print(f"Books currently in file: {books}")
            return books
        
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {FILE_PATH}")
        return []  # Return empty list if JSON is invalid
    except Exception as e:
        print(f"Error reading books from file: {e}")
        return []

def save_to_file(books):
    try:
        with open("books.json", "w") as file:
             # Convert books list to a list of dictionaries and write to file
            json.dump([book.to_dict() for book in books], file, indent=4)
    except Exception as e:
        print(f"Error saving books to file: {e}")

# Reusable function to validate book data
def validate_data(data, exclude_id=None):
    
    required_fields = {
        "title": str,
        "author": str,
        "isbn": int,
        "published_date": str,
    }

    isbn = data.get("isbn")
    published_date = data.get("published_date")
    book_type = data.get("type", "book").lower()

    # Check for missing fields and type mismatch
    for field, field_type in required_fields.items():
        if field not in data:
            return False, f"Missing field: {field}"

        if not isinstance(data[field], field_type):
           return False, f"Invalid type for field '{field}'."

    # ISBN validation
    if not isinstance(isbn, int) or len(str(isbn)) != 13:
        return False, "Invalid ISBN. It must be 13-digits number."
    
    # Date validation
    try:
        datetime.strptime(published_date, "%B %d, %Y")
    except ValueError:
        return False, "Invalid date format for 'published_date'. Use 'Month Day, Year' (e.g., 'December 18, 2024)."
    
    # Check for duplicates based on book type
    is_valid, error = check_duplicates(isbn, book_type, exclude_id)

    if not is_valid:
        return False, error

    return True, ""

# Reusable function for checking duplicates in Normal Book, Fiction and Non-Fiction
def check_duplicates(isbn, book_type, exclude_id=None):
    books = read_file()

    for book in books:
        # Skip the current book if updating
        if exclude_id and book.book_id == exclude_id:
            continue

        if isinstance(book, Book) and book.isbn == isbn and not isinstance(book, (Fiction, NonFiction)):
            return False, "A Book with this ISBN already exists!"
        
        if isinstance(book, Fiction) and book_type == "fiction" and book.isbn == isbn:
            return False, "A Fiction book with this ISBN already exists!"
        
        if isinstance(book, NonFiction) and book_type == "nonfiction" and book.isbn == isbn:
            return False, "A Non-Fiction book with this ISBN already exsists!"
        
    return True, ""

# Reusable function for finding book
def find_book(book_id):
    books = read_file()
    for book in books:
        print(f"Checking book with ID: {book.book_id}")
        if book.book_id == book_id:
            return book
    return None

# Routes implementation
@app.route("/")
def home():
    return "Welcome to the Library Systems"

# Get all books
@app.route("/view_books", methods=['GET'])
def get_books_list():
    # acess books.json file
    books = read_file()
    
    if not books:
        return jsonify({"error": "No books found in the library"}), 404

    return jsonify([book.to_dict() for book in books]), 200

# Get a specific book by title
@app.route("/search_book/<title>", methods=['GET'])
def get_book(title):
    books = read_file()

    title = str(title)
    print(f"Received search term: '{title}'")

    title = re.sub(r'\s+', ' ', title).strip()

    # Check if the title is empty or just contains whitespace
    if not title:
        return jsonify({"error": "Search term cannot be empty or just spaces."}), 400
    
    # find book with case-sensitive
    matching_books = [book.to_dict() for book in books if title.lower() in book.title.lower()]
    
    # If no books match, return an error
    if not matching_books:
        return jsonify({"error": "Book not found"}), 404

    # Return the list of matching books
    return jsonify({"books": matching_books, "success": "Books found successfully!"}), 200  

# Add a book
@app.route('/add_book', methods=['POST'])
def create_book():
    data = request.json
    books = read_file()
    
    is_valid, error = validate_data(data)

    if not is_valid:
        return jsonify({"error": error}), 400
    
    book_type = data.get("type", "book").lower()

    if book_type == "fiction":
        new_book = Fiction(
            book_id = len(books) + 1,
            title = data['title'],
            author = data['author'],
            isbn = data['isbn'],
            published_date = data['published_date'],
            genre = data.get('genre', "Unknown")
    ) 
    elif book_type == "nonfiction" or book_type == "non-fiction":
        new_book = NonFiction(
            book_id = len(books) + 1,
            title = data['title'],
            author = data['author'],
            isbn = data['isbn'],
            published_date = data['published_date'],
            subject = data.get('subject', "Unknown")
        )
    else:
        new_book = Book(
            book_id = len(books) + 1,
            title = data['title'],
            author = data['author'],
            isbn = data['isbn'],
            published_date = data['published_date']
            )

    books.append(new_book)
    # Save updated book list to file
    save_to_file(books)
    return jsonify({"book": new_book.to_dict(), "message": "Book added successfully!"}), 201

# Update a book
@app.route("/update_book/<book_id>", methods=['PUT'])
def update_book(book_id):
    books = read_file()
    data = request.json
    book_type = data.get("type")

    # explicit validation for book id
    if not book_id.isdigit():
        return jsonify({"error": "Invalid id. book id must be an int, not a string"}), 400
    else:
        book_id = int(book_id)
        book = find_book(book_id)

        if not book:
            return jsonify({"error": "Book not found!"}), 404
        
        # Check for duplicated title and isbn, but excluding the current book id being updated
        is_valid, error = validate_data(data, exclude_id=book_id)
        if not is_valid:
            return jsonify({"error": error}), 400
       
        # Update mutable attributes
        book.title = data.get("title", book.title)
        book.author = data.get("author", book.author)
        book.published_date = data.get("published_date", book.published_date)
        book.isbn = data.get("isbn", book.isbn)

        book_type = data.get("type")
        if book_type:
            if book_type.lower() == "fiction" and not isinstance(book, Fiction):
                # Convert book to Fiction
                book = Fiction(
                    book_id=book.book_id,
                    title=book.title,
                    author=book.author,
                    isbn=book.isbn,
                    published_date=book.published_date,
                    genre=data.get("genre", "Unknown")
                )
            elif book_type.lower() in ["nonfiction", "non-fiction"] and not isinstance(book, NonFiction):
                # Convert book to NonFiction
                book = NonFiction(
                    book_id=book.book_id,
                    title=book.title,
                    author=book.author,
                    isbn=book.isbn,
                    published_date=book.published_date,
                    subject=data.get("subject", "Unknown")
                )
            elif book_type.lower() not in ["fiction", "nonfiction", "non-fiction"]:
                return jsonify({"error": "Invalid type specified!"}), 400
        
        # Conditional check for additional attributes
        if isinstance(book, Fiction):
            book.genre = data.get("genre", book.genre)
        elif isinstance(book, NonFiction):
            book.subject = data.get("subject", book.subject)

        # Replace the old book with the updated one
        books = [b for b in books if b.book_id != book_id]
        books.append(book)
        # Save updated book list to file
        save_to_file(books)
        return jsonify({"message": "Book update successfully!", "book": book.to_dict()}), 200

# Delete a book
@app.route("/delete_book/<book_id>", methods=['DELETE'])
def delete_book(book_id):
    books = read_file()

    # explicit validation for book id
    if not book_id.isdigit():
        return jsonify({"error": "Invalid id. book id must be an int, not a string"}), 400
    else:
        book_id = int(book_id)
        
        book_to_delete = None
        for book in books:
            if book.book_id == book_id:
                book_to_delete = book
                break

        if not book_to_delete:
            return jsonify({"error": "Book not found!"}), 404

        books.remove(book_to_delete)
        # Save updated book list to file
        save_to_file(books)
        return jsonify({"book": book_to_delete.to_dict(), "success": "Book deleted successfully!"}), 200
        

    
# Bulk delete books
@app.route("/delete_books", methods=["DELETE"])
def bulk_delete_books():
    data = request.json
    books = read_file()
    print(f"Books loaded from file: {books}")
    books_deleted = 0

    book_ids = data.get("book_ids", [])

    if not book_ids:
        return jsonify({"error": "No book ids provided"}), 400
    
    # Iterate through book_ids and delete the books
    for book_id in book_ids:
        book = find_book(book_id)
        if book:
            # Create a new list except to the book ids to be deleted
            books = [b for b in books if b.book_id != book_id]
            books_deleted += 1
    # Save updated book list to file
    save_to_file(books)

    if books_deleted == 0:
        return jsonify({"error": "No books were deleted. Check if the book is existing or book IDs are valid."}), 400

    return jsonify({"success": f"{books_deleted} book/s were successfully deleted."}), 200

if __name__ == '__main__':
    app.run(debug=True)
