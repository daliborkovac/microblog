from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length
from .models import User


class LoginForm(Form):
    '''Web forms are represented in Flask-WTF as classes, subclassed
    from base class Form. A form subclass simply defines the fields
    of the form as class variables.'''
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)


class EditForm(Form):
    nickname = StringField('nickname', validators=[DataRequired(), Length(min=1, max=64)])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])

    # a new custom constructor, to get the original_nickname attribute in the object
    def __init__(self, original_nickname, *args, **kwargs):
        """ This overrides the constructor from Form class. We're ignoring all the named arguments from
        the parent class - their default values will be used when calling the constructor from parent class.
        :param original_nickname: our custom parameter for getting in the original nickname of the user
        :param args:    optional tuple parameters that the parent class also has
        :param kwargs:  optionsal keyword parameters that the parent class also has
        :return: creates a form object, with the additional attribute original_nickname
        """
        # at the beginning call the constructor from the parent class:
        super().__init__(*args, **kwargs)
        # and then set our additional attribute:
        self.original_nickname = original_nickname

    # overriding the validate method to include our custom validation
    def validate(self):
        # first do the default validation
        default_validation = super().validate()
        # and then our custom validation
        custom_validation = True
        if self.nickname.data != self.original_nickname:
            # user has changed a nickname, we have to check that for uniqueness
            new_nickname = User.make_unique_nickname(self.nickname.data)
            if new_nickname != self.nickname.data:
                # we have a new nickname suggestion, let's warn the user about that and get him back to the form
                self.nickname.errors.append('Nickname {} is already taken.'.format(self.nickname.data) +
                                            ' A unique nickname has been suggested for you.')
                self.nickname.data = new_nickname
                custom_validation = False
        return default_validation and custom_validation

class PostForm(Form):
    post = StringField('post', validators=[DataRequired(), Length(min=1, max=140)])