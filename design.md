Design Document

Our project code is based off of the distribution code from problem set 7 (CS50 Finance), and
an open source HTML style from Bootstrap. Our code can be decomposed into two main parts:
application.py, our main function code written in Python, and our HTML templates for our various
webpages.

We decided to base our project off of the distribution code from C$50 Finance due to
the similar nature of the two projects. Both are centered around database information (we also
used SQLite to create and store our databases), and rely on user input from HTML forms to
populate these databases. Each page has essentially one functionality: either to pull information
from the database based on certain characteristics of the user and display it; or to hold a form
into which the user can enter information into the database.

The design of our file application.py is such that each function correlating to an HTML page is
defined as an app route and goes through the necessary steps to extract any information from that
page's form and display it in a rendered HTML template. The HTML pages extend the layout taken
from the Bootstrap template, as well as that utilized in CS50 finance.

