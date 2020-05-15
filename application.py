import os

from flask import Flask, session, render_template, jsonify, redirect, request
from flask_session import Session
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from flask_api import status
import requests

app = Flask(__name__)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
Session(app)

@app.route("/")
def index():
    session.clear()
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()
    if request.method == "POST":
        # Check user provided username
        if not request.form.get("username"):
            return render_template("login.html", nousername=True)
        # Check if user provided password
        elif not request.form.get("psw"):
            return render_template("login.html", nopassword=True)
        else:
            username = request.form.get("username")
            psw = request.form.get("psw")
            # Query database for provided username
            user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
            if not user:
                return render_template("login.html", notanuser=True)
            else:
                if not check_password_hash(user["password"], psw):
                    return render_template("login.html", wrongpsw=True)
                else:
                    session["user_id"] = user["id"]
                    return redirect("/homepage")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check if username is provided, if not return boolean to display message
        if not request.form.get("username"):
            return render_template("register.html", nousername=True)
        # Check if password is provided, if not return boolean to display message
        elif not request.form.get("psw"):
            return render_template("register.html", nopassword=True)
        # Check if password confirmation is provided, if not return boolean to display message
        elif not request.form.get("pswcnf"):
            return render_template("register.html", nopasswordconf=True)
        # Check if password and match, if not return boolean to display message
        elif request.form.get("psw") != request.form.get("pswcnf"):
            return render_template("register.html", nomatch=True)
        else:
            # Get all data from form
            username = request.form.get("username")
            psw = request.form.get("psw")
            # Hash password
            password = generate_password_hash(psw)
            taken = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()

            # Check if username is already taken, if yes return boolean to display message
            if taken:
                return render_template("register.html", taken=True)
            else:
                # Insert user into the users table
                db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": username, "password": password})
                db.commit()
                # Remember which user has logged in
                loguser = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
                session["user_id"] = loguser["id"]
                user = loguser["username"]
                # Redirect user to his homepage
                return redirect("homepage/")
    else:
        return render_template("register.html")


@app.route("/homepage/", methods=["GET", "POST"])
def home():
    # if the user is not logged in he will be redirected to the index.html
    try:
        user = db.execute("SELECT * FROM users WHERE id = :logged_id", {"logged_id" : session["user_id"]}).fetchone()
    except KeyError as identifier:
        return render_template("index.html", notlogged=True)
    user = db.execute("SELECT * FROM users WHERE id = :logged_id", {"logged_id" : session["user_id"]}).fetchone()
    if request.method == "POST":
        # Get for input and store in variable 'lookFor'
        query = request.form.get("book")
        # Concatenate strings to match psql 'LIKE' cause syntax
        lookFor = '%' + query + '%'
        # Capitalize first letter to include first character of author's name and title in the query
        lookForCap = '%' + query.capitalize() + '%'
        # check if user provided query to search, if not display a message
        if not lookFor:
            return render_template("homepage.html", noquery=True, user=user)
        else:
            # Query the database, title and author can start with capital letter, therefor the capitalize query ('lookForCap'),
            # In some cases ISBN can contain a capital letter as well
            found = db.execute('''SELECT * FROM books WHERE (isbn LIKE :lookFor)   
                                 OR (isbn LIKE :lookForCap)                            
                                 OR (title LIKE :lookFor)
                                 OR (title LIKE :lookForCap)
                                 OR (author LIKE :lookFor)
                                 OR (author LIKE :lookForCap)
                                 ''',{"lookFor": lookFor, "lookForCap": lookForCap}).fetchall()
            if not found:
                # If nothing in database matches the query display a message
                return render_template("homepage.html", empty=True, user=user)
            else:
                # Else return all book  
                return render_template("homepage.html", user=user, found=found, query=query)
    else:
        return render_template("homepage.html", user=user)


@app.route("/book/<id>", methods=["GET", "POST"])
def mybook(id):
    # If the user is not logged in he will be redirected to the index.html
    try:
        user = db.execute("SELECT * FROM users WHERE id = :logged_id", {"logged_id" : session["user_id"]}).fetchone()
    except KeyError as identifier:
        return render_template("index.html", notlogged=True)
    
    # Get required data from the database
    book = db.execute("SELECT * FROM books WHERE id = :id", {"id": id}).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :id", {"id" : id}).fetchall()
    
    # Get data from goodreads API
    goodreads = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "kC0K5Hsz1hL99geEXGpwQ", "isbns": book.isbn})
    grdata = goodreads.json()

    # Get review count and average rating from the database (not goodreads data)
    review_count = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id" : book["id"]}).fetchall()
    scores = db.execute("SELECT rating FROM reviews WHERE book_id = :book_id", {"book_id" : book["id"]}).fetchall()

    # If there are no reviews in database the review count and average scores are set to 0
    if not review_count:
        review_count = 0
        average_score = 0
    else:
        totalscore = 0
        for score in scores:
            totalscore += score[0]
        review_count = len(reviews)
        average_score = totalscore / review_count

    if request.method == "POST":
        # Get form input
        rating = request.form.get("rate")
        review = request.form.get("review")
        if not rating:
            return render_template("book.html", book=book, grdata=grdata, user=user, reviews=reviews, review_count=review_count, average_score=average_score, notrated=True)
        # Check if user already submitted review for the book
        reviewed = db.execute("SELECT * FROM reviews WHERE user_id = :logged_id AND book_id = :book_id",
                                    {"logged_id" : user["id"], "book_id" : book["id"]}).fetchone()
        if reviewed:
            return render_template("book.html", book=book, grdata=grdata, user=user, reviews=reviews, review_count=review_count, average_score=average_score, reviewed=True, )
        else:
            # INSERT review into the dabase
            db.execute("INSERT INTO reviews (review, rating, book_id, user_id) VALUES (:review, :rating, :book_id, :logged_id)",
                            {"review" : review, "rating" : rating, "book_id" : book["id"], "logged_id" : user["id"]})
            db.commit()
            
            # Get all reviews of the book from databse
            reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id" : book["id"]}).fetchall()
            return render_template("book.html", book=book, grdata=grdata, message='Review submitted', user=user, reviews=reviews, review_count=review_count, average_score=average_score)
    else:
        return render_template("book.html", book=book, grdata=grdata, user=user, reviews=reviews, review_count=review_count, average_score=average_score)


@app.route('/api/<isbn>')
def giveapi(isbn):
    # Query database for requested data
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn" : isbn}).fetchone()
    # If book is None return 404 NOT FOUND
    if not book:
        response = {'Sorry': 'Requested book is not in the database'}
        return jsonify(response), status.HTTP_404_NOT_FOUND
    else:
        review_count = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id" : book["id"]}).fetchall()
        scores = db.execute("SELECT rating FROM reviews WHERE book_id = :book_id", {"book_id" : book["id"]}).fetchall()

    # If there are no reviews in database the review count and average scores are set to 0
    if not review_count:
        review_count = 0
        average_score = 0
    else:
        totalscore = 0
        for score in scores:
            totalscore += score[0]
        review_count = len(review_count)
        average_score = totalscore / review_count
    
    # Compile response dictionary
    response = {
     "title": book["title"],
     "author": book["author"],
     "year": book["year"],
     "isbn": book["isbn"],
     "review_count": review_count,
     "average_score": average_score
     }

    # Return JSON object 
    return jsonify(response)


