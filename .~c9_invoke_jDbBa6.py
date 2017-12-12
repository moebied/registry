from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///registry.db")

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    return render_template("home.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # ensure that a symbol is inputted
        if not request.form.get("symbol"):
            return apology("Please enter a valid symbol")
        # ensure the symbol entered is valid
        if not lookup(request.form.get("symbol")):
            return apology("Please enter a valid symbol")

        # ensure a number of shares is inputted
        if not request.form.get("shares"):
            return apology("Please enter the number of shares you would like to buy")

        if int(request.form.get("shares")) < 1:
            return apology("Please enter a positive integer number of shares")

        # initialize variables to ensure enough available credit
        stock = lookup(request.form.get("symbol"))
        cost = stock["price"] * int(request.form.get("shares"))
        credit = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])

        # check that user has enough money available
        if cost > credit[0]["cash"]:
            return apology("You do not have enough cash to make this purchase.")

        # otherwise update the transactions table to reflect current transaction
        else:
            buy = "buy"
            # record the stocks purchased in the user's transaction history
            db.execute("INSERT INTO transactions (symbol,price,shares,id,Type) VALUES(:symbol,:price,:shares,:id,:Type)",
                        symbol=request.form.get("symbol").upper(), price=stock["price"], shares=int(request.form.get("shares")),
                        id=session["user_id"], Type = "buy")

            # subtract the cost of the transaction from available cash
            db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash = credit[0]["cash"] - cost, id=session["user_id"])

        # select previous shares
        past_shares = db.execute("SELECT * FROM portfolio WHERE id = :id AND symbol = :symbol", id=session["user_id"], symbol = stock["symbol"].upper())

        # if no past shares exist, create new row in the portfolio table
        if not past_shares:
            db.execute("INSERT INTO portfolio (symbol, name, shares, price, id, TOTAL) VALUES (:symbol, :name, :shares, :price, :id, :TOTAL)",
                    symbol=request.form.get("symbol").upper(), name=stock["name"],
                    shares=int(request.form.get("shares")), price=stock["price"], id=session["user_id"], TOTAL=cost)

        # else if there is an existing entry with the stock price, just update total and number of shares
        else:
            db.execute("UPDATE portfolio SET TOTAL = :TOTAL WHERE id = :id AND symbol = :symbol", TOTAL=past_shares[0]["TOTAL"]
            + cost, id=session["user_id"], symbol=request.form.get("symbol").upper())
            db.execute("UPDATE portfolio SET shares = :shares WHERE id = :id AND symbol = :symbol", shares=past_shares[0]["shares"]
            + int(request.form.get("shares")), id=session["user_id"], symbol=request.form.get("symbol").upper())

        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # create an array to hold the relevant values from the transactions table
    history = db.execute(
        "SELECT symbol, price, shares, id, time, Type FROM transactions WHERE id = :id", id=session["user_id"])

    # loop over the array, parsing the necessary values
    for value in history:
        stock = lookup(value["symbol"])
        price = value["price"]
        shares = value["shares"]
        time = value["time"]
        Type = value["Type"]

    # return history page
    return render_template("history.html", history=history)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        # if no symbol is inputted return an apology
        if not request.form.get("symbol"):
            return apology("Please input a valid stock symbol")

        # if an invalid symbol is inputted return an apology
        if not lookup(request.form.get("symbol")):
            return apology("Please input a valid stock symbol")

        # return the stock quote
        return render_template("quoted.html", stock=lookup(request.form.get("symbol")))

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Send user to relevant Register pages"""

    if request.method == "POST":
        user=request.form.get("usertype")
        if user=="physician":
            return redirect("phyregister")
        elif user=="hospital":
            return redirect("hosregister")
        elif user=="industry":
            return redirect("indregister")

    else:
        return render_template("register.html")

@app.route("/phyregister", methods=["GET", "POST"])
def phyregister():
    """Physician Register page"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password")

        # Ensure confirm password was submitted
        if not request.form.get("confirmation"):
            return apology("Please confirm password")

        # check to make sure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match")


        password = request.form.get("password")
        encrypted_pass = generate_password_hash(password)

        # Insert username into the database
        result = db.execute("INSERT INTO users (usertype,username,hash) VALUES(:usertype,:username,:hash)",
                                usertype="physician", username=request.form.get("username"), hash=encrypted_pass)

        # If username already exists return apology
        if not result:
            return apology("Username already taken")
        # Remember which user has logged in
        session["user_id"] = result

        # Redirect user to login page
        return redirect("login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("phyregister.html")

@app.route("/hosregister", methods=["GET", "POST"])
def hosregister():
    """Hospital Register page"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Ensure confirm password was submitted
        elif not request.form.get("confirmation"):
            return apology("Please confirm password")

        # check to make sure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match")

        else:
            password = request.form.get("password")
            encrypted_pass = generate_password_hash(password)

            # Insert username into the database
            result = db.execute("INSERT INTO users (usertype,username,hash) VALUES(:usertype, :username, :hash)",
                                usertype="hosptial", username=request.form.get("username"), hash=encrypted_pass)
            # If username already exists return apology
            if not result:
                return apology("Username already taken")
            # Remember which user has logged in
            session["user_id"] = result

            # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("hosregister.html")


@app.route("/indregister", methods=["GET", "POST"])
def indregister():
    """Hospital Register page"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Ensure confirm password was submitted
        elif not request.form.get("confirmation"):
            return apology("Please confirm password")

        # check to make sure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match")

        else:
            password = request.form.get("password")
            encrypted_pass = generate_password_hash(password)

            # Insert username into the database
            result = db.execute("INSERT INTO users (usertype,username,hash) VALUES(:usertype,:username, :hash)",
                                usertype="company", username=request.form.get("username"), hash=encrypted_pass)
            # If username already exists return apology
            if not result:
                return apology("Username already taken")
            # Remember which user has logged in
            session["user_id"] = result

            # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("indregister.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        # check to ensure a stock symbol is inputted
        if not request.form.get("symbol"):
            return apology("please provide a symbol")

        # ensure user actually owns shares they are trying to sell
        if not lookup(request.form.get("symbol")):
            return apology("please provide a valid symbol")
        # ensure a number of shares is inputted
        if not request.form.get("shares"):
            return apology("Please enter the number of shares you would like to sell")

        # ensure a positive integer is inputted
        if (int(request.form.get("shares")) < 1):
            return apology("Please enter a positive integer number of shares")

        stock = lookup(request.form.get("symbol"))
        purchased = db.execute("SELECT * FROM portfolio WHERE id = :id AND symbol = :symbol",
                                id=session["user_id"], symbol=stock["symbol"].upper())

        # ensure user has enough of the desired stock to sell
        if purchased[0]["shares"] < int(request.form.get("shares")):
            return apology("Please enter a valid number of shares to sell")

        sale_value = stock["price"] * int(request.form.get("shares"))

        # increase cash available by the sale value
        user_cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        db.execute("UPDATE 'users' SET cash = :cash WHERE id = :id",
                    cash=user_cash[0]["cash"] + sale_value, id=session["user_id"])

        # update portfolio to reflect sale
        db.execute("UPDATE portfolio SET shares = :shares WHERE id = :id AND symbol = :symbol", shares=purchased[0]["shares"] - int(
            request.form.get("shares")), id=session["user_id"], symbol=request.form.get("symbol").upper())
        db.execute("UPDATE portfolio SET TOTAL = :TOTAL WHERE id = :id AND symbol = :symbol",
                    TOTAL=purchased[0]["TOTAL"] - sale_value, id=session["user_id"], symbol=request.form.get("symbol").upper())

        # update transactions table
        db.execute("INSERT INTO transactions (symbol,price,shares,id,type) VALUES(:symbol,:price,:shares,:id,:type)",
                    symbol=request.form.get("symbol").upper(), price=sale_value,
                    shares=int(request.form.get("shares")), id=session["user_id"], type="sell")

        return redirect("/")

    else:
        return render_template("sell.html")



# function to allow users to deposit more cash
@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    if request.method == "POST":

        # check to make sure the user inputs some value
        if not request.form.get("amount"):
            return apology("please input the desired deposit amount")

        # check to ensure the user inputs a valid deposit amount
        if (int(request.form.get("amount"))) < 1:
            return apology("please input a positive deposit amount")

        # initialize variables and access database to add cash
        deposit = int(request.form.get("amount"))
        database_cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        current_cash = database_cash[0]["cash"]

        # add deposit to currently available cash
        db.execute("UPDATE users SET cash = :cash WHERE id = :id",
                    cash=current_cash + deposit, id=session["user_id"])

        # redirect to index page
        return redirect("/")

    else:
        return render_template("deposit.html")


@app.route("/home", methods=["GET", "POST"])
def home():
    """Home screen"""
    return render_template("home.html")



def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
