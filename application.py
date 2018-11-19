import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

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
db = SQL("sqlite:///finance.db")


@app.route("/", methods=["GET", "PODT"])
@login_required
def index():
    print(session)
    if request.method == "GET":
        info = db.execute("SELECT * FROM portfolio WHERE id = :dbID", dbID=session["user_id"])



        for item in info:
            rows = lookup(item["Symbol"])
            db.execute("UPDATE portfolio SET Price = :currentPrice WHERE id = :currentID AND Symbol = :currentSymbol", currentSymbol=item["Symbol"], currentPrice=rows["price"] , currentID=session["user_id"] )

        updatedInfo = db.execute("SELECT * FROM portfolio WHERE id = :dbID", dbID=session["user_id"])

        return render_template("index.html", results=updatedInfo)





@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":


        if not request.form.get("symbol") or request.form.get("symbol") =='':
            return apology("Invalid Symbol")

        try:
            shares = int(request.form.get("shares"))
        except:
            return apology("Gimme a whole number", 400)


        if shares <= 0:
            return apology("Need postive number of shares")

        rows = lookup(request.form.get("symbol"))

        if not rows:
            return apology("Invalid ticker symbol", 400)

        price = int(rows["price"])
        cash = int(db.execute("SELECT cash FROM users WHERE id = :Id", Id=session["user_id"])[0]["cash"])
        totalPrice = price * shares


        newCash = cash - totalPrice
        if newCash < 0:
            return apology("Not enough money")

        yes = db.execute("UPDATE users SET cash = :newTotal WHERE id = :ID", ID=session["user_id"], newTotal=newCash)


        if not yes:
            return apology("Could not make transaction")

        updatePortfolio = db.execute("UPDATE portfolio SET Shares = Shares + :newdbshares, Price = :newPrice WHERE id = :ID AND Symbol = :dbsymbol", ID=session["user_id"], newdbshares= shares, newPrice = rows["price"], dbsymbol=rows["symbol"])

        if not updatePortfolio:
            newPortfolioEntry = db.execute("INSERT INTO portfolio (Name, Shares, Price, Symbol, Id) VALUES(:name, :dbshares, :price, :symbol, :dbid)", name=rows["name"], dbshares=shares, price=rows["price"], symbol = rows["symbol"], dbid =session["user_id"])


        db.execute("INSERT INTO histories (Symbol, Shares, Price, Id) VALUES(:symbol, :shares1, :price, :iD)", symbol=rows["symbol"], shares1=shares, price=rows["price"], iD=session["user_id"])


        return render_template("buy.html", results=rows, shares1=shares, newCash=newCash)

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():

    transactions = db.execute("SELECT * FROM histories WHERE Id = :ID", ID = session["user_id"])

    return render_template("history.html", results=transactions)


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
    if request.method == "POST":
        rows = lookup(request.form.get("symbol"))

        if not rows:
            return apology("Error. Invalid ticker", 400)


        return render_template("quote.html", results=rows)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("must confirm password", 400)

        # Query database for username


        result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hashed)", username=request.form.get("username"), hashed=generate_password_hash(request.form.get("password")))
        # if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
        #     return apology("invalid username and/or password", 403)
        if not result:
            return apology("Username already exist")

        # Remember which user has logged in

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    Companies = db.execute("SELECT Symbol FROM portfolio where id = :ID", ID = session["user_id"])
    if request.method =="POST":
       rows = lookup(request.form.get("symbol"))
       dbnumberOfShares = db.execute("SELECT Shares FROM portfolio WHERE id = :ID AND Symbol = :symbol1", symbol1 = request.form.get("symbol"), ID = session["user_id"])
       numberOfShares = request.form.get("shares")

       if int(numberOfShares) <= 0:
           return apology("Must be a positive number")

       if int(numberOfShares) > dbnumberOfShares[0]["Shares"]:
           return apology("You do not own that many shares")

       sell = db.execute("UPDATE portfolio SET Shares = Shares - :sold WHERE id = :ID AND Symbol = :symbol", symbol = request.form.get("symbol"), sold = int(numberOfShares), ID = session["user_id"])
       addmoney = db.execute("UPDATE users SET cash = cash + :newcash WHERE id = :ID", ID=session["user_id"], newcash = (int(numberOfShares)*rows["price"]) )
       db.execute("INSERT INTO histories (Symbol, Shares, Price, Id) VALUES(:symbol, :shares1, :price, :iD)", symbol=rows["symbol"], shares1= 0 - int(numberOfShares), price=rows["price"], iD=session["user_id"])
       newCash = db.execute("SELECT cash FROM users WHERE id = :ID", ID=session["user_id"] )
       return render_template("sell.html", results=Companies, soldPrice=(int(numberOfShares)*rows["price"]), newCash1=newCash[0]["cash"])

    else:
        return render_template("sell.html", results=Companies)



def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
