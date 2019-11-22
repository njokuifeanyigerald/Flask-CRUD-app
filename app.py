from flask import Flask, render_template, redirect, request, url_for, flash,session, logging
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form,StringField, TextAreaField, PasswordField, validators, DateField,BooleanField
from werkzeug.security  import generate_password_hash, check_password_hash
from wtforms.fields.html5 import EmailField
from data import Articles
from flask_login import UserMixin, LoginManager, login_required, logout_user, current_user, login_user, login_fresh
from datetime import datetime
from functools import wraps

app = Flask(__name__)

app.debug=True
app.config['SQLALCHEMY_DATABASE_URI']= 'postgresql://postgres:12345@localhost/viral'
app.config['SQLALCHEMY_BINDS'] = {
    'viral'  : 'postgresql://postgres:12345@localhost/viral',
    'articles' : 'postgresql://postgres:12345@localhost/Article_Data'

}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db = SQLAlchemy(app)
Articles = Articles()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class Viral(UserMixin,db.Model):
    __bind_key__ = "viral"
    __tablename__= "viral"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(70))
    username = db.Column(db.String(700), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String())
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self,name,username,email,password):
        self.name = name
        self.username = username
        self.email =email
        self.password =password

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

@login_manager.user_loader
def load_user(user_id):
    return Viral.query.get(int(user_id))


class RegisterForm(Form):
    name = StringField('name',[validators.Length(min=3, max=60)])
    username = StringField('username', [validators.Length(min=1, max=60)])
    email = EmailField('Email address', [validators.DataRequired(), validators.Email()])
    password = PasswordField('password', [validators.DataRequired(), validators.EqualTo('confirm', message="password do not match")])
    confirm = PasswordField('confirm password')

class LoginForm(Form):
    email = EmailField('Email address', [validators.DataRequired(), validators.Email()])
    password = PasswordField('password', [validators.DataRequired()])
    remember =BooleanField('remember me' )

@app.route('/')
def home():
    data = Article_data.query.all()
    if data: 
        return render_template('home.html',data=data)
    else:
        flash('No Article Found', "info")
        return render_template('home.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    
    if request.method == 'POST' and form.validate():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = Viral(name= form.name.data,username= form.username.data, email= form.email.data,password= hashed_password )
        if Viral.query.filter_by(username = form.username.data ).count() == 0:
            if Viral.query.filter_by(email = form.email.data).count() == 0:
                db.session.add(new_user)
                db.session.commit()
                flash('you are now registered and can login', 'success')
                return redirect(url_for('login'))
            else:
                flash('email already exist', 'warning')
                return render_template ('register.html', form=form)
        else: 
            flash('username already exist', 'warning')
            return render_template ('register.html', form=form)
        
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm(request.form)
    if request.method=="POST" and form.validate:
        old_user = Viral.query.filter_by(email=form.email.data).first()
        if old_user:
            
            if check_password_hash(old_user.password, form.password.data):
                
                login_user(old_user)
                flash('you have successfully logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('invalid password', 'danger')
                return render_template('login.html', form=form)
            
        else:
            flash('invalid email', 'danger')
            return render_template('login.html', form=form)
    else:
        return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()

    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    name=current_user.username
    data = Article_data.query.all()
    if data: 
        return render_template('dashboard.html',data=data, name=name)
    else:
        flash('No Article Found', "info")
        return render_template('dashboard.html',name=name)

class Article_data(UserMixin,db.Model):
    __bind_key__ = "articles"
    __tablename__= "articles"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    subtitle = db.Column(db.String(200))
    author = db.Column(db.String(100))
    body = db.Column(db.Text )    
    date = db.Column(db.DateTime, default=datetime.utcnow)
    

    def __init__(self,title,author,subtitle,body):
        self.title = title
        self.subtitle = subtitle
        self.author = author
        self.body =body   

  
class ArticleForm(Form):
    title = StringField('title', [validators.Length(min=1, max=60)])
    subtitle = StringField('subtitle', [validators.Length(min=20, max=200)])
    body = TextAreaField('body', [validators.Length(min=30)])


@app.route('/add_article', methods=['GET', 'POST']) 
@login_required  
def add_article():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        data = Article_data(title = form.title.data,author=current_user.username,subtitle=form.subtitle.data, body=form.body.data )
        db.session.add(data)
        db.session.commit()
        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

@app.route('/article/<id>/')
def article(id):
    data = Article_data.query.filter_by(id=int(id)).first()
    return render_template('article.html', data=data, id=id)

@app.route('/edit_article/<id>/', methods=['GET','POST'])
@login_required
def edit_article(id):
    
    data = Article_data.query.filter_by(id=int(id)).first()
    form = ArticleForm(request.form)
    data.title = form.title.data
    data.subtitle = form.subtitle.data
    data.body = form.body.data
    
    if request.method == 'POST' and form.validate():
        
        db.session.commit()
        flash('article updated', 'success')
        return redirect('/dashboard')
    
    return render_template("edit_article.html",form=form)


@app.route('/delete_article/<id>/', methods=['POST'])
@login_required
def delete_article(id):
    if request.method == 'POST':
        data = Article_data.query.filter_by(id=int(id)).first()
        db.session.delete(data)
        db.session.commit()
        return redirect(url_for('dashboard'))

if __name__=="__main__":
    app.secret_key = "heyyf"
    app.run()