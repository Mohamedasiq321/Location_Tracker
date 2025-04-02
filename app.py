from flask import Flask, render_template, request, redirect, url_for, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/location_tracker"
mongo = PyMongo(app)

def get_users_collection():
    return mongo.db.users

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        org_name = request.form['org_name']
        
        users = get_users_collection()
        user = users.find_one({"email": email, "org_name": org_name})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['email'] = user['email']
            session['org_name'] = user['org_name']
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials or organization name."
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        users = get_users_collection()
        if users.find_one({"email": email}):
            return "Email already registered."
        
        users.insert_one({"email": email, "password": hashed_password})
        return redirect(url_for('login'))
    
    invite_code = request.args.get('invite', '')
    return render_template('register.html', invite_code=invite_code)

@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        org_name = request.form['org_name']
        hashed_password = generate_password_hash(password)
        
        users = get_users_collection()
        if users.find_one({"email": email, "org_name": org_name}):
            return "Admin already registered."
        
        users.insert_one({"email": email, "password": hashed_password, "org_name": org_name, "role": "admin"})
        return redirect(url_for('login'))
    
    return render_template('admin_register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return f"Welcome {session['email']} from {session['org_name']}!"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
