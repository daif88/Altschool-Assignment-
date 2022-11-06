from project import app, db, bcrypt
from flask import render_template, flash, redirect,url_for, request, abort
from project.form import LoginForm, RegistrationForm, UpdateAccountForm, NewsForm, ContactForm
from project.models import User, News
import os
import secrets
from PIL import Image
from flask_login import login_user, current_user, logout_user, login_required

@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    news = News.query.order_by(News.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template("home.html", news=news)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, email=form.email.data, password = hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account Created Successfully, Welcome!!', category="success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("Login Unsuccessful. Please check email and password", category="danger")
            
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, "static/profile_pics", picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account")
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.validate_on_submit():
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        #The user edited on the form will become the new username
        current_user.username = form.username.data
        #The user edited on the form will become the new username
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', category='success')
        return redirect(url_for("account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template("account.html", image_file=image_file, form=form)

@app.route("/post/new", methods=["GET", "POST"])
@login_required
def new_post():
    form = NewsForm()
    if form.validate_on_submit():
        lastest_post = News(title = form.title.data, content = form.content.data, user_id=current_user.id)
        db.session.add(lastest_post)
        db.session.commit()
        flash("Your Post Has been created", category="success")
        return redirect(url_for("home"))
    return render_template ("create_news.html", title="New Post", form=form, legend="New Post")

#Routes to get a particular blogpost on a different page
@app.route("/post/<int:post_id>")
def post(post_id):
    post = News.query.get_or_404(post_id)
    return render_template("news.html", new=post)

@app.route("/post/<int:post_id>/update", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    post = News.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = NewsForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Your Post has been updated", category="success")
        return redirect(url_for("post", post_id=post.id))
    elif request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content
    return render_template ("create_news.html", form=form)

@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = News.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your Post has been deleted", category="success")
    return redirect(url_for("home"))

@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    news = News.query.filter_by(author=user).order_by(News.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template("user_news.html", news=news, user=user)

