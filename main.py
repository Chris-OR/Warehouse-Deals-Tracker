import game_checker as gc
import threading
import os
import requests
import time
import smtplib
from flask import Flask, render_template, request
from sqlalchemy import desc
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

PS4_URL = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A7089437011%2Cn%3A6458584011&dc&qid=1613426168&rnid=8929975011&ref=sr_nr_n_2"
PS5_URL = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A20974860011%2Cn%3A20974876011&dc&qid=1614274309&rnid=8929975011&ref=sr_nr_n_2"
SWITCH = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A16329248011%2Cn%3A16329255011&dc&qid=1621288946&rnid=8929975011&ref=sr_nr_n_3"
XBOX_ONE = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A7089610011%2Cn%3A6920196011&dc&qid=1621288993&rnid=8929975011&ref=sr_nr_n_2"
XBOX_SERIES = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A20974877011%2Cn%3A20974893011&s=price-desc-rank&dc&qid=1621898797&rnid=8929975011&ref=sr_nr_n_3"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
Bootstrap(app)

# connect to database
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///game-deals-collection.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


email = os.environ.get("EMAIL")
password = os.environ.get("PASSWORD")


def checker_thread():
    print("I am the thread and I am running the scan")
    while True:
        gc.clear_stock("PlayStation 4")
        gc.initialize_webpages(PS4_URL, "PlayStation 4")
        price_data()
        time.sleep(300)
        gc.clear_stock("PlayStation 5")
        gc.initialize_webpages(PS5_URL, "PlayStation 5")
        price_data()
        time.sleep(300)
        gc.clear_stock("Xbox One")
        gc.initialize_webpages(XBOX_ONE, "Xbox One")
        price_data()
        time.sleep(300)
        gc.clear_stock("Xbox Series X")
        gc.initialize_webpages(XBOX_SERIES, "Xbox Series X")
        price_data()
        time.sleep(300)
        gc.clear_stock("Nintendo Switch")
        gc.initialize_webpages(SWITCH, "Nintendo Switch")
        price_data()
        time.sleep(300)
        print("\nDone with this round\n")


@app.route('/')
def home():
    print("At the homepage")
    ps4_games = gc.Games.query.filter_by(system="PlayStation 4", in_stock=True).all()
    ps5_games = gc.Games.query.filter_by(system="PlayStation 5", in_stock=True).all()
    xbox_one_games = gc.Games.query.filter_by(system="Xbox One", in_stock=True).all()
    xbox_series_games = gc.Games.query.filter_by(system="Xbox Series X", in_stock=True).all()
    switch_games = gc.Games.query.filter_by(system="Nintendo Switch", in_stock=True).all()
    all_games = gc.Games.query.filter_by(in_stock=True).all()
    all_games_rarest = gc.Games.query.filter_by(in_stock=True).order_by("rarity")
    return render_template("index.html", all_games=all_games_rarest, ps4_games=ps4_games, ps5_games=ps5_games, xbox_one_games=xbox_one_games, xbox_series_games=xbox_series_games, switch_games=switch_games, length=len(all_games))


@app.route('/help')
def help():
    return render_template('help.html')


@app.route('/contact', methods=["GET", "POST"])
def contact():
    alert = False
    if request.method == "POST":
        data = request.form
        with smtplib.SMTP("smtp.gmail.com", 587) as connection:
            connection.starttls()
            connection.login(user=email, password=password)
            connection.sendmail(from_addr=email, to_addrs="chris.oreilly97@gmail.com", msg=f"Subject:New Message for Warehouse Deals\n\nName: {data['name']}\nEmail: {data['email']}\nMessage: {data['message']}")
        alert = True
    return render_template('contact.html', alert=alert)


@app.route('/ps4')
def ps4():
    in_stock = gc.Games.query.filter_by(system="PlayStation 4", in_stock=True).all()
    all_games = gc.Games.query.filter_by(system="PlayStation 4").all()
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sorter="ps4_sorted", url=PS4_URL)


@app.route('/ps5')
def ps5():
    in_stock = gc.Games.query.filter_by(system="PlayStation 5", in_stock=True).all()
    all_games = gc.Games.query.filter_by(system="PlayStation 5").all()
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sorter="ps5_sorted", url=PS5_URL)


@app.route('/xbox-one')
def xbox_one():
    in_stock = gc.Games.query.filter_by(system="Xbox One", in_stock=True).all()
    all_games = gc.Games.query.filter_by(system="Xbox One").all()
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sorter="xbox_one_sorted", url=XBOX_ONE)


@app.route('/xbox-series-x')
def xbox_series():
    in_stock = gc.Games.query.filter_by(system="Xbox Series X", in_stock=True).all()
    all_games = gc.Games.query.filter_by(system="Xbox Series X").all()
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sorter="xbox_series_sorted", url=XBOX_SERIES)


@app.route('/switch')
def switch():
    in_stock = gc.Games.query.filter_by(system="Nintendo Switch", in_stock=True).all()
    all_games = gc.Games.query.filter_by(system="Nintendo Switch").all()
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sorter="switch_sorted", url=SWITCH)


@app.route('/ps4/<sort_method>')
def ps4_sorted(sort_method):
    in_stock, all_games, sort_method = sorter(sort_method, "PlayStation 4")
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sort_method=sort_method, sorter="ps4_sorted", url=PS4_URL)


@app.route('/ps5/<sort_method>')
def ps5_sorted(sort_method):
    in_stock, all_games, sort_method = sorter(sort_method, "PlayStation 5")
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sort_method=sort_method, sorter="ps5_sorted", url=PS5_URL)


@app.route('/switch/<sort_method>')
def switch_sorted(sort_method):
    in_stock, all_games, sort_method = sorter(sort_method, "Nintendo Switch")
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sort_method=sort_method, sorter="switch_sorted", url=SWITCH)


@app.route('/xbox-one/<sort_method>')
def xbox_one_sorted(sort_method):
    in_stock, all_games, sort_method = sorter(sort_method, "Xbox One")
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sort_method=sort_method, sorter="xbox_one_sorted", url=XBOX_ONE)


@app.route('/xbox-series-x/<sort_method>')
def xbox_series_sorted(sort_method):
    in_stock, all_games, sort_method = sorter(sort_method, "Xbox Series X")
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sort_method=sort_method, sorter="xbox_series_sorted", url=XBOX_SERIES)


def sorter(sort_method, system):
    in_stock = gc.Games.query.filter_by(system=system, in_stock=True).all()
    all_games = gc.Games.query.filter_by(system=system).all()
    if sort_method == "oldest":
        all_games = gc.Games.query.filter_by(system=system).order_by("id")
        sort_method = "Oldest First"
    elif sort_method == "newest":
        all_games = gc.Games.query.filter_by(system=system).order_by(desc("id"))
        sort_method = "Newest First"
    elif sort_method == "cheapest":
        all_games = gc.Games.query.filter_by(system=system).order_by("price")
        sort_method = "Price: Low to High"
    elif sort_method == "priciest":
        all_games = gc.Games.query.filter_by(system=system).order_by(desc("price"))
        sort_method = "Price: High to Low"
    elif sort_method == "rarest":
        all_games = gc.Games.query.filter_by(system=system).order_by("rarity")
        sort_method = "Rarity: Most to Least"
    elif sort_method == "most-common":
        all_games = gc.Games.query.filter_by(system=system).order_by(desc("rarity"))
        sort_method = "Rarity: Least to Most"
    return in_stock, all_games, sort_method


def price_data():
    games = gc.db.session.query(gc.Games).all()
    for game in games:
        prices = get_price_list(game)
        dates = get_date_list(game)

        game.average = round(sum(prices) / len(prices), 2)
        game.high = max(prices)
        game.low = min(prices)
    db.session.commit()


def get_price_list(game):
    date = game.date.split(",")
    price_list = []
    for day in date:
        price_list.append(day.split(": "))
    price_list = price_list[:-1]
    # print(price_list)
    prices = []
    for i in range(len(price_list)):
        prices.append(float(price_list[i][1]))
    return prices


def get_date_list(game):
    date = game.date.split(",")
    date_list = []
    for day in date:
        date_list.append(day.split(": "))
    date_list = date_list[:-1]
    dates = []
    for i in range(len(date_list)):
        dates.append(date_list[i][0])
    return dates


print("paging the scanner...")
threading.Thread(target=checker_thread, daemon=True).start()

if __name__ == "__main__":

    app.run(debug=False)

