# Project 1
https://youtu.be/259eEiwYo-I

Web Programming with Python and JavaScript
Marek Janda
2019

@ app route "/"
At first page (index.html) the user can see title and two buttons "Log in" and "Register" which will redirect him or her to login or register page respectively

@ app route "/register"
At register page (register.html) the user is asked to input username, password and to confirm password. If the input is correct, username not already existing and passwords are matching, the user is registered and redirected to his or her home page. User data area stored in table "users" and password is hashed using "werkzeug.security" library.

@ app route "/login"
At login page (login.html) the user is asked for username and password. If provided username exists in the database and passowrd hash matches the stored password the user is redirected to his or her home page.

@ app route "/home"
At home page (homepage.html) there is an text input field with submit button and log out button. Via the text input field the user can search for book by filling any combination of characters (numbers included) and the application will query the database and returns a list of all books (from "books" table) containing the looked for combination of characters in either title, author or ISBN. Each item in the list is a link which wil redirect user to book page of selected book. If there is no match in the database for the looked for combination of characters appropriate message is displayed. By clicking the "Log Out" button the user is log out and redirected to first page (app route "/").

@ app route "/book/<book_id>"
At book page ("book_id" is the id of selected book in the database) book.html is rendered. At this page user can see all the book information (title, author, year and ISBN) as well as goodreads average rating, number of ratings and average rating and number of revies from our (project 1's) database. If there are no reviews and ratings yet in the database these values will be 0. After the information user can make his own rating,through star rating input field and write his own review in review input field (textarea). Below the review and rating input all previous ratings and reviews are dispalyed. When user submits his rating and review those are added to the displayed ratings and reviews. Each user can review the one particular book only once. There is log out button on the book page at same location and with the same functionality as at home page.

@ app route "/api/<isbn>"
Book data and average score and number of ratings is available for other people via api. Where isbn is the isbn of the book. The returned json object has structure: {
                        "title": title of the book,
                        "author": books author,
                        "year": year,
                        "isbn": ISBN,
                        "review_count": number of reviews,
                       "average_score": average score
                      }
Python orders the dictionary alphabetically for faster search. If book with such isbn does not exists in the database the application will send and http status code with following json object: {'Sorry': 'Requested book is not in the database'}. To make HTTP response and status code "flask_api" library is used.
