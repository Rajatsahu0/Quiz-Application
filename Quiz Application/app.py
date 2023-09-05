from flask import Flask, render_template, redirect, request, url_for, session, flash
import sqlite3, random , secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = secrets.token_hex(16) 

DATABASE = "Quiz.db"

def create_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS quiz_submission (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, score INTEGER, time_taken FLOAT)''')
    conn.commit()
    conn.close()

def save_submission_time(name, score, time_taken):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quiz_submission (name, score, time_taken) VALUES (?, ?, ?)", (name, score, time_taken))
    conn.commit()
    conn.close()

def get_winner():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, score, time_taken FROM quiz_submission ORDER BY score DESC, time_taken ASC")
    winners = cursor.fetchall()
    conn.close()
    return winners

questions = [
    {"question": "What is the capital of France?", "options": ["London", "Berlin", "Paris", "Madrid"], "correct_answer": "Paris"},
    {"question": "Who Invented the 3-D printer?", "options": ["Nick Holonyak", "Elias Howe", "Chuck Hull", "Christiaan Huygens"], "correct_answer": "Chuck Hull"},
    {"question": "What is the maximum number of Members in Lok Sabha?", "options": ["512", "542", "552", "532"], "correct_answer": "552"},
    {"question": "Fatehpur Sikri was founded as the capital of the Mughal Empire by ______.", "options": ["Jahangir", "Akbar", "Babur", "Humayun"], "correct_answer": "Akbar"},
    {"question": "Who was court poet of Samudragupta?", "options": ["Chand Bardai", "Bhavabhuti", "Banabhatta", "Harishen"], "correct_answer": "Harishen"},
    # {"question" : "Which Veda depicts the information about the most ancient Vedic age culture?", "options": ["Samaveda","Atharvaveda","Rig Veda","Yajurveda"], "correct_answer":"Rig Veda"} ,
    # {"question" : "Which of the following rulers issued copper coins named as Jittal? ", "options": ["Iltutmish","Firoz Shah Tughlaq","Mohammad bin Tughlaq","Quli Qutub Shah"], "correct_answer":"Iltutmish"} ,
    # {"question" : "Who was the first Tirthankara of the Jains?", "options": ["Ajitnath","Rishabhdev","Aristhenemi","Parshwnath"], "correct_answer":"Rishabhdev"} ,
    # {"question" : "The maginot line exists between which country? ", "options": ["France and Germany","Germany and Poland","Namibia and Angola","USA and Canada"], "correct_answer":"France and Germany"} ,
    # {"question" : "The Grand Canyon located in which country?", "options": ["Ghana","The US","Canada","Bolivia"], "correct_answer":"The US"} ,
    # {"question" : "What does Triratna mean in Buddhism? ", "options": ["Satya, Ahimsa, Karuna","Sheel, Samadhi, Sangha","Tripitaka","Buddha, Dhamma (dharma), Sangha"], "correct_answer":"Buddha, Dhamma (dharma), Sangha"} ,
    # {"question" : "The famous Lucknow pact of 1916 was signed between __________.", "options": ["Mahatma Gandhi and Muhammad Ali Jinnah","Bal Gangadhar Tilak and Aga Khan","Mahatma Gandhi and Aga Khan","Bal Gangadhar Tilak and Muhammad Ali Jinnah"], "correct_answer":"Bal Gangadhar Tilak and Muhammad Ali Jinnah"} ,
    # {"question" : "In which year Forest Conservation Act was passed? ", "options": ["1980","1988","1986","1990"], "correct_answer":"1980"} ,
    # {"question" : "Kalinga's King Kharvela was associated with which of the following dynasty? ", "options": ["Rath-Bhojak dynasty","Satvahana dynasty","Mahameghavahana dynasty","Haryanka dynasty"], "correct_answer":"Mahameghavahana dynasty"} ,
    # {"question" : "The dockyard was found in which of the following sites of Indus valley civilization?", "options": ["Kalibangan","Banawali","Chanhudaro","Lothal"], "correct_answer":"Lothal"} ,
]

random.shuffle(questions)

user_score = 0
current_question_index = -1
quiz_start_time = None
quiz_time_limit = 900

@app.route('/')
def index():
    global current_question_index, user_score, quiz_start_time
    current_question_index = -1
    user_score = 0
    quiz_start_time = None
    return render_template('index.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        flash('Account created successfully! You can now log in.')
        return render_template('admin_login.html')
    return render_template('admin_register.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
        admin = cursor.fetchone()
        conn.close()

        if admin and admin[2] == password:
            return redirect(url_for('admin_dashboard'))
        else:
            return "INVALID username or password"
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    winners = get_winner()
    return render_template('admin_dashboard.html', winners=winners)

@app.route('/participant/login', methods=['GET', 'POST'])
def participant_login():
    if request.method == 'POST':
        name = request.form.get('name', '')
        if not name:
            return redirect(url_for('participant_login'))

        session['name'] = name  # Store the participant's name in the session
        return redirect(url_for('quiz'))

    return render_template('participant_login.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    global current_question_index, user_score, quiz_start_time

    name = session.get('name', '')  # Retrieve the participant's name from the session

    if request.method == 'POST':
        if current_question_index >= 0:
            answer = request.form.get('answer')
            correct_answer = questions[current_question_index]['correct_answer']
            if answer == correct_answer:
                user_score += 1

        length = len(questions)
        if current_question_index < length - 1:
            current_question_index += 1
        else:
            quiz_end_time = datetime.now()
            time_taken = (quiz_end_time - quiz_start_time).total_seconds()
            save_submission_time(name, user_score, time_taken)
            return redirect(url_for('result'))

        question = questions[current_question_index]
        return render_template('question.html', question=question, user_score=user_score, length=length, current_question_index=current_question_index)

    if quiz_start_time is None:
        quiz_start_time = datetime.now()

    length = len(questions)
    if current_question_index < length - 1:
        current_question_index += 1
    else:
        return redirect(url_for('result'))

    question = questions[current_question_index]
    random.shuffle(question['options'])
    return render_template('question.html', question=question, user_score=user_score, length=length, current_question_index=current_question_index)

@app.route('/result')
def result():
    global user_score, quiz_start_time, current_question_index

    name = session.get('name', '')

    if quiz_start_time is not None and current_question_index == len(questions) - 1:
        quiz_end_time = datetime.now()
        time_taken = (quiz_end_time - quiz_start_time).total_seconds()

    score = user_score
    user_score = 0
    current_question_index = -1
    quiz_start_time = None
    return render_template('result.html', name=name, score=score)

if __name__ == '__main__':
    create_table()
    app.run(debug=True)
