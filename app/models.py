from app import db
from datetime import datetime

class AccountOrderAssociation(db.Model):
    __tablename__ = 'accounts_orders_association'
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)

class OrderProductAssociation(db.Model):
    __tablename__ = 'orders_products_association'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)

class ProductCartAssociation(db.Model):
    __tablename__ = 'products_cart_association'
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), primary_key=True)
    quantity = db.Column(db.Integer)

class Accounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    email = db.Column(db.String, unique=True)

    orders = db.relationship('Orders', secondary='accounts_orders_association', back_populates='accounts')
    cart = db.relationship('Carts', back_populates='account', uselist=False)
    likes = db.relationship('Likes', back_populates='account', uselist=False)

class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    date = db.Column(db.DateTime)
    amount = db.Column(db.Float)
    item_count = db.Column(db.Integer)
    products = db.Column(db.String)
    shipping_address = db.Column(db.String)

    accounts = db.relationship('Accounts', secondary='accounts_orders_association', back_populates='orders')
    products = db.relationship('Products', secondary='orders_products_association', back_populates='orders')

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String, unique=True)
    price = db.Column(db.Float)
    likes = db.Column(db.Integer)

    stock = db.relationship('Stock', back_populates='product', uselist=False)
    orders = db.relationship('Orders', secondary='orders_products_association', back_populates='products')
    cart = db.relationship('Carts', back_populates='product')
    likes = db.relationship('Likes', back_populates='product')
    picture = db.relationship('Pictures', back_populates='product', uselist=False)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity_left = db.Column(db.Integer)

    product = db.relationship('Products', back_populates='stock')

class Carts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer)

    account = db.relationship('Accounts', back_populates='cart')
    product = db.relationship('Products', back_populates='cart')

class Pictures(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    url = db.Column(db.String)

    product = db.relationship('Products', back_populates='picture')

class Likes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))

    product = db.relationship('Products', back_populates='likes')
    account = db.relationship('Accounts', back_populates='likes')