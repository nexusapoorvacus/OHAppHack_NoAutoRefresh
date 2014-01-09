# all the imports
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
	 abort, render_template, flash, jsonify
from contextlib import closing

# configuration - can be put in a different config files
DATABASE = 'ohapp.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

mode = 0

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

#initializes database
def init_db():
	with closing(connect_db()) as db:
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()

#More elegant way of opening and closing requests
@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	db = getattr(g, 'db', None)
	if db is not None:
		db.close()

# connect to specified database
#can open a connection on request and also from he the interactive Python shell or a script
def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

@app.route('/changedmode/<m>')
def changemode(m):
	global mode
	mode = m
	return redirect(url_for('show_entries'))

def sort(entries):
	for i in range(len(entries)):
		for j in range(i + 1, len(entries)):
			if entries[i]["Category"]< entries[j]["Category"]:
				entries[i], entries[j] = entries[j], entries[i]
	return entries

#The view function will pass the entries as dicts to the show_entries.html template and return the rendered one
@app.route('/')
def show_entries():
	cur = g.db.execute('select Name, Description, Category, id from entries order by id desc')
	entries = [dict(Name=row[0], Description=row[1], Category=row[2], id=row[3]) for row in cur.fetchall()][::-1]
	if mode == "Category":
		entries = sort(entries)
	return render_template('show_entries.html', entries=entries)

# @app.route('/entries')
# def entries():
# 	cur = g.db.execute('select Name, Description, Category, id from entries order by id desc')
# 	entries = [dict(Name=row[0], Description=row[1], Category=row[2], id=row[3]) for row in cur.fetchall()][::-1]
# 	if mode == "Category":
# 		entries = sort(entries)
# 	return render_template('entries.html', entries=entries)

#This view lets the user add new entries if they are logged in. This only responds to POST requests. If everything worked out well we will flash() an information message to the next request and redirect back to the show_entries page.
@app.route('/add', methods=['POST'])
def add_entry():
	if not session.get('logged_in'):
		abort(401)
	g.db.execute('insert into entries (Name, Description, Category) values (?, ?, ?)',
				 [request.form['Name'], request.form['Description'], request.form['Category']])
	g.db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries'))

@app.route('/delete')
def general_delete():
	if not session.get('logged_in'):
		abort(401)
	g.db.execute('delete from entries where id=(select min(id) from entries)') 
	g.db.commit()
	flash('The student was deleted')
	return redirect(url_for('show_entries'))

@app.route('/delete/<int:entry_id>/')
def delete_student(entry_id):
	if not session.get('logged_in'):
		abort(401)
	g.db.execute('delete from entries where id=' + str(entry_id))
	g.db.commit()
	flash('The student was deleted')
	return redirect(url_for('show_entries'))

@app.route('/helpedbystudent/<int:entry_id>/', methods=["POST"])
def helpedbystudent(entry_id):
	if not session.get('logged_in'):
		abort(401)
	peer_name = request.form["peername"]
	print(peer_name)
	g.db.execute('delete from entries where id=' + str(entry_id))
	g.db.commit()
	flash('The student was deleted')
	return redirect(url_for('show_entries'))

#These functions are used to sign the user in and out. Login checks the username and password against the ones from the configuration and sets the logged_in key in the session. If the user logged in successfully, that key is set to True, and the user is redirected back to the show_entries page. In addition, a message is flashed that informs the user that he or she was logged in successfully. If an error occurred, the template is notified about that, and the user is asked again.
@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':
		if request.form['username'] != app.config['USERNAME']:
			error = 'Invalid username'
		elif request.form['password'] != app.config['PASSWORD']:
			error = 'Invalid password'
		else:
			session['logged_in'] = True
			flash('You were logged in')
			return redirect(url_for('show_entries'))
	return render_template('login.html', error=error)

# The logout function, on the other hand, removes that key from the session again. We use a neat trick here: if you use the pop() method of the dict and pass a second parameter to it (the default), the method will delete the key from the dictionary if present or do nothing when that key is not in there. 
@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	flash('You were logged out')
	return redirect(url_for('show_entries'))

#fires up server if we want to run this as a stand alone application
if __name__ == '__main__':
	#app.run(host = '0.0.0.0')
	app.run()