import requests
import telegram
import os
from flask import Flask

from proxy_requests import ProxyRequests

from flask_sqlalchemy import SQLAlchemy
from bs4 import BeautifulSoup
import datetime as dt

PS4_URL = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A7089437011%2Cn%3A6458584011&dc&qid=1613426168&rnid=8929975011&ref=sr_nr_n_2 "
PS5_URL = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A20974860011%2Cn%3A20974876011&dc&qid=1614274309&rnid=8929975011&ref=sr_nr_n_2 "
SWITCH = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A16329248011%2Cn%3A16329255011&dc&qid=1621288946&rnid=8929975011&ref=sr_nr_n_3"
XBOX_ONE = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A7089610011%2Cn%3A6920196011&dc&qid=1621288993&rnid=8929975011&ref=sr_nr_n_2"
XBOX_SERIES = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A20974877011%2Cn%3A20974893011&s=price-desc-rank&dc&qid=1621898797&rnid=8929975011&ref=sr_nr_n_3"

# headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Accept-Encoding": "gzip,deflate,br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
    "DNT": "1",
    "Connection": "close",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://www.google.com/",
}

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

# connect to database
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///game-deals-collection.db"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///game-deals-collection.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

warehouse_deals_url = "https://warehouse-deals.herokuapp.com/"

# template for adding new entries into database
# class Games(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(250), unique=True, nullable=False)
#     price = db.Column(db.DECIMAL(0, 2), nullable=False)
#     system = db.Column(db.String(250), nullable=False)
#     url = db.Column(db.String(), nullable=False)
#     img_url = db.Column(db.String(), nullable=False)
#     in_stock = db.Column(db.Boolean, nullable=False)
#     date = db.Column(db.String, nullable=False)
#     rarity = db.Column(db.Integer, nullable=False)
#     available = db.Column(db.Boolean, nullable=False)
#     low = db.Column(db.DECIMAL(0, 2), nullable=False)
#     high = db.Column(db.DECIMAL(0, 2), nullable=False)
#     average = db.Column(db.DECIMAL(0, 2), nullable=False)

class Games(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    system = db.Column(db.String(250), nullable=False)
    url = db.Column(db.String(), nullable=False)
    img_url = db.Column(db.String(), nullable=False)
    in_stock = db.Column(db.Boolean, nullable=False)
    date = db.Column(db.String, nullable=False)
    rarity = db.Column(db.Integer, nullable=False)
    available = db.Column(db.Boolean, nullable=False)
    low = db.Column(db.Numeric(10, 2), nullable=False)
    high = db.Column(db.Numeric(10, 2), nullable=False)
    average = db.Column(db.Numeric(10, 2), nullable=False)


# db.create_all()


def initialize_webpages(url, console):
    print(f"trying to load {console} games...")
    searching = True
    list_of_price_changes = []
    new_game = False
    price_change = False
    back_in_stock = False

    while searching:
        r = ProxyRequests("https://www.google.com/")
        r.set_headers(headers)
        r.get_with_headers()
        # print(r.get_status_code())
        proxy = r.get_proxy_used()
        # print(proxy)

        proxy = {
            "http": f"http://{proxy}",
            "https": f"https://{proxy}",
        }

        try:
            response = requests.get(url, headers=headers, proxies=proxy)
            response.raise_for_status()
            searching = False
        except:
            print("something went wrong")

    # webpage = r

    webpage = response.text
    webpage_soup = BeautifulSoup(webpage, "html.parser")
    # print(webpage_soup)
    game_titles = webpage_soup.find_all(name="span", class_="a-size-base-plus a-color-base a-text-normal")
    game_titles = [game.getText() for game in game_titles]

    game_price = webpage_soup.select(selector=".a-spacing-medium .a-section .a-row .a-color-base")
    game_price = [game.getText() for game in game_price]
    game_price = [game.replace("$", "") for game in game_price]

    game_link = webpage_soup.find_all(name="a", class_="a-link-normal s-no-outline")
    game_link = ["https://amazon.ca" + link.get("href") for link in game_link]

    game_image = webpage_soup.find_all(name="img", class_="s-image")
    game_image = [link.get("src") for link in game_image]

    captcha_catcher = webpage_soup.find(name="p", class_="a-last")
    captcha = False

    if captcha_catcher is not None:
        print("caught a captcha - we will move on")
        captcha = True

    if len(game_titles) == len(game_price) and not captcha:
        clear_stock(console)
        print(f"the length of game_titles is {len(game_titles)} and the length of game_price is {len(game_price)}")
        available_games = Games.query.filter_by(available=True).all()
        all_games = db.session.query(Games).all()
        for i in range(len(game_titles)):
            new_game = False
            price_change = False
            back_in_stock = False
            date = dt.datetime.now()
            date = date.strftime("%b %d %Y")
            print(game_titles[i])
            game = Games.query.filter_by(title=game_titles[i]).first()
            # there is a new game not yet added to the database
            if not game:
                # check price of all new games to make sure it is good
                # checked_price = check_price()
                """ uncomment me in a few days
                response = requests.get(game_link[i], headers=headers)
                response.raise_for_status()
                webpage = response.text
                webpage_soup = BeautifulSoup(webpage, "html.parser")
                try:
                    checked_price = webpage_soup.find(name="span", class_="a-size-base a-color-price offer-price a-text-normal").getText().replace("$", "")

                except AttributeError:
                    checked_price = game_price[i]
                    print("tried to scan but was rejected")
                
                uncomment me in a few days """

                checked_price = game_price[i]  # delete this when you uncomment above

                new_game = Games(title=game_titles[i],
                                 price=checked_price,
                                 system=console,
                                 url=game_link[i],
                                 img_url=game_image[i],
                                 in_stock=True,
                                 date=f"{date}: {checked_price},",
                                 rarity=0,
                                 available=True,
                                 low=checked_price,
                                 high=checked_price,
                                 average=checked_price,
                                 )
                db.session.add(new_game)
                db.session.commit()
                print(f"added {game_titles[i]} to the database")
                # send_telegram_message(game_titles[i], checked_price, game_link[i], console, price_change=False)
                new_game = True
            # check for price changes
            """ uncomment me in a few days
            try:
                if game.price != float(game_price[i]):
                    print(f"checking for new price on {game_titles[i]}")
                    response = requests.get(game_link[i], headers=headers)
                    response.raise_for_status()
                    webpage = response.text
                    webpage_soup = BeautifulSoup(webpage, "html.parser")
                    try:
                        checked_price = webpage_soup.find(name="span",
                                                          class_="a-size-base a-color-price offer-price a-text-normal").getText().replace(
                            "$", "")
                        game.price = checked_price
                        print(f"changed {game.title}'s price to {game.price}")
                        db.session.commit()
                    except AttributeError:
                        print(f"tried to check {game.title}'s price but was rejected")
            except AttributeError:
                pass
            uncomment me in a few days """

            game = Games.query.filter_by(title=game_titles[i]).first()
            game.available = True
            game.in_stock = True
            game.rarity += 1
            game.price = game_price[i]  # delete this line if you can get around the captcha on the price check
            tracked_dates = game.date.split(",")
            tracked_dates = [dates.split(":") for dates in tracked_dates]
            tracked_prices = game.date.split(",")
            # print(tracked_prices)
            last_tracked = tracked_prices[-2]
            # print(last_tracked)
            last_tracked_split = last_tracked.split(": ")
            last_price = last_tracked_split[1]

            # print(last_price)

            tracked = False
            for tracked_date in tracked_dates:
                if date in tracked_date and game.price == last_price:
                    # print(f"{game.title} has a price of ${game.price} which matches its last price of ${last_price}")
                    tracked = True
                    break
            if not tracked:
                if game.in_stock:
                    if game.price != last_price:
                        print(f"we found a new price for {game.title}.  The old price was ${last_price}.  The new price is ${game.price}")
                        # send_telegram_message(game.title, game.price, game.url, console, price_change=True)
                        price_change = True
                        list_of_price_changes.append(game.title)
                    game.date += f"{date}: {game.price},"
                    db.session.commit()
                # else:
                #     game.date += f"{date}: 0,"
            db.session.commit()

            if new_game | price_change | back_in_stock:
                send_telegram_message(game.title, game.price, game.url, console, new_game, price_change, back_in_stock)

        updated_available_games = Games.query.filter_by(available=True).all()
        in_stock = Games.query.filter_by(in_stock=True).all()

        # check if a previously tracked game is back in stock
        for game in updated_available_games:
            if game not in available_games and game in all_games:
                print(list_of_price_changes)
                print(game.title)
                if game.title not in list_of_price_changes:
                    send_telegram_message(game.title, game.price, game.url, console, new_game=False, price_change=False, back_in_stock=True)
        # set availability to false if it is out of stock
        for game in all_games:
            if game not in in_stock and game in updated_available_games:
                print(f"{game.title} is now unavailable")
                game.available = False
                db.session.commit()

    else:
        print("uh oh")
    if new_game | price_change | back_in_stock:
        send_telegram_message(game.title, game.price, game.url, console, new_game, price_change, back_in_stock)
    print("moving on to next console...")


def clear_stock(console):
    game_list = Games.query.filter_by(system=console).all()
    for game in game_list:
        game.in_stock = False


def check_price():
    pass


def send_telegram_message(title, price, url, console, new_game, price_change, back_in_stock):
    print("sending message...")
    ps_bot_token = os.environ.get("PS_TOKEN")
    ps_bot_chat_id = os.environ.get("CHAT_ID")

    xbox_bot_token = os.environ.get("XBOX_TOKEN")
    xbox_bot_chat_id = os.environ.get("CHAT_ID")

    switch_bot_token = os.environ.get("SWITCH_TOKEN")
    switch_bot_chat_id = os.environ.get("CHAT_ID")

    if console == "PlayStation 4":
        console = "PS4"
        section_url = PS4_URL
        token = ps_bot_token
        chat_id = ps_bot_chat_id
    elif console == "PlayStation 5":
        console = "PS5"
        section_url = PS5_URL
        token = ps_bot_token
        chat_id = ps_bot_chat_id
    elif console == "Xbox One":
        section_url = XBOX_ONE
        token = xbox_bot_token
        chat_id = xbox_bot_chat_id
    elif console == "Xbox Series X":
        section_url = XBOX_SERIES
        token = xbox_bot_token
        chat_id = xbox_bot_chat_id
    elif console == "Nintendo Switch":
        section_url = SWITCH
        token = switch_bot_token
        chat_id = switch_bot_chat_id

    bot = telegram.Bot(token)

    if new_game:
        message = f"<b>New Game Alert ⚠\nFor {console}:</b><a href='{url}'>\n{title}</a> has just been tracked at ${price}\n\nOr, click <a href='{section_url}'>here</a> for all {console} deals\n\nCheck out our <a href='{warehouse_deals_url}'>Website!</a>"
    elif back_in_stock:
        message = f"<b>Back in Stock Alert ⚠\nFor {console}:</b><a href='{url}'>\n{title}</a> is back in stock for ${price}\n\nOr, click <a href='{section_url}'>here</a> for all {console} deals\n\nCheck out our <a href='{warehouse_deals_url}'>Website!</a>"
    else:
        message = f"<b>Price Change Alert ⚠\nFor {console}:</b><a href='{url}'>\n{title}</a> is in stock and has just been tracked at ${price}\n\nOr, click <a href='{section_url}'>here</a> for all {console} deals\n\nCheck out our <a href='{warehouse_deals_url}'>Website!</a>"
    bot.sendMessage(chat_id, message, parse_mode=telegram.ParseMode.HTML)
