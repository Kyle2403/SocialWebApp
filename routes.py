# Importing the Flask Framework
from flask import Flask, session
from flask_session import Session
from flask import redirect, url_for,render_template, request, flash
import sql
import os 
import hashlib
from flask_socketio import SocketIO, send, emit
from loadFile import readPosts, savePost, delPost, addComment
import webbrowser
from threading import Timer

def open_browser():
      webbrowser.open_new("http://localhost:443")

page = {}
sql_db = sql.SQLDatabase()
sql_db.database_setup()
# Initialise the FLASK application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Receive message from user and send it to others connected users
@socketio.on("message")
def sendMessage(message):
    message1 = session['name'] + ": " + message
    emit("message", (message1), broadcast=True)

@socketio.on("comment")
def saveComment(comment):
    title = comment.split(':')[0]
    comment = comment.split(":")[1]
    owner = session['name']
    addComment(comment,title,owner)

app.debug = True

#####################################################
##  INDEX
#####################################################

# What happens when we go to our website
@app.route('/')
def index():
    # If the user is not logged in, then make them go to the login page
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('login'))
    page['title'] = 'Home'
    return render_template('home.html', session=session, page=page)

################################################################################
# Login Page
################################################################################

# This is for the login
# Look at the methods [post, get] that corresponds with form actions etc.
@app.route('/login', methods=['POST', 'GET'])
def login():
    page = {'title' : 'Login', 'username' : "bruh"}
    # If it's a post method handle it nicely
    if(request.method == 'POST'):
        # Get our login value
        val = sql_db.check_credentials(request.form['username'], request.form['password'])
        if(val == False):
            if sql_db.username_exists(request.form['username']):
                flash("""Wrong Password""")
                return redirect(url_for('login'))
            flash("""Username does not exist""")
            return redirect(url_for('login'))
        session['name'] = request.form['username']
        session['logged_in'] = True
        session['admin'] = sql_db.userAdmin(session['name'])
        session['firstadmin'] = sql_db.firstAdmin(session['name'])
        return redirect(url_for('index'))
    else:
        # Else, they're just looking at the page :)
        return render_template('index.html', page=page)


################################################################################
# Logout Endpoint
################################################################################

@app.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect(url_for('index'))

###############################################################################
# Register
################################################################################
@app.route('/register',methods=['POST','GET'])
def register():
    page['title'] = "Register"
    if(request.method == 'POST'):
        username = request.form['username']
        password = request.form['password']
        # Check if username already exists
        if sql_db.username_exists(username):
            flash("Username already exists, choose another")
            return redirect(url_for('register'))
        # Add a salt to the password, hash it and store in database for security purpose
        salt = os.urandom(16)
        new_password = salt + password.encode('utf-8')
        hashed_password = hashlib.sha256(new_password).hexdigest()
        sql_db.add_user(salt.hex(),username, hashed_password, 0)
        page['title'] = "Login"
        flash('Successfully registered, try to log in:)')
        return redirect(url_for('login'))
    return render_template('register.html',page=page)

###############################################################################
# Database of user accounts
################################################################################
@app.route('/database')
def database():
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('index'))
    users = sql_db.database()
    if (users is None):
        users = []
    page['title'] = 'Database'
    return render_template('database.html',page=page,session=session,users=users)


###############################################################################
# Message
################################################################################
@app.route('/message')
def message():
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('index'))
    page['title'] = "Message"
    return render_template("message.html",page=page,session=session)

###############################################################################
# Read existing ones
################################################################################
@app.route('/posts')
def posts():
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('index'))
    page['title'] = "Knowledge Repository"
    
    posts = readPosts()
    return render_template("posts.html",page=page,session=session, posts=posts)

###############################################################################
# Make new post
################################################################################
@app.route('/newpost',methods=['POST','GET'])
def newpost():
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('index'))
    muted = sql_db.userMuted(session['name'])
    if muted:
        flash("You are muted, thus can not make new post")
        return redirect(url_for('posts'))
    if(request.method == 'POST'):
        title = request.form['title'] + "END123"
        body = request.form['body'] + "END123"
        image = request.form['image']
        savePost(title,body,image)
        return redirect(url_for('posts'))
    page['title'] = "New Post Prompt"
    return render_template('newpost.html',page=page,session=session)

###############################################################################
# Delete a post for admin
################################################################################
@app.route('/delpost',methods=['POST','GET'])
def delpost():
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('index'))
    admin = sql_db.userAdmin(session['name'])
    if not admin:
        flash("You are not an admin, thus can not delete any posts")
        return redirect(url_for('posts'))
    if(request.method == 'POST'):
        title = request.form['title']
        message = delPost(title)
        if message != "exists":
            flash("""No Post with such Title exists, nothing changed""")
        return redirect(url_for('posts'))
    page['title'] = "Delete Post Prompt"
    posts = readPosts()
    post_titles = []
    for post in posts:
        title = post[0]
        post_titles.append(title)
    return render_template('delpost.html',page=page,session=session,post_titles=post_titles)

###############################################################################
# Mute or delete an user for admin
################################################################################
@app.route('/usercontrol',methods=['POST','GET'])
def usercontrol():
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('index'))
    admin = sql_db.userAdmin(session['name'])
    users = sql_db.users()
    usernames = []
    for user in users:
        usernames.append(user[0])
    if not admin:
        flash("You are not an admin")
        return redirect(url_for('index'))
    if(request.method == 'POST'):
        type = request.form['action']
        username = request.form['username']
        page['title'] = "User Control"
        if not sql_db.username_exists(username):
            flash("User does not exist, nothing changed")
            return render_template('usercontrol.html',page=page,session=session,usernames=usernames)
        if sql_db.firstAdmin(username):
            flash("Cannot mute/delete super admin, nothing changed")
            return render_template('usercontrol.html',page=page,session=session,usernames=usernames)
        if sql_db.userAdmin(username):
            if not sql_db.firstAdmin(session['name']):
                flash("You are not super admin, thus cannot mute/delete other admins, nothing changed")
                return render_template('usercontrol.html',page=page,session=session,usernames=usernames)
        if type == 'mute':
            muted = sql_db.userMuted(username)
            if not muted:
                sql_db.muteUser(username)
                flash("""User {} has been muted""".format(username))
            else:
                flash("""User {} is already muted, nothing changed""".format(username))
        if type == 'delete':
            sql_db.deluser(username)
            flash("""User {} has been deleted""".format(username))
            usernames.remove(username)
    return render_template('usercontrol.html',page=page,session=session,usernames=usernames)

###############################################################################
# Change username and password
################################################################################
@app.route('/accountsetting',methods=['POST','GET'])
def accountsetting():
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('index'))
    page['title'] = "Account Setting"
    if(request.method == 'POST'):
        type = request.form['action']
        if type == "username":
            new_username = request.form['username']
            username_exist = sql_db.username_exists(new_username)
            if not username_exist:
                sql_db.updateName(session['name'],new_username)
                session['name'] = new_username
                flash("""You username has been changed to {}""".format(new_username))
            else:
                if new_username == session['name']:
                    flash("New username is the same as current, nothing changed")
                else:
                    flash("""Username already exists, choose another""")
        if type =="password":
            old_password = request.form['old_password']
            new_password = request.form['new_password']
            val = sql_db.check_credentials(session['name'],old_password)
            if not val:
                flash("Wrong current password, nothing changed")
                return render_template('accountsetting.html',page=page,session=session)
            same_password = sql_db.check_credentials(session['name'],new_password)
            if not same_password:
                sql_db.updatePassword(session['name'], new_password)
                flash("""You password has been changed""")
            else:
                flash("""New password is the same as current, nothing changed""")
    return render_template('accountsetting.html',page=page,session=session)

###############################################################################
# Make an user admin, or revoke admin priviledges
################################################################################
@app.route('/grantadmin',methods=['POST','GET'])
def grantadmin():
    if( 'logged_in' not in session or not session['logged_in']):
        return redirect(url_for('index'))
    if not session['firstadmin']:
        flash("""You are not super admin""")
        return redirect(url_for('index'))
    page['title'] = "Grant/Revoke Admin Privileges"
    users = sql_db.users()
    usernames = []
    for user in users:
        usernames.append(user[0])
    if(request.method == 'POST'):
        type = request.form['action']
        username = request.form['username']
        if not sql_db.username_exists(username):
            flash("""Username does not exist, nothing changed""")
            return render_template('grantadmin.html',page=page,session=session,usernames=usernames)
        if sql_db.firstAdmin(username):
            flash("""Can not make changes to super admin, nothing changed""")
            return render_template('grantadmin.html',page=page,session=session,usernames=usernames)
        if type == "grant":
            if sql_db.userAdmin(username):
                flash("""This user is already an admin, nothing changed""")
                return render_template('grantadmin.html',page=page,session=session,usernames=usernames)
            sql_db.grantAdmin(username)
            flash("""Successfully grant admin access to {}""".format(username))
        if type == 'revoke':
            if not sql_db.userAdmin(username):
                flash("""This user is not an admin, nothing changed""")
                return render_template('grantadmin.html',page=page,session=session,usernames=usernames)
            sql_db.revokeAdmin(username)
            flash("""Successfully revoke admin access from {}""".format(username))
    return render_template('grantadmin.html',page=page,session=session,usernames=usernames)
    