from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pdfplumber
import pandas as pd
import re
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='template')
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=true)
    username = db.Column(db.String(150), unique=true, nullable=false)
    password = db.Column(db.String(150), nullable=false)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('homepageV1'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash('Invalid credentials')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('homepageV1'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def homepageV1():
    return render_template('homepage.html')


@app.route('/extract-pdf-dataV1', methods=['POST'])
@login_required
def extract_pdf_data():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        pdf_file = request.files['file']
        if pdf_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if pdf_file and pdf_file.filename.endswith('.pdf'):
            data = extract_table_from_pdf(pdf_file)
            return jsonify(data), 200

        return jsonify({'error': 'Invalid file format. Only PDF files are supported.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def extract_from_pdf(pdf_file_path):
    pass  # Existing implementation


def extract_table_from_pdf(pdf_file_path):
    pass  # Existing implementation


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=true, port=8000)