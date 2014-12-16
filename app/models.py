from app import db    # this is our database object, created in __init_py__
from app import app    # this is our flask application object, created in __init_py__
from hashlib import md5   # we'll need this for the avatars from Gravatar

import sys
if sys.version_info >= (3, 0):
    enable_search = False
else:
    enable_search = True
    import flask.ext.whooshalchemy as whooshalchemy


# For the many-to-many table that will record followers we're not using a model like for
# other tables. Since this is an auxiliary table that has no data other than the foreign keys,
# we use the lower level APIs in flask-sqlalchemy to create the table without an associated model.
# Flask-SQLAlchemy documentation on https://pythonhosted.org/Flask-SQLAlchemy/models.html#many-to-many-relationships
# also recommends that: "For this helper table it is strongly recommended to not use a model but an actual table".
#
# The 'followers' is just an object that defines a table, it doesn't contain data.
# The actual data in this table will be maintained through relationships of the User objects ('followed' and
# 'followers').
followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))

class User(db.Model):
    ''' This class represents a record in User database table
    '''
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    # This is not an actual database field. With this relationship we get a user.posts member
    # that gets us the list of posts from the user.
    # The backref argument defines a field that will be added to the objects of the Post class
    # that points back at the user object. In our case this means that we can use post.author
    # to get the User instance that created a post.
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)
    # Relationship to get a list of followed users. This list acts as a member of objects of this class
    # and we can work with this list as with any other list (count it, get first or last element, ...).
    followed = db.relationship('User',                                           # We're ultimately linking to
                                                                                 # this entity (also a user).
                               secondary=followers,                              # A table with many-to-many links
                                                                                 #  (association table).
                               primaryjoin=(followers.c.follower_id == id),      # Join from this entity's id to
                                                                                 # association table's follower_id.
                               secondaryjoin=(followers.c.followed_id == id),    # Join from association table's
                                                                                 # followed_id to other user's id.
                               backref=db.backref('followers', lazy='dynamic'),  # On the opposite side (that other
                                                                                 # user), this same relationship will
                                                                                 # be called followers.
                               lazy='dynamic')

    def __repr__(self):
        return '<User %r>' % (self.nickname)

    # The following few methods (is_authenticated, is_active, is_anonymous, get_id) are
    # required by Flask-Login extension to be part of User class

    def is_authenticated(self):
        '''
        :return:  True if this user is allowed to authenticate (to log in)
                  False if this user is not allowed to log in
        We don't have a mechanism to disallow someone from logging in, so we're returning
        True for all users. But, if we had such a mechanism we would have to write some
        logic here.
        '''
        return True

    def is_active(self):
        '''
        :return:  True  if this user is active
                  False if this user is inactive
        We don't have an active/inactive indicator on users, so we're returning True
        for all users. But, if we had that we would have to write some logic here.
        '''
        return True

    def is_anonymous(self):
        '''
        :return:  True  if this user is anonymous
                  False if this user is not anonymous
        This method should return True only for fake users that are not supposed to log in to the system.
        '''
        return False

    def get_id(self):
        '''
        :return:  unique identifier of the user, in unicode format string
        '''
        try:
            return unicode(self.id)    # this works in Python 2
        except NameError:
            return str(self.id)        # this works in Python 3

    def avatar(self, size):
        """
        :param size: the size of the avatar image you need
        :return: returns the URL of the user's avatar image, scaled to the requested size in pixels.
        """
        return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % (md5(self.email.encode('utf-8')).hexdigest(), size)

    @staticmethod        # because this method does not apply to any particular instance of the User class
    def make_unique_nickname(nickname):
        """ This method checks if the given nickname already exists in the database, and if
        it does then creates a new unique nickname by adding numbers to original nickname
        :param nickname: the nickname we want to check for uniqueness
        :return: a new nickname with added suffix to make it unique
        """
        new_nickname = nickname
        suffix = 1
        while User.query.filter_by(nickname=new_nickname).first():
            # query has returned a user, increase suffix and generate a new nickname
            suffix += 1
            new_nickname = nickname + str(suffix)
        return new_nickname

    # The follow and unfollow methods are amazingly simple, thanks to the power of sqlalchemy who does a lot of
    # work under the covers. We just add or remove items from the followed relationship and sqlalchemy takes care
    # of managing the association table for us.
    # The follow and unfollow methods are defined so that they return an object when they succeed or None when they
    # do nothing. When an object is returned, this object has to be added to the database session and committed.
    # See http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-viii-followers-contacts-and-friends
    # for further explanation.
    def follow(self, user_to_follow):
        """ This method is used to create a 'follows' relationship.
        :param user_to_follow: a user that we want to follow
        :return: This method inserts a record that indicates the 'follows' relationship.
        """
        if not self.is_following(user_to_follow):
            self.followed.append(user_to_follow)
            return self

    def unfollow(self, user_to_unfollow):
        """ This method is used to delete a 'follows' relationship
        :param user_to_unfollow: a user that we want to un-follow
        :return: This method deletes a record that indicates the 'follows' relationship.
        """
        if self.is_following(user_to_unfollow):
            self.followed.remove(user_to_unfollow)
            return self

    def is_following(self, user):
        """ This method is used to check if this user is following another user
        :param user: we want to check if we're following that user
        :return: True or False
        """
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        return ((Post.query.join(followers,                                  # join Post query with followers table
                                 (followers.c.followed_id == Post.user_id)   # with this join condition
                                )
                ).filter(followers.c.follower_id == self.id)    # filter posts where I am the follower
               ).order_by(Post.timestamp.desc())                # and order them by time, descending


class Post(db.Model):
    ''' This class represents a record in Post database table
    '''
    __searchable__ = ['body']    # this indicates that body column will be indexed by Flask-WhooshAlchemy
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post "{}" by {}>'.format(self.body, self.author.nickname)


if enable_search:
    whooshalchemy.whoosh_index(app, Post)