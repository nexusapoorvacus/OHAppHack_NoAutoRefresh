# all the imports
import sqlite3
import time, datetime
from flask import Flask, request, session, g, redirect, url_for, \
	 abort, render_template, flash, jsonify
#from flask.ext.login import fresh_login_required, LoginManager
from contextlib import closing

# configuration - can be put in a different config files
DATABASE = '/tmp/ohapp.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

STUDENT_USERNAME = 'username'
STUDENT_PASSWORD = 'password'

mode = 0
TAview = False 

#login_manager = LoginManager()

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
#@fresh_login_required
def show_entries():
	cur = g.db.execute('select Name, Description, Category, id, Position, Username, Password, Time from entries order by Position')
	entries = [dict(Name=row[0], Description=row[1], Category=row[2], id=row[3], Position=row[4], Username=row[5], Password=row[6], Time=row[7]) for row in cur.fetchall()]
	if mode == "Category":
		entries = sort(entries)
	return render_template('show_entries.html', entries=entries, TAview=TAview, STUDENT_USERNAME=STUDENT_USERNAME, USERNAME=USERNAME, STUDENT_PASSWORD=STUDENT_PASSWORD)


@app.route('/entries')
def entries():
	cur = g.db.execute('select Name, Description, Category, id from entries order by id desc')
	entries = [dict(Name = row[0], Description = row[1], Category = row[2], id = row[3]) for row in cur.fetchall()][::-1]
	if m == "Category":
		entries = sort(entries)
	return render_template('entries.html', entries=entries)

#This view lets the user add new entries if they are logged in. This only responds to POST requests. If everything worked out well we will flash() an information message to the next request and redirect back to the show_entries page.
@app.route('/add', methods=['POST'])
def add_entry():
	if not session.get('logged_in'):
		abort(401)
	countTable = g.db.execute('select count(*) from entries').fetchall()
	Position = 1 + countTable[0][0]

	ts = time.time()
	st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

	if not TAview:
		g.db.execute('insert into entries (Name, Description, Category, Username, Password, Position, Time) values (?, ?, ?, ?, ?, ?, ?)',
				 [request.form['Name'], request.form['Description'], request.form['Category'], STUDENT_USERNAME, STUDENT_PASSWORD, Position, st])
	else:
		g.db.execute('insert into entries (Name, Description, Category, Username, Password, Position, Time) values (?, ?, ?, ?, ?, ?, ?)',
				 [request.form['Name'], request.form['Description'], request.form['Category'], USERNAME, PASSWORD, Position, st])

	g.db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries'))

@app.route('/delete')
def general_delete():
	if not session.get('logged_in'):
		abort(401)
	#g.db.execute('delete from entries where id=(select min(id) from entries)') 
	g.db.execute('delete from entries where Position=1')
	g.db.execute('update entries set Position=Position-1')
	g.db.commit()
	flash('The student was deleted')
	return redirect(url_for('show_entries'))

@app.route('/delete/<int:entry_id>')
def delete_student(entry_id):
	if not session.get('logged_in'):
		abort(401)

	if not TAview:
		cur = g.db.execute('select Name, Description, Category, id, Username, Password from entries order by id desc')
		entries = [dict(Name=row[0], Description=row[1], Category=row[2], id=row[3], Username=row[4], Password=row[5]) for row in cur.fetchall()][::-1]
		studentusername = ""
		studentpassword = ""
		for i in range(len(entries)):
			if entries[i]["id"] == entry_id:
				studentusername = entries[i]["Username"]
				studentpassword = entries[i]["Password"]
		if studentusername == STUDENT_USERNAME and studentpassword == STUDENT_PASSWORD:
			row = g.db.execute('select id, Position from entries where id=?', [entry_id]).fetchall()[0]
			entry = dict(id=row[0], Position=row[1])
			g.db.execute('delete from entries where id=' + str(entry_id))
			print(entry['Position'])
			g.db.execute('update entries set Position=Position-1 where Position>?',[entry['Position']])
			g.db.commit()
			flash('The student was deleted')
			return redirect(url_for('show_entries'))
		else:
			flash('You do not have permission to delete ' + studentusername)
			return redirect(url_for('show_entries'))
	else:
		row = g.db.execute('select id, Position from entries where id=?', [entry_id]).fetchall()[0]
		entry = dict(id=row[0], Position=row[1])
		g.db.execute('delete from entries where id=' + str(entry_id))
		g.db.execute('update entries set Position=Position-1 where Position>?',[entry['Position']])
		g.db.commit()
		flash('The student was deleted')
		return redirect(url_for('show_entries'))

@app.route('/helpedbystudent', methods=["POST"])
def helpedbystudent():
	if not session.get('logged_in'):
		abort(401)
	peer_name = request.form["peername"]
	entry_id = request.form["entryid"]
	print("Peer Name:", peer_name)
	print("Entry ID:", entry_id)

	if not TAview:
		cur = g.db.execute('select Name, Description, Category, id, Username, Password from entries order by id desc')
		entries = [dict(Name=row[0], Description=row[1], Category=row[2], id=row[3], Username=row[4], Password=row[5]) for row in cur.fetchall()][::-1]
		studentusername = ""
		studentpassword = ""
		for i in range(len(entries)):
			if entries[i]["id"] == int(entry_id):
				studentusername = entries[i]["Username"]
				studentpassword = entries[i]["Password"]
		if studentusername == STUDENT_USERNAME and studentpassword == STUDENT_PASSWORD:
			row = g.db.execute('select id, Position from entries where id=?', [entry_id]).fetchall()[0]
			entry = dict(id=row[0], Position=row[1])
			g.db.execute('delete from entries where id=' + str(entry_id))
			print(entry['Position'])
			g.db.execute('update entries set Position=Position-1 where Position>?',[entry['Position']])
			g.db.commit()
			flash('The student was deleted')

			row = g.db.execute('select id, Position from entries where id=?', [peer_name]).fetchall()[0]
			peerid = row[0] #14
			peerpos = row[1] #5
			print(peerid, peerpos, peerpos-1)
			studentabove = g.db.execute('select id, Position from entries where Position=?', [peerpos - 1]).fetchall()[0]
			aboveid = studentabove[0]
			abovepos = studentabove[1]
			print(aboveid, abovepos)
			if(peerpos != 1):
				g.db.execute('update entries set position=? where id=?', [abovepos, peerid])
				g.db.execute('update entries set position=? where id=?', [peerpos, aboveid])
				g.db.commit()
			return redirect(url_for('show_entries'))
		#	return redirect(url_for('show_entries'))
		else:
			flash('You do not have permission to delete ' + studentusername)
			return redirect(url_for('show_entries'))
	else:
		row = g.db.execute('select id, Position from entries where id=?', [entry_id]).fetchall()[0]
		entry = dict(id=row[0], Position=row[1])
		g.db.execute('delete from entries where id=' + str(entry_id))
		g.db.execute('update entries set Position=Position-1 where Position>?',[entry['Position']])
		g.db.commit()
		flash('The student was deleted')
		return redirect(url_for('show_entries'))

@app.route('/reorder', methods=['POST'])
def reorder_entry():
	if not session.get('logged_in'):
		abort(401)
	#form (id, current_position) pairs, preparing for changing the database
	pos, pairs = 0, []
	for ele in request.json:
		pos += 1
		id = int(ele) #json stores the list of entries' ids in unicode
		pairs.append((id, pos))
	for id, pos in pairs:
		g.db.execute('update entries set position=? where id=?', [pos, id])
	g.db.commit()

	return redirect(url_for('show_entries'))

#These functions are used to sign the user in and out. Login checks the username and password against the ones from the configuration and sets the logged_in key in the session. If the user logged in successfully, that key is set to True, and the user is redirected back to the show_entries page. In addition, a message is flashed that informs the user that he or she was logged in successfully. If an error occurred, the template is notified about that, and the user is asked again.
@app.route('/login', methods=['GET', 'POST'])
def login():
	global TAview, STUDENT_USERNAME, STUDENT_PASSWORD
	error = None
	if request.method == 'POST':
		if request.form['username'] == app.config['USERNAME'] and request.form['password'] == app.config['PASSWORD']:
			session['logged_in'] = True
			TAview = True
			STUDENT_USERNAME = None 
			STUDENT_PASSWORD = None 
			flash('You were logged in as a TA')
			return redirect(url_for('show_entries'))
		else:
			session['logged_in'] = True
			TAview = False
			STUDENT_USERNAME = request.form['username']
			STUDENT_PASSWORD = request.form['password']
			flash('You were logged in as a student')
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
