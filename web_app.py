from routes import *

# Starting the python applicaiton
if __name__ == '__main__':
    # Note, you're going to have to change the PORT number
    socketio.run(app)#,ssl_context=('local.crt','local.key'))
