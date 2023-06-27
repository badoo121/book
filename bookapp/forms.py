from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo

from flask_wtf.file import FileField, FileAllowed, FileRequired

#from wtforms import StringField, SubmitField,TextAreaField, PasswordField




class SignupForm(FlaskForm):
    fullname = StringField("Fullname",validators=[DataRequired(message="yourfullname is required")])
   
    email = StringField("Your Email",validators=[Email()])
    password =PasswordField("password",validators=[DataRequired()])
    #confirm_password=PasswordField("Confirm password",validators =[EqualTo('password',message="Confirm password must be equal to password")])
    #message = TextAreaField("Message", validators=[Length(1,30)])
    
    btn = SubmitField("Sign Up!")

 
class ProfileForm(FlaskForm):
    fullname = StringField("Fullname",validators=[DataRequired(message="yourfullname is required")])
    pix= FileField('Display Picture', validators=[FileRequired(), FileAllowed(['jpg', 'png'], 'Image only!')])
    btn = SubmitField("update profile!")
    
    
    
    
    
     
    

