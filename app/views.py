from app import app, models, db
import hashlib, re
from .forms import ShippingInfoForm, ProductForm
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import insert
from datetime import datetime
import json

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        # prevents original password exposure
        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()

        exist = checkAccount(username, password)

        # check if the username exists in the accounts database
        if exist==0:
            userAccount = findAccount(username)
            session['loggedin'] = True
            session['id'] = userAccount.id
            session['username'] = userAccount.username

            # redirect to homepage 
            return redirect(url_for('home'))
        elif exist == 1:
            msg = 'Incorrect password!'
        elif exist == 2:
            msg = 'Account with username does not exist!'
        
    return render_template('login.html', msg=msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # check if the data entered is valid, and return appropriate error message
        valid = checkRegistration(username, password, email)
        if valid == 1:
            msg = 'Account already registered with email address!'
        elif valid == 2:
            msg = 'Invalid email address!'
        elif valid == 3:
            msg = 'Username must be unique & contain no special chars!'
        elif valid == 0:
            # add account to database
            addAccount(username, password, email)
            msg = 'Account added: please now log in!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'

    return render_template('register.html', msg=msg)

@app.route('/home')
def home():
    if 'loggedin' in session:
        products = models.Products.query.all()
        cart = models.Carts.query.filter_by(customer_id=session['id'])
        account = models.Accounts.query.get(session['id'])

        enable = {}
        
        for item in cart:
            if item.product is not None:
                enable = {item.product_id: item.quantity < item.product.stock.quantity_left for item in cart}
            else: 
                enable = {item.product_id: False}

        return render_template('home.html', user=account, id=session['id'], username=session['username'], title="please get your shit together.", products=products, cart=cart, enable=enable)
    else:
        return redirect(url_for('login'))

# @csrf.exempt
@app.route('/like', methods=['POST'])
def like():
    data = json.loads(request.data)
    product_id = int(data.get('product_id'))
    current_product = models.Products.query.get(product_id)
    current_account = models.Accounts.query.get(session['id'])
    like = models.Likes.query.filter_by(account=current_account, product=current_product).first()

    if like:
        db.session.delete(like)
    else:
        like = models.Likes(account=current_account, product=current_product)
        db.session.add(like)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        
    return json.dumps({'status': 'OK', 'likes': len(current_product.likes), "liked": current_account.id in map(lambda x: x.author, current_product.likes) })

@app.route('/profile')
def profile():
    if 'loggedin' in session:
        accounts = models.Accounts.query.all()

        for a in accounts:
            if a.id == session['id']:
                current_account=a

        return render_template('profile.html', account=current_account, username=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'loggedin' in session:
        if session['username']=='admin':
            form=ProductForm()
            
            products = models.Products.query.all()

            return render_template('admin.html', products=products, username=session['username'], form=form)
        else:
            return redirect(url_for('login')) 
    else:
        return redirect(url_for('login'))

@app.route('/add-product', methods=['GET', 'POST'])
def addProduct():
    if 'loggedin' in session:
        form=ProductForm()

        if form.validate_on_submit():
            p_name=form.name.data
            p_price=form.price.data
            p_url=form.url.data
            p_quantity=form.quantity_left.data

            a=models.Products(product_name=p_name, price=p_price)
            p=models.Pictures(url=p_url, product=a)
            s=models.Stock(quantity_left=p_quantity, product=a)

            db.session.add(a)
            db.session.add(p)
            db.session.add(s)
            db.session.commit()

            return redirect('/admin')
        return render_template('admin.html', title='Admin View', form=form)
    else:
        return redirect(url_for('login'))


@app.route('/delete-product', methods=['GET', 'POST'])
def deleteProduct():
    id=request.form.get('name')
    product = models.Products.query.get(id)

    if product:

        # delete products from any carts it is in
        carts = models.Carts.query.filter_by(product_id=id)
        for item in carts:
            db.session.delete(item)

        db.session.delete(product)
        db.session.commit()

    return redirect('/admin')

# @csrf.exempt
@app.route('/stock', methods=['POST'])
def stock():
    data = json.loads(request.data)
    product_id = int(data.get('product_id'))
    current_product = models.Products.query.get(product_id)

    if data.get('vote_type') == "plus":
        current_product.stock.quantity_left += 1
    else:
        if current_product.stock.quantity_left>0:
            current_product.stock.quantity_left -= 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        
    return json.dumps({'status': 'OK', 'quantity_left': current_product.stock.quantity_left })


@app.route('/logout')
def logout():
    # remove the session variables related to the logged in user
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)

    return redirect(url_for('login'))

@app.route('/viewcart')
def shoppingcart():
    if 'loggedin' in session:

        cart = models.Carts.query.filter_by(customer_id=session['id'])

        return render_template('viewcart.html', username=session['username'], items=cart, title="Shopping Cart", total=totalCart())
    else:
        return redirect(url_for('login'))


def totalCart():
    cart = models.Carts.query.filter_by(customer_id=session['id'])

    total=0
    for item in cart:
        for i in range(0, item.quantity):
            total += item.product.price
            i=i+1
        
    return total

@app.route('/viewliked')
def viewliked():
    if 'loggedin' in session:
        products = models.Products.query.all()
        cart = models.Carts.query.filter_by(customer_id=session['id'])
        account = models.Accounts.query.get(session['id'])

        enable = {item.product_id: item.quantity < item.product.stock.quantity_left for item in cart}

        liked_products = (
            db.session.query(models.Products)
            .join(models.Likes, models.Products.id == models.Likes.product_id)
            .filter(models.Likes.author == session['id'])
            .all()
        )

        return render_template('likes.html', username=session['username'], title="Liked Products", liked_products=liked_products, products=products, enable=enable, user=account)
    else:
        return redirect(url_for('login'))

@app.route('/addtocart/<int:product_id>', methods=['GET', 'POST'])
def addToCart(product_id):
    p_id = product_id
    c_id = session['id']
    p = models.Products.query.get(p_id)

    customer_cart = models.Carts.query.filter_by(customer_id=c_id, product_id=p_id).first()

    # check if the customer already has entry with this product
    if not customer_cart:
        # add cart if it doesn't exist
        customer_cart = models.Carts(customer_id=c_id, product=p, quantity=1)
        db.session.add(customer_cart)
    else:
        customer_cart.quantity +=1

    db.session.commit()

    return redirect(url_for('home'))

@app.route('/deleteitem', methods=['POST'])
def deleteItem():
    id=request.form.get('name')
    p = models.Products.query.get(id)
    to_delete = models.Carts.query.filter_by(customer_id=session['id'], product=p).first()

    if to_delete:
        db.session.delete(to_delete)
        print(f"Deleting item with id={id}")
        db.session.commit()
    else: 
        print(f"Item with id={id} not found.")

    return redirect('/viewcart')

@app.route('/order', methods=['GET', 'POST'])
def order():
    if 'loggedin' in session:
        shipping_form = ShippingInfoForm()
        cart = models.Carts.query.filter_by(customer_id=session['id'])
        account = models.Accounts.query.get(session['id'])

        if shipping_form.validate_on_submit():
            first_name=shipping_form.first_name.data
            surname=shipping_form.last_name.data

            full_name=first_name + ' ' + surname

            address_line = shipping_form.address_line1.data
            city = shipping_form.city.data
            pcode = shipping_form.postcode.data

            address = address_line + '\n' + city + '\n' + pcode

            item_count=0
            for item in cart:
                item_count+=item.quantity

            current_datetime = datetime.now()
            current_date = current_datetime.date()
            
            new_order=models.Orders(name=full_name, date=current_date, shipping_address=address, item_count=item_count, amount=totalCart())

            # add new order to the account
            account.orders.append(new_order)

            for item in cart:
                new_order.products.append(item.product)

            db.session.add(new_order)

            # update stock
            for item in cart:
                product_stock = models.Stock.query.filter_by(product_id=item.product_id).first()

                product_stock.quantity_left -= item.quantity

            # remove all items from cart
            for item in cart:
                db.session.delete(item)

            db.session.commit()

            return redirect('/home')

        return render_template('order.html', items=cart, username=session['username'], total=totalCart(), form=ShippingInfoForm())
    else:
        return redirect(url_for('login'))


def checkAccount(user, passw):
    accounts = models.Accounts.query.all()
    if not accounts:
        # if there are no accounts, return 2 because account cannot exist
        return 2
    else:
        # check each entry in accounts database
        for acc in accounts:
            # check username exists
            tempU = acc.username
            if tempU == user:
                # check password matches that of username
                tempP = acc.password
                if tempP == passw:
                    # return 0 due to correct user and passw
                    return 0
                else: 
                    # usernames have to be unique: if user is found but password incorrect, we can return 1
                    return 1
    
    # if no matches found, return 2 (account with username doesnt exist)
    return 2

def findAccount(user):
    accounts = models.Accounts.query.all()
    for acc in accounts:
        if acc.username == user:
            return acc

def checkRegistration(user, passw, emai):
    # check account doesnt already exist with that email
    accounts = models.Accounts.query.all()

    for a in accounts:
        tempE = a.email
        if tempE == emai:
            # return 1 if account is already registered with email
            return 1
    
    # check if email is a valid email address
    if not re.match(r'[^@]+@[^@]+\.[^@]+', emai):
        return 2

    # check if username is unique
    for a in accounts:
        tempU = a.username
        if tempU == user:
            # return 3 if username is invalid
            return 3

    # check username is valid (only contains letters and numbers)
    if not re.match(r'[A-Za-z0-9]+', user):
        return 3

    # if nothing has been returned at this point, account is valid
    return 0

def addAccount(u, p, e):
    # Hash the password
    hash = p + app.secret_key
    hash = hashlib.sha1(hash.encode())
    p = hash.hexdigest()

    # add account to database
    new_account=models.Accounts(username=u, password=p, email=e)
    db.session.add(new_account)
    db.session.commit()

