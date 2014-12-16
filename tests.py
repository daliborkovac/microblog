#!/home/dkovac/virtualenv/python3.4_flask/bin/python
# This is a unit test script.
# For more information see: http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-vii-unit-testing
import os
import unittest

from datetime import datetime, timedelta
from config import basedir
from app import app, db
from app.models import User, Post


class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_avatar(self):
        u = User(nickname='john', email='john@example.com')
        avatar = u.avatar(128)
        expected = 'http://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6'
        assert avatar[0:len(expected)] == expected

    def test_make_unique_nickname(self):
        u = User(nickname='john', email='john@example.com')
        db.session.add(u)
        db.session.commit()
        nickname = User.make_unique_nickname('john')
        assert nickname != 'john'
        u = User(nickname=nickname, email='susan@example.com')
        db.session.add(u)
        db.session.commit()
        nickname2 = User.make_unique_nickname('john')
        assert nickname2 != 'john'
        assert nickname2 != nickname

    def test_follow(self):
        u1 = User(nickname='john', email='john@example.com')
        u2 = User(nickname='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        assert u1.unfollow(u2) is None          # test: u1 is still not following u2
        u = u1.follow(u2)
        db.session.add(u)
        db.session.commit()
        assert u1.follow(u2) is None       # test: u1 cannot follow u2 because u1 is already following u2
        assert u1.is_following(u2)         # test: u1 is following u2
        assert u1.followed.count() == 1    # test: u1 is following one other user
        assert u1.followed.first().nickname == 'susan'   # test: u1 is following susan
        assert u2.followers.count()        # test: u2 has one follower
        assert u2.followers.first().nickname == 'john'   # test: u2's follower is john
        u = u1.unfollow(u2)
        db.session.add(u)
        db.session.commit()
        assert not u1.is_following(u2)     # test: u1 is no longer following u2
        assert u1.followed.count() == 0    # test: u1 is not following anyone
        assert u2.followers.count() == 0   # test: u2 has no followers

    def test_follow_posts(self):
        # make four users
        u1 = User(nickname='john', email='john@example.com')
        u2 = User(nickname='susan', email='susan@example.com')
        u3 = User(nickname='mary', email='mary@example.com')
        u4 = User(nickname='david', email='david@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.add(u4)
        # make four posts
        utcnow = datetime.utcnow()
        p1 = Post(body="post from john", author=u1, timestamp=utcnow + timedelta(seconds=1))
        p2 = Post(body="post from susan", author=u2, timestamp=utcnow + timedelta(seconds=2))
        p3 = Post(body="post from mary", author=u3, timestamp=utcnow + timedelta(seconds=3))
        p4 = Post(body="post from david", author=u4, timestamp=utcnow + timedelta(seconds=4))
        db.session.add(p1)
        db.session.add(p2)
        db.session.add(p3)
        db.session.add(p4)
        db.session.commit()
        # setup the followers
        u1.follow(u1)  # john follows himself
        u1.follow(u2)  # john follows susan
        u1.follow(u4)  # john follows david
        u2.follow(u2)  # susan follows herself
        u2.follow(u3)  # susan follows mary
        u3.follow(u3)  # mary follows herself
        u3.follow(u4)  # mary follows david
        u4.follow(u4)  # david follows himself
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.add(u4)
        db.session.commit()
        # check the followed posts of each user
        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()
        assert len(f1) == 3
        assert len(f2) == 2
        assert len(f3) == 2
        assert len(f4) == 1
        assert f1 == [p4, p2, p1]
        assert f2 == [p3, p2]
        assert f3 == [p4, p3]
        assert f4 == [p4]


from coverage import coverage
# This will make our tests run with 'coverage', so that at the end we get a report of how much of our code
# has actually been run (tested).
# The omit parameter excludes some parts from coverage (e.g. we're not interested in coverage of standard python
# or Flask code).
cov = coverage(branch=True, omit=['tests.py', '/home/dkovac/virtualenv/*'])
cov.start()

if __name__ == '__main__':
    try:
        unittest.main()     # runs the tests through unittest module
    except:
        pass
    # stop the coverage monitoring and show the report
    cov.stop()
    cov.save()
    print('\n\nCoverage report:\n')
    cov.report()
    print('HTML version: {}'.format(os.path.join(basedir, 'tmp/coverage/index.html')))
    cov.html_report(directory='tmp/coverage')
    cov.erase()    # clean up the memory taken by coverage
