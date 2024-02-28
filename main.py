from crypt import methods
import email
from fileinput import filename
from http.client import responses
import logging
from os import access
from sqlite3 import Cursor
from urllib import response
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import math, random
from flask_mail import Mail, Message
from datetime import datetime
import numpy as np
from pandas import read_sql
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import pickle
from io import TextIOWrapper
import csv, codecs


app = Flask(__name__)

app.secret_key = 'our_super_secret_password'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'our_super_secret_password'
app.config['MYSQL_DB'] = 'pythonlogin'

# Intialize MySQL
mysql = MySQL(app)

# Mail server config
sender = "001tatyavinchu@gmail.com"
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = '001tatyavinchu@gmail.com'
app.config['MAIL_PASSWORD'] = 'TatyaVinchu@12345'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


@app.route('/start')
def start():
    return render_template('start.html')


@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['access'] = account['access']
            session['csid'] = account['csid']
            print(account)
            if account['access'] == 'a':
                return redirect(url_for('administrator'))
            if account['access'] == 't':
                return redirect(url_for('teacher'))
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('index.html', msg=msg)
            
@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM course ")
        mysql.connection.commit()
        courses = cursor.fetchall()
        return render_template('register.html', courses = courses)
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        access = request.form['access']
        course = request.form['course']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email or not access:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s, %s, NULL)', (username, password, email, access, course))
            mysql.connection.commit()
            msg = request.form['username'] + ' is successfully added to database'        
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return redirect(url_for('administrator', msg=msg))


@app.route('/home')
def home():
    if 'loggedin' in session:
        if session['access'] == 'a':
            return redirect(url_for('administrator'))
        if session['access'] == 't':
            return redirect(url_for('teacher'))
        if session['access'] == 's':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM test_schedule WHERE csid = %s', (session['csid'],))
            test = cursor.fetchall()
            for i in test:
                check_test_deadline(i['test_id'])
            cursor.execute('SELECT * FROM course WHERE csid = %s', (session['csid'],))
            subject= cursor.fetchone()
            cursor.execute("SELECT * FROM que_response where id = %s", (session['id'],))
            response = cursor.fetchall()
            result = {}
            for i in response:
                if i['test_res_id'] not in result.keys():
                    result[i['test_res_id']] = [i['marks_score'], i['test_id']]
                else:
                    result[i['test_res_id']][0] += i['marks_score']
            mysql.connection.commit()
            for i in test:
                for j,k in result.items():
                    if(k[1] == i['test_id']):
                        i['score'] = k[0]
                        result.pop(j)
                        break
            return render_template('home.html', username=session['username'], test = test, subject=subject)
        else:
            return redirect(url_for('login'))


@app.route('/profile')
def profile():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM student_info WHERE id = %s",(session['id'],))
    tmp = cursor.fetchone()
    if not tmp and session['access']=='s':
        return render_template('new_user.html')
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM course WHERE csid = %s', (account['csid'],))
        subject = cursor.fetchone()
        return render_template('profile.html', account=account, subject=subject)
    return redirect(url_for('login'))


@app.route('/new_user', methods=['GET','POST'])
def new_user():
    if request.method=="GET":
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        return render_template("new_user.html")
    if request.method == "POST":
        gender = request.form['gender']
        famsize = request.form['famsize']
        Medu = request.form['Medu']
        Fedu = request.form['Fedu']
        Mjob = request.form['Mjob']
        Fjob = request.form['Fjob']
        guardian = request.form['guardian']
        schoolsup = request.form['schoolsup']
        famsup = request.form['famsup']
        activities = request.form['activities']
        nursery = request.form['nursery']
        higher = request.form['higher']
        internet = request.form['internet']
        traveltime = request.form['traveltime']
        studytime = request.form['studytime']
        freetime = request.form['freetime']
        gout = request.form['gout']
        health = request.form['health']
        ssc = request.form['ssc']
        hsc = request.form['hsc']
        attendance = request.form['attendance']
        avg_pointer = request.form['avg_pointer']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO student_info VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)", (str(session['id']), gender, famsize, Medu, Fedu, guardian, schoolsup, famsup, activities, nursery, higher, internet, traveltime, studytime, freetime, gout, health, attendance, avg_pointer, hsc, ssc, Mjob, Fjob))
        cursor.connection.commit()
        stdtype = learner(session['id'])
        cursor.execute("UPDATE student_info SET learner_type = %s WHERE (id = %s)",(stdtype,session['id'],))
        mysql.connection.commit()
        return redirect(url_for('profile'))

@app.route('/teachersubject', methods=['POST'])
def teachersubject():
    if request.method == 'POST' and session['access']=='t':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("UPDATE accounts SET teacher_subject = %s WHERE (id = %s)", (request.form['subject'], session['id'],))
        mysql.connection.commit()
        return redirect(url_for('profile'))
    else:
        msg = "Dont Have proper access!!"
        return render_template('index.html', msg = msg)


@app.route('/administrator', methods=['GET'])
def administrator():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT csid, course_name from course;")
    data = cursor.fetchall()
    return render_template("administrator.html", data=data)


@app.route('/administrator_analysis', methods=['POST'])
def administrator_analysis():
    if request.method=="POST":
        csid = request.form['csid']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE csid = %s',(csid,))
        accounts = cursor.fetchall()
        cursor.execute('SELECT * FROM course WHERE csid = %s',(csid,))
        course = cursor.fetchone()   
        return render_template('admin_course_analysis.html', accounts=accounts, course=course)


@app.route('/administrator_subject_analysis/<subject>', methods=['GET'])
def administrator_subject_analysis(subject):
    if request.method=="GET" and session['access']=='a':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM que_response WHERE subject = %s',(subject,))
        response = cursor.fetchall()
        result = {}
        for res in response:
            if res['test_id'] not in result.keys():
                result[res['test_id']] = [res['marks_score'], res['marks_total']]
            else:
                result[res['test_id']][0] += res['marks_score']
                result[res['test_id']][1] += res['marks_total'] 
        return render_template('administrator_subject_analysis.html',result=result)


@app.route('/learner_system/<csid>')
def learner_system(csid):
    if session['access']=='a':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if csid == '0':
            response = {}
        else:
            cursor.execute("SELECT student_info.id,accounts.username, student_info.learner_type FROM accounts INNER JOIN student_info ON accounts.id=student_info.id WHERE accounts.csid=%s",(csid,))
            response = cursor.fetchall()
        cursor.execute("SELECT csid, course_name from course")
        course = cursor.fetchall()
        return render_template('learner_system.html', response=response, course=course)


@app.route('/accuracy')
def accuracy():
    if session['access'] == 'a':
        return render_template('accuracy.html')
    else:
        return render_template('index.html')


@app.route('/refresh_learner_system')
def refresh_learner_system():
    if session['access']=='a':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id from student_info")
        accounts = cursor.fetchall()
        for i in accounts:
            type = learner(str(i['id']))
            cursor.execute("UPDATE student_info SET learner_type = %s WHERE (id = %s)",(type,str(i['id']),))
            mysql.connection.commit()
        return str("SUCCESS")


@app.route("/csv_upload", methods=['GET','POST'])
def csv_upload():
    if request.method == 'GET':
        return render_template('csv_upload.html')
    elif request.method == 'POST':
        csv_file = request.files['file']
        csv_file = TextIOWrapper(csv_file, encoding='utf-8')
        csv_reader = csv.reader(csv_file, delimiter=',')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        for row in csv_reader:
            cursor.execute("INSERT INTO question_bank VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s)", (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]))
            cursor.connection.commit()
        return redirect(url_for('csv_upload',msg="SUCCESS"))


        upload_file = request.files['file']
        content = upload_file.read()
        read = csv.reader(codecs.iterdecode(content, 'utf-8'))
        return str(content)
        csv_dicts = [{k: v for k, v in row.items()} for row in csv.DictReader(read.splitlines(), skipinitialspace=True)]
        return str(csv_dicts)
        if upload_file.filename != '':
            return upload_file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            uploaded_file.save(file_path)
    return redirect(url_for('index'))



@app.route('/teacher', methods=['GET'])
def teacher():
    if request.method=='GET':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT teacher_subject FROM accounts where id = %s", (str(session['id']),))
        tmp = cursor.fetchone()
        cursor.execute("SELECT * FROM test_schedule where subject = %s", (tmp['teacher_subject'],))
        all_test = cursor.fetchall()
        for i in all_test:
            check_test_deadline(i['test_id'])
        cursor.execute("SELECT teacher_subject from accounts where id = %s",(session['id'],))
        subject = cursor.fetchone()
        cursor.execute("SELECT * FROM que_response where subject = %s", (subject['teacher_subject'],))
        response = cursor.fetchall()
        result = {}
        for res in response:
            if res['subtopic'] not in result.keys():
                result[res['subtopic']] = [res['marks_score'], res['marks_total']]
            else:
                result[res['subtopic']][0] += res['marks_score']
                result[res['subtopic']][1] += res['marks_total']
        
        return render_template('teacher.html', all_test = all_test, result=result)


@app.route('/forgotpassword', methods=['GET','POST'])
def forgotpassword():
	if request.method == 'POST':
		email = request.form['email']
		cur = mysql.connection.cursor()
		results = cur.execute('SELECT * from accounts where email = %s' , [email])
		if results > 0:
			sesOTPfp = generateOTP()
			session['tempOTPfp'] = sesOTPfp
			session['seslpemail'] = email
			msg1 = Message('OTP Verification for Lost Password', sender = sender, recipients = [email])
			msg1.body = "Your OTP Verfication code for reset password is "+sesOTPfp+"."
			mail.send(msg1)
			return redirect(url_for('verifyOTPfp')) 
		else:
			return render_template('lostpassword.html',error="Account not found.")
	return render_template('lostpassword.html')


@app.route('/verifyOTPfp', methods=['GET','POST'])
def verifyOTPfp():
	if request.method == 'POST':
		OTP = request.form['otp']
		fpsOTP = session['tempOTPfp']
		if(OTP == fpsOTP):
			return redirect(url_for('lpnewpwd')) 
	return render_template('verifyOTPfp.html')


@app.route('/lpnewpwd', methods=['GET','POST'])
def lpnewpwd():
	if request.method == 'POST':
		npwd = request.form['npwd']
		cpwd = request.form['cpwd']
		slpemail = session['seslpemail']
		if(npwd == cpwd ):
			cur = mysql.connection.cursor()
			cur.execute('UPDATE accounts set password = %s where email = %s', (npwd, slpemail))
			mysql.connection.commit()
			cur.close()
			session.clear()
			return render_template('index.html',msg="Your password was successfully changed.")
		else:
			return render_template('index.html',msg="Password doesn't matched.")
	return render_template('lpnewpwd.html')

def generateOTP() : 
    digits = "0123456789"
    OTP = "" 
    for i in range(5) : 
        OTP += digits[math.floor(random.random() * 10)] 
    return OTP 


@app.route('/addque', methods=['GET', 'POST'])
def add_question():
    if request.method == "GET":
        if 'loggedin' in session:
            if session['access'] == 't':
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("SELECT teacher_subject from accounts where id = %s", (session['id'],))
                account = cursor.fetchone()
                return render_template('add_question.html', msg="Hello", account= account)
            else:
                return render_template('index.html',msg="You dont have proper access for requested action!!")
        else:
            return render_template('index.html',msg="You dont have proper access for requested action!!")
    if request.method == 'POST' and 'question' in request.form and 'answer' in request.form and 'subject' in request.form and 'subtopic' in request.form:
        question = request.form['question']
        type = request.form['type']
        answer = request.form['answer']
        op1 = request.form['op1']
        op2 = request.form['op2']
        op3 = request.form['op3']
        subject = request.form['subject']
        subtopic = request.form['subtopic']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO question_bank VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s)', (type, subject, subtopic, question, answer, op1, op2, op3))
        mysql.connection.commit()
        return redirect(url_for('teacher'))


@app.route('/availablecourse', methods=['GET', 'POST'])
def availablecourse():
    if request.method == "GET":
        if 'loggedin' in session:
            if session['access'] == 'a':
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("SELECT * FROM course ")
                mysql.connection.commit()
                courses = cursor.fetchall()
                return render_template('add_course.html', courses = courses)
            else:
                return render_template('index.html',msg="You dont have proper access for requested action!!")
        else:
            return render_template('index.html',msg="You dont have proper access for requested action!!")
    if request.method == 'POST' and 'course_name' in request.form and 'subject1' in request.form and 'subject2' in request.form:
        course_name = request.form['course_name']
        subject1 = request.form['subject1']
        subject2 = request.form['subject2']
        subject3 = request.form['subject3']
        subject4 = request.form['subject4']
        subject5 = request.form['subject5']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO course VALUES (NULL, %s, %s, %s, %s, %s, %s)', (course_name, subject1, subject2, subject3, subject4, subject5))
        mysql.connection.commit()
        msg = "Course is successfully added to the course database!!!"
        return redirect(url_for('availablecourse'))
    else:
        return render_template('index.html',msg="Something went wrong, Please try again!!")

@app.route('/schedule_test', methods=['GET', 'POST'])
def schedule_test():
    if request.method == "POST":
        if ('loggedin' in session) and (session['access']=='t'):
            csid = session['csid']
            quiznum = request.form['quiznum']
            deadline = request.form['deadline']
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT teacher_subject FROM accounts where id = %s',(session['id'],))
            subject = cursor.fetchone()
            cursor.execute('INSERT INTO test_schedule VALUES (NULL, %s, %s, %s, %s, %s, %s)', (csid, '1', now, deadline,subject['teacher_subject'], quiznum))
            mysql.connection.commit()
            return redirect(url_for('teacher'))


def check_test_deadline(test_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT is_active, end_at FROM test_schedule where test_id = %s',(test_id,))
    schedule = cursor.fetchone()
    if schedule['is_active'] == 1:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        end = schedule['end_at'].strftime("%Y-%m-%d %H:%M:%S.%f")
        if now > end :
            cursor.execute("UPDATE test_schedule SET is_active = 0 WHERE (test_id = %s);",(test_id,))
            cursor.connection.commit()
            return str("True")
        else:
            return str('False')
    else:
        return str("False")



@app.route('/attempt_test/<test_id>', methods=['GET','POST'])
def attempt_test(test_id):
    if request.method=='GET':
        if 'loggedin' in session and session['access'] == 's':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            id = str(session['id'])+str(test_id)
            cursor.execute("SELECT * FROM que_response where test_res_id = %s",(id,))
            lock = cursor.fetchone()
            if lock:
                return redirect(url_for('home'))
            cursor.execute("SELECT * FROM test_schedule where test_id = %s ",(test_id,))
            test = cursor.fetchall()
            que_num = test[0]['total_question']
            if len(test) > 0 and test[0]['is_active']==1:
                mysql.connection.commit()
                cursor.execute("SELECT * FROM question_bank where subject = %s ",(test[0]['subject'],))
                test = cursor.fetchall()
                test= random.sample(test, len(test))
                gen_test = []
                for i in test:
                    temp = []
                    temp.append(i['qid'])
                    temp.append(i['question'])
                    temp2 = []
                    temp2.append(i['answer'])
                    temp2.append(i['op1'])
                    temp2.append(i['op2'])
                    temp2.append(i['op3'])
                    random.shuffle(temp2)
                    temp.append(temp2)
                    gen_test.append(temp)
                    if len(gen_test)>que_num:
                        gen_test = gen_test[0: que_num]
                return render_template('test_attempt.html', test = tuple(gen_test), test_id=test_id)
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
    if request.method == "POST":
        if 'loggedin' in session and session['access'] == 's':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            result = {}
            id = str(session['id'])+str(test_id)
            cursor.execute("SELECT * FROM que_response where test_res_id = %s",(id,))
            lock = cursor.fetchone()
            if lock:
                return redirect(url_for('home'))
            for qid, sel in request.form.items():
                cursor.execute("SELECT * FROM question_bank where qid = %s",(qid,))
                res = cursor.fetchone()
                if res['answer'] == sel:
                    tmp = [1 , 1]
                else:
                    tmp = [ 0 , 1]
                if res['subtopic'] not in result.keys():
                    result[res['subtopic']] = tmp
                else:
                    result[res['subtopic']][0] += tmp[0]
                    result[res['subtopic']][1] += tmp[1]
            for subtopic, marks in result.items():
                cursor.execute("INSERT INTO que_response VALUES (%s, NULL, NULL, %s, %s, %s, %s, %s, %s)",(id, res['subject'], subtopic, str(marks[0]), str(marks[1]), test_id, str(session['id']))) 
                mysql.connection.commit()
            return redirect(url_for('home'))


@app.route('/test_analysis/<test_id>')
def test_analysis(test_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM que_response where test_id = %s", (test_id,))
    response = cursor.fetchall()
    total_std = len(set([x['test_res_id'] for x in response]))
    avg = sum([x['marks_score'] for x in response])/total_std
    result = {}
    for res in response:
        if res['subtopic'] not in result.keys():
            result[res['subtopic']] = [res['marks_score'], res['marks_total']]
        else:
            result[res['subtopic']][0] += res['marks_score']
            result[res['subtopic']][1] += res['marks_total']    
    return render_template('test_analysis.html', result = result, total_std=total_std, avg = avg, test_id = test_id)


@app.route('/students_test_score/<test_id>')
def students_test_score(test_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT test_res_id, subtopic, marks_score,  id FROM que_response where test_id = %s", (test_id,))
    response = cursor.fetchall()
    cursor.execute("SELECT total_question FROM test_schedule where test_id = %s", (test_id,))
    total = cursor.fetchone()
    result = {}
    for i in response:
        if i['test_res_id'] not in result.keys():
            result[i['test_res_id']] = i['marks_score']
        else:
            result[i['test_res_id']] += i['marks_score']
    return render_template('students_test_score.html', response=result, total= total, test_id= test_id)
                

@app.route('/student_view_subject_analysis/<subject>/<type>')
def student_view_subject_analysis(subject, type):
    if request.method == 'GET':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if type=="subtopic" :
            cursor.execute("SELECT test_res_id, subtopic, marks_score, marks_total, id FROM que_response where subject = %s", (subject,))
            response = cursor.fetchall()
            result ={}
            user = {}
            recommend = {}
            for res in response:
                if res['subtopic'] not in result.keys():
                    result[res['subtopic']] = [res['marks_score'], res['marks_total']]
                    if(res['id'] == session['id']):
                        user[res['subtopic']] = [res['marks_score'], res['marks_total']]
                else:
                    result[res['subtopic']][0] += res['marks_score']
                    result[res['subtopic']][1] += res['marks_total']
                    if(res['id'] == session['id']) and res['subtopic'] not in user:
                        user[res['subtopic']] = [res['marks_score'], res['marks_total']]
                    elif(res['id'] == session['id']):
                        user[res['subtopic']][0] += res['marks_score']
                        user[res['subtopic']][1] += res['marks_total']
            for subtopic in result.keys():
                if subtopic not in user.keys():
                    temp = "https://www.youtube.com/results?search_query="+subtopic+"+"+subject
                    recommend[subtopic]=temp
                elif (result[subtopic][0] * 100)/result[subtopic][1] >= (user[subtopic][0] * 100)/user[subtopic][1]:
                    temp = "https://www.youtube.com/results?search_query="+subtopic+"+"+subject
                    recommend[subtopic]=temp
            return render_template('student_view_subject_analysis.html', user=user, result=result, subject=subject, type=type, recommend=recommend)
        elif type=="test" :
            cursor.execute('SELECT * FROM que_response WHERE subject = %s and id = %s',(subject, session['id'],))
            response = cursor.fetchall()
            test = {}
            for res in response:
                if res['test_id'] not in test.keys():
                    test[res['test_id']] = [res['marks_score'], res['marks_total']]
                else:
                    test[res['test_id']][0] += res['marks_score']
                    test[res['test_id']][1] += res['marks_total']
            cursor.execute('SELECT * FROM que_response WHERE subject = %s',(subject,))
            response = cursor.fetchall()
            result = {}
            for res in response:
                if res['test_id'] not in result.keys():
                    result[res['test_id']] = [res['marks_score'], res['marks_total']]
                else:
                    result[res['test_id']][0] += res['marks_score']
                    result[res['test_id']][1] += res['marks_total'] 
            return render_template('student_view_subject_analysis.html',test=test, type=type, subject=subject, result=result, recommend={})



@app.route('/get_student_view_subject_analysis', methods=['POST','GET'])
def get_student_view_subject_analysis():
    if request.method == 'POST' and 'subject' in request.form:
        return redirect(url_for('student_view_subject_analysis', subject=request.form['subject'], type="subtopic"))



@app.route('/tep/<std_id>')
def learner(std_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT gender,famsize,guardian,schoolsup,famsup,activities,nursery,higher,internet,Medu,Fedu,Mjob,Fjob,traveltime,studytime,freetime,gout,health,attendance,ssc,hsc,avg_pointer FROM student_info where id = %s',(std_id,))
    response = cursor.fetchone()
    lst =[]
    for k, v in response.items():
        lst.append(int(v))
    filename = "/home/prasad/pybox/LOGIN/learner_type.sav"
    loaded_model = pickle.load(open(filename, 'rb'))
    res = loaded_model.predict([lst])
    return str(res[0])

    


@app.route('/tep')
def tep():
    return str("ELLO")




if __name__ == "__main__":
    app.run(debug=True)