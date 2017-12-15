import cs50
import os
import sqlalchemy
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure responses aren't cached

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# defining SQL object natively
class SQL(object):
    def __init__(self, url):
        try:
            self.engine = sqlalchemy.create_engine(url)
        except Exception as e:
            raise RuntimeError(e)
    def execute(self, text, *multiparams, **params):
        try:
            statement = sqlalchemy.text(text).bindparams(*multiparams, **params)
            result = self.engine.execute(str(statement.compile(compile_kwargs={"literal_binds": True})))
            # SELECT
            if result.returns_rows:
                rows = result.fetchall()
                return [dict(row) for row in rows]
            # INSERT
            elif result.lastrowid is not None:
                return result.lastrowid
            # DELETE, UPDATE
            else:
                return result.rowcount
        except sqlalchemy.exc.IntegrityError:
            return None
        except Exception as e:
            raise RuntimeError(e)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///registry.db")

@app.route("/")
def home():
    """Show home screen"""
    return render_template("home.html")

@app.route("/data")
@login_required
def data():

    #physician names
    names = db.execute("SELECT physfirst,physlast FROM physicians WHERE userid = :userid", userid=session["user_id"])
    fname = names[0]["physfirst"]
    lname = names[0]["physlast"]

    # physician id to access relevant patients
    pid = db.execute("SELECT physid FROM physicians WHERE userid = :userid", userid=session["user_id"])
    physicianid = pid[0]["physid"]

    # access relevant patient information
    patients = db.execute("SELECT * FROM patients WHERE physid = :physid",
                                physid = physicianid)

    # counter for number of patients
    count = 0

    # counters and lists to hold patient information
    ages = []
    allages=[]
    allmales=0
    allfemales=0
    allhips=0
    allknees=0
    males = 0
    females = 0
    hips = 0
    knees = 0

    # loops through patient table, extracting relevant values and incrementing counters
    for entry in patients:
        age = entry["age"]
        ages.append(age)

        sex = entry["sex"]
        if sex == "male":
            males += 1
        elif sex == "female":
            females += 1
        count += 1

        bodypart = entry["bodypart"]
        if bodypart == "hip":
            hips += 1
        elif bodypart == "knee":
            knees +=1

    #average age
    avg = sum(ages)/len(ages)

    # total number of patients
    total = count

    # percentage split of sex
    males = (males/total)*100
    females = (females/total)*100

    # percentage split of bodypart
    hips = (hips/total)*100
    knees = (knees/total)*100

    # pull information about all patients
    allpatients = db.execute("SELECT * FROM patients")
    # counter for all patients
    allcount = 0

    # for loop to increment relevant counters
    for entry in allpatients:
        age = entry["age"]
        allages.append(age)

        sex = entry["sex"]
        if sex == "male":
            allmales += 1
        elif sex == "female":
            allfemales += 1

        bodypart = entry["bodypart"]
        if bodypart == "hip":
            allhips += 1
        elif bodypart == "knee":
            allknees +=1

        allcount += 1

    #average age of all patients
    AVG = sum(allages)/len(allages)

    # total number of patients
    TOTAL = allcount

    # percentage split of sex
    allmales = (allmales/TOTAL)*100
    allfemales = (allfemales/TOTAL)*100

    # percentage split of bodypart
    allhips = (allhips/TOTAL)*100
    allknees = (allknees/TOTAL)*100


    return render_template("data.html", fname=fname, lname=lname, patients=patients, total=total, avg=avg, ages=ages, males=males,
                                        females=females, hips=hips, knees=knees,AVG=AVG,allmales=allmales,allfemales=allfemales,
                                        allhips=allhips,allknees=allknees,allcount=allcount, TOTAL=TOTAL)


# Define index
@app.route("/index")
@login_required
def index():
    # render index page
    physname = db.execute("SELECT * FROM physicians WHERE userid = :userid", userid = session["user_id"])
    fname = physname[0]["physfirst"]
    return render_template("index.html",fname=fname)

# Define index for hospitals
@app.route("/indexhosp")
@login_required
def indexhosp():

    return render_template("indexhosp.html")

# Pages for hospital
@app.route("/suppliershosp")
@login_required
def suppliershosp():
    return render_template("suppliershosp.html")

# Pages for hospitals
@app.route("/hospitalshosp")
@login_required
def hospitalshosp():
    return render_template("hospitalshosp.html")

# Pages for hospitals
@app.route("/datahosp")
@login_required
def datahosp():
    return render_template("datahosp.html")

# Define index for suppliers
@app.route("/indexind")
@login_required
def indexind():
    return render_template("indexind.html")

# Supplier layout-based code
@app.route("/newproduct")
@login_required
def newproduct():
    return render_template("newproduct.html")

# Products page for industry
@app.route("/products")
@login_required
def products():
    return render_template("products.html")

@app.route("/suppliersind")
@login_required
def suppliersind():
    """Show table of implant suppliers"""

    # access relevant supplier information
    suppliers = db.execute("SELECT indname FROM industry")

    return render_template("suppliers.html", suppliers = suppliers)

@app.route("/hospitalsind")
@login_required
def hospitalsind():
    return render_template("hospitalsind.html")

@app.route("/dataind")
@login_required
def dataind():
    return render_template("dataind.html")

@app.route("/suppliers")
@login_required
def suppliers():
    """Show table of implant suppliers"""

    # access relevant supplier information
    suppliers = db.execute("SELECT indname FROM industry")

    return render_template("suppliers.html", suppliers = suppliers)

@app.route("/hospitals")
@login_required
def hospitals():
    """Show table of hospitals"""

    # access relevant supplier information
    hospitals = db.execute("SELECT hospname FROM hospital")

    return render_template("hospitals.html", hospitals = hospitals)


# inputting a new patient file
@app.route("/patient", methods=["GET", "POST"])
@login_required
def patient():
    """create a new record for a patient"""
    if request.method == "POST":

        # Get userid to insert into physicians table

        copy = db.execute("SELECT physid FROM physicians WHERE userid = :userid", userid = session["user_id"])
        physicianid=copy[0]["physid"]

        patient = db.execute("INSERT INTO patients (firstname,lastname,age,sex,bodypart,implanttype,bodyside,proceduretype,scorebefore,scoreafter,date,city,hospital,physid) VALUES(:firstname,:lastname,:age,:sex,:bodypart,:implanttype,:bodyside,:proceduretype,:scorebefore,:scoreafter,:date,:city,:hospital,:physid)",
                        firstname=request.form.get("firstname"),
                        lastname=request.form.get("lastname"),
                        age=request.form.get("age"),
                        sex=request.form.get("sex"),
                        bodypart=request.form.get("bodypart"),
                        implanttype=request.form.get("implanttype"),
                        bodyside=request.form.get("bodyside"),
                        proceduretype=request.form.get("proceduretype"),
                        scorebefore=request.form.get("scorebefore"),
                        scoreafter=request.form.get("scoreafter"),
                        date=request.form.get("date"),
                        city=request.form.get("city"),
                        hospital=request.form.get("hospital"),
                        physid=physicianid
                        )

        return redirect("/index")
    else:
        return render_template("patient.html")

@app.route("/pastpatients", methods=["GET","POST"])
@login_required
def pastpatients():
    """Show table of inputted patients"""

    # physician first and last name
    names = db.execute("SELECT physfirst,physlast FROM physicians WHERE userid = :userid", userid=session["user_id"])
    fname = names[0]["physfirst"]
    lname = names[0]["physlast"]

    # physician id to access relevant patients
    pid = db.execute("SELECT physid FROM physicians WHERE userid = :userid", userid=session["user_id"])
    physicianid = pid[0]["physid"]

    # access relevant patient information
    patients = db.execute("SELECT * FROM patients WHERE physid = :physid",
                                physid = physicianid)
    # counter for number of patients
    count = 0

    for entry in patients:
        count += 1

    total = count

    return render_template("pastpatients.html", fname=fname, lname=lname, patients=patients, total=total)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Show user profile"""

    if request.method == "POST":
        user = db.execute("SELECT usertype FROM users WHERE id = :id", id=session["user_id"])
        if user=="physician":
            return redirect("phyprofile")
        elif user=="hospital":
            return redirect("hosprofile")
        elif user=="industry":
            return redirect("indprofile")
    else:
        return render_template("home.html")

@app.route("/phyprofile", methods=["GET", "POST"])
@login_required
def phyprofile():
    """Show physician profile"""
    physinfo = db.execute("SELECT * FROM physicians WHERE userid=:userid", userid=session["user_id"])
    first = physinfo[0]["physfirst"]
    last = physinfo[0]["physlast"]
    phone = physinfo[0]["physphone"]
    email = physinfo[0]["physemail"]
    practice = physinfo[0]["physarea"]
    hospital = physinfo[0]["physhospital"]
    city = physinfo[0]["physcity"]
    physid = physinfo[0]["physid"]

    return render_template("phyprofile.html", first=first,last=last,physid=physid, phone=phone, email=email, hospital=hospital, practice=practice, city=city)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)
        # Remember which user has logged in
        session["user_id"] = rows[0]["userid"]

        utype = db.execute("SELECT * FROM users WHERE userid = :userid",
                          userid=session["user_id"])
        usertype = utype[0]["usertype"]
        if(usertype == "physician"):
            return redirect("/index")
        elif(usertype == "hospital"):
            return redirect("/indexhosp")
        else:
            return redirect("/indexind")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Send user to relevant Register pages"""

    if request.method == "POST":
        user=request.form.get("usertype")
        if user=="physician":
            return redirect("phyregister")
        elif user=="hospital":
            return redirect("hosregister")
        elif user=="industry":
            return redirect("indregister")

    else:
        return render_template("register.html")


@app.route("/phyregister", methods=["GET", "POST"])
def phyregister():
    """Physician Register page"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password")

        # Ensure confirm password was submitted
        if not request.form.get("confirmation"):
            return apology("Please confirm password")

        # check to make sure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match")

        password = request.form.get("password")
        encrypted_pass = generate_password_hash(password)

        # Insert username into the database
        result = db.execute("INSERT INTO users (usertype,username,hash) VALUES(:usertype,:username,:hash)",
                                usertype="physician", username=request.form.get("username"), hash=encrypted_pass)
        if not result:
            return apology("Username already taken")

        # Get userid to insert into physicians table
        copy = db.execute("SELECT * FROM users WHERE username = :username", username = request.form.get("username"))
        # Remember which user registered and remain logged in
        session["user_id"] = copy[0]["userid"]
        uid = session["user_id"]

        # Insert personal information into physicians table
        db.execute("INSERT INTO physicians (physfirst,physlast,physemail,physphone,physarea,physcity,physhospital,userid) VALUES(:physfirst,:physlast,:physemail,:physphone,:physarea,:physcity,:physhospital,:userid)",
                                physfirst=request.form.get("firstname"),
                                physlast=request.form.get("lastname"),
                                physemail=request.form.get("email"),
                                physphone=request.form.get("phone"),
                                physarea=request.form.get("practice"),
                                physcity=request.form.get("city"),
                                physhospital=request.form.get("hospital"),
                                userid=uid)

        usertype = copy[0]["usertype"]
        # Redirect user to index page
        return redirect("/index")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("phyregister.html")

@app.route("/hosregister", methods=["GET", "POST"])
def hosregister():
    """Hospital Register page"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Ensure confirm password was submitted
        elif not request.form.get("confirmation"):
            return apology("Please confirm password")

        # check to make sure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match")

        else:
            password = request.form.get("password")
            encrypted_pass = generate_password_hash(password)

            # Insert username into the database
            result = db.execute("INSERT INTO users (usertype,username,hash) VALUES(:usertype, :username, :hash)",
                                usertype="hospital", username=request.form.get("username"), hash=encrypted_pass)
            # If username already exists return apology
            if not result:
                return apology("Username already taken")

        copy = db.execute("SELECT * FROM users WHERE username = :username", username = request.form.get("username"))
        # Remember which user registered and remain logged in
        session["user_id"] = copy[0]["userid"]
        uid = session["user_id"]

        # Insert personal information into physicians table
        db.execute("INSERT INTO hospital (hospname,hospcity,hospbeds,hosemail,hosphone,userid) VALUES(:hospname,:hospcity,:hospbeds,:hosemail,:hosphone,:userid)",
                                hospname=request.form.get("hospitalname"),
                                hospcity=request.form.get("hospitalcity"),
                                hospbeds=request.form.get("hospitalbeds"),
                                hosemail=request.form.get("hospitalemail"),
                                hosphone=request.form.get("hospitalnumber"),
                                userid=uid)

        usertype = copy[0]["usertype"]
        # Redirect user to home page
        return redirect("/indexhosp")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("hosregister.html")


@app.route("/indregister", methods=["GET", "POST"])
def indregister():
    """Industry Register page"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Ensure confirm password was submitted
        elif not request.form.get("confirmation"):
            return apology("Please confirm password")

        # check to make sure passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match")

        else:
            password = request.form.get("password")
            encrypted_pass = generate_password_hash(password)

            # Insert username into the database
            result = db.execute("INSERT INTO users (usertype,username,hash) VALUES(:usertype,:username, :hash)",
                                usertype="industry", username=request.form.get("username"), hash=encrypted_pass)

            # If username already exists return apology
            if not result:
                return apology("Username already taken")

        copy = db.execute("SELECT * FROM users WHERE username = :username", username = request.form.get("username"))

        # Remember which user registered and remain logged in
        session["user_id"] = copy[0]["userid"]
        uid = session["user_id"]

        # Insert personal information into physicians table
        db.execute("INSERT INTO industry (indname,indtype,indrepfirst,indreplast,indrepphone,indemail,userid) VALUES(:indname,:indtype,:indrepfirst,:indreplast,:indrepphone,:indemail,:userid)",
                                indname=request.form.get("indname"),
                                indtype=request.form.get("indtype"),
                                indrepfirst=request.form.get("indrepfirst"),
                                indreplast=request.form.get("indreplast"),
                                indrepphone=request.form.get("indrepphone"),
                                indemail=request.form.get("indemail"),
                                userid=uid)

        usertype = copy[0]["usertype"]

        # Redirect user to home page
        return redirect("/indexind")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("indregister.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)



# allow local hosting
if __name__=='__main__':
	app.debug = True
	port = int(os.environ.get("PORT", 5000))
	app.run(host='0.0.0.0', port=port)