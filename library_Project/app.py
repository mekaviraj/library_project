from flask import Flask, render_template, request, redirect, url_for, flash, session
from db_config import mysql
from models import User, Book, BookRequest, IssuedBook
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Import database configuration
from db_config import app

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('Admin access required.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        books = Book.get_available_books()
        return render_template('index.html', books=books)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_user_by_username(username)
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login successful!')
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form['email']
        
        try:
            User.create_user(username, password, email)
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed. Username or email might already exist.')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/add_book', methods=['POST'])
@login_required
@admin_required
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        quantity = int(request.form['quantity'])
        
        try:
            Book.add_book(title, author, isbn, quantity)
            flash('Book added successfully!')
        except Exception as e:
            flash('Error adding book. ISBN might already exist.')
    return redirect(url_for('index'))

@app.route('/delete_book/<int:book_id>')
@login_required
@admin_required
def delete_book(book_id):
    try:
        Book.delete_book(book_id)
        flash('Book deleted successfully!')
    except Exception as e:
        flash('Error deleting book.')
    return redirect(url_for('index'))

@app.route('/request_book/<int:book_id>', methods=['POST'])
@login_required
def request_book(book_id):
    try:
        BookRequest.create_request(session['user_id'], book_id)
        flash('Book request submitted successfully!')
    except Exception as e:
        flash('Error submitting request.')
    return redirect(url_for('index'))

@app.route('/admin/requests')
@login_required
@admin_required
def view_requests():
    requests = BookRequest.get_pending_requests()
    return render_template('admin/requests.html', requests=requests)

@app.route('/admin/approve_request/<int:request_id>')
@login_required
@admin_required
def approve_request(request_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE book_requests SET status = 'approved' 
            WHERE request_id = %s
        """, (request_id,))
        
        cur.execute("""
            SELECT user_id, book_id FROM book_requests 
            WHERE request_id = %s
        """, (request_id,))
        request_data = cur.fetchone()
        
        IssuedBook.issue_book(request_data['user_id'], request_data['book_id'])
        mysql.connection.commit()
        cur.close()
        flash('Request approved and book issued!')
    except Exception as e:
        flash('Error approving request.')
    return redirect(url_for('view_requests'))

if __name__ == '__main__':
    app.run(debug=True) 