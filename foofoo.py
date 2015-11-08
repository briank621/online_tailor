#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.

eugene wu 2015
"""

import os
from functools import wraps
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following uses the sqlite3 database test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@w4111db1.cloudapp.net:5432/proj1part2
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@w4111db1.cloudapp.net:5432/proj1part2"
#
DATABASEURI = "postgresql://bck2116:354@w4111db1.cloudapp.net:5432/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
# 
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
# 
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
# 
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
#
# END SQLITE SETUP CODE
#


app.secret_key = 'G]\xb2kU<\xe7\x12\xd7\xf3y\\\xe4R\x82\xa4Hv\x9e\xab\x81\x8a\x94\xf7'


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#inspired from http://stackoverflow.com/questions/32640090/python-flask-keeping-track-of-user-sessions-how-to-get-session-cookie-id
def check_login(function):
  @wraps(function)
  def wrapper(*args, **kwargs):
    user_id = session.get('username')
    if user_id:
      user=database.get(user_id)
      if user:
        #User is logged in
        return function(*args, **kwargs)
      else:
        render_template("index.html", HEADER="Session exists, but user doesn't exist anymore")
    else:
      render_template("index.html", HEADER="Please log in")

@check_login
@app.route("/menu", methods=["POST","GET"])
def show_menu():
  print request.args
  print "session id" + session.get('username')
  return render_template("menu.html")


@app.route("/log-in/", methods=["POST", "GET"])
def loginfunction():
  print request.args
  print "\n"

  username = request.args["username"]
  password = request.args["password"]
  
  q = "SELECT pwd FROM user_account u WHERE u.username = %s LIMIT 1"
  cursor = g.conn.execute(q, (username,))
  real_pass = ""
  for row in cursor:
    real_pass = row[0]
  if(real_pass == password):
    session['username'] = username
    return render_template("menu.html", HEADER="Successfully logged in", USER=username)
  else:
    return render_template("index.html", HEADER="Incorrect username/password")

@check_login
@app.route("/logout/", methods=["POST","GET"])
def log_out():
  user_id = session.get('username')
  session.pop(user_id, None)
  return render_template("index.html", HEADER="Successfully Logged out")

@check_login
@app.route("/dimensions/", methods=["POST","GET"])
def list_dimensions():
   user_id = session.get('username')
   q = "SELECT waist, neck, torso, leglength FROM dimensions d WHERE d.username = %s"
   cursor = g.conn.execute(q, (username,))
   for row in cursor:
     print row[0]
     

@app.route("/register/", methods=["POST","GET"])
def register():
  return render_template("register.html")

@app.route("/create-account/", methods=["POST","GET"])
def createacc():
  print request.args
  print "\n"

  username = request.args["username"]
  password = request.args["password"]
  
  found = False
  
  q = "SELECT pwd FROM user_account u WHERE u.username = %s LIMIT 1"
  cursor = g.conn.execute(q, (username,))
  real_pass = ""
  row = cursor.fetchone()
  if(not row):
    print "New registration"
    i = "INSERT INTO user_account (pwd, username) VALUES (%s, %s)"
    cursor = g.conn.execute(i, (password, username))
    return render_template("index.html", HEADER="Successfully registered. Please log-in")
  else:
    print "Username exists"
    return render_template("register.html", HEADER="Username already taken. Please try again")
  return render_template("index.hmml", HEADER="Account not registered")

#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a POST or GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
# 
@app.route('/', methods=["POST", "GET"])
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM test")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict( data = names )


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another/
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/another/', methods=["POST", "GET"])
def another():
  return render_template("anotherfile.html")

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
