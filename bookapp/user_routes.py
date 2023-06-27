import re,random,os, requests, json
from flask import render_template, request, redirect, flash,make_response,session,url_for
from sqlalchemy.sql import text

from werkzeug.security import generate_password_hash, check_password_hash

from functools import wraps

from bookapp import app, csrf
from bookapp.models import db, Book, User, Category, Donation

from bookapp.forms import SignupForm, ProfileForm

# from bookapp.forms import ContactForm

def login_required(f):
    @wraps(f)
    def login_decorate(*args,**kwargs):
        if session.get('userid') and session.get('user_loggedin'):
            return f(*args, **kwargs)
        else:
            flash ('access denied, please login in')
            return redirect('/login')
    return login_decorate

@app.route("/")
def home():
    books= db.session.query(Book).filter(Book.book_status=='1').order_by(Book.book_id.desc()).limit(4).all()
    useronline= session.get('userid')
    userdeets = db.session.query(User).get(useronline)
    headers = {'Content-Type':'application/json'}
    response = requests.get('http://127.0.0.1:5000/api/v1.0/listall', headers, auth=('bookworm','python'))
    partner_stores=response.json()
    return render_template("user/home.html",books=books, userdeets=userdeets, partner_stores=partner_stores )

@app.route("/reviews/<bookid>")
def reviews(bookid):
    bookdeets = db.session.query(Book).get(bookid)
    return render_template("user/reviews.html", bookdeets=bookdeets)

@app.route("/dashboard")
@login_required
def dashboard():
    useronline= session.get_or_404('userid')
    userdeets = db.session.query(User).get(useronline)
    return render_template("user/dashboard.html", userdeets=userdeets)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method== "GET":
        return render_template("user/loginpage.html")
    else:
        username = request.form.get('email')
        password = request.form.get('password')
        deets= db.session.query(User).filter(User.user_email == username).first()
        if deets:
            hashedpwd = deets.user_pwd
            chk = check_password_hash(hashedpwd,password)
            if chk:
                session['user_loggedin'] = True
                session['userid'] = deets.user_id
                return redirect("/dashboard")
            else:
                flash('invaild user and 1')
                return redirect('/login')
        else:
                flash('invaild user and 2')
                return redirect('/login')

@app.route("/register", methods=["GET","POST"])
def register():
    signupform = SignupForm()
    if request.method== "GET":
        return render_template("user/signup.html", signupform=signupform)
    else:
        if signupform.validate_on_submit():
            userpass= request.form.get('password')
            u= User(user_fullname=request.form.get('fullname'), user_email=request.form.get('email'), user_pwd=generate_password_hash(userpass))
            db.session.add(u)
            db.session.commit()
            flash ("created succussful")
            return render_template("user/dashboard.html")
        else:
            return render_template("user/signup.html", signupform=signupform)
        
@app.route('/signout')
def signout():
    if session.get('userid') or session.get('user_loggedin'):
        session.pop('userid', None)
        session.pop('user_loggedin', None)
    return redirect("/login")



@app.route('/profile',  methods=["GET","POST"])
@login_required
def profile():
    pforms=ProfileForm()
    useronline = session.get('userid')
    userdeets = db.session.query(User).get(useronline)
    if request.method == "GET":
        return render_template('user/profile.html', pforms=pforms, userdeets=userdeets )
    else:
        if pforms.validate_on_submit():
            fullname= request.form.get('fullname')#or pforms.fullname.data
            picture = request.files.get('pix')# or pforms.pix.data.filename
            filename= pforms.pix.data.filename
            picture.save('bookapp/static/images/profile/'+ filename)
            userdeets.user_fullname=fullname
            userdeets.user_pix=filename
            db.session.commit()
            flash('profile updated')
            return redirect('/dashboard')
        else:
            return render_template('user/profile.html', pforms=pforms, userdeets=userdeets )

@app.route('/submitreview', methods=["POST"])
@login_required
def submit_review():
    return "only form submission allowed"


@app.route('/explore', methods=["POST","GET"])
def explore():
    books=db.session.query(Book).filter(Book.book_status=='1').all()
    cat = db.session.query(Category).all()
    return render_template('user/explore.html', books=books)

@app.route('/search/book')
def search_book():
    cate= request.args.get('category')
    title= request.args.get('title')
    search_title = '%'+title +'%' #or %{}%.format('title')
    result = db.session.query(Book).filter(Book.book_catid ==cate).filter(Book.book_title.ilike(search_title)).all()
    return result 


@app.route('/donate', methods=["POST","GET"])
def donation():
    useronline = session.get('userid')
    userdeets= db.session.query(User).get(useronline)
    if request.method == 'GET':
        return render_template('user/donation.html',userdeets=userdeets)
    else:
        #retrieve form data
        fullname= request.form.get('fullname')
        email= request.form.get('email')
        amount= request.form.get('amount')
        userid = request.form.get('userid')
        refno = int(random.random()*10000000)
        #create a new donation  instance
        don = Donation(don_amt=amount, don_userid=userid, don_fullname=fullname, don_email=email, don_refno=refno, don_status='pending')
        db.session.add(don)
        db.session.commit()
        #save the refno in a session so that we can retrive the details on the next page
        session['ref'] = refno
        return redirect('/payment')
    

@app.route('/payment')
def make_payment():
    userdeets= db.session.query(User).get(session.get('userid'))
    if session.get('ref')!= None:
        ref = session['ref']
        #to do we want to get the detail of the transaction and display to the user
        trxdeets= db.session.query(Donation).filter(Donation.don_refno==ref).first()
        return render_template('user/payment.html',trxdeets=trxdeets, userdeets=userdeets )
    else:
        return redirect('/donate')
    


@app.route("/paystack", methods=["POST"])
def paystack():
    if session.get('ref') != None:
        ref = session['ref']
        trx = db.session.query(Donation).filter(Donation.don_refno==ref).first()
        email= trx.don_email
        amount= trx.don_amt
        #we want to connect to psystack api
        url = 'https://api.paystack.co/transaction/initialize'
        headers= {"content-Type": "application/json", "Authorization":"Bearer sk_test_aa761236f6128d8be489aa460429c7f3f249f579"}
        data ={'email': email, 'amount': amount*100, 'reference':ref}
        response =requests.post(url, headers=headers, data=json.dumps(data))
        rspjson = response.json()
        if rspjson['status']== True:
            paygateway = rspjson['data']['authorization_url']
            return redirect(paygateway)
        else:
            return rspjson
    else:
        return redirect('/donate')
    

@app.route("/landing")
def paystack_landing():
    ref = session.get('ref')
    if ref == None:
        return redirect('/donate')
    else:
        #connect to paystack verify
        verifyurl = 'https://api.paystack.co/transaction/verify/'+str(ref)
        headers= {"content-Type": "application/json", "Authorization":"Bearer sk_test_aa761236f6128d8be489aa460429c7f3f249f579"}
        response = requests.get(verifyurl, headers=headers )
        rspjson = json.loads(response.text)
        if rspjson['status']==True:
            #payment was successfull
            return rspjson
        else:
            return "payment was not successfull"