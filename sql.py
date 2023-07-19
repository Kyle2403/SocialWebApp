import sqlite3
import os
import hashlib
# This class is a simple handler for all of our SQL database actions
# Practicing a good separation of concerns, we should only ever call 
# These functions from our models

# If you notice anything out of place here, consider it to your advantage and don't spoil the surprise

class SQLDatabase():
    '''
        Our SQL Database

    '''

    # Get the database running
    def __init__(self, database_arg=":memory:"):
        self.conn = sqlite3.connect(database_arg,check_same_thread=False)
        self.cur = self.conn.cursor()

    # SQLite 3 does not natively support multiple commands in a single statement
    # Using this handler restores this functionality
    # This only returns the output of the last command
    def execute1(self, sql_string):
        for string in sql_string.split(";"):
            try:
                self.conn.execute(string)
                self.commit()
            except:
                pass
        return True

    # Commit changes to the database
    def commit(self):
        self.conn.commit()

    #-----------------------------------------------------------------------------
    
    # Sets up the database
    # Default admin password
    def database_setup(self, admin_password='admin'):

        # Clear the database if needed
        self.execute1("DROP TABLE IF EXISTS Users")
        self.commit()

        # Create the users table
        self.execute1("""CREATE TABLE Users(
            salt BINARY(16),
            username TEXT,
            hashed_password BINARY(64),
            admin INTEGER DEFAULT 0,
            first_admin INTEGER DEFAULT 0,
            muted INTEGER DEFAULT 0
        )""")

        self.commit()

        # Add our admin user
        salt = os.urandom(16)
        new_password = salt + admin_password.encode('utf-8')
        hashed_password = hashlib.sha256(new_password).hexdigest()
        self.add_user(salt.hex(),'admin', hashed_password, 1,1,0)

    #-----------------------------------------------------------------------------
    # User handling
    #-----------------------------------------------------------------------------

    # Add a user to the database
    def add_user(self,salt, username, hashed_password, admin=0,first_admin=0,muted=0):
        sql_cmd = """INSERT INTO Users VALUES( '{salt}','{username}', '{hashed_password}', {admin},{first_admin},{muted})"""
        sql_cmd = sql_cmd.format(salt=salt,username=username, hashed_password=hashed_password, admin=admin,first_admin=first_admin,muted=muted)
        self.execute1(sql_cmd)
        self.commit()
        return True

    #-----------------------------------------------------------------------------
    # Make a user an admin
    def grantAdmin(self,username):
        sql_query = """Update Users Set admin = 1 where username='{username}'"""
        sql_query = sql_query.format(username=username)
        self.cur.execute(sql_query)

    def revokeAdmin(self,username):
        sql_query = """Update Users Set admin = 0 where username='{username}'"""
        sql_query = sql_query.format(username=username)
        self.cur.execute(sql_query)

    # Check username exists:
    def username_exists(self,username):
        sql_query = """
                SELECT 1
                FROM Users
                where username='{username}'
            """
        sql_query = sql_query.format(username=username)
        self.cur.execute(sql_query)
        user_exists = self.cur.fetchone()
        if not user_exists:
            return False
        return True
    # Check if muted
    def userMuted(self,username):
        sql_query = """
                SELECT muted
                FROM Users
                where username='{username}'
            """
        sql_query = sql_query.format(username=username)
        self.cur.execute(sql_query)
        user_muted = self.cur.fetchone()[0]
        if user_muted==0:
            return False
        return True
    
    #Check if user is admin
    def userAdmin(self,username):
        sql_query = """
                SELECT admin
                FROM Users
                where username='{username}'
            """
        sql_query = sql_query.format(username=username)
        self.cur.execute(sql_query)
        user_admin = self.cur.fetchone()[0]
        if user_admin==0:
            return False
        return True
    
    #Check if user is first admin
    def firstAdmin(self,username):
        sql_query = """
                SELECT first_admin
                FROM Users
                where username='{username}'
            """
        sql_query = sql_query.format(username=username)
        self.cur.execute(sql_query)
        first_admin = self.cur.fetchone()[0]
        if first_admin==0:
            return False
        return True
    
    # Delete an user
    def deluser(self,username):
        sql_query = """Delete from Users where username='{username}'"""
        sql_query = sql_query.format(username=username)
        self.cur.execute(sql_query)

    # Mute an user
    def muteUser(self,username):
        sql_query = """Update Users Set muted = 1 where username='{username}'"""
        sql_query = sql_query.format(username=username)
        self.cur.execute(sql_query)

    # Change username
    def updateName(self,current_name, new_name):
        sql_query = """Update Users Set username = '{new_name}' where username='{current_name}'"""
        sql_query = sql_query.format(new_name=new_name,current_name=current_name)
        self.cur.execute(sql_query)
    
    # Change password
    def updatePassword(self,username,new_password):
        # Get the salt in hex
        salt_query = """SELECT salt FROM Users Where username='{username}'"""
        salt_query = salt_query.format(username=username)
        self.cur.execute(salt_query)
        salt_hex = self.cur.fetchone()[0]
        self.commit()

        # Compute the hash for new password
        salt = bytes.fromhex(salt_hex)
        new_pwd = salt + new_password.encode('utf-8')
        new_hashed = hashlib.sha256(new_pwd).hexdigest()

        sql_query = """Update Users Set hashed_password = '{new_hashed}' where username='{username}'"""
        sql_query = sql_query.format(new_hashed=new_hashed,username=username)
        self.cur.execute(sql_query)

    # Get all users
    def users(self):
        sql_query = """
                SELECT username
                FROM Users
            """
        self.cur.execute(sql_query)
        self.commit()
        val = self.cur.fetchall()
        self.commit()
        return val
    # Show all records
    def database(self):
        sql_query = """
                SELECT *
                FROM Users
            """
        self.cur.execute(sql_query)
        self.commit()
        val = self.cur.fetchall()
        self.commit()
        return val
    # Check login credentials
    def check_credentials(self, username, password):
    	# Check if username is valid
    	username_exists_query ="""SELECT 1 FROM Users WHERE username='{username}'"""
    	username_exists_query = username_exists_query.format(username=username)
    	self.cur.execute(username_exists_query)
    	user_exists = self.cur.fetchone()
    	if not user_exists:
    	    return False
    	
    	# Get the salt in hex
    	salt_query = """SELECT salt FROM Users Where username='{username}'"""
    	salt_query = salt_query.format(username=username)
    	self.cur.execute(salt_query)
    	salt_hex = self.cur.fetchone()[0]
    	self.commit()
    	
    	# Get the right hashed password for the corresponding username
    	pwd_query = """SELECT hashed_password FROM Users Where username='{username}'"""
    	pwd_query = pwd_query.format(username=username)
    	self.cur.execute(pwd_query)
    	actual_hashed = self.cur.fetchone()[0]

    	# Compute the hash for given password
    	salt = bytes.fromhex(salt_hex)
    	given_pwd = salt + password.encode('utf-8')
    	given_hashed = hashlib.sha256(given_pwd).hexdigest()

    	if given_hashed != actual_hashed:
    	    return False
    	return True

