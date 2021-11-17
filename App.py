from email import message
from flask import Flask,render_template, request, redirect, url_for,session, g, flash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime, timedelta
from model import db
import folium, random, smtplib, os


key = URLSafeTimedSerializer('sprinkler rule')

app = Flask(__name__, template_folder="Templates", static_folder="static")
app.config['SECRET_KEY'] =  'sprinkler rule'
app.permanent_session_lifetime = timedelta(minutes=60)

@app.route('/login', methods=['GET', 'POST'])
def login():
    Cursor = db.cursor()
    if request.method == "POST":
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=120)
        Username = request.form["username"]
        Password = request.form["password"]
        
        
        Cursor.execute("""SELECT Username FROM users WHERE Username=%s """,(Username, ))
        username = Cursor.fetchone()

        if username:
            Cursor.execute("""SELECT Password FROM users WHERE Username=%s """,(Username, ))
            password = Cursor.fetchone()
            result = check_password_hash(password[0], Password)
            if result == True:
                Cursor.execute("""SELECT acc_confirm FROM users WHERE Username=%s """,(Username, ))
                verify = Cursor.fetchone()
                if verify[0] == 1:
                    Cursor.execute("""SELECT ID FROM users WHERE Username=%s AND Password=%s""",(Username, password[0]))
                    ID = Cursor.fetchone()
                    session['user'] = Username
                    session['id'] = ID[0]
                    return redirect(url_for("home"))
                else:
                    flash('User must verify email account first, please check user email')
            else:
                if 'user' in session:
                    return redirect(url_for("home"))
                flash("Invalid username or password")
        else:
            if 'user' in session:
                return redirect(url_for("home"))
            flash("Invalid username or password")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def sign_up():
    Cursor = db.cursor()

    if request.method == 'POST':
        Username = request.form.get('username')
        Email = request.form.get('email')
        Password = request.form.get('password')
        Password2 = request.form.get('password2')
        Cursor.execute("""SELECT Username FROM users WHERE Username = %s """,(Username, ))
        checkuser = Cursor.fetchone()
        Cursor.execute("""SELECT Email FROM users WHERE Email = %s """,(Email, ))
        checkmail = Cursor.fetchone()

        if checkuser:
            flash("username already exist")
        elif checkmail:
            flash("Account already exist")
        elif Password != Password2:
            flash("password doesn't match")
        else:
            num = 0
            hash_password = generate_password_hash(Password, method='sha256')
            Cursor.execute("""INSERT INTO users (Username,Email,Password,acc_confirm) VALUES (%s,%s,%s,%s)""",(Username,Email,hash_password, 0))
            db.commit()
            flash('A verification is needed before login in, please check your email')
            session['email'] = Email
            return redirect(url_for("send_email"))

    return render_template('register.html')

@app.route('/authorize', methods=['GET', 'POST'])
def otp():
    Cursor = db.cursor()
    
    if 'email' in session:
        Code = session['code']
        Email = session['email']
        if request.method == 'POST':
            
            Code2 = request.form.get('codex')
            if int(Code2) == Code:
                Cursor.execute("""UPDATE users SET acc_confirm = 1 WHERE Email = %s """,(Email, ))
                db.commit()
                session.pop('email', None)
                flash('Account authorized, user can login now')
                return redirect(url_for("login"))
            else:
                flash('Invalid code')
        return render_template('otp.html')
    else:
        flash('The time limit for the otp has expired, Please register again')
        Cursor.execute("""DELETE FROM users WHERE acc_confirm = 0""")
        db.commit()
        return redirect(url_for("login"))

@app.route('/resend')
def send_email():
    if 'email' in session:
        Email = session['email']
        code = random.randint(000000,999999)
        message = EmailMessage()
        message['Subject'] = 'OTP verification'
        message['From'] = 'Esprinkler123@gmail.com'
        message['To'] = Email
        content = '''
        Your OTP code is : %s
        '''%(code)
        message.set_content(content)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('Esprinkler123@gmail.com', 'EG49vqyaqzWW')
            smtp.send_message(message)
        session['code'] = code
        return redirect(url_for("otp", Code = code))
    else:
        flash('The time limit for the otp has expired, Please try again')
        return redirect(url_for("login"))

@app.route('/forget', methods=['GET', 'POST'])
def forget():
    Cursor = db.cursor()
    Email_Address = os.environ.get('dani772001@gmail.com')
    Email_Password = os.environ.get('password')

    if request.method == 'POST':
        Email = request.form.get('email')
        token = key.dumps(Email, salt='mail-confirm')
        Cursor.execute("""SELECT * FROM users WHERE Email = %s """,(Email, ))
        checkmail = Cursor.fetchone()
        if checkmail:
            flash('email has been sent, please check your email')
            session['email'] = Email
            session['Token'] = token
            link = url_for('reset', token=token)
            message = EmailMessage()
            message['Subject'] = 'Reset Password'
            message['From'] = Email_Address
            message['To'] = Email
            message.set_content("This link will expire in 10 min: http://localhost:4000/{}".format(link))
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login('dani772001@gmail.com', 'password')
                smtp.send_message(message)
        else:
            flash('There is no such account registered')

    return render_template ('forgotPass.html')

@app.route('/<token>', methods =['GET', 'POST'])
def reset(token):
    Cursor = db.cursor()

    try:
        email = key.loads(token, salt='mail-confirm', max_age=600)
        if request.method == 'POST':
            Email = session['email']
            Password = request.form.get('password')
            Password2 = request.form.get('password2')
            if Password == Password2:
                hash_password = generate_password_hash(Password, method='sha256')
                Cursor.execute("""UPDATE users SET Password = %s WHERE Email = %s """,(hash_password, Email, ))
                db.commit()
            return redirect(url_for("views.login"))
    except SignatureExpired:
        return 'Time session out'
    return render_template ('resetpass.html', token = token)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/select', methods =['GET', 'POST'])
def select():
    if 'user' in session:
        Cursor = db.cursor()
        id = session['id']
        Cursor.execute("""SELECT Location FROM sprinkler WHERE user_ID = %s""", (id, ))
        locate = Cursor.fetchall()
        if request.method == 'POST':
            lcn_name = request.form.get('gps')

            Cursor.execute("""SELECT ID FROM sprinkler WHERE user_ID = %s AND Location = %s""", (id, lcn_name))
            lcn_id = Cursor.fetchone()
            lcn = int(lcn_id[0])
            session['gpsID'] = lcn
            return redirect(url_for("schedule"))
        return render_template('locationselect.html', location = locate)
    else:
        return redirect(url_for("login"))

@app.route('/schedule', methods =['GET', 'POST'])
def schedule():
    if 'user' in session:
        Cursor = db.cursor()
        if 'gpsID' in session:
            id = session['id']
            ID = session['gpsID']
            Cursor.execute("""SELECT Location FROM sprinkler WHERE user_ID = %s AND ID = %s""",(id, ID ))
            location = Cursor.fetchone()
            Cursor.execute("""SELECT * FROM wtr_schedule WHERE sprinkler_ID = (SELECT ID FROM sprinkler WHERE user_ID = %s AND ID = %s);""",(id, ID))
            detail = Cursor.fetchall()

            Cursor.execute("""SELECT MON,TUE,WED,THU,FRI,SAT,SUN FROM day_list WHERE sch_ID IN (SELECT ID FROM wtr_schedule WHERE sprinkler_ID = %s)""",(ID, ))
            days = Cursor.fetchall()
            day_list = []

            i = 0
            for x in days:
                day_list.append([])
                if x[0] == 1:
                    day_list[i].append('mon')
                if x[1] == 1:
                    day_list[i].append('tue')
                if x[2] == 1:
                    day_list[i].append('wed')
                if x[3] == 1:
                    day_list[i].append('thu')
                if x[4] == 1:
                    day_list[i].append('fri')
                if x[5] == 1:
                    day_list[i].append('sat')
                if x[6] == 1:
                    day_list[i].append('sun')
                i += 1

            #lists=str(day_list)[1:-1]
            #print(day_list)
            #method for sprinkler timer
            Cursor.execute("""SELECT DATE_FORMAT(Time, '%H:%i') FROM wtr_schedule WHERE sprinkler_ID IN (SELECT ID FROM sprinkler WHERE user_ID = %s AND ID = %s);""",(id, ID ))
            time = Cursor.fetchall()
            Cursor.execute("""SELECT DATE_FORMAT(Date, '%Y-%m-%d') FROM wtr_schedule WHERE sprinkler_ID IN (SELECT ID FROM sprinkler WHERE user_ID = %s AND Location = %s);""",(id, ID ))
            date = Cursor.fetchall()
            alarm(time, date, days)

            return render_template ('schedule.html', row = detail, name = location, day = day_list)
        else:
            return redirect(url_for("select"))
    else:
        return redirect(url_for("login"))

def alarm(times, dates, days): #method for sprinkler timer
    Cursor = db.cursor()

    '''
    while True:
        nowDay = int(date.today().weekday())
        for Date in dates:

            if Date[0] == None:
                for day in days:
                    if day[nowDay] == 1:
                        for Time in times:
                            if Time == datetime.now().strftime("%H:%M"):
                                print('spraying now')
            elif Date[0] == datetime.today().strftime('%Y-%m-%d'):
                for Time in times:
                    if Time[0] == datetime.now().strftime("%H:%M"):
                        print('spraying now')
    '''
@app.route('/add', methods =['GET', 'POST'])
def add():
    if 'user' in session:
        Cursor = db.cursor()
        if 'gpsID' in session:
            ID = session['gpsID']
            ID = str(ID)
            Cursor.execute("""SELECT Location FROM sprinkler WHERE ID = %s""",(ID, ))
            name = Cursor.fetchone()
            if request.method == 'POST':
                date = request.form.get('date')
                time = request.form.get('time')
                days = request.form.getlist('day_pick')
                daytally = [0, 0, 0, 0, 0, 0, 0]

                if (date == '' or len(days) == 0) and time == '':
                    flash('Form must be filled in')
                elif date == '' and len(days) == 0:
                    flash('Date or Days must be filled in')
                elif time == '':
                    flash('Time must be filled in')
                elif date < datetime.today().strftime('%Y-%m-%d') and date != '':
                    flash("Invalid Date")
                elif time <= datetime.now().strftime("%H:%M") and date == datetime.today().strftime('%Y-%m-%d'):
                    flash("Invalid Time")
                else:
                    flash("schedule created")

                    for i in days:
                        count = int(i)
                        daytally[count] = 1 #add the checked days to the list

                    if days:
                        date = None

                    Cursor.execute("""INSERT INTO wtr_schedule (Date,Time,sprinkler_ID) VALUES ( %s, %s, %s)""",(date,time, ID))
                    db.commit()

                    Cursor.execute("""SELECT MAX(ID) FROM wtr_schedule""")
                    shID = Cursor.fetchone()
                    schID = int(shID[0])
                    Cursor.execute("""INSERT INTO day_list (MON, TUE, WED, THU, FRI, SAT, SUN, sch_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",(daytally[0], daytally[1], daytally[2], daytally[3], daytally[4], daytally[5], daytally[6], schID))
                    db.commit()
                    return redirect(url_for("schedule"))

            return render_template ('addschedule.html', location = name)
        else:
            return redirect(url_for("select"))
    else:
        return redirect(url_for("login"))

@app.route('/update')
def update():
    Id = request.args.get('Id') #get ID from clicking schedule
    session['Id'] = Id
    return redirect(url_for("adjust"))

@app.route('/adjust', methods =['GET', 'POST'])
def adjust():
    if 'user' in session:
        Cursor = db.cursor()
        if 'gpsID' in session:
            ID = session['gpsID']
            ID = str(ID)
            Id = session['Id']

            Cursor.execute("""SELECT Location FROM sprinkler WHERE ID = %s""",(ID, ))
            name = Cursor.fetchone()

            Cursor.execute("""SELECT DATE_FORMAT(Time, '%H:%i') FROM wtr_schedule WHERE ID = %s;""",(Id, ))
            time = Cursor.fetchone()
            Cursor.execute("""SELECT DATE_FORMAT(Date, '%Y-%m-%d') FROM wtr_schedule WHERE ID = %s;""",(Id, ))
            date = Cursor.fetchone()

            days_check = []

            Cursor.execute("""SELECT MON,TUE,WED,THU,FRI,SAT,SUN FROM day_list WHERE sch_ID = %s""",(Id, ))
            day_data = Cursor.fetchone()

            for days in day_data:  #while row is not None:
                if days == 1:
                    days_check.append("checked")
                else:
                    days_check.append("null")

            if request.method == 'POST':
                date = request.form.get('date')
                time = request.form.get('time')
                days = request.form.getlist('day_pick')
                daytally = [0, 0, 0, 0, 0, 0, 0]

                if (date == '' or days == '') and time == '':
                    flash('Form must be filled in')
                elif date == '' and days == '':
                    flash('Date or Days must be filled in')
                elif time == '':
                    flash('Time must be filled in')
                else:
                    flash('schedule changed')
                    saveAdj(days, daytally, date, time, ID, Id)
                    return redirect(url_for("schedule"))

            return render_template ('adjustschedule.html', date=date, time=time, location = name, days = days_check)
        else:
            return redirect(url_for("select"))
    else:
        return redirect(url_for("login"))

def saveAdj(days, daytally, date, time, ID, Id):
    Cursor = db.cursor()

    for i in days:
        count = int(i)
        daytally[count] = 1 #add the checked days to the list
    if days:
        date = None

    Cursor.execute("""UPDATE wtr_schedule SET DATE = %s, Time = %s, sprinkler_ID = %s WHERE ID = %s """,(date,time, ID, Id))
    db.commit()
    Cursor.execute("""UPDATE day_list SET MON =%s ,TUE =%s ,WED =%s ,THU =%s ,FRI =%s ,SAT =%s ,SUN =%s WHERE sch_ID = %s""",(daytally[0], daytally[1], daytally[2], daytally[3], daytally[4], daytally[5], daytally[6], Id))
    db.commit()
    return redirect(url_for("schedule"))

@app.route('/delete', methods =['GET', 'POST'])
def delete():
    if 'user' in session:
        Cursor = db.cursor()
        if 'gpsID' in session:
            id = session['id']
            ID = session['gpsID']
            Cursor.execute("""SELECT Location FROM sprinkler WHERE user_ID = %s AND ID = %s""",(id, ID ))
            name = Cursor.fetchone()
            Cursor.execute("""SELECT * FROM wtr_schedule WHERE sprinkler_ID = (SELECT ID FROM sprinkler WHERE user_ID = %s AND ID = %s);""",(id, ID))
            detail = Cursor.fetchall()
            Cursor.execute("""SELECT MON,TUE,WED,THU,FRI,SAT,SUN FROM day_list WHERE sch_ID IN (SELECT ID FROM wtr_schedule WHERE sprinkler_ID = %s)""",(ID, ))
            days = Cursor.fetchall()
            day_list = []

            i = 0
            for x in days:
                day_list.append([])
                if x[0] == 1:
                    day_list[i].append('mon')
                if x[1] == 1:
                    day_list[i].append('tue')
                if x[2] == 1:
                    day_list[i].append('wed')
                if x[3] == 1:
                    day_list[i].append('thu')
                if x[4] == 1:
                    day_list[i].append('fri')
                if x[5] == 1:
                    day_list[i].append('sat')
                if x[6] == 1:
                    day_list[i].append('sun')
                i += 1

            if request.method == 'POST':
                sch_id = request.form.getlist('schedule') #get value from selected checkbox
                del_id = [str(i) for i in sch_id] #convert checkbox value to string
                for x in del_id:
                    Cursor.execute("""DELETE FROM day_list WHERE sch_ID = %s""",(x, ))
                    db.commit()
                    Cursor.execute("""DELETE FROM wtr_schedule WHERE ID = %s""",(x, ))
                    db.commit()
                flash("schedule deleted")
                return redirect(url_for("schedule"))

            return render_template ('deleteschedule.html', active = detail, name = name, day = day_list)
        else:
            return redirect(url_for("select"))
    else:
            return redirect(url_for("login"))

@app.route("/", methods=['GET', 'POST'])
def home():
    if 'user' in session: #if user time session run out or not yet login return to login
        Email_Address = os.environ.get('dani772001@gmail.com')
        Email_Password = os.environ.get('password')
        username = session['user']
        if request.method == 'POST':
            Name = request.form.get('name')
            Email = request.form.get('email')
            Message = request.form.get('message')
            if Name and Email and Message:
                message = EmailMessage()
                message['Subject'] = 'Inquiry for problem'
                message['From'] = Email_Address
                message['To'] = 'dani772001@outlook.com'
                content = '''
                Name:  %s
                Email: %s
                Message: %s
                '''%(Name, Email, Message)
                message.set_content(content)
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login('dani772001@gmail.com', 'Agito2001')
                    smtp.send_message(message)
        return render_template ('index.html',Username = username)
    else:
        return redirect(url_for("login"))

@app.route("/about.html")
def about():
    if 'user' in session:
        return render_template ("about.html")
    else:
        return redirect(url_for("login"))

@app.route('/weather.html')
def weather_forecast():
    if 'user' in session:
        return render_template("weather.html")
    else:
        return redirect(url_for("login"))

@app.route('/dashboard.html', methods = ['GET'])
def get_temperature():
    if 'user' in session:
        cursor = db.cursor(buffered=True)
        # get username from database
        cursor.execute(""" SELECT Username FROM tempLog ORDER BY ID DESC LIMIT 1""")
        record = cursor.fetchone()
        session['User'] = (record[0])

        # Get temperature value from databases
        cursor.execute(""" SELECT temperature FROM tempLog WHERE Username = %s """,(session['User'], ))
        record = cursor.fetchone()

        # selecting column value into variable
        temp = float(record[0])
        print(temp)
        
        cursor = db.cursor(buffered=True)
        # Get soil moisture data from databases
        cursor.execute(""" SELECT soilmoisture FROM moisture_log ORDER BY ID DESC LIMIT 1 """)
        data = cursor.fetchone()
        
        return render_template("dashboard.html", temp = temp)
    else:
        return redirect(url_for("login"))

def get_waterlevel():
    if 'user' in session:
        return render_template("dashboard.html")
    else:
        return redirect(url_for("login"))

def get_soil_moisture():
    if 'user' in session:
        cursor = db.cursor(buffered=True)
        # Get soil moisture data from databases
        cursor.execute(""" SELECT soilmoisture FROM moisture_log ORDER BY ID DESC LIMIT 1 """)
        data = cursor.fetchone()

        # selecting column value into variable
        

        return redirect(url_for("dashboard.html", soil = data[0]))
    else:
        return redirect(url_for("login"))

@app.route('/location.html')
def add_location():
    return render_template("location.html")

@app.route('/trial', methods=['GET', 'POST'])
def trial():
    Cursor = db.cursor()
    if request.method == 'POST':
        Details = request.form
        name = Details['name']
        latitude = Details['latitude']
        longitude = Details['longitude']
        Cursor.execute("""INSERT INTO location (name,latitude,longitude) VALUES (%s, %s, %s)""", (name,latitude,longitude) )
        db.commit()
        return redirect(url_for('map_marker'))

    return render_template("location.html")

@app.route('/map')
def map_marker():

    start_coords = (-6.1753924, 106.8271528)
    folium_map = folium.Map(
        location=start_coords, 
        zoom_start=17
    )
    folium_map.save('Templates/map.html')
    return render_template('mapper.html')

@app.route('/mapper')
def mapper():
    return render_template('map.html')

@app.route('/sensor.html')
def sensor():
    if 'user' in session:
        return render_template("sensor.html")
    else:
        return redirect(url_for("login"))

@app.route('/sensorlocation')
def location():
    if 'user' in session:
        return render_template("sensorlocation.html")
    else:
        return redirect(url_for("login"))

@app.route('/waterlevel')
def waterlevel():
    if 'user' in session:
        return render_template("waterlevel.html")
    else:
        return redirect(url_for("login"))

@app.route('/temp')
def temp():
    Cursor = db.cursor()
    if 'user' in session:
        Cursor.execute("SELECT temperature FROM tempLog WHERE Id=8")
        temp2 = Cursor.fetchone()
        temp2 = temp2[0]/100
        return render_template("temp.html", temp = temp2)
    else:
        return redirect(url_for("login"))

@app.route('/moisture')
def moisture():
    if 'user' in session:
        return render_template("moisture.html")
    else:
        return redirect(url_for("login"))

# Invalid URL

@app.errorhandler(404)
def page_not_found(e):
	return render_template("404.html"), 404

# Internal Error Page URL
@app.errorhandler(500)
def page_not_found(e):
	return render_template("500.html"), 500

# to run a web server using a file
if __name__ == "__main__":
    app.run(host='localhost', port=4000, debug=True)
