import operator
from flask import Flask, render_template, request, redirect, url_for, session,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models.model import db, User, Admin ,Subject ,Chapter ,Quiz ,Question ,Score 
from flask_login import current_user
from models.model import db 
from sqlalchemy.sql import func
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_platform.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('user_dashboard'))  # Redirect to user dashboard

        return render_template("index.html", again=True)

    return render_template("index.html", again=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('user_dashboard'))

    return render_template("index.html", again=True)  # Ensure a valid response


 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form["username"]
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return render_template("userregister.html", again=True)

        # Hash password
        hashed_password = generate_password_hash(request.form["password"], method='pbkdf2:sha256')

        # Convert date string to datetime object
        dob = datetime.strptime(request.form["dob"], "%Y-%m-%d")

        new_user = User(
            username=username,
            password=hashed_password,
            full_name=request.form["full_name"],
            qualification=request.form["qualification"],
            dob=dob
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('index'))  # Redirect to login page after registration

    return render_template("userregister.html", again=False)




@app.route('/admin_dashboard')
def admin_dashboard():
    subjects = Subject.query.all()
    return render_template("admin_dashboard.html", subjects=subjects)



@app.route('/user_dashboard')
def user_dashboard():
    # Fetch the logged-in user
    user = User.query.filter_by(id=session.get('user_id')).first()  # Adjust based on your authentication system
    full_name = user.full_name if user else "Guest"  

    # Fetch all quizzes
    quizzes = Quiz.query.all()

    return render_template('user_dashboard.html', quizzes=quizzes, full_name=full_name)

with app.app_context():
    if not Admin.query.first():
        new_admin = Admin(username="admin@gmail.com", password=generate_password_hash("admin123"))
        db.session.add(new_admin)
        db.session.commit()

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Correcting the query
        admin_user = Admin.query.filter_by(username=username).first()

        if admin_user and check_password_hash(admin_user.password, password):
            session['admin_id'] = admin_user.id
            return redirect(url_for("admin_dashboard"))

        return render_template("adminlogin.html", again=True)

    return render_template("adminlogin.html", again=False)

@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')

        if Subject.query.filter_by(name=name).first():
            return render_template('add_subject.html', error="Subject already exists", subject=name)


        new_subject = Subject(name=name, description=description)
        db.session.add(new_subject)
        db.session.commit()

        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_subject.html')



@app.route('/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/add_chapter/<int:subject_id>', methods=['GET', 'POST'])
def add_chapter(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    if request.method == 'POST':
        name = request.form['name']
        new_chapter = Chapter(name=name, subject=subject)
        db.session.add(new_chapter)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))  # Redirect to Admin Dashboard
    
    return render_template('add_chapter.html', subject=subject, chapters=subject.chapters)

@app.route('/edit_chapter/<int:chapter_id>', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)

    if request.method == 'POST':
        chapter_name = request.form.get('name')  
        num_questions = request.form.get('num_questions', type=int)  

        if chapter_name:
            chapter.name = chapter_name

        # Get existing quiz count
        existing_quizzes = len(chapter.quizzes)

        if num_questions != existing_quizzes:
            if num_questions > existing_quizzes:
                # Add new quizzes with dynamic titles
                for i in range(existing_quizzes + 1, num_questions + 1):
                    new_quiz = Quiz(chapter_id=chapter.id, title=f"Quiz {i}")
                    db.session.add(new_quiz)

            elif num_questions < existing_quizzes:
                # Sort quizzes by ID (oldest first) before removing
                quizzes_to_remove = sorted(chapter.quizzes, key=lambda q: q.id)[:existing_quizzes - num_questions]
                for quiz in quizzes_to_remove:
                    db.session.delete(quiz)

        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    num_questions = len(chapter.quizzes)
    return render_template('edit_chapter.html', chapter=chapter, num_questions=num_questions)


@app.route('/delete_chapter/<int:chapter_id>', methods=['POST'])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return "Chapter not found", 404  # Debugging step

    
    db.session.delete(chapter)
    db.session.commit()
    return redirect(url_for('admin_dashboard', chapter_id=chapter_id))


@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        chapter_id = request.form.get('chapter_id') 
        quiz_id = request.form.get('quiz_id')
        question_statement = request.form.get('question-statement')
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        correct_option = request.form.get('correct-option')

        new_question = Question(
            chapter_id=chapter_id,
            quiz_id=quiz_id,# Correct field name
            question_statement=question_statement,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=int(correct_option)
        )
        db.session.add(new_question)
        db.session.commit()

        flash('Question added successfully!', 'success')
        return redirect(url_for('admin_quiz_panel'))  # Redirect to Admin Quiz Panel

    return render_template('add_question.html')

@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        # Update the question details from the form
        question.chapter_id = request.form['chapter_id']
        question.quiz_id = request.form['quiz_id']
        question.question_statement = request.form['question-statement']
        question.option1 = request.form['option1']
        question.option2 = request.form['option2']
        question.option3 = request.form['option3']
        question.option4 = request.form['option4']
        question.correct_option = int(request.form['correct-option'])

        try:
            db.session.commit()
            flash("Question updated successfully!", "success")
            return redirect(url_for('admin_quiz_panel'))  # Redirect to admin panel
        except:
            db.session.rollback()
            flash("Error updating the question.", "danger")

    return render_template('edit_question.html', question=question)

@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)

    try:
        db.session.delete(question)
        db.session.commit()
        flash("Question deleted successfully!", "success")
    except:
        db.session.rollback()
        flash("Error deleting the question.", "danger")

    return redirect(url_for('admin_quiz_panel'))  # Redirect to admin panel

@app.route('/admin_quiz_panel')
def admin_quiz_panel():
    quizzes = Quiz.query.outerjoin(Chapter).outerjoin(Subject).all()

    return render_template('quiz.html', quizzes=quizzes, full_name=User.full_name)

@app.route('/add_quiz', methods=['GET', 'POST'])
def add_quiz():
    if request.method == 'POST':
        chapter_id = request.form.get('chapter_id')
        title = request.form.get('title')
        date_of_quiz = request.form.get('date_of_quiz')  # MM/DD/YYYY format
        time_duration = request.form.get('time_duration')  # HH:MM format

        if not chapter_id or not date_of_quiz or not time_duration:
            return "Missing form fields", 400

        # Convert date_of_quiz to datetime object (MM/DD/YYYY format)
        date_of_quiz = datetime.strptime(date_of_quiz, "%Y-%m-%d").date()


        # Convert time_duration to time object (HH:MM format)
        time_duration = datetime.strptime(time_duration, "%H:%M").time()

        new_quiz = Quiz(
            chapter_id=chapter_id,
            title=title,
            date_of_quiz=date_of_quiz,
            time_duration=time_duration
        )

        db.session.add(new_quiz)
        db.session.commit()
        return redirect(url_for('admin_quiz_panel'))

    return render_template('add_quiz.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    if not query:
        return render_template('search_results.html', subjects=[], quizzes=[], scores=[], users=[])

    users = User.query.filter(User.full_name.ilike(f'%{query}%')).all()
    subjects = Subject.query.filter(Subject.name.ilike(f'%{query}%')).all()
    quizzes = Quiz.query.filter(Quiz.title.ilike(f'%{query}%')).all()
    scores = Score.query.filter(Score.score_value.ilike(f'%{query}%')).all()  # If needed

    return render_template('search_results.html', users=users, subjects=subjects, quizzes=quizzes, scores=scores)

@app.route('/quiz_info/<int:quiz_id>')
def quiz_info(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('quiz_info.html', quiz=quiz)

from sqlalchemy.sql import case

@app.route('/scores')
def scores():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)
    full_name = user.full_name if user else "Guest"

    user_scores = (
        db.session.query(
            Quiz.id,
            Quiz.title,
            func.count(Question.id.distinct()).label("total_questions"),
            func.count(func.distinct(Score.question_id)).filter(Score.score_value > 0).label("total_score"),
            func.max(Score.timestamp).label("latest_attempt")
        )
        .join(Score, Score.quiz_id == Quiz.id)
        .join(Question, Question.quiz_id == Quiz.id)
        .filter(Score.user_id == user_id)
        .group_by(Quiz.id, Quiz.title)
        .order_by(func.max(Score.timestamp).desc())
        .all()
    )

    return render_template('scores.html', scores=user_scores, full_name=full_name)



@app.route('/user_summary')
def user_summary():
    # Assuming user authentication is handled, retrieve the logged-in user's full name
    user = User.query.filter_by(id=session.get('user_id')).first()  # Adjust based on your auth logic
    full_name = user.full_name if user else "Guest"

    # Fetch subject-wise quiz counts
    subject_data = (
        db.session.query(Subject.name, func.count(Quiz.id))
        .join(Chapter, Chapter.subject_id == Subject.id)  # Correct join via Chapter
        .join(Quiz, Quiz.chapter_id == Chapter.id)
        .group_by(Subject.name)
        .all()
    )
    subjects = [sub[0] for sub in subject_data]
    quizzes_count = [sub[1] for sub in subject_data]

    # Fetch month-wise quiz counts
    month_data = (
        db.session.query(func.strftime('%m', Quiz.date_of_quiz), func.count(Quiz.id))
        .group_by(func.strftime('%m', Quiz.date_of_quiz))
        .all()
    )
    months = [m[0] for m in month_data]  # Extract month (01, 02, etc.)
    quizzes_per_month = [m[1] for m in month_data]

    return render_template(
        'user_summary.html',
        full_name=full_name,  # Pass full name to the template
        subjects=subjects,
        quizzes_count=quizzes_count,
        months=months,
        quizzes_per_month=quizzes_per_month
    )

@app.route('/adminsummary')
def adminsummary():
    # Retrieve subjects
    subjects = [subject.name for subject in Subject.query.all()]

    # Retrieve top scores for each subject
    top_scores = []
    for subject in subjects:
        top_score = (
            db.session.query(func.max(Score.score_value))
            .join(User, Score.user_id == User.id)
            .join(Quiz, Score.quiz_id == Quiz.id)
            .join(Chapter, Quiz.chapter_id == Chapter.id)
            .join(Subject, Chapter.subject_id == Subject.id)
            .filter(Subject.name == subject)
            .scalar()
        )
        top_scores.append(top_score if top_score else 0)

    # Retrieve user attempts for each subject
    user_attempts = []
    for subject in subjects:
        attempts = (
            db.session.query(func.count(func.distinct(Score.user_id)))
            .join(Quiz, Score.quiz_id == Quiz.id)
            .join(Chapter, Quiz.chapter_id == Chapter.id)
            .join(Subject, Chapter.subject_id == Subject.id)
            .filter(Subject.name == subject)
            .scalar()
        )
        user_attempts.append(attempts)

    return render_template('admin_summary.html', subjects=subjects, top_scores=top_scores, user_attempts=user_attempts)


@app.route('/start_quiz/<int:quiz_id>')
def start_quiz(quiz_id):
    session['quiz_id'] = quiz_id
    session['question_number'] = 1
    return redirect(url_for('next_question', quiz_id=quiz_id,question_number=1))


@app.route('/quiz/<int:quiz_id>/<int:question_number>')
def next_question(quiz_id, question_number):

    session_quiz_id = session.get('quiz_id')
    if not session_quiz_id or session_quiz_id != quiz_id:
        flash("No quiz found. Start a quiz first.")
        return redirect(url_for('user_dashboard'))
    
    quiz = Quiz.query.get(quiz_id)
    question = Question.query.filter_by(quiz_id=quiz_id).offset(question_number - 1).first()
    total_questions = Question.query.filter_by(quiz_id=quiz_id).count()

    if not question:
        return redirect(url_for('submit_quiz', quiz_id=quiz_id))
    return render_template('start_quiz.html', question=question, question_number=question_number, total_questions=total_questions, quizzes=quiz)

@app.route('/save_answer/<int:quiz_id>/<int:question_id>/<int:question_number>', methods=['POST'])
def save_answer(quiz_id, question_id, question_number):
    selected_option = int(request.form.get('option'))
    question = Question.query.get(question_id)
    correct_option = question.correct_option
    is_correct = (selected_option == correct_option)
    score_value = 1 if is_correct else 0  

    existing_score = Score.query.filter_by(user_id=session['user_id'], quiz_id=quiz_id, question_id=question_id).first()
    if existing_score:
        print(f"Updating existing score for user {session['user_id']}, question {question_id}")
        existing_score.selected_option = selected_option
        existing_score.is_correct = is_correct
        existing_score.score_value = score_value
        existing_score.timestamp = datetime.utcnow()
    else:
        print(f"Creating new score for user {session['user_id']}, question {question_id}")
        new_score = Score(quiz_id=quiz_id, user_id=session['user_id'], question_id=question_id,
                          selected_option=selected_option, is_correct=is_correct,
                          score_value=score_value, timestamp=datetime.utcnow())
        db.session.add(new_score)

    db.session.commit()
    return redirect(url_for('next_question', quiz_id=quiz_id, question_number=question_number + 1))

@app.route('/submit_quiz/<int:quiz_id>')
def submit_quiz(quiz_id):
    score_value = db.session.query(func.sum(Score.score_value)).filter_by(user_id=session['user_id'], quiz_id=quiz_id).scalar() or 0
    total_questions = Question.query.filter_by(quiz_id=quiz_id).count()
    
    flash(f"Quiz completed! Your score: {score_value}/{total_questions}")
    
    return redirect(url_for('scores'))


@app.route('/logout')
def logout():
    session.clear()  # Clears session data
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)



