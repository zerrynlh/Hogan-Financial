from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from helpers import login_required, lookup, usd

# Configure application
app = Flask(__name__, static_url_path='/static')

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET"])
@login_required
def index():
    user_portf = db.execute("SELECT * FROM user_portfolio WHERE user_id = ?", session["user_id"])

    usergreeting = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]

    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]

    #List to store dictionaries
    show_portfolio = []

    if len(user_portf) > 0:
        for data in user_portf:

            queried = lookup(data["stock_symbol"])
            thesymbol = queried["symbol"]

            #Selects number of shares user currently owns of the stock
            theshares = db.execute("SELECT share_numbers FROM user_portfolio WHERE stock_symbol = ? AND user_id = ?", thesymbol, session["user_id"])[0]['share_numbers']

            #Updates price in real time with lookup query
            theprice = round(queried["price"], 2)

            #Updates total value of each stock in real time with lookup query
            thevalue = round(theshares * theprice, 2)

            stock_dict = {}
            stock_dict["thesymbol"] = thesymbol
            stock_dict["theshares"] = theshares
            stock_dict["theprice"] = theprice
            stock_dict["thevalue"] = thevalue

            #Inserts updated values of the stock price and total value into the user's portfolio
            db.execute("UPDATE user_portfolio SET stock_price = ? WHERE user_id = ? and stock_symbol = ?", theprice, session["user_id"], thesymbol)

            show_portfolio.append(stock_dict)

    #Variable to store total value of stocks
    stocks_value = 0

    #Loops through values in list of dictionaries show_portfolio to total stock value
    if len(show_portfolio) > 0:
        for values in show_portfolio:
            stocks_value += values["thevalue"]

    #Sums total of user's cash and stock value
    grand_total = round(cash + stocks_value, 2)

    return render_template("index.html", theportfolio = show_portfolio, cash = cash, stocks_value = stocks_value, grand_total = grand_total, usergreeting = usergreeting)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
  if request.method == "GET":
    return render_template("buy.html")

  elif request.method == "POST":

        #Stores name of stock
        buy_stock = request.form.get("symbol")

        if not buy_stock or buy_stock.isnumeric():
            flash("Enter a valid stock.")
            return redirect("/buy")
        buy_stock = buy_stock.upper()

        quoted = lookup(buy_stock)
        if quoted is None:
            flash("Stock was not found.")
            return redirect("/buy")

        #Stores number of shares
        num_shares = request.form.get("shares")
        if not num_shares or not num_shares.isdigit():
            flash("Enter a valid number of stocks.")
            return redirect("/buy")
        num_shares = int(num_shares)
        if num_shares < 1:
            flash("Enter a valid number of stocks.")
            return redirect("/buy")

        #Rounds stock price to hundredths place value
        stock_price = round(quoted["price"], 2)

        #Determines price of purchase by multiplying number of shares by stock price, rounded to hundredths place value
        purchase_price = round(stock_price * num_shares, 2)

        db.execute("BEGIN TRANSACTION;")

        #Gets logged in users cash balance and rounds to to hundredths place value
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
        cash = round(cash, 2)

        #Checks if user has enough cash
        if cash < purchase_price:
            flash("Insufficient funds for purchase.")
            return redirect("/buy")

        #Subtracts purchase price from users cash balance
        cash = cash - purchase_price
        cash = round(cash, 2)

        #Gets logged in user's username to store in history table
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]

        current_time = datetime.datetime.now()
        current_time = current_time.time()

        db.execute("INSERT INTO history (user_name, user_id, method, stock_symbol, stock_price, share_numbers, transact_date, transact_time, total_value) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", username, session["user_id"], 'BUY', quoted["symbol"], stock_price, num_shares, datetime.date.today(), current_time, purchase_price)

        #Updates user's cash balance
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash, session["user_id"])

        portfolio_rows = db.execute("SELECT stock_symbol FROM user_portfolio WHERE user_id = ?", session["user_id"])

        #Checks is user does not have a portfolio and performs the first insertion of data
        if len(portfolio_rows) == 0:
            db.execute("INSERT INTO user_portfolio (user_id, stock_symbol, stock_price, share_numbers, total_value) VALUES (?, ?, ?, ?, ?)", session["user_id"], buy_stock, stock_price, num_shares, purchase_price)

        elif len(portfolio_rows) > 0:

            #Creates list of user's stock names to loop through
            stock_list = []
            for sym in portfolio_rows:
                stock_name = sym["stock_symbol"]
                stock_list.append(stock_name)

            #Checks if the stock exist in a particular row and then updates the price, share numbers and total value
            if buy_stock in stock_list:

                #Updates price of stock in real time before selling
                db.execute("UPDATE user_portfolio SET stock_price = ? WHERE stock_symbol = ? AND user_id = ?", stock_price, buy_stock, session["user_id"])

                #Adds new shares to the user's current shares
                current_shares = db.execute("SELECT share_numbers FROM user_portfolio WHERE stock_symbol = ? AND user_id = ?", buy_stock, session["user_id"])[0]["share_numbers"]
                new_shares = current_shares + num_shares
                db.execute("UPDATE user_portfolio SET share_numbers = ? WHERE stock_symbol = ? AND user_id = ?", new_shares, buy_stock, session["user_id"])

                #Adds stock value of purchase to the user's current stock value
                current_value = db.execute("SELECT total_value FROM user_portfolio WHERE stock_symbol = ? AND user_id = ?", buy_stock, session["user_id"])[0]["total_value"]
                current_value = round(current_value, 2)
                new_value = round(current_value + purchase_price, 2)
                db.execute("UPDATE user_portfolio SET total_value = ? WHERE stock_symbol = ? AND user_id = ?", new_value, buy_stock, session["user_id"])
            else:
                #Satisfies condition where length of portfolio list is not 0 and the stock also does not already exist in the user's portfolio
                db.execute("INSERT INTO user_portfolio (user_id, stock_symbol, stock_price, share_numbers, total_value) VALUES (?, ?, ?, ?, ?)", session["user_id"], buy_stock, stock_price, num_shares, purchase_price)

        db.execute("COMMIT;")

        return redirect("/")

@app.route("/history", methods=["GET"])
@login_required
def history():
    rows = db.execute("SELECT * FROM history WHERE user_id = ? ORDER BY transact_date DESC, transact_time DESC", session["user_id"])
    return render_template("history.html", thehistory = rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    try:
        if session["user_id"]:
            session.clear()
    except KeyError:
        pass

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Username was not provided.")
            return redirect("/login")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Password was not provided.")
            return redirect("/login")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username and/or password.")
            return redirect("/login")

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
    if request.method == "GET":
        return render_template("quote.html")

    elif request.method == "POST":
        get_stock = request.form.get("symbol")

        if not get_stock or get_stock.isnumeric():
            flash("Enter a valid stock.")
            return redirect("/quote")

        #Stores stock in dictionary
        quoted = lookup(get_stock)

        #Checks if dictionary returned is empty or not
        if quoted is None:
            flash("Stock not found.")
            return redirect("/quote")
        else:
            return render_template("quoted.html", thequotes=quoted)



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    elif request.method == "POST":

        created_username = request.form.get("username")

        if not created_username:
            flash("Username was not provided.")
            return redirect("/register")

        created_password = request.form.get("password")
        if not created_password:
            flash("Password was not provided.")
            return redirect("/register")

        confirmed_password = request.form.get("confirmation")
        if not confirmed_password:
            flash("Confirmation of password was not provided.")
            return redirect("/register")

        if created_password != confirmed_password:
            flash("Passwords must match.")
            return redirect("/register")

        #Checks if username exists in database by querying SQL table using the name from the form
        user_check = db.execute("SELECT username FROM users WHERE username = ?", created_username)
        print(user_check)

        db.execute("BEGIN TRANSACTION;")

        if len(user_check) != 0:
            flash("Username is already taken.")
            return redirect("/register")

        hashed_password = generate_password_hash(created_password, method='pbkdf2', salt_length=16)

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", created_username, hashed_password)
        db.execute("COMMIT;")
        flash("Account was successfully created!")
        return redirect("/login")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():

    get_stocks = db.execute("SELECT stock_symbol FROM user_portfolio WHERE user_id = ?", session["user_id"])

    owned_stocks = []
    if len(get_stocks) > 0:
        for data in get_stocks:
            this_stock = data["stock_symbol"]
            owned_stocks.append(this_stock)

    if request.method == "GET":
        return render_template("sell.html", ownedstocks = owned_stocks)

    elif request.method == "POST":

        #Stores name of stock
        sell_stock = request.form.get("symbol")
        if not sell_stock or sell_stock.isnumeric():
            flash("Enter a valid stock.")
            return redirect("/sell")
        sell_stock = sell_stock.upper()

        #Checks if stock is valid
        quoted = lookup(sell_stock)
        if quoted is None:
            flash("Stock was not found.")
            return redirect("/sell")

        #Stores number of shares
        num_shares = request.form.get("shares")
        if not num_shares or not num_shares.isdigit():
            flash("Enter a valid number of shares.")
            return redirect("/sell")
        num_shares = int(num_shares)
        if num_shares < 1:
            flash("Enter a valid number of shares.")
            return redirect("/sell")

        db.execute("BEGIN TRANSACTION;")

        #Checks if user owns the stock
        users_stocks = db.execute("SELECT stock_symbol FROM user_portfolio WHERE stock_symbol = ? AND user_id = ?", sell_stock, session["user_id"])
        if len(users_stocks) == 0:
            flash("You don't own this stock.")
            return redirect("/sell")

        #Selects number of shares user currently owns of the stock
        user_shares = db.execute("SELECT share_numbers FROM user_portfolio WHERE stock_symbol = ? AND user_id = ?", sell_stock, session["user_id"])[0]["share_numbers"]

        if num_shares > user_shares:
            flash("You don't own enough shares of this stock.")
            return redirect("/sell")

        current_price = quoted["price"]

        current_cash = db.execute("SELECT cash FROM users where id = ?", session["user_id"])[0]["cash"]

        #Ensures that the user's stock's most recent value is updated before subtracting values
        update_portf_value = round(current_price * user_shares, 2)

        #Calculates price of sale using current price
        sale_price = round(current_price * num_shares, 2)

        #Stores new total value of stock to be inserted
        new_value = round(update_portf_value - sale_price, 2)

        #Stores new number of shares user owns of the stock
        new_shares = user_shares - num_shares

        #Calculates users new amount of cash based on the sale price
        new_cash = round(current_cash + sale_price, 2)

        #Updates dates new number of shares the user owns, the new stock price and total value
        db.execute("UPDATE user_portfolio SET stock_price = ? WHERE stock_symbol = ? AND user_id = ?", current_price, sell_stock, session["user_id"])
        db.execute("UPDATE user_portfolio SET share_numbers = ? WHERE stock_symbol = ? AND user_id = ?", new_shares, sell_stock, session["user_id"])
        db.execute("UPDATE user_portfolio SET total_value = ? WHERE stock_symbol = ? AND user_id = ?", new_value, sell_stock, session["user_id"])
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, session["user_id"])

        #Gets logged in user's username to store in history table
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]

        current_time = datetime.datetime.now()
        current_time = current_time.time()

        db.execute("INSERT INTO history (user_name, user_id, method, stock_symbol, stock_price, share_numbers, transact_date, transact_time, total_value) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", username, session["user_id"], 'SELL', sell_stock, current_price, num_shares, datetime.date.today(), current_time, sale_price)

        if new_shares == 0:
            db.execute("DELETE FROM user_portfolio WHERE stock_symbol = ? AND user_id = ?", sell_stock, session["user_id"])

        db.execute("COMMIT;")

        return redirect("/")

if __name__ == "__main__":
    app.run()