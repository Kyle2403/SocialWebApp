from routes import *
import os

# Starting the python applicaiton
if __name__ == '__main__':
    # Note, you're going to have to change the PORT number
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)#,ssl_context=('local.crt','local.key'))
