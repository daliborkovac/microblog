#!/home/dkovac/virtualenv/python3.4_flask/bin/python
from app import app     # the app object (instance of Flask) will be created during initialization of the "app"
                        # package as part of this import (__init__.py from app package gets executed at this point)
app.run(debug=True)
# you have to run it this way if you want to use PyCharm's debugger, because the reloader gets in the way of
# debugging (it starts a new process and the debugger is still monitoring the original one):
# app.run(debug=True, use_reloader=False)