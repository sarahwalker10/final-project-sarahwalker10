import string
import random
from datetime import datetime
from flask import *
from functools import wraps
import sqlite3


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

def get_db():
    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect('db/belay.sqlite3')
        db.row_factory = sqlite3.Row
        setattr(g, '_database', db)
    return db

def query_db(query, args=(), one=False):
    db = get_db()
    cursor = db.execute(query, args)
    rows = cursor.fetchall()
    db.commit()
    cursor.close()
    if rows:
        if one: 
            return rows[0]
        return rows
    return None


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
@app.route('/profile')
@app.route('/login')
@app.route('/channels')
@app.route('/threads')
def index(chat_id=None):
    return app.send_static_file('index.html')



# def index(chat_id=None):
#     return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run()

@app.errorhandler(404)
def page_not_found(e):
    return 404


def new_user():
    name = "User #" + ''.join(random.choices(string.digits, k=6))
    password = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    api_key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=40))
    u = query_db('insert into users (username, password, api_key) ' + 
        'values (?, ?, ?) returning user_id, username, password, api_key',
        (name, password, api_key),
        one=True)
    return u

#POST a new user account in the database when the user signs up
@app.route('/api/', methods = ["POST"])
def signup():
    u = new_user()
    user_dict = {}
    user_dict["user_api"] = u["api_key"]
    user_dict["user_name"] = u["username"]
    user_dict["user_id"] = u["user_id"]
    
    return jsonify([user_dict])


# GET to get the user account from login
# POST a new user account when the user clicks to create a new one
@app.route('/api/login', methods = ["GET", "POST"])
def login():
    if request.method == "GET":
        #get the username
        user = request.headers.get('username')
        #get the password
        pw = request.headers.get('password')
        print(user, pw)
        query = "SELECT * FROM users WHERE username = ? and password=?"
        rows = query_db(query, [user, pw])
        print(rows)
        if rows is None:
            error_user = [{"user_id": None, "user_api_key": None}]
            return jsonify(error_user)
        
        else:
            user = []
            for row in rows:
                row_dict = {}

                if isinstance(row["api_key"], bytes):
                    user_api_key = row["api_key"].decode('utf-8')
                else:
                    user_api_key = row["api_key"]

                if isinstance(row["user_id"], bytes):
                    user_id = row["user_id"].decode('utf-8')
                else:
                    user_id = row["user_id"]
            
                row_dict["user_id"] = user_id
                row_dict["user_api_key"] = user_api_key

                user.append(row_dict)
            return jsonify(user)
        
    if request.method == 'POST':
        u = new_user()
        user_dict = {}
        user_dict["user_api"] = u["api_key"]
        user_dict["user_name"] = u["username"]
        user_dict["user_id"] = u["user_id"]
        
        return jsonify([user_dict])


# POST to change the user's name
# POST to change the user's password
@app.route('/api/profile', methods = ["POST"])
def update_profile():
    #get the infromation sent in the script.js request 
    api_key = request.headers.get('auth-key')
    print(api_key)
    user_name = request.headers.get('username')
    print(user_name)
    update_type = request.headers.get('update-type')

    #update username in the db
    if update_type == "username":
        db = get_db()
        cursor = db.execute("UPDATE users SET username = ? WHERE api_key = ?", [user_name, api_key])
        db.commit()
        cursor.close()
        return jsonify({})
    #update password in the db
    elif update_type == "password":
        new_pw = request.headers.get('new-pw')
        print(new_pw)
        db = get_db()
        cursor = db.execute("UPDATE users SET password = ? WHERE api_key = ? and username = ?", [new_pw, api_key, user_name])
        db.commit()
        cursor.close()
        return jsonify({})


current_datetime = datetime.now()
iso_timestamp = current_datetime.isoformat()
