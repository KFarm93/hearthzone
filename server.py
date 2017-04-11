from flask import Flask, render_template, request, redirect, session
from flaskext.mysql import MySQL
import os
import time
import unirest
import collections
from ast import literal_eval

app = Flask('checkMyDeck')
app.secret_key = 'Super Secret Key'
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
app.config['MYSQL_DATABASE_DB'] = 'checkMyDeck'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()

def convert(data):
    if isinstance(data, basestring):
        return data.encode('utf-8')
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data

# default route
@app.route('/')
def welcome():
    return render_template(
    'layout.html',
    header='CheckMyDeck.com'
    )

# this route will take the user to the signup page
@app.route('/signup')
def signup():
    return render_template('signup.html',
    header='Sign Up'
    )

@app.route('/submit_signup', methods=["POST"])
def submit_signup():
    entered_username = request.form.get('username')
    entered_password_1 = request.form.get('password1')
    entered_password_2 = request.form.get('password2')
    if entered_password_1 != entered_password_2:
        return render_template('signup.html', error = True, error_message = "Entered passwords did not match", header="Sign Up")
    else:
        cursor.execute("SELECT name FROM checkMyDeck.User WHERE User.name = %s", [entered_username])
        try:
            cursor.fetchone()[0]
        except TypeError:
            cursor.execute("INSERT INTO checkMyDeck.User VALUES (%s, %s, NULL)", [entered_username, entered_password_1])
            conn.commit()
            return render_template('layout.html', message="User Created: Now Sign In!")




# route handler for allowing user to login
@app.route('/signin', methods=["POST"])
def signin():
    entered_username = request.form.get('username')
    entered_password = request.form.get('password')
    cursor.execute("SELECT name FROM checkMyDeck.User WHERE User.name = %s", [entered_username])
    try:
        # determines if query found the user
        username = cursor.fetchone()[0]
    except TypeError:
        # if the username didn't match any users in the db:
        return render_template('layout.html', message='User not found')
    cursor.execute("SELECT password FROM checkMyDeck.User WHERE User.name = %s", [entered_username])
    # finds password of entered user in the database
    password = cursor.fetchone()[0]
    if entered_password == password:
        session['username'] = entered_username
        # set session name
        return render_template('deck-view.html')
    else:
        return render_template('layout.html', message='Incorrect password!')

@app.route('/logout')
def logout():
    # deletes session name required for showing information relative to the user
    del session['username']
    return redirect('/')

@app.route('/search', methods=["POST"])
def search():
    searchTerm = request.form.get('search-term')
    response = unirest.get("https://omgvamp-hearthstone-v1.p.mashape.com/cards/search/" + searchTerm,
        headers = {
            "X-Mashape-Key": "kwOvBij0LymshHBSreEfodjU6zIsp1bojDujsntTYcApcvprMR",
            "Accept": "application/json"
        }
    )
    results = convert(response.body)
    print "RESULTS:"
    results_num = len(results)
    return render_template('search-results.html', results=results, results_num=results_num, search_term=searchTerm)


@app.route('/card-info', methods=["POST"])
def cardInfo():
    card = request.form.get('card')
    real_card = literal_eval(card)
    def findMissingInfo(key):
        try:
            real_card[key]
        except KeyError:
            real_card[key] = '**Not Available / Not Applicable**'

    findMissingInfo('img')
    findMissingInfo('type')
    findMissingInfo('cardSet')
    findMissingInfo('rarity')
    findMissingInfo('flavor')
    findMissingInfo('playerClass')
    return render_template('card-info.html', image_path=real_card['img'], type=real_card['type'], set=real_card['cardSet'], rarity=real_card['rarity'], desc=real_card['flavor'], clas=real_card['playerClass'])


if __name__ == '__main__':
    app.run(debug=True)
