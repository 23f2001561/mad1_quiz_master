from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_platform.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)

# Admin Table (Only one admin, predefined in DB)
class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

# User Table
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    full_name = db.Column(db.String, nullable=False)
    qualification = db.Column(db.String)
    dob = db.Column(db.DateTime)

# Subject Table
class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.Text)
    chapters = db.relationship("Chapter", back_populates="subject", cascade="all, delete-orphan")

# Chapter Table
class Chapter(db.Model):
    __tablename__ = 'chapters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    
    subject = db.relationship("Subject", back_populates="chapters")
    quizzes = db.relationship("Quiz", back_populates="chapter", cascade="all, delete-orphan")
    questions = db.relationship("Question", back_populates="chapter", cascade="all, delete-orphan")  # ✅ Add relationship


# Quiz Table
class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    date_of_quiz = db.Column(db.Date)
    time_duration = db.Column(db.Time)  # Format: HH:MM
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id')) 
    subject = db.relationship('Subject', backref='quizzes')
    chapter = db.relationship("Chapter", back_populates="quizzes")
    questions = db.relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    scores = db.relationship("Score", back_populates="quiz", cascade="all, delete-orphan")

# Question Table
class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)  
    question_statement = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String, nullable=False)
    option2 = db.Column(db.String, nullable=False)
    option3 = db.Column(db.String, nullable=False)
    option4 = db.Column(db.String, nullable=False)
    correct_option = db.Column(db.Integer, nullable=False) 
    quiz = db.relationship("Quiz", back_populates="questions")
    chapter = db.relationship("Chapter", back_populates="questions")  
    scores = db.relationship("Score", back_populates="question", cascade="all, delete-orphan")
class Score(db.Model):
    __tablename__ = 'scores'

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    selected_option = db.Column(db.Integer, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    score_value = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    quiz = db.relationship("Quiz", back_populates="scores")
    user = db.relationship("User")
    question = db.relationship("Question")  

    __table_args__ = (db.UniqueConstraint('user_id', 'quiz_id', 'question_id', name='unique_score_entry'),)
  
    

# Create the database and tables
with app.app_context():
    db.create_all()

# Prepopulate Admin
with app.app_context():
    if not Admin.query.first():
        admin = Admin(username="admin@gmail.com", password=generate_password_hash("admin123"))
        db.session.add(admin)
        db.session.commit()

print("Database and tables created successfully!")
