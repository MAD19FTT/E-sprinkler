from flask import Blueprint, render_template, request, redirect, url_for, session, g, flash

auth = Blueprint('views', __name__)

class User:
    def __init__(var,id,username,password):
        var.id = id
        var.username = username
        var.password = password

userlist = []
userlist.append(User(id = 1, username = "mama", password = "1234567"))
userlist.append(User(id = 2, username = "allen", password = "walker"))
userlist.append(User(id = 3, username = "kanda", password = "yu"))

@auth.before_request
def before_request():
    g.user = None
    
    if 'user_id' in session:
        user = [x for x in userlist if x.id == session['user_id']][0]
        g.user = user

@auth.route('/', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        session.pop('user_id', None)
        Username = request.form["username"]
        Password = request.form["password"]

        #if request.form['press2'] == 'SIGN UP':
            #return print("clicked")
        #elif request.form['press'] == 'LOG IN':
        for x in userlist:
            if x.username == Username:
                if x.password == Password:
                    flash("success")
                    session['user_id'] = x.id
                    return redirect(url_for("views.home"))
                else:
                    flash("wrong password")
            else:
                flash("wrong credential")
                break
                
    
    return render_template('Log.html')

@auth.route('/logout')
def logout():
    if request.method == "POST":
        user = request.form["username"]
    return "<p>logout</p>"

@auth.route('/register', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        if password == password2:
            return redirect(url_for("views.login"))
    else:
        print("Error")
        
    return render_template('Reg.html')

@auth.route('/home')
def home():
    if not g.user:
        return redirect(url_for('login'))
    return render_template ('home.html')

@auth.route('/forget')
def forget():
    return render_template ('forgotPass.html')



