from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.orm import joinedload


app = Flask(__name__)
# Configurations
app.config['SECRET_KEY'] = 'a_very_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.String(20), nullable=False)
    isbn = db.Column(db.String(20), nullable=True)
    published_date = db.Column(db.Date, nullable=False)
    is_available = db.Column(db.Boolean, default=True)

    borrow_records = db.relationship('BorrowRecord', back_populates='book', cascade="all, delete-orphan")

class BorrowRecord(db.Model):
    __tablename__ = 'borrow_records'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    borrower_name = db.Column(db.String(100), nullable=False)
    borrower_email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=True)

    book = db.relationship('Book', back_populates='borrow_records')

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Librarian(db.Model):
    __tablename__ = 'librarians'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
with app.app_context():
    db.create_all()
    # Seed data if empty
    if not Book.query.first():
        books_to_seed = [
            Book(title="The Great Gatsby", author="F. Scott Fitzgerald", rating="4.5", isbn="978-0743273565", published_date=datetime(1925, 4, 10).date(), is_available=True),
            Book(title="To Kill a Mockingbird", author="Harper Lee", rating="4.8", isbn="978-0060935467", published_date=datetime(1960, 7, 11).date(), is_available=True),
            Book(title="1984", author="George Orwell", rating="4.7", isbn="978-0451524935", published_date=datetime(1949, 6, 8).date(), is_available=True),
            Book(title="Pride and Prejudice", author="Jane Austen", rating="4.6", isbn="978-1503290563", published_date=datetime(1813, 1, 28).date(), is_available=True)
        ]
        db.session.add_all(books_to_seed)
        db.session.commit()

    if not Student.query.first():
        students_to_seed = [Student(name=f"Student {i+1}") for i in range(6)]
        db.session.add_all(students_to_seed)
        db.session.commit()

    if not Librarian.query.first():
        librarians_to_seed = [Librarian(name=f"Librarian {i+1}") for i in range(5)]
        db.session.add_all(librarians_to_seed)
        db.session.commit()

    if not BorrowRecord.query.first() and Book.query.first():
        book_to_borrow = Book.query.first()
        book_to_borrow.is_available = False
        borrow_record = BorrowRecord(
            book_id=book_to_borrow.id,
            borrower_name="Student 1",
            borrower_email="student1@example.com",
            phone="1234567890"
        )
        db.session.add(borrow_record)
        db.session.commit()

# ----------- Routes ------------- #

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/Contact')
def contact():
    return render_template('contact.html')

@app.route('/About')
def about():
    return render_template('about.html')

@app.route('/Dashboard')
def dashboard():
    total_books = Book.query.count()
    total_students = Student.query.count()
    total_librarians = Librarian.query.count()
    total_borrow_records = BorrowRecord.query.count()
    return render_template('dashboard.html', total_books=total_books, total_students=total_students, total_librarians=total_librarians, total_borrow_records=total_borrow_records)

@app.route('/Login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/Logout')
def logout():
    return redirect(url_for('login'))

@app.route('/Books')
@app.route('/Books/Index')
def index():
    books = Book.query.options(joinedload(Book.borrow_records)).all()
    return render_template('index.html', books=books)

@app.route('/Books/Details/<int:id>')
def details(id):
    book = Book.query.get(id)
    if not book:
        flash(f'No book found with ID {id}.', 'danger')
        return render_template('not_found.html')
    return render_template('details.html', book=book)

@app.route('/Books/Create', methods=['GET', 'POST'])
def create_book():
    if request.method == 'POST':
        title = request.form['Title']
        author = request.form['Author']
        rating = request.form['Rating']
        published_date_str = request.form['PublishedDate']
        try:
            published_date = datetime.strptime(published_date_str, '%Y-%m-%d').date()
            new_book = Book(title=title, author=author, rating=rating, published_date=published_date)
            db.session.add(new_book)
            db.session.commit()
            flash(f'Successfully added the book: {title}.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash('An error occurred while adding the book.', 'danger')
    return render_template('create.html')

@app.route('/Books/Edit/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    book = Book.query.get(id)
    if not book:
        flash(f'No book found with ID {id} for editing.', 'danger')
        return render_template('not_found.html')

    if request.method == 'POST':
        book.title = request.form['Title']
        book.author = request.form['Author']
        book.rating = request.form['Rating']
        published_date_str = request.form['PublishedDate']
        try:
            book.published_date = datetime.strptime(published_date_str, '%Y-%m-%d').date()
            db.session.commit()
            flash(f'Successfully updated the book: {book.title}.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash('An error occurred while updating the book.', 'danger')
    
    return render_template('edit.html', book=book)

@app.route('/Books/Delete/<int:id>', methods=['GET', 'POST'])
def delete_book(id):
    book = Book.query.get(id)
    if not book:
        flash(f'No book found with ID {id} for deletion.', 'danger')
        return render_template('not_found.html')

    if request.method == 'POST':
        try:
            db.session.delete(book)
            db.session.commit()
            flash(f'Successfully deleted the book: {book.title}.', 'success')
            return redirect(url_for('index'))
        except:
            flash('An error occurred while deleting the book.', 'danger')
            
    return render_template('delete.html', book=book)

@app.route('/Borrow/Create/<int:bookId>', methods=['GET', 'POST'])
def borrow_create(bookId):
    book = Book.query.get(bookId)
    if not book:
        flash(f'No book found with ID {bookId} to borrow.', 'danger')
        return render_template('not_found.html')
    if not book.is_available:
        flash(f"The book '{book.title}' is currently not available for borrowing.", 'danger')
        return render_template('not_available.html')

    if request.method == 'POST':
        borrower_name = request.form['BorrowerName']
        borrower_email = request.form['BorrowerEmail']
        phone = request.form['Phone']
        
        record = BorrowRecord(book_id=book.id, borrower_name=borrower_name, borrower_email=borrower_email, phone=phone)
        book.is_available = False
        db.session.add(record)
        db.session.commit()
        flash(f'Successfully borrowed the book: {book.title}.', 'success')
        return redirect(url_for('index'))

    return render_template('borrow.html', book=book)

@app.route('/Borrow/Return/<int:borrowRecordId>', methods=['GET', 'POST'])
def borrow_return(borrowRecordId):
    record = BorrowRecord.query.get(borrowRecordId)
    if not record:
        flash(f'No borrow record found with ID {borrowRecordId} to return.', 'danger')
        return render_template('not_found.html')
    if record.return_date:
        flash(f"The borrow record for '{record.book.title}' has already been returned.", 'danger')
        return render_template('already_returned.html')

    if request.method == 'POST':
        record.return_date = datetime.utcnow()
        record.book.is_available = True
        db.session.commit()
        flash(f'Successfully returned the book: {record.book.title}.', 'success')
        return redirect(url_for('index'))
    
    return render_template('return.html', record=record)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
