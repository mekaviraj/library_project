from db_config import mysql
from datetime import datetime

class User:
    @staticmethod
    def create_user(username, password, email, role='user'):
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)",
            (username, password, email, role)
        )
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def get_user_by_username(username):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        return user

class Book:
    @staticmethod
    def add_book(title, author, isbn, quantity=1):
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO books (title, author, isbn, quantity, available) VALUES (%s, %s, %s, %s, %s)",
            (title, author, isbn, quantity, quantity)
        )
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def get_all_books():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM books")
        books = cur.fetchall()
        cur.close()
        return books

    @staticmethod
    def get_available_books():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM books WHERE available > 0")
        books = cur.fetchall()
        cur.close()
        return books

    @staticmethod
    def delete_book(book_id):
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
        mysql.connection.commit()
        cur.close()

class BookRequest:
    @staticmethod
    def create_request(user_id, book_id):
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO book_requests (user_id, book_id) VALUES (%s, %s)",
            (user_id, book_id)
        )
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def get_pending_requests():
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT br.*, b.title, b.author, u.username 
            FROM book_requests br
            JOIN books b ON br.book_id = b.book_id
            JOIN users u ON br.user_id = u.user_id
            WHERE br.status = 'pending'
        """)
        requests = cur.fetchall()
        cur.close()
        return requests

class IssuedBook:
    @staticmethod
    def issue_book(user_id, book_id):
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO issued_books (user_id, book_id) VALUES (%s, %s)",
            (user_id, book_id)
        )
        cur.execute(
            "UPDATE books SET available = available - 1 WHERE book_id = %s",
            (book_id,)
        )
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def return_book(issue_id):
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE issued_books SET status = 'returned', return_date = CURRENT_TIMESTAMP WHERE issue_id = %s",
            (issue_id,)
        )
        cur.execute(
            "UPDATE books b JOIN issued_books ib ON b.book_id = ib.book_id SET b.available = b.available + 1 WHERE ib.issue_id = %s",
            (issue_id,)
        )
        mysql.connection.commit()
        cur.close() 