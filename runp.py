#!/home/dkovac/virtualenv/python3.4_flask/bin/python
# This is a PRODUCTION version of starting script, with debug mode turned off
from app import app     # the app object (instance of Flask) will be created during initialization of the "app"
                        # package as part of this import
app.run(debug=False)