from flask import Flask, render_template, url_for, flash, redirect, request, session, make_response, send_file
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from pymysql import escape_string as thwart
from functools import wraps
from datetime import datetime, timedelta
import gc
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import pygal
from werkzeug.utils import secure_filename
from content import Content
from db_connect import connection

UPLOAD_FOLDER = "/var/www/FlaskApp/FlaskApp/uploads"

ALLOWED_EXTENSIONS = set(["txt", "png", "jpg", "pdf", "jpeg", "gif"])

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_files(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Please Login.")
            return redirect(url_for('index'))
    return wrap
        
APP_CONTENT = Content()

@app.route("/", methods=["GET", "POST"])
def index():
    error = ""
    try:
        c, conn = connection()
        if request.method == "POST":
            
            data = c.execute("SELECT * FROM users WHERE username = ('{0}')".format(thwart(request.form['username'])))
            
            data = c.fetchone()[2]
            
            if sha256_crypt.verify(request.form["password"],data):
                session['logged_in'] = True
                session['username'] = request.form['username']
                
                flash("You are now logged in "+session['username']+"!")
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid Credentials, Try Again"
                
        return render_template("main.html", error = error)
    
    except Exception as e:
        flash(e) # Remove for Production
        error = "Invalid Credentials, Try Again"
        return render_template("main.html", error = error)

@app.route("/dashboard/")
@login_required
def dashboard():
    try:
        #flash("This is a Flash notification!")
        return render_template("dashboard.html", APP_CONTENT = APP_CONTENT)
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route("/about/")
@login_required
def about():
    try:
        #flash("This is a Flash notification!")
        return render_template("about.html", APP_CONTENT = APP_CONTENT)
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route("/login/", methods=["GET", "POST"])
def login():
    error = ""
    try:
        c, conn = connection()
        if request.method == "POST":
            
            data = c.execute("SELECT * FROM users WHERE username = ('{0}')".format(thwart(request.form['username'])))
            
            data = c.fetchone()[2]
            
            if sha256_crypt.verify(request.form["password"],data):
                session['logged_in'] = True
                session['username'] = request.form['username']
                
                flash("You are now logged in "+session['username']+"!")
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid Credentials, Try Again"
                
        return render_template("login.html", error = error)
    
    except Exception as e:
        flash(e) # Remove for Production
        error = "Invalid Credentials, Try Again"
        return render_template("login.html", error = error)

@app.route("/logout/")
@login_required
def logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for("index"))

class RegistrationForm(Form):
    username = TextField("Username", [validators.Length(min=4, max=20)])
    email = TextField("Email Address", [validators.Length(min=6, max=50)])
    password = PasswordField("New Password", [validators.Required(),
                                             validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField("Repeat Password")
    accept_tos = BooleanField("I accept the Terms of Service and Privacy Notice",[validators.Required()])

@app.route('/register/', methods=["GET", "POST"])
def register_page():
#    c, conn = connection()
    try:
        form = RegistrationForm(request.form)
        if request.method == "POST":
            if 'register' in request.form and form.validate():
                username = form.username.data
                email = form.email.data
                password = sha256_crypt.encrypt((str(form.password.data)))

                c, conn = connection()

                x = c.execute("SELECT * FROM users WHERE username = ('{0}')".format((thwart(username))))

                if int(x) > 0:
                    flash("Username is already taken.")
                    return render_template("register.html", form = form)
                else:
                    c.execute("INSERT INTO users (username,password,email,tracking) VALUES ('{0}','{1}','{2}','{3}')".format(thwart(username),thwart(password),thwart(email),thwart("/dashboard/")))

                    conn.commit()
                    flash("Thanks for Registering")
                    conn.close()
                    gc.collect()

                    session['logged_in'] = True
                    session['username'] = username

                    return redirect(url_for('dashboard'))

            if 'login' in request.form:
                c, conn = connection() 
                data = c.execute("SELECT * FROM users WHERE username = ('{0}')".format(thwart(request.form['username'])))
            
                data = c.fetchone()[2]
                
                if sha256_crypt.verify(request.form["password"],data):
                    session['logged_in'] =True
                    session['username'] = request.form['username']
                    
                    flash("You are now logged in "+session['username']+"!")
                    return redirect(url_for("dashboard"))
                else:
                    error = "Invalid credentials, try again."

        return render_template("register.html", form = form)
            
    except Exception as e:
        return(str(e)) # remember to remove! For debugging only!
    
@app.route("/test/")
def test():
    """
    
    Safe place for broken/janky code.
    
    """
    return render_template("test.html", test = test)

@app.route('/welcome/')
def welcome_to_jinja():
    try:
        #This is where all the python goes!
        
        def my_function():
            output = ["DIGIT 400 is good", "Python, Java, php, SQL, C++", "<p><strong>hello world</strong></p>", 42, "42"]
            return output
        
        output = my_function()
        
        return render_template("templating_demo.html", output = output)
    except Exception as e:
        return str(e) #remove for production
    
@app.route("/uploads/", methods=["GET","POST"])
@login_required
def upload_file():
    try:
        if request.method == "POST":
            if "file" not in request.files:
                flash("No file part")
                return redirect(request.url)
            file = request.files["file"]
            
            if file.filename == "":
                flash("No selected file")
                return redirect(request.url)
            if file and allowed_files(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                flash("File "+ str(filename) +" upload successful")
                return render_template('uploads.html', filename = filename)
        return render_template("uploads.html")
    except Exception as e:
        return str(e) # remove for production
    
@app.route("/download/")
@login_required
def download():
    try:
        return send_file("/var/www/FlaskApp/FlaskApp/uploads/boat.PNG", attachment_filename="boat.jpeg")
    except Exception as e:
        return str(e) # remove for production

## Site Map

@app.route("/sitemap.xml/", methods=["GET"])
def sitemap():
    try:
        pages = []
        week = (datetime.now() - timedelta(days = 7)).date().isoformat()
        for rule in app.url_map.iter_rules():
            if "GET" in rule.methods and len(rule.arguments) == 0:
                pages.append(["http://104.248.120.233"+str(rule.rule), week])
        
        sitemap_xml = render_template("sitemap_template.xml", pages = pages)
        response = make_response(sitemap_xml)
        response.headers["Content-Type"] = "application/xml"
        return response
    
    except Exception as e:
        return(str(e)) # remove for production
        
@app.route("/robots.txt")
def robots():
    return("User-agent: \nDisallow /login \nDisallow /register")

@app.route("/search/")
@login_required
def search():
    try:
        #flash("This is a Flash notification!")
        return render_template("search.html", APP_CONTENT = APP_CONTENT)
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route('/pygalexample/')
def pygalexample():
	try:
		graph = pygal.Line()
		graph.title = '% Change Coolness of programming languages over time.'
		graph.x_labels = ['2011','2012','2013','2014','2015','2016']
		graph.add('Python',  [15, 31, 89, 200, 356, 900])
		graph.add('Java',    [15, 45, 76, 80,  91,  95])
		graph.add('C++',     [5,  51, 54, 102, 150, 201])
		graph.add('All others combined!',  [5, 15, 21, 55, 92, 105])
		graph_data = graph.render_data_uri()
		return render_template("graphing.html", graph_data = graph_data)
	except Exception as e:
		return(str(e))
    
@app.route('/TheGreatDepression/')
def TheGreatDepression():
	try:
		pie_chart = pygal.Pie(width=500, height=400, explicit_size=True)
		pie_chart.title = 'Source Reviews for The Great Depression'
		pie_chart.add('Bad Sources', 6)
		pie_chart.add('Good Sources', 13)
		chart = pie_chart.render(is_unicode=True)
		return render_template("TheGreatDepression.html", chart=chart)
        #pie_chart = pygal.Pie()
        #pie_chart.title = 'The Great Depression Source 1'
        #pie_chart.add('Bad Source', 6)
        #pie_chart.add('Good Source', 13)
        #pie_chart.render_to_file('/static/images/TGDOne.svg')
	except Exception as e:
		return(str(e))

    #    def test():
#        bar_chart = pygal.HorizontalStackedBar()
#        bar_chart.title = "Remarquable sequences"
#        bar_chart.x_labels = map(str, range(11))
#        bar_chart.add('Fibonacci', [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55])
#        bar_chart.add('Padovan', [1, 1, 1, 2, 2, 3, 4, 5, 7, 9, 12]) 
#        chart = bar_chart.render(is_unicode=True)
#        return render_template('test.html', chart=chart )

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

@app.errorhandler(405)
def method_not_allowed(e):
    return render_template("405.html")

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html", error = e)

if __name__ == "__main__":
	app.run(debug=False) # should be turned off/False for production

