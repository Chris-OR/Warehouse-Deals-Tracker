import requests
import telegram
import random
import os
import re
import urllib
import time
from flask import Flask
from amazoncaptcha import AmazonCaptcha

from proxy_requests import ProxyRequests

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.ext.mutable import MutableList
from bs4 import BeautifulSoup
import datetime as dt
import praw
import telebot
# from telebot.async_telebot import AsyncTeleBot
import asyncio


PS4_URL = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A7089437011%2Cn%3A6458584011&dc&qid=1613426168&rnid=8929975011&ref=sr_nr_n_2&_encoding=UTF8&tag=awglf-20&linkCode=ur2&linkId=67c919358e64dfac3554553a359cde0e&camp=15121&creative=330641"
PS5_URL = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A20974860011%2Cn%3A20974876011&dc&qid=1614274309&rnid=8929975011&ref=sr_nr_n_2&_encoding=UTF8&tag=awglf-20&linkCode=ur2&linkId=67c919358e64dfac3554553a359cde0e&camp=15121&creative=330641"
SWITCH = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A16329248011%2Cn%3A16329255011&dc&qid=1621288946&rnid=8929975011&ref=sr_nr_n_3&_encoding=UTF8&tag=awglf-20&linkCode=ur2&linkId=67c919358e64dfac3554553a359cde0e&camp=15121&creative=330641"
XBOX_ONE = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A7089610011%2Cn%3A6920196011&dc&qid=1621288993&rnid=8929975011&ref=sr_nr_n_2&_encoding=UTF8&tag=awglf-20&linkCode=ur2&linkId=67c919358e64dfac3554553a359cde0e&camp=15121&creative=330641"
XBOX_SERIES = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A20974877011%2Cn%3A20974893011&s=price-desc-rank&dc&qid=1621898797&rnid=8929975011&ref=sr_nr_n_3&_encoding=UTF8&tag=awglf-20&linkCode=ur2&linkId=67c919358e64dfac3554553a359cde0e&camp=15121&creative=330641"

proxy_list = []

# headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}

client_id = os.environ.get("client_id")
client_secret = os.environ.get("client_secret")
username = os.environ.get("reddit_username")
password = os.environ.get("reddit_password")
user_agent = os.environ.get("user_agent")

reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     username=username,
                     password=password,
                     user_agent=user_agent)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
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

# ps_bot = AsyncTeleBot(os.environ.get("PS_TOKEN"))
# x_bot = AsyncTeleBot(os.environ.get("XBOX_TOKEN"))
# switch_bot = AsyncTeleBot(os.environ.get("SWITCH_TOKEN"))

ps_bot = telebot.TeleBot(os.environ.get("PS_TOKEN"))
x_bot = telebot.TeleBot(os.environ.get("XBOX_TOKEN"))
switch_bot = telebot.TeleBot(os.environ.get("SWITCH_TOKEN"))


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


class Hardware(db.Model):
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


class ActivePosts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.String(), nullable=False)
    title = db.Column(db.String(250), nullable=False)


class PSTelegramUsers(db.Model):
    chatID = db.Column(db.Integer, primary_key=True)
    subscribed = db.Column(db.Boolean, nullable=False)
    unsubscribed_games = db.Column(MutableList.as_mutable(db.PickleType), default=[])
    # subscribed_games = db.Column(MutableList.as_mutable(db.PickleType), default=[])


class XboxTelegramUsers(db.Model):
    chatID = db.Column(db.Integer, primary_key=True)
    subscribed = db.Column(db.Boolean, nullable=False)
    unsubscribed_games = db.Column(MutableList.as_mutable(db.PickleType), default=[])
    # subscribed_games = db.Column(MutableList.as_mutable(db.PickleType), default=[])


class SwitchTelegramUsers(db.Model):
    chatID = db.Column(db.Integer, primary_key=True)
    subscribed = db.Column(db.Boolean, nullable=False)
    unsubscribed_games = db.Column(MutableList.as_mutable(db.PickleType), default=[])
    # subscribed_games = db.Column(MutableList.as_mutable(db.PickleType), default=[])


db.PSTelegramUsers.drop()
db.SwitchTelegramUsers.drop()
db.XboxTelegramUsers.drop()
db.session.commit()


# db.create_all()
# db.session.commit()


def initialize_webpages(url, console):
    print(f"trying to load {console} games...")
    searching = True
    establishing_connection = True
    list_of_price_changes = []
    new_game = False
    price_change = False
    back_in_stock = False
    ware = "Software"

    while searching:
        try:
            response = requests.get(url, headers=headers, proxies=urllib.request.getproxies())
            response.raise_for_status()
            searching = False
        except Exception as e:
            print(e)
            time.sleep(random.randint(3, 20))

        # if len(proxy_list) != 0:
        #     try:
        #         for proxy in proxy_list:
        #             response = requests.get(url, headers=headers, proxies=proxy)
        #             response.raise_for_status()
        #             searching = False
        #             establishing_connection = False
        #
        #     except Exception as e:
        #         # print(e)
        #         print("something went wrong")
        # else:
        #     print("proxy list is empty, searching for a new one...")
        #
        # if establishing_connection:
        #     try:
        #         print("getting proxy")
        #         r = ProxyRequests("https://www.google.com/")
        #         r.set_headers(headers)
        #         r.get_with_headers()
        #         # print(r.get_status_code())
        #         proxy = r.get_proxy_used()
        #         # print(proxy)
        #
        #         proxy = {
        #             "http": f"http://{proxy}",
        #             "https": f"https://{proxy}",
        #         }
        #
        #     except:
        #         print("proxy connection could not be established")
        #
        #     try:
        #         print("outside of getting proxy")
        #         while establishing_connection:
        #             response = requests.get(url, headers=headers, proxies=proxy)
        #             response.raise_for_status()
        #             searching = False
        #             establishing_connection = False
        #             if proxy not in proxy_list:
        #                 proxy_list.append(proxy)
        #
        #     except Exception as e:
        #         # print(e)
        #         print("something went wrong")

    # webpage = r
    webpage = response.text
    webpage_soup = BeautifulSoup(webpage, "html.parser")
    # print(webpage_soup)
    game_titles = webpage_soup.find_all(name="span", class_="a-size-base-plus a-color-base a-text-normal")
    game_titles = [game.getText() for game in game_titles]

    game_price = webpage_soup.select(
        selector=".s-card-container .a-section.a-spacing-base .a-section.a-spacing-small.s-padding-left-small.s-padding-right-small .a-section.a-spacing-none.a-spacing-top-mini .a-row.a-size-base.a-color-secondary .a-color-base")
    # game_price = webpage_soup.select(selector=".a-spacing-medium .a-section .a-row .a-color-base")
    game_price = [game.getText() for game in game_price if "$" in game.getText()]
    game_price = [game.replace("$", "") for game in game_price]

    game_link = webpage_soup.find_all(name="a", class_="a-link-normal s-no-outline")
    game_link = ["https://amazon.ca" + link.get("href") for link in game_link]
    link_no_tag = game_link
    game_link = [
        link + "&_encoding=UTF8&tag=awglf-20&linkCode=ur2&linkId=67c919358e64dfac3554553a359cde0e&camp=15121&creative=330641"
        for link in game_link]

    game_image = webpage_soup.find_all(name="img", class_="s-image")
    game_image = [link.get("src") for link in game_image]

    captcha_catcher = webpage_soup.find(name="p", class_="a-last")
    captcha = False

    if captcha_catcher is not None:
        # print(webpage_soup)
        captcha_link = webpage_soup.find(name="img").get("src")
        captcha = AmazonCaptcha.fromlink(captcha_link)
        solution = captcha.solve()
        print(solution)
        print("caught a captcha - we will move on")
        captcha = True
        captcha_alert()
        return captcha

    if len(game_titles) != len(game_price):
        game_price = webpage_soup.select(selector=".a-spacing-medium .a-section .a-row .a-color-base")
        game_price = [game.getText() for game in game_price if "$" in game.getText()]
        game_price = [game.replace("$", "") for game in game_price]

    if len(game_titles) == len(game_price) and not captcha and len(game_titles) != 0:
        clear_stock(console, ware)
        print(f"the length of game_titles is {len(game_titles)} and the length of game_price is {len(game_price)}")
        available_games = Games.query.filter_by(available=True).all()
        all_games = db.session.query(Games).all()
        for i in range(len(game_titles)):
            new_game = False
            price_change = False
            back_in_stock = False
            date = dt.datetime.now()
            date = date.strftime("%b %d %Y")
            print(f"{game_titles[i]} is ${game_price[i]}")
            game = Games.query.filter_by(title=game_titles[i]).first()
            if check_regex(game_titles[i], game):
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
                checked_price = game_price[i]
                game = Games.query.filter_by(title=game_titles[i]).first()
                try:
                    if float(game.price) != float(game_price[i]):
                        print(f"checking for new price on {game_titles[i]}")
                        response = requests.get(link_no_tag[i], headers=headers, proxies=urllib.request.getproxies())
                        response.raise_for_status()
                        webpage = response.text
                        webpage_soup = BeautifulSoup(webpage, "html.parser")
                        try:
                            checked_price = webpage_soup.find(name="span",
                                                              class_="a-size-base a-color-price offer-price a-text-normal").getText().replace(
                                "$", "")
                            print(f"changed {game_titles[i]}'s price to {checked_price}")
                        except AttributeError:
                            print(f"tried to check {game_titles[i]}'s price but was rejected")
                except:
                    print(f"tried to check the price of {game_titles[i]} but URL was denied access")
                    checked_price = game.price

                game = Games.query.filter_by(title=game_titles[i]).first()
                game.available = True
                game.in_stock = True
                game.rarity += 1
                game.url = game_link[i]
                game.price = checked_price
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
                            print(
                                f"we found a new price for {game.title}.  The old price was ${last_price}.  The new price is ${game.price}")
                            # send_telegram_message(game.title, game.price, game.url, console, price_change=True)
                            price_change = True
                            list_of_price_changes.append(game.title)
                        game.date += f"{date}: {game.price},"
                        db.session.commit()
                    # else:
                    #     game.date += f"{date}: 0,"
                db.session.commit()

                if new_game | price_change | back_in_stock:
                    send_telegram_message(game.title, game.price, game.url, console, game.low, game.average, new_game,
                                          price_change, back_in_stock, "Software")

        updated_available_games = Games.query.filter_by(available=True).all()
        in_stock = Games.query.filter_by(in_stock=True).all()

        # check if a previously tracked game is back in stock
        for game in updated_available_games:
            if game not in available_games and game in all_games:
                print(list_of_price_changes)
                print(game.title)
                if game.title not in list_of_price_changes:
                    send_telegram_message(game.title, game.price, game.url, console, game.low, game.average,
                                          new_game=False, price_change=False, back_in_stock=True, ware="Software")
        # set availability to false if it is out of stock
        for game in all_games:
            if game not in in_stock and game in updated_available_games:
                print(f"{game.title} is now unavailable")
                game.available = False
                db.session.commit()
                try:
                    post = ActivePosts.query.filter_by(title=game.title).first()
                    submission = reddit.submission(post.post_id)
                    submission.reply("spoiler")
                    print(f"added spoiler tag to {game.title}'s post")
                    db.session.delete(post)
                    db.session.commit()
                except:
                    print(
                        f"we could not find {game.title} in the database, or reddit may be down so we could not set post status to spoiled")

        if new_game | price_change | back_in_stock and game.in_stock:
            send_telegram_message(game.title, game.price, game.url, console, game.low, game.average, new_game,
                                  price_change, back_in_stock, "Software")
    else:
        print(f"the length of game_titles is {len(game_titles)} and the length of game_price is {len(game_price)}")
        for game in game_price:
            print(game)
        print(webpage_soup.select(selector=".a-spacing-medium .a-section .a-row .a-color-base"))
        print("Everything was mistakenly out of stock or the prices and titles did not line up")

    # active_posts = ActivePosts.query.all()
    # for post in active_posts:
    #     print(f"{post.title} ({post.post_id}) is currently an active post")

    print("\nmoving on to next console...\n")


def clear_stock(console, ware):
    if ware == "Software":
        game_list = Games.query.filter_by(system=console).all()
    elif ware == "Hardware":
        game_list = Hardware.query.filter_by(system=console).all()

    for game in game_list:
        game.in_stock = False


def check_regex(title, game):
    game_regex = re.compile(
        r'bluetooth|playstation 3|InvisibleShield|Just Dance 2021 - PlayStation 5 - PlayStation 5 Edition|PDP Gaming LVL40|Goplay Grip Provides')
    mo = game_regex.search(title.lower())
    if mo:
        # print(f"{title} has been regexxed.  We will skip its rotation")
        if game:
            print(f"We have found a match in the database.  We will now remove {title} from the database")
            db.session.delete(game)
            db.session.commit()

        # -- delete this once database is cleaned -- #
        # game_list = Games.query.filter_by(system="PlayStation 4").all()
        # for game in game_list:
        #     mo = game_regex.search(game.title.lower())
        #     if mo:
        #         print(f"We have found a match in the database.  We will now remove {title} from the database")
        #         db.session.delete(game)
        #         db.session.commit()

        return False
    else:
        return True


def check_price():
    pass


def initialize_hardware(url, console):
    print(f"trying to load {console} hardware deals...")
    searching = True
    establishing_connection = True
    list_of_price_changes = []
    new_game = False
    price_change = False
    back_in_stock = False
    ware = "Hardware"

    while searching:
        try:
            response = requests.get(url, headers=headers, proxies=urllib.request.getproxies())
            response.raise_for_status()
            searching = False
        except Exception as e:
            print(e)
            time.sleep(random.randint(3, 20))

    # webpage = r
    webpage = response.text
    webpage_soup = BeautifulSoup(webpage, "html.parser")
    # print(webpage_soup)
    game_titles = webpage_soup.find_all(name="span", class_="a-size-base-plus a-color-base a-text-normal")
    game_titles = [game.getText() for game in game_titles]

    game_price = webpage_soup.select(
        selector=".s-card-container .a-section.a-spacing-base .a-section.a-spacing-small.s-padding-left-small.s-padding-right-small .a-section.a-spacing-none.a-spacing-top-mini .a-row.a-size-base.a-color-secondary .a-color-base")
    # game_price = webpage_soup.select(selector=".a-spacing-medium .a-section .a-row .a-color-base")
    game_price = [game.getText() for game in game_price if "$" in game.getText()]
    game_price = [game.replace("$", "") for game in game_price]

    game_link = webpage_soup.find_all(name="a", class_="a-link-normal s-no-outline")
    game_link = ["https://amazon.ca" + link.get("href") for link in game_link]
    link_no_tag = game_link
    game_link = [
        link + "&_encoding=UTF8&tag=awglf-20&linkCode=ur2&linkId=67c919358e64dfac3554553a359cde0e&camp=15121&creative=330641"
        for link in game_link]

    game_image = webpage_soup.find_all(name="img", class_="s-image")
    game_image = [link.get("src") for link in game_image]

    captcha_catcher = webpage_soup.find(name="p", class_="a-last")
    captcha = False

    if captcha_catcher is not None:
        # print(webpage_soup)
        captcha_link = webpage_soup.find(name="img").get("src")
        captcha = AmazonCaptcha.fromlink(captcha_link)
        solution = captcha.solve()
        print(solution)
        print("caught a captcha - we will move on")
        captcha = True
        captcha_alert()
        return captcha

    if len(game_titles) != len(game_price):
        game_price = webpage_soup.select(selector=".a-spacing-medium .a-section .a-row .a-color-base")
        game_price = [game.getText() for game in game_price if "$" in game.getText()]
        game_price = [game.replace("$", "") for game in game_price]

    if len(game_titles) == len(game_price) and not captcha and len(game_titles) != 0:
        clear_stock(console, ware)
        print(f"the length of game_titles is {len(game_titles)} and the length of game_price is {len(game_price)}")
        available_games = Hardware.query.filter_by(available=True).all()
        all_games = db.session.query(Hardware).all()
        for i in range(len(game_titles)):
            new_game = False
            price_change = False
            back_in_stock = False
            date = dt.datetime.now()
            date = date.strftime("%b %d %Y")
            game = Hardware.query.filter_by(title=game_titles[i]).first()
            # print(f"{game_titles[i]} is ${game_price[i]}")
            if check_regex(game_titles[i], game):
                # hardware deals only looks for deals on hardware that we added ourselves
                if not game:
                    # print(f"{game_titles[i]} is not in the database and thus was skipped")
                    pass
                # check for price changes
                else:
                    print(f"{game_titles[i]} is ${game_price[i]}")
                    checked_price = game_price[i]
                    game = Hardware.query.filter_by(title=game_titles[i]).first()
                    try:
                        if float(game.price) != float(game_price[i]):
                            print(f"checking for new price on {game_titles[i]}")
                            response = requests.get(link_no_tag[i], headers=headers,
                                                    proxies=urllib.request.getproxies())
                            response.raise_for_status()
                            webpage = response.text
                            webpage_soup = BeautifulSoup(webpage, "html.parser")
                            try:
                                checked_price = webpage_soup.find(name="span",
                                                                  class_="a-size-base a-color-price offer-price a-text-normal").getText().replace(
                                    "$", "")
                                print(f"changed {game_titles[i]}'s price to {checked_price}")
                            except AttributeError:
                                print(f"tried to check {game_titles[i]}'s price but was rejected")
                    except:
                        print(f"tried to check the price of {game_titles[i]} but URL was denied access")
                        checked_price = game.price

                    game = Hardware.query.filter_by(title=game_titles[i]).first()
                    game.available = True
                    game.in_stock = True
                    game.rarity += 1
                    game.url = game_link[i]
                    game.price = checked_price
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
                                print(
                                    f"we found a new price for {game.title}.  The old price was ${last_price}.  The new price is ${game.price}")
                                # send_telegram_message(game.title, game.price, game.url, console, price_change=True)
                                price_change = True
                                list_of_price_changes.append(game.title)
                            game.date += f"{date}: {game.price},"
                            db.session.commit()
                        # else:
                        #     game.date += f"{date}: 0,"
                    db.session.commit()

                if new_game | price_change | back_in_stock:
                    send_telegram_message(game.title, game.price, game.url, game.system, game.low, game.average,
                                          new_game,
                                          price_change, back_in_stock, "Hardware")

        updated_available_games = Hardware.query.filter_by(available=True).all()
        in_stock = Hardware.query.filter_by(in_stock=True).all()

        # check if a previously tracked game is back in stock
        for game in updated_available_games:
            if game not in available_games and game in all_games:
                print(list_of_price_changes)
                print(game.title)
                if game.title not in list_of_price_changes:
                    send_telegram_message(game.title, game.price, game.url, game.system, game.low, game.average,
                                          new_game=False, price_change=False, back_in_stock=True, ware="Hardware")
        # set availability to false if it is out of stock
        for game in all_games:
            if game not in in_stock and game in updated_available_games:
                print(f"{game.title} is now unavailable")
                game.available = False
                db.session.commit()
                try:
                    post = ActivePosts.query.filter_by(title=game.title).first()
                    submission = reddit.submission(post.post_id)
                    submission.reply("spoiler")
                    print(f"added spoiler tag to {game.title}'s post")
                    db.session.delete(post)
                    db.session.commit()
                except:
                    print(
                        f"we could not find {game.title} in the database, or reddit may be down so we could not set post status to spoiled")

        if new_game | price_change | back_in_stock and game.in_stock:
            send_telegram_message(game.title, game.price, game.url, game.system, game.low, game.average, new_game,
                                  price_change, back_in_stock, "Hardware")
    else:
        print(f"the length of game_titles is {len(game_titles)} and the length of game_price is {len(game_price)}")
        for game in game_price:
            print(game)
        print(webpage_soup.select(selector=".a-spacing-medium .a-section .a-row .a-color-base"))
        print("Everything was mistakenly out of stock or the prices and titles did not line up")

    # active_posts = ActivePosts.query.all()
    # for post in active_posts:
    #     print(f"{post.title} ({post.post_id}) is currently an active post")

    print("\nmoving on to next console...\n")


def manually_add_game(title, price, system, url, image_url, ware):
    is_new = False
    price_change = False
    back_in_stock = False
    date = dt.datetime.now()
    date = date.strftime("%b %d %Y")
    print(ware)
    if ware == "Software":
        game = Games.query.filter_by(title=title).first()
    elif ware == "Hardware":
        game = Hardware.query.filter_by(title=title).first()
    if not game:
        is_new = True
        if ware == "Software":
            new_game = Games(title=title,
                             price=price,
                             system=system,
                             url=url,
                             img_url=image_url,
                             in_stock=True,
                             date=f"{date}: {price},",
                             rarity=0,
                             available=True,
                             low=price,
                             high=price,
                             average=price,
                             )
        elif ware == "Hardware":
            new_game = Hardware(title=title,
                                price=price,
                                system=system,
                                url=url,
                                img_url=image_url,
                                in_stock=True,
                                date=f"{date}: {price},",
                                rarity=0,
                                available=True,
                                low=price,
                                high=price,
                                average=price,
                                )
        db.session.add(new_game)
        db.session.commit()
        print(f"added {title} to the database")
    if ware == "Software":
        game = Games.query.filter_by(title=title).first()
    elif ware == "Hardware":
        game = Hardware.query.filter_by(title=title).first()
    game.available = True
    game.in_stock = True
    game.rarity += 1
    game.url = url
    game.price = price
    game.date += f"{date}: {game.price},"
    db.session.commit()
    back_in_stock = True
    send_telegram_message(title, price, url, system, game.low, game.average, is_new, price_change, back_in_stock, ware)


def send_telegram_message(title, price, url, console, low, average, new_game, price_change, back_in_stock, ware):
    if ware == "Software":
        console_list = Games.query.filter_by(system=console).all()
    elif ware == "Hardware":
        console_list = Hardware.query.filter_by(system=console).all()
    title_list = [game.title for game in console_list]
    if title in title_list:
        print("sending message...")
        ps_bot_token = os.environ.get("PS_TOKEN")
        # ps_bot_chat_id = os.environ.get("CHAT_ID")

        xbox_bot_token = os.environ.get("XBOX_TOKEN")
        # xbox_bot_chat_id = os.environ.get("CHAT_ID")

        switch_bot_token = os.environ.get("SWITCH_TOKEN")
        # switch_bot_chat_id = os.environ.get("CHAT_ID")

        if console == "PlayStation 4":
            console = "PS4"
            section_url = PS4_URL
            token = ps_bot_token
            users = PSTelegramUsers.query.filter_by(subscribed=True).all()
            # chat_id = ps_bot_chat_id
            flair = "4e5b6756-d373-11eb-9563-0ee70d6a723d"
        elif console == "PlayStation 5":
            console = "PS5"
            section_url = PS5_URL
            token = ps_bot_token
            users = PSTelegramUsers.query.filter_by(subscribed=True).all()
            # chat_id = ps_bot_chat_id
            flair = "71f32bc2-d373-11eb-a352-0ef5d618d05d"
        elif console == "Xbox One":
            section_url = XBOX_ONE
            token = xbox_bot_token
            users = XboxTelegramUsers.query.filter_by(subscribed=True).all()
            # chat_id = xbox_bot_chat_id
            flair = "6678027c-d373-11eb-9d99-0e2e2eefa571"
        elif console == "Xbox Series X":
            section_url = XBOX_SERIES
            token = xbox_bot_token
            users = XboxTelegramUsers.query.filter_by(subscribed=True).all()
            # chat_id = xbox_bot_chat_id
            flair = "7cb3db06-d373-11eb-a655-0eb11db1fdb5"
        elif console == "Nintendo Switch":
            section_url = SWITCH
            token = switch_bot_token
            users = SwitchTelegramUsers.query.filter_by(subscribed=True).all()
            # chat_id = switch_bot_chat_id
            flair = "95d720ca-d373-11eb-85bc-0e3981761d6d"

        bot = telegram.Bot(token)

        if new_game:
            message = f"<b>New Game Alert ⚠\nFor {console}:</b><a href='{url}'>\n{title}</a> is ${price}\n\nOr, click <a href='{section_url}'>here</a> for all {console} deals"
        elif back_in_stock:
            message = f"<b>[{console}]</b> <a href='{url}'>{title}</a> is  ${price}\n\nOr, click <a href='{section_url}'>here</a> for all {console} deals"
        else:
            message = f"<b>[{console}] </b><a href='{url}'>{title}</a> is ${price}\n\nOr, click <a href='{section_url}'>here</a> for all {console} deals"
            try:
                post = ActivePosts.query.filter_by(title=title).first()
                submission = reddit.submission(post.post_id)
                submission.delete()
                print(f"deleting {title} from active post database.  It will be replaced with a price change")
                db.session.delete(post)
                db.session.commit()
            except:
                print(
                    f"could not find {title} in the database.  It is supposed to be replaced with a new post following price change")
        for user in users:
            if title not in user.unsubscribed_games and console not in user.unsubscribed_games:
                bot.sendMessage(user.chatID, message, parse_mode=telegram.ParseMode.HTML)
        # print(console, title, price, flair, console, url)
        try:
            post = reddit.subreddit("WarehouseConsoleDeals").submit(title=f"[{console}] {title} is ${price}",
                                                                    flair_id=flair, flair_text=f"{console}", url=url)
            new_post = ActivePosts(
                post_id=post.id,
                title=title,
            )

            db.session.add(new_post)
            db.session.commit()

            submission = reddit.submission(new_post.post_id)
            submission.reply(
                f"Our previously lowest tracked price for this item is ${low} and the average price is ${average}.  Click [here]({section_url}) to see all of the active {console} listings.")
        except Exception as e:
            print("Tried to send a message to reddit but it didn't work.  Check reddit's status if this happens again")
            print(e)
        print(f"Sent message.  We tracked {title} for {console} at {price}")
    else:
        print(f"stopped {title} being sent as a message to {console}")


def captcha_alert():
    bot = telegram.Bot(os.environ.get("CAPTCHA_TOKEN"))
    message = "⚠ SCANNER HIT A CAPTCHA - RESET IT NOW ⚠"
    bot.sendMessage("1779921442", message, parse_mode=telegram.ParseMode.HTML)


def initialize_ps_bot():
    # asyncio.run(ps_bot.polling())
    # ps_bot.set_my_commands([
    #     telebot.types.BotCommand(command="/mute", description="Mute notifications for a specific title"),
    #     telebot.types.BotCommand(command="/unmute", description="Unmute notifications for a specific title"),
    #     telebot.types.BotCommand(command="/unmuteall", description="Unmute all notifications"),
    #     telebot.types.BotCommand(command="/muteps4", description="Mute notifications for all PS4 titles"),
    #     telebot.types.BotCommand(command="/muteps5", description="Mute notifications for all PS5 titles"),
    #     telebot.types.BotCommand(command="/list", description="View all titles that you have muted notifications for"),
    #     telebot.types.BotCommand(command="/start", description="Allow interactions from this bot"),
    #     telebot.types.BotCommand(command="/stop", description="Stop receiving all notifications"),
    #     telebot.types.BotCommand(command="/help", description="Display help"),
    # ])
    ps_bot.polling()

    # ps_bot.set_my_commands(commands)


def initialize_switch_bot():
    # asyncio.run(switch_bot.polling())
    # switch_bot.set_my_commands([
    #     telebot.types.BotCommand(command="/mute", description="Mute notifications for a specific title"),
    #     telebot.types.BotCommand(command="/unmute", description="Unmute notifications for a specific title"),
    #     telebot.types.BotCommand(command="/unmuteall", description="Unmute all notifications"),
    #     telebot.types.BotCommand(command="/list", description="View all titles that you have muted notifications for"),
    #     telebot.types.BotCommand(command="/start", description="Allow interactions from this bot"),
    #     telebot.types.BotCommand(command="/stop", description="Stop receiving all notifications"),
    #     telebot.types.BotCommand(command="/help", description="Display help"),
    # ])
    switch_bot.polling()


def initialize_xbox_bot():
    # asyncio.run(x_bot.polling())
    # x_bot.set_my_commands([
    #     telebot.types.BotCommand(command="/mute", description="Mute notifications for a specific title"),
    #     telebot.types.BotCommand(command="/unmute", description="Unmute notifications for a specific title"),
    #     telebot.types.BotCommand(command="/unmuteall", description="Unmute all notifications"),
    #     telebot.types.BotCommand(command="/muteone", description="Mute notifications for all Xbox One titles"),
    #     telebot.types.BotCommand(command="/muteseries", description="Mute notifications for all Xbox Series titles"),
    #     telebot.types.BotCommand(command="/list", description="View all titles that you have muted notifications for"),
    #     telebot.types.BotCommand(command="/start", description="Allow interactions from this bot"),
    #     telebot.types.BotCommand(command="/stop", description="Stop receiving all notifications"),
    #     telebot.types.BotCommand(command="/help", description="Display help"),
    # ])
    x_bot.polling()


# PS BOT COMMANDS
@ps_bot.message_handler(commands=["start"])
def start_message(msg):
    ps_bot.send_message(msg.chat.id, 'Welcome! You have just opted to receive notifications for new deals. You may type /stop to stop getting all notifications. You may type /help to see a list of available commands for this bot.')
    user = PSTelegramUsers.query.filter_by(chatID=msg.chat.id).first()
    if not user:
        print("new user subscribed to receive PS Bot notifications")
        new_user = PSTelegramUsers(
            chatID=msg.chat.id,
            subscribed=True
        )
        db.session.add(new_user)
        db.session.commit()
        print(f"added chatID: {msg.chat.id} to the PS Telegram Users database")
    else:
        user.subscribed = True
        db.session.commit()
        print("An unsubscribed user has opted to receive notifications again")


@ps_bot.message_handler(commands=["stop"])
def stop_message(msg):
    ps_bot.send_message(msg.chat.id, "We're sorry to see you go!  You will receive no more notifications from us.  You can type /start to start getting notifications once again.")
    user = PSTelegramUsers.query.filter_by(chatID=msg.chat.id).first()
    if user:
        user.subscribed = False
        db.session.commit()
        print(f"{msg.chat.id} has opted out of notifications from PS Bot")
    else:
        print("A non subscriber attempted to unsubscribe")


@ps_bot.message_handler(commands=["help"])
def help_message(msg):
    ps_bot.send_message(msg.chat.id, "You may type /start to receive notifications. Type /stop to stop receiving notifications. You may start and stop notifications at any time.  Type /mute to mute notifications for specific titles.  Type /unmute to unmute notifications that you have muted.  Type /unmuteall to unmute all of your notifications.  Type /list to see a list of everything you have muted." )


@ps_bot.message_handler(commands=["mute"])
def mute_notification(msg):
    sent = ps_bot.send_message(msg.chat.id, "Please type the title of the game you wish to stop receiving notifications for.")
    ps_bot.register_next_step_handler(sent, ps_mute)


def ps_mute(message):
    message_formatted = message.text.replace("’", "'").strip()
    game = Games.query.filter((func.lower(Games.title) == func.lower(message_formatted)) & ((Games.system == "PlayStation 5") | (Games.system == "PlayStation 4"))).first()
    if not game:
        game = Hardware.query.filter((func.lower(Hardware.title) == func.lower(message_formatted)) & ((Hardware.system == "PlayStation 5") | (Games.system == "PlayStation 4"))).first()
    if not game:
        games = db.session.query(Games).filter(func.lower(Games.title).contains(func.lower(message_formatted)) & ((Games.system == "PlayStation 5") | (Games.system == "PlayStation 4"))).limit(15).all()
        if games:
            msg = "We were not able to find an exact match. But, your query returned this:\n\n"
            for i in range(0, len(games)):
                msg += f"{i+1}. {games[i].title}\n"
            msg += "\nPlease enter the number corresponding to the game you would like to mute"
            sent = ps_bot.send_message(message.chat.id, msg)
            ps_bot.register_next_step_handler(sent, ps_mute_game, games)
        if not games:
            games = db.session.query(Hardware).filter(func.lower(Hardware.title).contains(func.lower(message_formatted)) & ((Games.system == "PlayStation 5") | (Games.system == "PlayStation 4"))).limit(15).all()
            if games:
                msg = "We were not able to find an exact match. But, your query returned this:\n\n"
                for i in range(0, len(games)):
                    msg += f"{i + 1}. {games[i].title}\n"
                msg += "\nPlease enter the number corresponding to the game you would like to mute"
                sent = ps_bot.send_message(message.chat.id, msg)
                ps_bot.register_next_step_handler(sent, ps_mute_game, games)
            else:
                ps_bot.send_message(message.chat.id, "Sorry, but we were unable to find that title in our database. Please check for typos or try broadening your search.  We should be able to help you find a match with just 1 keyword from the title.  You can type /mute to try again.")
    elif game:
        ps_bot.send_message(message.chat.id, "Thank you.  You will stop receiving notifications for that title.")
        if game.title not in PSTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games:
            PSTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games += [game.title]
            db.session.commit()
        else:
            print("A user tried to mute a game that was already muted")


def ps_mute_game(message, games):
    try:
        if int(message.text) > 0:
            msg = f"You entered {message.text}, which corresponds to {games[int(message.text)-1].title}.\n\nType 'yes' if this is the title you want to stop receiving notifications for."
            sent = ps_bot.send_message(message.chat.id, msg)
            ps_bot.register_next_step_handler(sent, ps_confirm_mute, games, message.text)
        else:
            ps_bot.send_message(message.chat.id, f"Your selection, {message.text}, does not correspond to any item in the list.  You must select a number between 1 and {len(games)}.  You can type /mute to try again.")
    except:
        ps_bot.send_message(message.chat.id, f"Your selection, {message.text}, does not correspond to any item in the list.  You must select a number between 1 and {len(games)}.  You can type /mute to try again.")

    # if message.text.strip().lower() == "yes":
    #     ps_bot.send_message(message.chat.id, "Thank you.  You will stop receiving notifications for that title.")
    #     if title not in PSTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games:
    #         PSTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games += [title]
    #         db.session.commit()
    #     else:
    #         print("A user tried to mute a game that was already muted")
    # else:
    #     ps_bot.send_message(message.chat.id, "We did not receive a 'yes' as confirmation to stop notifications for this title.  You will continue receiving notifications for this item.  If there was a mistake, please try again by typing /mute")


def ps_confirm_mute(message, games, i):
    if message.text.strip().lower() == "yes":
        ps_bot.send_message(message.chat.id, "Thank you.  You will stop receiving notifications for that title.")
        if games[int(i)-1].title not in PSTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games:
            PSTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games += [games[int(i)-1].title]
            db.session.commit()
        else:
            print("A user tried to mute a game that was already muted")
    else:
        ps_bot.send_message(message.chat.id, "We did not receive a 'yes' as confirmation to stop notifications for this title.  You will continue receiving notifications for this item.  If there was a mistake, please try again by typing /mute")


@ps_bot.message_handler(commands=["list"])
def ps_list(msg):
    games = PSTelegramUsers.query.filter_by(chatID=msg.chat.id).first().unsubscribed_games
    message = ""
    for game in games:
        message += f"• {game}\n"
    if len(games) == 0:
        message = "You are not currently muting notifications for any titles.  You can type /mute to mute notifications for specific titles."
    ps_bot.send_message(msg.chat.id, message.strip())


@ps_bot.message_handler(commands=["unmute"])
def ps_unmute_game(msg):
    message = "Below is a list of titles you have opted out of notifications for:\n\n"
    muted_games = PSTelegramUsers.query.filter_by(chatID=msg.chat.id).first().unsubscribed_games
    if len(muted_games) == 0:
        ps_bot.send_message(msg.chat.id, "You are not currently muting notifications for any titles and thus have nothing to unmute.  You can type /mute to mute notifications for specific titles.")
    else:
        for i in range(0, len(muted_games)):
            message += f"{i+1}. {muted_games[i]}\n"
        message += "\nPlease type the number corresponding to the game you would like to start receiving notifications for again."
        sent = ps_bot.send_message(msg.chat.id, message)
        ps_bot.register_next_step_handler(sent, ps_unmute, muted_games)


def ps_unmute(message, muted_games):
    try:
        if int(message.text) > 0:
            msg = f"You entered {message.text}, which corresponds to {muted_games[int(message.text)-1]}.\n\nType 'yes' if this is the title you want to start receiving notifications for again."
            sent = ps_bot.send_message(message.chat.id, msg)
            ps_bot.register_next_step_handler(sent, ps_confirm_unmute, muted_games, message.text)
        else:
            ps_bot.send_message(message.chat.id, f"Your selection, {message.text}, does not correspond to any item in the list.  You must select a number between 1 and {len(muted_games)}.  You can type /unmute to try again.")
    except:
        ps_bot.send_message(message.chat.id, f"Your selection, {message.text}, does not correspond to any item in the list.  You must select a number between 1 and {len(muted_games)}.  You can type /unmute to try again.")


def ps_confirm_unmute(message, muted_games, i):
    if message.text.strip().lower() == "yes":
        del muted_games[int(i)-1]
        ps_bot.send_message(message.chat.id, "Thank you.  You will start receiving notifications for that title again.")
        PSTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games = muted_games
        db.session.commit()
    else:
        ps_bot.send_message(message.chat.id, "We did not receive a 'yes' as confirmation to start notifications again for this title.  You will continue receiving no notifications for this item.  If there was a mistake, please try again by typing /unmute")


@ps_bot.message_handler(commands=["unmuteall"])
def ps_unmute_all(msg):
    sent = ps_bot.send_message(msg.chat.id, "You are about to unmute all of your muted titles.\n\nTo confirm this action, please reply with 'yes'")
    ps_bot.register_next_step_handler(sent, ps_confirm_unmute_all)


def ps_confirm_unmute_all(message):
    if message.text.strip().lower() == "yes":
        ps_bot.send_message(message.chat.id, "Thank you.  Your list of muted games has been cleared.")
        PSTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games = []
        db.session.commit()
    else:
        ps_bot.send_message(message.chat.id,
                            "We did not receive a 'yes' as confirmation.  Your list of muted games will remain as is.  If there was a mistake, you can type /unmuteall to try again.")


@ps_bot.message_handler(commands=["muteps4", "muteps5"])
def mute_console_ps(msg):
    if msg.text == "/muteps4":
        sent = ps_bot.send_message(msg.chat.id, "You are about to mute all notifications for PS4 games.  Type 'yes' to confirm this action.")
        ps_bot.register_next_step_handler(sent, confirm_mute_console, msg.text)
    elif msg.text == "/muteps5":
        sent = ps_bot.send_message(msg.chat.id, "You are about to mute all notifications for PS5 games.  Type 'yes' to confirm this action.")
        ps_bot.register_next_step_handler(sent, confirm_mute_console, msg.text)


# <!-- END OF PS BOT COMMANDS --!>
# SWITCH BOT COMMANDS
@switch_bot.message_handler(commands=["start"])
def start_message(msg):
    switch_bot.send_message(msg.chat.id, 'Welcome! You have just opted to receive notifications for new deals. You may type /stop to stop getting all notifications. You may type /help to see a list of available commands for this bot.')
    user = SwitchTelegramUsers.query.filter_by(chatID=msg.chat.id).first()
    if not user:
        print("new user subscribed to receive Switch Bot notifications")
        new_user = SwitchTelegramUsers(
            chatID=msg.chat.id,
            subscribed=True
        )
        db.session.add(new_user)
        db.session.commit()
        print(f"added chatID: {msg.chat.id} to the Switch Telegram Users database")
    else:
        user.subscribed = True
        db.session.commit()
        print("An unsubscribed user has opted to receive notifications again")


@switch_bot.message_handler(commands=["stop"])
def stop_message(msg):
    switch_bot.send_message(msg.chat.id, "We're sorry to see you go!  You will receive no more notifications from us.  You can type /start to start getting notifications once again.")
    user = SwitchTelegramUsers.query.filter_by(chatID=msg.chat.id).first()
    if user:
        user.subscribed = False
        db.session.commit()
        print(f"{msg.chat.id} has opted out of notifications from Switch Bot")
    else:
        print("A non subscriber attempted to unsubscribe")


@switch_bot.message_handler(commands=["help"])
def help_message(msg):
    switch_bot.send_message(msg.chat.id, "You may type /start to receive notifications. Type /stop to stop receiving notifications. You may start and stop notifications at any time.  Type /mute to mute notifications for specific titles.  Type /unmute to unmute notifications that you have muted.  Type /unmuteall to unmute all of your notifications.  Type /list to see a list of everything you have muted." )


@switch_bot.message_handler(commands=["mute"])
def mute_notification(msg):
    sent = switch_bot.send_message(msg.chat.id, "Please type the title of the game you wish to stop receiving notifications for.")
    switch_bot.register_next_step_handler(sent, switch_mute)


def switch_mute(message):
    message_formatted = message.text.replace("’", "'").strip()
    game = Games.query.filter((func.lower(Games.title) == func.lower(message_formatted)) & (Games.system == "Nintendo Switch")).first()
    if not game:
        game = Hardware.query.filter((func.lower(Hardware.title) == func.lower(message_formatted)) & (Hardware.system == "Nintendo Switch")).first()
    if not game:
        games = db.session.query(Games).filter(func.lower(Games.title).contains(func.lower(message_formatted)) & (Games.system == "Nintendo Switch")).limit(15).all()
        if games:
            msg = "We were not able to find an exact match. But, your query returned this:\n\n"
            for i in range(0, len(games)):
                msg += f"{i+1}. {games[i].title}\n"
            msg += "\nPlease enter the number corresponding to the game you would like to mute"
            sent = switch_bot.send_message(message.chat.id, msg)
            switch_bot.register_next_step_handler(sent, switch_mute_game, games)
        if not games:
            games = db.session.query(Hardware).filter(func.lower(Hardware.title).contains(func.lower(message_formatted)) & (Games.system == "Nintendo Switch")).limit(15).all()
            if games:
                msg = "We were not able to find an exact match. But, your query returned this:\n\n"
                for i in range(0, len(games)):
                    msg += f"{i + 1}. {games[i].title}\n"
                msg += "\nPlease enter the number corresponding to the game you would like to mute"
                sent = switch_bot.send_message(message.chat.id, msg)
                switch_bot.register_next_step_handler(sent, switch_mute_game, games)
            else:
                switch_bot.send_message(message.chat.id, "Sorry, but we were unable to find that title in our database. Please check for typos or try broadening your search.  We should be able to help you find a match with just 1 keyword from the title.  You can type /mute to try again.")
    elif game:
        switch_bot.send_message(message.chat.id, "Thank you.  You will stop receiving notifications for that title.")
        if game.title not in SwitchTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games:
            SwitchTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games += [game.title]
            db.session.commit()
        else:
            print("A user tried to mute a game that was already muted")


def switch_mute_game(message, games):
    try:
        if int(message.text) > 0:
            msg = f"You entered {message.text}, which corresponds to {games[int(message.text)-1].title}.\n\nType 'yes' if this is the title you want to stop receiving notifications for."
            sent = switch_bot.send_message(message.chat.id, msg)
            switch_bot.register_next_step_handler(sent, switch_confirm_mute, games, message.text)
        else:
            switch_bot.send_message(message.chat.id, f"Your selection, {message.text}, does not correspond to any item in the list.  You must select a number between 1 and {len(games)}.  You can type /mute to try again.")
    except:
        switch_bot.send_message(message.chat.id, f"Your selection, {message.text}, does not correspond to any item in the list.  You must select a number between 1 and {len(games)}.  You can type /mute to try again.")


def switch_confirm_mute(message, games, i):
    if message.text.strip().lower() == "yes":
        switch_bot.send_message(message.chat.id, "Thank you.  You will stop receiving notifications for that title.")
        if games[int(i)-1].title not in SwitchTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games:
            SwitchTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games += [games[int(i)-1].title]
            db.session.commit()
        else:
            print("A user tried to mute a game that was already muted")
    else:
        switch_bot.send_message(message.chat.id, "We did not receive a 'yes' as confirmation to stop notifications for this title.  You will continue receiving notifications for this item.  If there was a mistake, please try again by typing /mute")


@switch_bot.message_handler(commands=["list"])
def switch_list(msg):
    games = SwitchTelegramUsers.query.filter_by(chatID=msg.chat.id).first().unsubscribed_games
    message = ""
    for game in games:
        message += f"• {game}\n"
    if len(games) == 0:
        message = "You are not currently muting notifications for any titles.  You can type /mute to mute notifications for specific titles."
    switch_bot.send_message(msg.chat.id, message.strip())


@switch_bot.message_handler(commands=["unmute"])
def switch_unmute_game(msg):
    message = "Below is a list of titles you have opted out of notifications for:\n\n"
    muted_games = SwitchTelegramUsers.query.filter_by(chatID=msg.chat.id).first().unsubscribed_games
    if len(muted_games) == 0:
        switch_bot.send_message(msg.chat.id, "You are not currently muting notifications for any titles and thus have nothing to unmute.  You can type /mute to mute notifications for specific titles.")
    else:
        for i in range(0, len(muted_games)):
            message += f"{i+1}. {muted_games[i]}\n"
        message += "\nPlease type the number corresponding to the game you would like to start receiving notifications for again."
        sent = switch_bot.send_message(msg.chat.id, message)
        switch_bot.register_next_step_handler(sent, switch_unmute, muted_games)


def switch_unmute(message, muted_games):
    try:
        if int(message.text) > 0:
            msg = f"You entered {message.text}, which corresponds to {muted_games[int(message.text)-1]}.\n\nType 'yes' if this is the title you want to start receiving notifications for again."
            sent = switch_bot.send_message(message.chat.id, msg)
            switch_bot.register_next_step_handler(sent, switch_confirm_unmute, muted_games, message.text)
        else:
            switch_bot.send_message(message.chat.id, f"Your selection, {message.text}, does not correspond to any item in the list.  You must select a number between 1 and {len(muted_games)}.  You can type /unmute to try again.")
    except:
        switch_bot.send_message(message.chat.id, f"Your selection, {message.text}, does not correspond to any item in the list.  You must select a number between 1 and {len(muted_games)}.  You can type /unmute to try again.")


def switch_confirm_unmute(message, muted_games, i):
    if message.text.strip().lower() == "yes":
        del muted_games[int(i)-1]
        switch_bot.send_message(message.chat.id, "Thank you.  You will start receiving notifications for that title again.")
        SwitchTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games = muted_games
        db.session.commit()
    else:
        switch_bot.send_message(message.chat.id, "We did not receive a 'yes' as confirmation to start notifications again for this title.  You will continue receiving no notifications for this item.  If there was a mistake, please try again by typing /unmute")


@switch_bot.message_handler(commands=["unmuteall"])
def switch_unmute_all(msg):
    sent = switch_bot.send_message(msg.chat.id, "You are about to unmute all of your muted titles.\n\nTo confirm this action, please reply with 'yes'")
    switch_bot.register_next_step_handler(sent, switch_confirm_unmute_all)


def switch_confirm_unmute_all(message):
    if message.text.strip().lower() == "yes":
        switch_bot.send_message(message.chat.id, "Thank you.  Your list of muted games has been cleared.")
        SwitchTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games = []
        db.session.commit()
    else:
        switch_bot.send_message(message.chat.id,
                            "We did not receive a 'yes' as confirmation.  Your list of muted games will remain as is.  If there was a mistake, you can type /unmuteall to try again.")


# @switch_bot.message_handler(commands=["start"])
# def start_message(msg):
#     switch_bot.send_message(msg.chat.id, 'Welcome! You have just opted to receive notifications for new deals. You may type /stop to stop getting all notifications. You may type /help to see a list of available commands for this bot.')
#     user = SwitchTelegramUsers.query.filter_by(chatID=msg.chat.id).first()
#     if not user:
#         print("new user subscribed to receive Switch Bot notifications")
#         new_user = SwitchTelegramUsers(
#             chatID=msg.chat.id,
#             subscribed=True
#         )
#         db.session.add(new_user)
#         db.session.commit()
#         print(f"added chatID: {msg.chat.id} to the Switch Telegram Users database")
#     else:
#         user.subscribed = True
#         db.session.commit()
#         print("An unsubscribed user has opted to receive notifications again")
#
#
# @switch_bot.message_handler(commands=["stop"])
# def stop_message(msg):
#     switch_bot.send_message(msg.chat.id, "We're sorry to see you go!  You will receive no more notifications from us.  You can type /start to start getting notifications once again.")
#     user = SwitchTelegramUsers.query.filter_by(chatID=msg.chat.id).first()
#     if user:
#         user.subscribed = False
#         db.session.commit()
#         print(f"{msg.chat.id} has opted out of notifications from Switch Bot")
#     else:
#         print("A non subscriber attempted to unsubscribe")
#
#
# @switch_bot.message_handler(commands=["help"])
# def help_message(msg):
#     switch_bot.send_message(msg.chat.id, "You may type /start to receive notifications. Type /stop to stop receiving notifications. You may start and stop notifications at any time." )
#

# X BOT COMMANDS
@x_bot.message_handler(commands=["start"])
def start_message(msg):
    x_bot.send_message(msg.chat.id, 'Welcome! You have just opted to receive notifications for new deals. You may type /stop to stop getting all notifications. You may type /help to see a list of available commands for this bot.')
    user = XboxTelegramUsers.query.filter_by(chatID=msg.chat.id).first()
    if not user:
        print("new user subscribed to receive X Bot notifications")
        new_user = XboxTelegramUsers(
            chatID=msg.chat.id,
            subscribed=True
        )
        db.session.add(new_user)
        db.session.commit()
        print(f"added chatID: {msg.chat.id} to the X Box Telegram Users database")
    else:
        user.subscribed = True
        db.session.commit()
        print("An unsubscribed user has opted to receive notifications again")


@x_bot.message_handler(commands=["stop"])
def stop_message(msg):
    x_bot.send_message(msg.chat.id, "We're sorry to see you go!  You will receive no more notifications from us.  You can type /start to start getting notifications once again.")
    user = XboxTelegramUsers.query.filter_by(chatID=msg.chat.id).first()
    if user:
        user.subscribed = False
        db.session.commit()
        print(f"{msg.chat.id} has opted out of notifications from X Bot")
    else:
        print("A non subscriber attempted to unsubscribe")


@x_bot.message_handler(commands=["help"])
def help_message(msg):
    x_bot.send_message(msg.chat.id, "You may type /start to receive notifications. Type /stop to stop receiving notifications. You may start and stop notifications at any time.  Type /mute to mute notifications for specific titles.  Type /unmute to unmute notifications that you have muted.  Type /unmuteall to unmute all of your notifications.  Type /list to see a list of everything you have muted." )


@x_bot.message_handler(commands=["mute"])
def mute_notification(msg):
    sent = x_bot.send_message(msg.chat.id, "Please type the title of the game you wish to stop receiving notifications for.")
    x_bot.register_next_step_handler(sent, x_mute)


def x_mute(message):
    message_formatted = message.text.replace("’", "'").strip()
    game = Games.query.filter((func.lower(Games.title) == func.lower(message_formatted)) & ((Games.system == "Xbox Series X") | (Games.system == "Xbox One"))).first()
    if not game:
        game = Hardware.query.filter((func.lower(Hardware.title) == func.lower(message_formatted)) & ((Hardware.system == "Xbox Series X") | (Games.system == "Xbox One"))).first()
    if not game:
        games = db.session.query(Games).filter(func.lower(Games.title).contains(func.lower(message_formatted)) & ((Games.system == "Xbox Series X") | (Games.system == "Xbox One"))).limit(15).all()
        if games:
            msg = "We were not able to find an exact match. But, your query returned this:\n\n"
            for i in range(0, len(games)):
                msg += f"{i+1}. {games[i].title}\n"
            msg += "\nPlease enter the number corresponding to the game you would like to mute"
            sent = x_bot.send_message(message.chat.id, msg)
            x_bot.register_next_step_handler(sent, x_mute_game, games)
        if not games:
            games = db.session.query(Hardware).filter(func.lower(Hardware.title).contains(func.lower(message_formatted)) & ((Games.system == "Xbox Series X") | (Games.system == "Xbox One"))).limit(15).all()
            if games:
                msg = "We were not able to find an exact match. But, your query returned this:\n\n"
                for i in range(0, len(games)):
                    msg += f"{i + 1}. {games[i].title}\n"
                msg += "\nPlease enter the number corresponding to the game you would like to mute"
                sent = x_bot.send_message(message.chat.id, msg)
                x_bot.register_next_step_handler(sent, x_mute_game, games)
            else:
                x_bot.send_message(message.chat.id, "Sorry, but we were unable to find that title in our database. Please check for typos or try broadening your search.  We should be able to help you find a match with just 1 keyword from the title.  You can type /mute to try again.")
    elif game:
        x_bot.send_message(message.chat.id, "Thank you.  You will stop receiving notifications for that title.")
        if game.title not in XboxTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games:
            XboxTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games += [game.title]
            db.session.commit()
        else:
            print("A user tried to mute a game that was already muted")


def x_mute_game(message, games):
    try:
        if int(message.text) > 0:
            msg = f"You entered {message.text}, which corresponds to {games[int(message.text)-1].title}.\n\nType 'yes' if this is the title you want to stop receiving notifications for."
            sent = x_bot.send_message(message.chat.id, msg)
            x_bot.register_next_step_handler(sent, x_confirm_mute, games, message.text)
        else:
            x_bot.send_message(message.chat.id, f"Your selection, {message.text}, does not correspond to any item in the list.  You must select a number between 1 and {len(games)}.  You can type /mute to try again.")
    except:
        x_bot.send_message(message.chat.id, f"Your selection, {message.text}, does not correspond to any item in the list.  You must select a number between 1 and {len(games)}.  You can type /mute to try again.")


def x_confirm_mute(message, games, i):
    if message.text.strip().lower() == "yes":
        x_bot.send_message(message.chat.id, "Thank you.  You will stop receiving notifications for that title.")
        if games[int(i)-1].title not in XboxTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games:
            XboxTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games += [games[int(i)-1].title]
            db.session.commit()
        else:
            print("A user tried to mute a game that was already muted")
    else:
        x_bot.send_message(message.chat.id, "We did not receive a 'yes' as confirmation to stop notifications for this title.  You will continue receiving notifications for this item.  If there was a mistake, please try again by typing /mute")


@x_bot.message_handler(commands=["list"])
def x_list(msg):
    games = XboxTelegramUsers.query.filter_by(chatID=msg.chat.id).first().unsubscribed_games
    message = ""
    for game in games:
        message += f"• {game}\n"
    if len(games) == 0:
        message = "You are not currently muting notifications for any titles.  You can type /mute to mute notifications for specific titles."
    x_bot.send_message(msg.chat.id, message.strip())


@x_bot.message_handler(commands=["unmute"])
def x_unmute_game(msg):
    message = "Below is a list of titles you have opted out of notifications for:\n\n"
    muted_games = XboxTelegramUsers.query.filter_by(chatID=msg.chat.id).first().unsubscribed_games
    if len(muted_games) == 0:
        x_bot.send_message(msg.chat.id, "You are not currently muting notifications for any titles and thus have nothing to unmute.  You can type /mute to mute notifications for specific titles.")
    else:
        for i in range(0, len(muted_games)):
            message += f"{i+1}. {muted_games[i]}\n"
        message += "\nPlease type the number corresponding to the game you would like to start receiving notifications for again."
        sent = x_bot.send_message(msg.chat.id, message)
        x_bot.register_next_step_handler(sent, x_unmute, muted_games)


def x_unmute(message, muted_games):
    try:
        if int(message.text) > 0:
            msg = f"You entered {message.text}, which corresponds to {muted_games[int(message.text)-1]}.\n\nType 'yes' if this is the title you want to start receiving notifications for again."
            sent = x_bot.send_message(message.chat.id, msg)
            x_bot.register_next_step_handler(sent, x_confirm_unmute, muted_games, message.text)
        else:
            x_bot.send_message(message.chat.id, f"Your selection, {message.text}, does not correspond to any item in the list.  You must select a number between 1 and {len(muted_games)}.  You can type /unmute to try again.")
    except:
        x_bot.send_message(message.chat.id, f"Your selection, {message.text}, does not correspond to any item in the list.  You must select a number between 1 and {len(muted_games)}.  You can type /unmute to try again.")


def x_confirm_unmute(message, muted_games, i):
    if message.text.strip().lower() == "yes":
        del muted_games[int(i)-1]
        x_bot.send_message(message.chat.id, "Thank you.  You will start receiving notifications for that title again.")
        XboxTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games = muted_games
        db.session.commit()
    else:
        x_bot.send_message(message.chat.id, "We did not receive a 'yes' as confirmation to start notifications again for this title.  You will continue receiving no notifications for this item.  If there was a mistake, please try again by typing /unmute")


@x_bot.message_handler(commands=["unmuteall"])
def x_unmute_all(msg):
    sent = x_bot.send_message(msg.chat.id, "You are about to unmute all of your muted titles.\n\nTo confirm this action, please reply with 'yes'")
    x_bot.register_next_step_handler(sent, x_confirm_unmute_all)


def x_confirm_unmute_all(message):
    if message.text.strip().lower() == "yes":
        x_bot.send_message(message.chat.id, "Thank you.  Your list of muted games has been cleared.")
        XboxTelegramUsers.query.filter_by(chatID=message.chat.id).first().unsubscribed_games = []
        db.session.commit()
    else:
        x_bot.send_message(message.chat.id,
                            "We did not receive a 'yes' as confirmation.  Your list of muted games will remain as is.  If there was a mistake, you can type /unmuteall to try again.")


@x_bot.message_handler(commands=["muteone", "muteseries"])
def mute_console_xbox(msg):
    if msg.text == "/muteone":
        sent = x_bot.send_message(msg.chat.id,
                                   "You are about to mute all notifications for Xbox One games.  Type 'yes' to confirm this action.")
        x_bot.register_next_step_handler(sent, confirm_mute_console, msg.text)
    elif msg.text == "/muteseries":
        sent = x_bot.send_message(msg.chat.id,
                                   "You are about to mute all notifications for Xbox Series games.  Type 'yes' to confirm this action.")
        x_bot.register_next_step_handler(sent, confirm_mute_console, msg.text)


def confirm_mute_console(msg, console_to_mute):
    if msg.text.strip().lower() == "yes":
        if console_to_mute == "/muteps4":
            ps_bot.send_message(msg.chat.id, "Thank you.  You will no longer receive notifications for PS4 games.")
            PSTelegramUsers.query.filter_by(chatID=msg.chat.id).first().unsubscribed_games += ["PlayStation 4"]
            db.session.commit()
        elif console_to_mute == "/muteps5":
            ps_bot.send_message(msg.chat.id, "Thank you.  You will no longer receive notifications for PS5 games.")
            PSTelegramUsers.query.filter_by(chatID=msg.chat.id).first().unsubscribed_games += ["PlayStation 5"]
            db.session.commit()
        elif console_to_mute == "/muteone":
            x_bot.send_message(msg.chat.id, "Thank you.  You will no longer receive notifications for Xbox One games.")
            XboxTelegramUsers.query.filter_by(chatID=msg.chat.id).first().unsubscribed_games += ["Xbox One"]
            db.session.commit()
        elif console_to_mute == "/muteseries":
            x_bot.send_message(msg.chat.id, "Thank you.  You will no longer receive notifications for Xbox Series games.")
            XboxTelegramUsers.query.filter_by(chatID=msg.chat.id).first().unsubscribed_games += ["Xbox One"]
            db.session.commit()
    else:
        if console_to_mute == "/muteps4" or console_to_mute == "/muteps5":
            ps_bot.send_message(msg.chat.id, "We did not receive a 'yes' as confirmation.  You will continue receiving notifications for that console.")
        elif console_to_mute == "/muteone" or console_to_mute == "/muteseries":
            ps_bot.send_message(msg.chat.id, "We did not receive a 'yes' as confirmation.  You will continue receiving notifications for that console.")


# @x_bot.message_handler(commands=["start"])
# def start_message(msg):
#     x_bot.send_message(msg.chat.id, 'Welcome! You have just opted to receive notifications for new deals. You may type /stop to stop getting all notifications. You may type /help to see a list of available commands for this bot.')
#     user = XboxTelegramUsers.query.filter_by(chatID=msg.chat.id).first()
#     if not user:
#         print("A new user subscribed to receive X Bot notifications")
#         new_user = XboxTelegramUsers(
#             chatID=msg.chat.id,
#             subscribed=True
#         )
#         db.session.add(new_user)
#         db.session.commit()
#         print(f"added chatID: {msg.chat.id} to the XBox Telegram Users database")
#     else:
#         user.subscribed = True
#         db.session.commit()
#         print("An unsubscribed user has opted to receive notifications again")
#
#
# @x_bot.message_handler(commands=["stop"])
# def stop_message(msg):
#     x_bot.send_message(msg.chat.id, "We're sorry to see you go!  You will receive no more notifications from us.  You can type /start to start getting notifications once again.")
#     user = XboxTelegramUsers.query.filter_by(chatID=msg.chat.id).first()
#     if user:
#         user.subscribed = False
#         db.session.commit()
#         print(f"{msg.chat.id} has opted out of notifications from X Bot")
#     else:
#         print("A non subscriber attempted to unsubscribe")
#
#
# @x_bot.message_handler(commands=["help"])
# def help_message(msg):
#     x_bot.send_message(msg.chat.id, "You may type /start to receive notifications. Type /stop to stop receiving notifications. You may start and stop notifications at any time." )
#

@ps_bot.message_handler(commands=["users"])
def show_users(msg):
    if str(msg.chat.id) == str(os.environ.get("CHAT_ID")):
        ps_users = PSTelegramUsers.query.all()
        switch_users = SwitchTelegramUsers.query.all()
        xbox_users = XboxTelegramUsers.query.all()

        message = "PS Users: "
        for user in ps_users:
            message += f"{user.chatID}"
        message += "\nSwitch Users: "
        for user in switch_users:
            message += f"{user.chatID}"
        message += "\nXbox Users: "
        for user in xbox_users:
            message += f"{user.chatID}"

        ps_bot.send_message(msg.chat.id, message)
