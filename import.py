import csv
import os

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


# Create table for books
db.execute('''CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                isbn VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                author VARCHAR NOT NULL,
                year VARCHAR(7) NOT NULL)''')

# Create table for users
db.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR NOT NULL, password VARCHAR(255) NOT NULL)")

# Create table for reviews
db.execute('''CREATE TABLE IF NOT EXISTS reviews (
                id SERIAL PRIMARY KEY,
                review TEXT,
                rating INTEGER NOT NULL,
                book_id INTEGER REFERENCES books NOT NULL,
                user_id INTEGER REFERENCES users NOT NULL)''')

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn,title,author,year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Added {isbn} - {title} - {author} - {year}")
    db.commit()

if __name__ == "__main__":
    with app.app_context():
        main()
