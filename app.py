from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import random
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///evoting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email Configuration for Flask-Mail 
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'dmtoravi@gmail.com'
app.config['MAIL_PASSWORD'] = 'naexdkaqfqnukxqh'  

mail = Mail(app)
db = SQLAlchemy(app)

# ----------------------- MODELS -----------------------

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    has_voted = db.Column(db.Boolean, default=False)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(100), nullable=False)
    votes = db.Column(db.Integer, default=0)

# --------------------- ROUTES ------------------------

@app.route('/') #for loding page
def loading():
    return render_template('loading.html')

@app.route('/home')
def home():
    return render_template('home.html') 

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == 'ravi' and request.form['password'] == '1234':
            session['admin'] = True
            return redirect('/admin/dashboard')
        else:
            flash('Invalid credentials')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin/login')
    voters = Voter.query.all()
    candidates = Candidate.query.all()
    return render_template('admin_dashboard.html', voters=voters, candidates=candidates)

@app.route('/admin/add_voter', methods=['GET', 'POST'])
def add_voter():
    if request.method == 'POST':
        voter_id = request.form['voter_id']
        email = request.form['email']
        new_voter = Voter(voter_id=voter_id, email=email)
        db.session.add(new_voter)
        db.session.commit()
        return redirect('/admin/dashboard')
    return render_template('add_voter.html')

@app.route('/admin/add_candidate', methods=['GET', 'POST'])
def add_candidate():
    if request.method == 'POST':
        name = request.form['name']
        image = request.files['image']
        image_path = 'static/uploads/candidates/' + image.filename
        image.save(image_path)
        new_candidate = Candidate(name=name, image=image_path)
        db.session.add(new_candidate)
        db.session.commit()
        return redirect('/admin/dashboard')
    return render_template('add_candidate.html')

@app.route('/view_candidates')
def view_candidates():
    candidates = Candidate.query.all()
    return render_template('view_candidates.html', candidates=candidates)

@app.route('/voter/login', methods=['GET', 'POST'])
def voter_login():
    if request.method == 'POST':
        voter_id = request.form['voter_id']
        voter = Voter.query.filter_by(voter_id=voter_id).first()
        if voter:
            otp = random.randint(1000, 9999)
            session['otp'] = str(otp)
            session['voter_id'] = voter_id
            try:
                msg = Message('Your OTP for voting', sender='dmtoravi@gmail.com', recipients=[voter.email])
                msg.body = f'Your OTP is {otp}'
                mail.send(msg)
            except Exception as e:
                return f"Error sending OTP: {str(e)}"
            return redirect('/voter/verify')
        else:
            flash('Voter ID not found')
    return render_template('voter_login.html')

@app.route('/voter/verify', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        if session.get('otp') == request.form['otp']:
            return redirect('/vote')
        else:
            flash('Invalid OTP')
    return render_template('verify.html')

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    voter = Voter.query.filter_by(voter_id=session.get('voter_id')).first()

    if voter.has_voted:
        return render_template('already_voted.html')  

    candidates = Candidate.query.all()

    if request.method == 'POST':
        selected = request.form['candidate']
        candidate = Candidate.query.get(selected)
        candidate.votes += 1
        voter.has_voted = True
        db.session.commit()
        return render_template('thankyou.html')  

    return render_template('vote.html', candidates=candidates)


@app.route('/admin/results')
def results():
    candidates = Candidate.query.all()
    return render_template('result.html', candidates=candidates)




@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('home'))

# --------------------- MAIN -------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
