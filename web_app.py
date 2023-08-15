from routes import *

# Starting the python applicaiton
if __name__ == '__main__':
    # Note, you're going to have to change the PORT number
    Timer(1, open_browser).start()
    socketio.run(app,host='localhost', port=443,debug=1,use_reloader=False)#,ssl_context=('local.crt','local.key'))
