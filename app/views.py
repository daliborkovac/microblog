from flask import render_template, flash, redirect, session, url_for, request, g, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from .forms import LoginForm, EditForm, PostForm    # .forms is the same as app.forms, just shorter
from .models import User, Post                      # .models is the same as app.models, just shorter
from datetime import datetime
import sys
from math import ceil
from config import POSTS_PER_PAGE, LANGUAGES
from .emails import follower_notification
from app import babel
from guess_language import guess_language
from .translate import microsoft_translate

@app.before_request
def before_request():
    ''' This function is called before each request in our application (app).
    It is used to copy the Flask-Login current_user to the Flask g object, to
    have better access to it .

    The flask.g global object is setup by Flask as a place to store and share data
    during the life of a request.
    On the other hand, the flask.session provides a much more complex service.
    Once data is stored in the session object it will be available during that
    request and any future requests made by the same client (a client session state).
    Data remains in the session until explicitly removed. To be able to do this,
    Flask keeps a different session container for each client of our application.
    '''
    g.locale = get_locale()
    g.config = app.config
    g.user = current_user
    if g.user.is_authenticated():
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])             # requests on these two routes will cause this
@app.route('/index', methods=['GET', 'POST'])        # function to be run (these are mappings from URL to the function)
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@login_required       # no access to this function if you're not logged in
def index(page=1):
    post_form = PostForm()
    if post_form.validate_on_submit():
        # Form validation successful.
        # Store the post into database.
        # The following 4 lines (creating the post object and setting values) could have been done in just
        # one line: post = Post(body = post_form.post.data, timestamp = datetime.utcnow(), author = g.user)
        post = Post()
        post.body = post_form.post.data
        post.timestamp = datetime.utcnow()
        post.user_id = g.user.id              # this could have been done as post.author = g.user
        language = guess_language(post.body)
        # we'll try to automatically detect the post language
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post.language = language
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!', 'info')
        return redirect(url_for('index'))
    # If we're here then we one of these things happened:
    #    a) the page is just opening, or
    #    b) form validation failed
    # Either way, show the index page with posts.
    #
    # This was how I did the pagination, but there's a far better way to do that in Flask:
    # total_posts = g.user.followed_posts().count()
    # first_page = None if total_posts <= POSTS_PER_PAGE else 1
    # prev_page = None if page == 1 else page-1
    # last_page = int(ceil(total_posts/POSTS_PER_PAGE))
    # next_page = None if page == last_page else page + 1
    posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)   # this is a Paginate object
    return render_template('index.html',
                           title='Home',
                           user=g.user,
                           posts=posts,
                           form=post_form)
# Why we sometimes use redirect and sometimes render_template?
# We could have easily skipped the redirect and allowed the function to continue down into the
# template rendering part, and it would have been more efficient (saved one client-server roundtrip).
# Because really, all the redirect does is return to this same view function to do that, after an
# extra trip to the client web browser.
# So, why the redirect? Consider what happens after the user writes a blog post, submits it and then
# hits the browser's refresh key. What will the refresh command do? Browsers resend the last issued
# request as a result of a refresh command.
# Without the redirect, the last request is the POST request that submitted the form, so a refresh
# action will resubmit the form, causing a second Post record that is identical to the first to be
# written to the database. Not good.
# By having the redirect, we force the browser to issue another request after the form submission,
# the one that grabs the redirected page. This is a simple GET request, so a refresh action will
# now repeat the GET request instead of submitting the form again.
# This simple trick avoids inserting duplicate posts when a user inadvertently refreshes the page
# after submitting a blog post.


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    """ This function handles GET and POST requests from the login page.
    GET request is when the user is opening the page and POST is when user
    is submitting login information.
    :return:  renders a login page or redirects to the main page (index)
    """
    if g.user is not None and g.user.is_authenticated():
        # the user is already authenticated, no need to show login form
        return redirect(url_for('index'))   # url_for will produce the URL associated with function "index"
    # Create form object
    form = LoginForm()
    # The validate_on_submit method does all the form processing work.
    # If you call it when the form is being presented to the user (i.e. before the user got a
    # chance to enter data on it) then it will return False, so in that case you know that you
    # have to render the template.
    # When validate_on_submit is called as part of a form submission request, it will gather all
    # the data, run all the validators attached to fields, and if everything is all right it will
    # return True, indicating that the data is valid and can be processed. This is your indication
    # that this data is safe to incorporate into the application.
    # If at least one field fails validation then the function will return False and that will cause
    # the form to be rendered back to the user, and this will give the user a chance to correct any
    # mistakes.
    if form.validate_on_submit():
        # Form validation successful.
        # Store remember_me setting to Flask session
        session['remember_me'] = form.remember_me.data
        # Use Flask-OpenID to try to login the user.
        #     This function call will actually return redirect. If login is successful Flask.OpenID
        #     will call a function decorated with oid.after_login decorator, which will then return
        #     the redirect to the page we want to go after successful login.
        #     If login is not successful this OpenID call will redirect us back to login page.
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
    # If we're here then we one of these things happened:
    #    a) the login form is just opening, or
    #    b) form validation failed
    # Either way, show the login page.
    return render_template('login.html',
                           title='Sign In',
                           form=form,
                           providers=app.config['OPENID_PROVIDERS'])


@oid.after_login
def after_login(resp):
    """
    :param resp:  response of the OpenID call
    :return:      redirects
    """
    if resp.email is None or resp.email == "":
        # The OpenID call did not return an email
        flash('Invalid login. Please try again')
        # go back to login page
        return redirect(url_for('login'))
    # fetch user by email
    usr = User.query.filter_by(email=resp.email).first()
    if usr is None:
        # Such a user doesn't exit yet, we'll create a new user now.
        # Get nickname from the OpenID response
        nickname = resp.nickname
        if nickname is None or nickname == "":
            # we didn't get the nickname from OpenID, we'll use first part of email
            nickname = resp.email.split('@')[0]
        # this will make sure that nickname is unique
        nickname = User.make_unique_nickname(nickname)
        # create user object
        usr = User(nickname=nickname, email=resp.email)
        # and insert it into the database
        db.session.add(usr)
        db.session.commit()
        # add the user as follower to himself (so he can see his own posts among the posts of followed users)
        db.session.add(usr.follow(usr))
        db.session.commit()
    # set remember_me, either from the value stored in session or default to False
    remember_me = False
    if 'remember_me' in session:
        # take the value from the session
        remember_me = session['remember_me']
        # and remove that value from the session (we will not be needing it in the session
        # any more because we'll hand it over to Flask-login in a call to login_user
        session.pop('remember_me', None)
    # log in the user with Flask-Login
    login_user(usr, remember=remember_me)
    # and redirect to the 'next' page provided in the request, or to the index page if there's no 'next'
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@lm.user_loader
def load_user(user_id):
    """ Used by Flask-Login extension to get the User object. In our case we're loading
    the user from database.
    @lm.user_loader is a Flask-Login extension decorator by which that extension will know it has to call
    this function to obtain the user object. The function itself can be called whatever you like. The only
    important thing is to decorate it with this specific decorator.

    :param id: ID of the user (unique identifier obtained by User.get_id(). That's why we need to convert it
               to int before handing it over to query.get method.
    :return:   object of class User.
    """
    return User.query.get(int(user_id))


@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
    """ This is the function for generating user's profile view.
    :param nickname: nickname of the user whose profile we want to show
    :return: renders the page that displays user profile
    """
    usr = User.query.filter_by(nickname=nickname).first()
    if usr is None:
        flash('User {} not found.'.format(nickname))
        return redirect(url_for('index'))
    posts = usr.posts.order_by(Post.timestamp.desc()).paginate(page, POSTS_PER_PAGE, False)   # this is a Paginate object
    return render_template('user.html',
                           user=usr,
                           posts=posts)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """ This is the function for generating user's edit profile view.
    :return: on GET: Renders the edit page
             on POST: if everything is ok saves data to database and redirects to user profile display page
                      if the form validation fails it displays the same page back with errors displayed
    """
    # this is my version
    form = EditForm(g.user.nickname)
    if request.method == 'GET':
        # populate the form and display it
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
        return render_template('edit.html',
                               form=form,
                               email=g.user.email)
    elif request.method == 'POST':
        # validate user input
        if form.validate_on_submit():
            g.user.nickname = form.nickname.data
            g.user.about_me = form.about_me.data
            db.session.add(g.user)
            db.session.commit()
            flash('Your changes have been saved.', 'info')
            # display new user profile
            return redirect(url_for('user', nickname=g.user.nickname))
        else:
            # form is not valid, redisplay it with error messages
            flash("Oops! Something's not quite right!", 'error')
            return render_template('edit.html',
                                   form=form,
                                   email=g.user.email)
    # this is the version from the tutorial
    # form = EditForm()
    # if form.validate_on_submit():
    #     g.user.nickname = form.nickname.data
    #     g.user.about_me = form.about_me.data
    #     db.session.add(g.user)
    #     db.session.commit()
    #     flash('Your changes have been saved.')
    #     return redirect(url_for('edit'))
    # else:
    #     form.nickname.data = g.user.nickname
    #     form.about_me.data = g.user.about_me
    # return render_template('edit.html', form=form)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    user_to_follow = User.query.filter_by(nickname=nickname).first()
    if user_to_follow is None:
        flash('Unknown user {}'.format(nickname), 'error')
    elif user_to_follow == g.user:
        flash('You cannot follow yourself!', 'error')
    elif not g.user.is_following(user_to_follow):
        u = g.user.follow(user_to_follow)
        if u is not None:
            db.session.add(u)
            db.session.commit()
            flash('You are now following {}'.format(nickname), 'info')
            # send a notification email to the followed user
            follower_notification(user_to_follow, g.user)
        else:
            flash('Cannot follow {}'.format(nickname), 'error')
    else:
        flash('You are already following {}'.format(nickname), 'error')
    # return to the user profile
    return redirect(url_for('user', nickname=nickname))


@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    user_to_unfollow = User.query.filter_by(nickname=nickname).first()
    if user_to_unfollow is None:
        flash('Unknown user {}'.format(nickname), 'error')
    elif user_to_unfollow == g.user:
        flash('You cannot unfollow yourself!', 'error')
    elif g.user.is_following(user_to_unfollow):
        u = g.user.unfollow(user_to_unfollow)
        if u is not None:
            db.session.add(u)
            db.session.commit()
            flash('You are not following {} any more'.format(nickname), 'info')
        else:
            flash('Cannot unfollow {}'.format(nickname), 'error')
    else:
        flash('You are not following {}'.format(nickname), 'error')
    # return to the user profile
    return redirect(url_for('user', nickname=nickname))


# The function that is marked with the localeselector decorator will be called before each request to
# give us a chance to choose the language to use when producing its response.
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())


@app.route('/translate', methods=['POST'])
@login_required
def translate():
    return jsonify({
        'text': microsoft_translate(request.form['text'],
                                    request.form['sourcelang'],
                                    request.form['destlang'])  })


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    post = Post.query.get(id)
    if post is None:
        flash('Post with ID {} not found'.format(id), 'error')
        return redirect(url_for('index'))
    if post.author != g.user:
        flash('You cannot delete this post!', 'error')
        return redirect(url_for('index'))
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted.', 'info')
    return redirect(url_for('index'))
