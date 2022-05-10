import game_checker as gc
import threading
import os

import email_validator

import requests
import time
import smtplib
from flask import Flask, render_template, request, send_from_directory, redirect
from flask_sitemap import Sitemap
from sqlalchemy import desc
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, RadioField
from wtforms.validators import DataRequired, Email
from flask_ckeditor import CKEditorField, CKEditor
from wtforms.fields.html5 import EmailField


PS4_URL = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A7089437011%2Cn%3A6458584011&dc&qid=1613426168&rnid=8929975011&ref=sr_nr_n_2&_encoding=UTF8&tag=awglf-20&linkCode=ur2&linkId=67c919358e64dfac3554553a359cde0e&camp=15121&creative=330641"
PS5_URL = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A20974860011%2Cn%3A20974876011&dc&qid=1614274309&rnid=8929975011&ref=sr_nr_n_2&_encoding=UTF8&tag=awglf-20&linkCode=ur2&linkId=67c919358e64dfac3554553a359cde0e&camp=15121&creative=330641"
SWITCH = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A16329248011%2Cn%3A16329255011&dc&qid=1621288946&rnid=8929975011&ref=sr_nr_n_3&_encoding=UTF8&tag=awglf-20&linkCode=ur2&linkId=67c919358e64dfac3554553a359cde0e&camp=15121&creative=330641"
XBOX_ONE = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A7089610011%2Cn%3A6920196011&dc&qid=1621288993&rnid=8929975011&ref=sr_nr_n_2&_encoding=UTF8&tag=awglf-20&linkCode=ur2&linkId=67c919358e64dfac3554553a359cde0e&camp=15121&creative=330641"
XBOX_SERIES = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A20974877011%2Cn%3A20974893011&s=price-desc-rank&dc&qid=1621898797&rnid=8929975011&ref=sr_nr_n_3&_encoding=UTF8&tag=awglf-20&linkCode=ur2&linkId=67c919358e64dfac3554553a359cde0e&camp=15121&creative=330641"

ps4_no_referral = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A7089437011%2Cn%3A6458584011&dc&qid=1613426168&rnid=8929975011&ref=sr_nr_n_2"
ps5_no_referral = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A20974860011%2Cn%3A20974876011&dc&qid=1614274309&rnid=8929975011&ref=sr_nr_n_2"
switch_no_referral = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A16329248011%2Cn%3A16329255011&dc&qid=1621288946&rnid=8929975011&ref=sr_nr_n_3"
xbox_one_no_referral = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A7089610011%2Cn%3A6920196011&dc&qid=1621288993&rnid=8929975011&ref=sr_nr_n_2"
series_x_no_referral = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A20974877011%2Cn%3A20974893011&s=price-desc-rank&dc&qid=1621898797&rnid=8929975011&ref=sr_nr_n_3"

# switch console = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A16329248011%2Cn%3A16329250011&dc&qid=1623869738&rnid=8929975011&ref=sr_nr_n_2"
# ps4 console = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A20974860011%2Cn%3A20974875011&dc&qid=1623869826&rnid=8929975011&ref=sr_nr_n_2"
    # - will need to regex some stuff out of that (stand cooling fan)
# series x console = "https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A20974877011%2Cn%3A20974892011&dc&qid=1623869878&rnid=8929975011&ref=sr_nr_n_2"

app = Flask(__name__)
# ext = Sitemap(app=app)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)

Bootstrap(app)

# connect to database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///game-deals-collection.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


email = os.environ.get("EMAIL")
password = os.environ.get("PASSWORD")


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    message = CKEditorField("Your Message", validators=[DataRequired()])
    submit = SubmitField("Send Message")


class AddGame(FlaskForm):
    title = StringField("title", validators=[DataRequired()])
    price = DecimalField("price", validators=[DataRequired()])
    system = RadioField("system", choices=[("PlayStation 4", "PlayStation 4"), ("PlayStation 5", "PlayStation 5"), ("Nintendo Switch", "Nintendo Switch"), ("Xbox One", "Xbox One"), ("Xbox Series X", "Xbox Series X")], validators=[DataRequired()])
    ware = RadioField("hardware/software", choices=[("Hardware", "Hardware"), ("Software", "Software")], validators=[DataRequired()])
    url = StringField("url", validators=[DataRequired()])
    image_url = StringField("image_url", validators=[DataRequired()])
    submit = SubmitField("Add Game")


def checker_thread():
    captcha = False
    while not captcha:
        # if not captcha:
        #     captcha = gc.initialize_webpages(ps4_no_referral, "PlayStation 4")
        #     price_data()
        #     time.sleep(151)
        # if not captcha:
        #     captcha = gc.initialize_hardware("https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cp_89%3APlaystation&s=popularity-rank&dc&qid=1649385940&ref=sr_ex_n_1", "PlayStation 5")
        #     price_data()
        #     time.sleep(31)
        if not captcha:
            captcha = gc.initialize_webpages(switch_no_referral, "Nintendo Switch")
            price_data()
            time.sleep(151)
        if not captcha:
            captcha = gc.initialize_webpages(ps5_no_referral, "PlayStation 5")
            price_data()
            time.sleep(151)
        if not captcha:
            captcha = gc.initialize_hardware("https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cn%3A16329248011%2Cp_72%3A11192170011&s=popularity-rank&dc&qid=1649385822&rnid=8929975011&ref=sr_nr_n_5", "Nintendo Switch")
            price_data()
            time.sleep(31)
        if not captcha:
            captcha = gc.initialize_webpages(xbox_one_no_referral, "Xbox One")
            price_data()
            time.sleep(151)
        if not captcha:
            captcha = gc.initialize_webpages(series_x_no_referral, "Xbox Series X")
            price_data()
            time.sleep(151)
        if not captcha:
            captcha = gc.initialize_hardware("https://www.amazon.ca/s?i=videogames&bbn=8929975011&rh=n%3A8929975011%2Cn%3A3198031%2Cp_89%3AMicrosoft&s=popularity-rank&dc&qid=1649386036&rnid=7590290011&ref=sr_nr_p_89_1", "Xbox Series X")
            price_data()
            time.sleep(31)
        print("\nDone with this round\n")


# @ext.register_generator
# def index():
#     yield 'home', {}


# @app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route('/')
def home():
    # ps4_games = gc.Games.query.filter_by(system="PlayStation 4", in_stock=True).all()
    # ps5_games = gc.Games.query.filter_by(system="PlayStation 5", in_stock=True).all()
    # xbox_one_games = gc.Games.query.filter_by(system="Xbox One", in_stock=True).all()
    # xbox_series_games = gc.Games.query.filter_by(system="Xbox Series X", in_stock=True).all()
    # switch_games = gc.Games.query.filter_by(system="Nintendo Switch", in_stock=True).all()
    all_games = gc.Games.query.filter_by(in_stock=True).all()
    all_games_rarest = gc.Games.query.filter_by(in_stock=True).order_by("rarity")
    # return render_template("index.html", all_games=all_games_rarest, ps4_games=ps4_games, ps5_games=ps5_games, xbox_one_games=xbox_one_games, xbox_series_games=xbox_series_games, switch_games=switch_games, length=len(all_games))
    return render_template("index.html", all_games=all_games_rarest, length=len(all_games))

@app.route("/add-game", methods=["GET", "POST"])
def add_game():
    form = AddGame()
    if form.validate_on_submit():
        title = request.form.get("title").strip()
        price = request.form.get("price")
        ware = request.form.get("ware")
        system = request.form.get("system")
        print(system)
        url = request.form.get("url") + "&_encoding=UTF8&tag=awglf-20&linkCode=ur2&linkId=67c919358e64dfac3554553a359cde0e&camp=15121&creative=330641"
        image_url = request.form.get("image_url")
        gc.manually_add_game(title, price, system, url, image_url, ware)
        return redirect("/")
    else:
        return render_template('add-game.html', form=form)


@app.route('/help')
def help():
    return render_template('help.html')


@app.route('/contact', methods=["GET", "POST"])
def contact(*args):
    form = ContactForm()
    alert = False

    if form.validate_on_submit():
        print("Trying to send an email...")
        name = request.form.get("name")
        contact_email = request.form.get("email")
        message = request.form.get("message")
        # print(name)
        # print(contact_email)
        # print(message)
        with smtplib.SMTP("smtp.gmail.com", 587) as connection:
            connection.starttls()
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "New Message for Warehouse Deals"
            msg['From'] = email
            msg['To'] = "chris.oreilly97@gmail.com"
            connection.login(user=email, password=password)
            html = f"""\
            <html>
              <head></head>
              <body>
                <p>New message from {name}:<br>
                   {message}
                   <br>
                   Sender's email: {contact_email}
                </p>
              </body>
            </html>
            """
            message_html = MIMEText(html, 'html')
            msg.attach(message_html)
            connection.sendmail(from_addr=email, to_addrs="chris.oreilly97@gmail.com", msg=msg.as_string())
            # connection.sendmail(from_addr=email, to_addrs="chris.oreilly97@gmail.com", msg=f"Subject:New Message for Warehouse Deals\n\nName: {name}\nEmail: {contact_email}\nMessage: {message}")
        alert = True
        form.name.data = ""
        form.email.data = ""
        form.message.data = ""
        return render_template('contact.html', alert=alert, form=form)
    return render_template('contact.html', alert=alert, form=form)


@app.route('/ps4')
def ps4():
    in_stock = gc.Games.query.filter_by(system="PlayStation 4", in_stock=True).order_by("rarity")
    all_games = gc.Games.query.filter_by(system="PlayStation 4").all()
    length = len(gc.Games.query.filter_by(system="PlayStation 4", in_stock=True).all())
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sorter="ps4_sorted", url=PS4_URL, length=length, console="PS4")


@app.route('/ps5')
def ps5():
    in_stock = gc.Games.query.filter_by(system="PlayStation 5", in_stock=True).order_by("rarity")
    all_games = gc.Games.query.filter_by(system="PlayStation 5").all()
    length = len(gc.Games.query.filter_by(system="PlayStation 5", in_stock=True).all())
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sorter="ps5_sorted", url=PS5_URL, length=length, console="PS5")


@app.route('/xbox-one')
def xbox_one():
    in_stock = gc.Games.query.filter_by(system="Xbox One", in_stock=True).order_by("rarity")
    all_games = gc.Games.query.filter_by(system="Xbox One").all()
    length = len(gc.Games.query.filter_by(system="Xbox One", in_stock=True).all())
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sorter="xbox_one_sorted", url=XBOX_ONE, length=length, console="Xbox One")


@app.route('/xbox-series-x')
def xbox_series():
    in_stock = gc.Games.query.filter_by(system="Xbox Series X", in_stock=True).order_by("rarity")
    all_games = gc.Games.query.filter_by(system="Xbox Series X").all()
    length = len(gc.Games.query.filter_by(system="Xbox Series X", in_stock=True).all())
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sorter="xbox_series_sorted", url=XBOX_SERIES, length=length, console="Series X")


@app.route('/switch')
def switch():
    in_stock = gc.Games.query.filter_by(system="Nintendo Switch", in_stock=True).order_by("rarity")
    all_games = gc.Games.query.filter_by(system="Nintendo Switch").all()
    length = len(gc.Games.query.filter_by(system="Nintendo Switch", in_stock=True).all())
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sorter="switch_sorted", url=SWITCH, length=length, console="Switch")


@app.route('/ps4/<sort_method>')
def ps4_sorted(sort_method):
    in_stock, all_games, sort_method = sorter(sort_method, "PlayStation 4")
    length = len(gc.Games.query.filter_by(system="PlayStation 4", in_stock=True).all())
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sort_method=sort_method, sorter="ps4_sorted", url=PS4_URL, length=length)


@app.route('/ps5/<sort_method>')
def ps5_sorted(sort_method):
    in_stock, all_games, sort_method = sorter(sort_method, "PlayStation 5")
    length = len(gc.Games.query.filter_by(system="PlayStation 5", in_stock=True).all())
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sort_method=sort_method, sorter="ps5_sorted", url=PS5_URL, length=length)


@app.route('/switch/<sort_method>')
def switch_sorted(sort_method):
    in_stock, all_games, sort_method = sorter(sort_method, "Nintendo Switch")
    length = len(gc.Games.query.filter_by(system="Nintendo Switch", in_stock=True).all())
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sort_method=sort_method, sorter="switch_sorted", url=SWITCH, length=length)


@app.route('/xbox-one/<sort_method>')
def xbox_one_sorted(sort_method):
    in_stock, all_games, sort_method = sorter(sort_method, "Xbox One")
    length = len(gc.Games.query.filter_by(system="Xbox One", in_stock=True).all())
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sort_method=sort_method, sorter="xbox_one_sorted", url=XBOX_ONE, length=length)


@app.route('/xbox-series-x/<sort_method>')
def xbox_series_sorted(sort_method):
    in_stock, all_games, sort_method = sorter(sort_method, "Xbox Series X")
    length = len(gc.Games.query.filter_by(system="Xbox Series X", in_stock=True).all())
    return render_template("console-game-page.html", in_stock=in_stock, all_games=all_games, sort_method=sort_method, sorter="xbox_series_sorted", url=XBOX_SERIES, length=length)


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
    games = gc.db.session.query(gc.Hardware).all()
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


threading.Thread(target=checker_thread, daemon=True).start()
threading.Thread(target=gc.initialize_ps_bot, daemon=True).start()
threading.Thread(target=gc.initialize_xbox_bot, daemon=True).start()
threading.Thread(target=gc.initialize_switch_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=False)

