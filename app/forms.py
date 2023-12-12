from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField
from wtforms.validators import DataRequired

class ShippingInfoForm(FlaskForm):
    first_name = StringField('first_name', validators=[DataRequired()])
    last_name = StringField('last_name', validators=[DataRequired()])
    address_line1 = StringField('address_line1', validators=[DataRequired()])
    city = StringField('city', validators=[DataRequired()])
    postcode = StringField('postcode', validators=[DataRequired()])

class ProductForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    price = FloatField('price', validators=[DataRequired()])
    url = StringField('url', validators=[DataRequired()])
    quantity_left = IntegerField('quantity_left', validators=[DataRequired()])
