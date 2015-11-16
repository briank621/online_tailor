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

def return_uid():
  username = session.get('username')
  q = "SELECT u_id FROM user_account WHERE username = %s LIMIT 1"
  cursor = g.conn.execute(q,(username,))
  row = cursor.fetchone()
  return int(row[0])
  

@check_login
@app.route("/select_product/", methods=["GET","POST"])
def select_typeofprod():
  print request
  print "\n"

  dim_list = request.form["dim"].split(" ")
  waist = dim_list[0]
  neck = dim_list[1]
  torso = dim_list[2]
  leg = dim_list[3]
  dim = dim_list[4]
  print str(dim_list)

  products = request.form.getlist("product")
  suit_lst = []
  blazer_lst = []
  shirts_lst = []
  pants_lst = []
  for p in products:
    if(p == "suits"):
      q = "SELECT * FROM Products P NATURAL JOIN Suits S NATURAL JOIN contains_product CP"
      cursor = g.conn.execute(q)
      for row in cursor:
        suit_lst.append(row)
    if(p == "blazers"):
      q = "SELECT * FROM Products P NATURAL JOIN Blazers B NATURAL JOIN contains_product CP"
      cursor = g.conn.execute(q)
      for row in cursor:
        blazer_lst.append(row)
    if(p == "shirts"):
      q = "SELECT * FROM Products P NATURAL JOIN Shirts S NATURAL JOIN contains_product CP"
      cursor = g.conn.execute(q)
      for row in cursor:
        shirts_lst.append(row)
    if(p == "pants"):
      q = "SELECT * FROM Products P NATURAL JOIN Pants Pa NATURAL JOIN contains_product CP"
      cursor = g.conn.execute(q)
      for row in cursor:
        pants_lst.append(row)
  user_id = session.get('username')
  u_id = return_uid()
  return render_template("display_prod.html", USER=user_id, SUITS=suit_lst, BLAZERS=blazer_lst, SHIRTS=shirts_lst, PANTS=pants_lst, DIM=dim)


@check_login
@app.route("/products/", methods=["GET"])
def pick_product():
  print request.args
  print "\n"

  user_id = session.get('username')
  u_id = return_uid()
  q = "SELECT waist, neck, torso, leglength, d_id FROM dimensions NATURAL JOIN has_dim WHERE u_id = %s"
  cursor = g.conn.execute(q, (u_id,))
  if not cursor:
     return render_template("products.html", USER=user_id)
  else:
     return render_template("products.html", d_rows=cursor, USER=user_id)


@check_login
@app.route("/dimensions/", methods=["POST","GET"])
def list_dimensions():
   user_id = session.get('username')
   u_id = return_uid()
   q = "SELECT waist, neck, torso, leglength FROM dimensions NATURAL JOIN has_dim WHERE u_id = %s"
   cursor = g.conn.execute(q, (u_id,))
   if not cursor:
      return render_template("dimensions.html", USER=user_id)
   else:
      return render_template("dimensions.html", rows=cursor, USER=user_id)

@check_login
@app.route("/insert_dim/", methods=["GET"])
def insert_dimensions():
  print request.args
  print "\n"

  waist = request.args["waist"]
  neck = request.args["neck"]
  torso = request.args["torso"]
  leg = request.args["leg"]

  q = "INSERT INTO Dimensions(waist, neck, torso, leglength) VALUES (%s, %s, %s, %s) RETURNING d_id"
  cursor = g.conn.execute(q, (waist, neck, torso, leg)) 
  d_id = cursor.fetchone()[0]

  user_id = session.get('username')
  u_id = return_uid()

  q = "INSERT INTO has_dim(u_id, d_id) VALUES (%s, %s)"
  cursor = g.conn.execute(q, (u_id, d_id))
  q = "SELECT waist, neck, torso, leglength FROM dimensions NATURAL JOIN has_dim WHERE u_id = %s"
  cursor = g.conn.execute(q, (u_id,))
  if not cursor:
     return render_template("dimensions.html", USER=user_id)
  else:
     return render_template("dimensions.html", rows=cursor, USER=user_id)

@app.route("/register/", methods=["POST","GET"])
def register():
  return render_template("register.html")

@check_login
@app.route("/update_account_addr/", methods=["POST","GET"])
def update_acc_addr():
  print request.args
  print "\n"

  user_id = session.get('username')
  u_id = return_uid()

  street = request.args['street']
  zip_code = request.args['zip']
  state = request.args['state']
  city = request.args['city']
  country = request.args['country']

  q = "INSERT INTO address(street, zip, state, city, country) VALUES (%s, %s, %s, %s, %s) RETURNING a_id"
  cursor = g.conn.execute(q, (street, zip_code, state, city, country))
  a_id = cursor.fetchone()[0]

  q = "INSERT INTO has_add(u_id, a_id) VALUES (%s, %s)"
  cursor = g.conn.execute(q, (u_id, a_id))

  q = "SELECT * FROM Address A NATURAL JOIN has_add H WHERE u_id = %s"
  cursor = g.conn.execute(q, u_id)
  add = []
  for row in cursor:
    add.append(row)

  q = "SELECT * FROM CreditCards C NATURAL JOIN has_cc H WHERE u_id = %s"
  cursor = g.conn.execute(q, u_id)
  card = []
  for row in cursor:
    card.append(row)

  return render_template("account.html", USER=user_id, ADD_LIST=add, CARD_LIST=card)

@check_login
@app.route("/orders/", methods=["POST", "GET"])
def order():
  print request.form
  print "\n"

  user_id = session.get('username')
  u_id = return_uid()

  q = "SELECT order_id, num_items, price FROM Orders WHERE u_id = %s"
  cursor = g.conn.execute(q, (u_id))
  l = []
  for row in cursor:
    order_id = row[0]
    q1 = "SELECT p_id FROM order_shows_products WHERE order_id = %s"
    cursor1 = g.conn.execute(q1, (order_id))
    prods = []
    for p in cursor1:
      print str(p)
      p_id = p[0]
      q2 = "SELECT type, price, color, fabric, qty FROM Products P NATURAL JOIN order_shows_products O WHERE p_id = %s AND O.order_id = %s"
      cursor2 = g.conn.execute(q2, (p_id, order_id))
      for desc in cursor2:
        prods.append(desc)
    num_items = row[1]
    price = row[2]
    l.append((prods, order_id, num_items, price))
 
  print str(l)

  return render_template("view_orders.html", ORDER=l);
  

@check_login
@app.route("/confirm/", methods=["POST", "GET"])
def confirm():
  print request.form
  print "\n"

  user_id = session.get('username')
  u_id = return_uid()

  cart_id = request.form.get('c_id')
  total = request.form.get('price')
  num_items = request.form.get('num_items')
  cc_id = request.form.get('cc')
  a_id = request.form.get('address')

  q = "INSERT INTO Orders(num_items, price, u_id) VALUES (%s, %s, %s) RETURNING order_id"
  cursor = g.conn.execute(q, (num_items, total,u_id))
  order_id = cursor.fetchone()[0]
  q = "INSERT INTO checked_out(cart_id, order_id) VALUES (%s, %s)"
  cursor = g.conn.execute(q, (cart_id, order_id))
  q = "SELECT p_id, qty from cart_has_products C WHERE C.cart_id = %s"
  cursor = g.conn.execute(q, (cart_id))
  for row in cursor:
    p_id = row[0]
    qty = row[1]
    q = "INSERT INTO order_shows_products(order_id, p_id, qty) VALUES (%s, %s, %s)"
    cursor = g.conn.execute(q, (order_id, p_id, qty))
  q = "INSERT INTO Payments(u_id, cc_id) VALUES (%s, %s) RETURNING pay_id"
  cursor = g.conn.execute(q, (u_id, cc_id))
  pay_id = cursor.fetchone()[0]
  q = "INSERT INTO pay_for_order(pay_id, u_id, order_id) VALUES (%s, %s, %s)"
  cursor = g.conn.execute(q, (pay_id, u_id, order_id))
  
  q = "SELECT * FROM Address A NATURAL JOIN has_add H WHERE u_id = %s AND A.a_id = %s"
  cursor = g.conn.execute(q, (u_id, a_id))
  add = cursor.fetchone()

  q = "SELECT * FROM CreditCards C NATURAL JOIN has_cc H WHERE u_id = %s AND C.cc_id = %s"
  cursor = g.conn.execute(q, (u_id, cc_id))
  card = cursor.fetchone()

  print add
  print card

  q = "SELECT type, price, color, fabric, dim, qty FROM cart_has_products C NATURAL JOIN products P WHERE C.cart_id = %s"
  cursor = g.conn.execute(q, (cart_id,))
  l = []
  for row in cursor:
    l.append(row)
    print "row: " + str(row)
  return render_template("confirm.html", PRODUCT=l, ORDER=order_id, PRICE=total, NUM=num_items, ADD=add, CARD=card)


@check_login
@app.route("/checkout/", methods=["POST", "GET"])
def check_out(): 
  print request.form
  print "\n"

  user_id = session.get('username')
  u_id = return_uid()
  cart_id = request.form.get('cart_id')
  total = request.form.get('price')
  num_items = request.form.get('num')

  q = "SELECT * FROM Address A NATURAL JOIN has_add H WHERE u_id = %s"
  cursor = g.conn.execute(q, u_id)
  add = []
  for row in cursor:
    add.append(row)

  q = "SELECT * FROM CreditCards C NATURAL JOIN has_cc H WHERE u_id = %s"
  cursor = g.conn.execute(q, u_id)
  card = []
  for row in cursor:
    card.append(row)

  q = "SELECT type, price, color, fabric, dim, qty FROM cart_has_products C NATURAL JOIN products P WHERE C.cart_id = %s"
  cursor = g.conn.execute(q, (cart_id,))

  l = []
  for row in cursor:
    l.append(row)
    print "row: " + str(row)
  return render_template("checkout.html", NUM=num_items, PRODUCT=l, C_ID=cart_id, PRICE=total, USER=user_id, ADD_LIST=add, CARD_LIST=card)

@check_login
@app.route("/add_cart/", methods=["POST", "GET"])
def add_cart(): 
  print request.form
  print "\n"

  user_id = session.get('username')
  u_id = return_uid()

  #check if user has existing cart
  q = "SELECT C.cart_id FROM cart_has_user C WHERE C.u_id = %s EXCEPT SELECT cart_id from checked_out"
  cursor = g.conn.execute(q, (u_id,))
  row = cursor.fetchone()
  #if so, add to that cart
  print "r: " + str(row)
  if not row:
    print 'creating cart'
    q = "INSERT INTO cart(num_items, price) VALUES (0, 0) RETURNING cart_id"
    cursor = g.conn.execute(q)
    cart_id = cursor.fetchone()[0]
    q = "INSERT INTO cart_has_user (cart_id, u_id) VALUES (%s, %s)"
    cursor = g.conn.execute(q, (cart_id, u_id))
  else:
    print 'cart exists'
    cart_id = row[0]
  print "cart_id: " + str(cart_id)

  suit = request.form.getlist("suit")
  blazer = request.form.getlist("blazer")
  pant = request.form.getlist("shirt")
  shirt = request.form.getlist("pant")
  for s in suit:
    p_id = s.split(" ")[1]
    dim = s.split(" ")[2]
    q = "SELECT qty FROM cart_has_products WHERE p_id = %s AND cart_id = %s"
    cursor = g.conn.execute(q, (p_id, cart_id ))
    row = cursor.fetchone()
    if row:
      qty = row[0] + 1
      q = "UPDATE cart_has_products SET qty = %s WHERE cart_id=%s AND p_id=%s"
      cursor = g.conn.execute(q, (str(qty), cart_id, p_id, ))
    else:
      q = "INSERT INTO cart_has_products(cart_id, p_id, dim) VALUES (%s, %s, %s)"
      cursor = g.conn.execute(q, (cart_id, p_id, dim))
  for b in blazer:
    p_id = b.split(" ")[1]
    dim = b.split(" ")[2]
    q = "SELECT qty FROM cart_has_products WHERE p_id = %s AND cart_id = %s"
    cursor = g.conn.execute(q, (p_id, cart_id))
    row = cursor.fetchone()
    if row:
      qty = row[0] + 1
      q = "UPDATE cart_has_products SET qty = %s WHERE cart_id=%s AND p_id=%s"
      cursor = g.conn.execute(q, (str(qty), cart_id, p_id, ))
    else:
      q = "INSERT INTO cart_has_products(cart_id, p_id, dim) VALUES (%s, %s, %s)"
      cursor = g.conn.execute(q, (cart_id, p_id, dim))
  for s in shirt:
    p_id = s.split(" ")[1]
    dim = s.split(" ")[2]
    q = "SELECT qty FROM cart_has_products WHERE p_id = %s AND cart_id=%s"
    cursor = g.conn.execute(q, (p_id, cart_id))
    row = cursor.fetchone()
    if row:
      qty = row[0] + 1
      q = "UPDATE cart_has_products SET qty = %s WHERE cart_id=%s AND p_id=%s"
      cursor = g.conn.execute(q, (str(qty), cart_id, p_id, ))
    else:
      q = "INSERT INTO cart_has_products(cart_id, p_id, dim) VALUES (%s, %s, %s)"
      cursor = g.conn.execute(q, (cart_id, p_id, dim))
  for p in pant:
    p_id = p.split(" ")[1]
    dim = p.split(" ")[2]
    q = "SELECT qty FROM cart_has_products WHERE p_id = %s AND cart_id = %s"
    cursor = g.conn.execute(q, (p_id, cart_id))
    row = cursor.fetchone()
    if row:
      qty = row[0] + 1
      q = "UPDATE cart_has_products SET qty = %s WHERE cart_id=%s AND p_id=%s"
      cursor = g.conn.execute(q, (str(qty), cart_id, p_id, ))
    else:
      q = "INSERT INTO cart_has_products(cart_id, p_id, dim) VALUES (%s, %s, %s)"
      cursor = g.conn.execute(q, (cart_id, p_id, dim))
  
  q = "SELECT P.price, C.qty FROM Products P NATURAL JOIN cart_has_products C WHERE C.cart_id = %s" 
  cursor = g.conn.execute(q, (cart_id,))
  total = 0
  num_items = 0
  for row in cursor:
    print "price: " + str(row[0]) + "\nqty: " + str(row[1])
    total += row[0] * row[1]
    num_items += row[1]
  q = "UPDATE Cart  SET price = %s WHERE cart_id = %s"
  cursor = g.conn.execute(q, (total, cart_id,))
  q = "UPDATE Cart  SET num_items = %s WHERE cart_id = %s"
  cursor = g.conn.execute(q, (num_items, cart_id,))

  q = "SELECT type, price, color, fabric, dim, qty FROM cart_has_products C NATURAL JOIN products P WHERE C.cart_id = %s"
  cursor = g.conn.execute(q, (cart_id,))

  l = []
  for row in cursor:
    l.append(row)
    print "row: " + str(row)
  return render_template("cart.html", PRODUCT=l, C_ID=cart_id, PRICE=total, NUM=num_items )

@check_login
@app.route("/update_account_card/", methods=["POST","GET"])
def update_acc_card():
  print request.args
  print "\n"

  user_id = session.get('username')
  u_id = return_uid()

  name = request.args['Name']
  exp = request.args['Exp']
  ccn = request.args['Ccn']
  sec = request.args['Sec']

  print 'what'
  q = "INSERT INTO Creditcards(name, exp, ccnum, sec) VALUES (%s, %s, %s, %s) RETURNING cc_id"
  cursor = g.conn.execute(q, (name, exp, ccn, sec))
  cc_id = cursor.fetchone()[0]

  q = "INSERT INTO has_cc(u_id, cc_id) VALUES (%s, %s)"
  cursor = g.conn.execute(q, (u_id, cc_id))

  q = "SELECT * FROM Address A NATURAL JOIN has_add H WHERE u_id = %s"
  cursor = g.conn.execute(q, u_id)
  add = []
  for row in cursor:
    add.append(row)

  q = "SELECT * FROM CreditCards C NATURAL JOIN has_cc H WHERE u_id = %s"
  cursor = g.conn.execute(q, u_id)
  card = []
  for row in cursor:
    card.append(row)

  return render_template("account.html", USER=user_id, ADD_LIST=add, CARD_LIST=card)

@check_login
@app.route("/account/", methods=["POST","GET"])
def acc_settings():
  print request.args
  print "\n"

  user_id = session.get('username')
  u_id = return_uid()

  q = "SELECT * FROM Address A NATURAL JOIN has_add H WHERE u_id = %s"
  cursor = g.conn.execute(q, u_id)
  add = []
  for row in cursor:
    add.append(row)

  q = "SELECT * FROM CreditCards C NATURAL JOIN has_cc H WHERE u_id = %s"
  cursor = g.conn.execute(q, u_id)
  card = []
  for row in cursor:
    card.append(row)

  return render_template("account.html", USER=user_id, ADD_LIST=add, CARD_LIST=card)

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
