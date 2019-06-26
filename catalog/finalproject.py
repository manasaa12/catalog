#!/usr/bin/env python3

from flask import (
    Flask,
    flash,
    render_template,
    request,
    url_for,
    redirect,
    jsonify
    )

import sys

from sqlalchemy import(
    Column,
    ForeignKey,
    Integer,
    String
    )

from sqlalchemy.ext.declarative import declarative_base
from flask import make_response

from sqlalchemy.orm import relationship, backref

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from sqlalchemy import create_engine


from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import os
import random
import string
import httplib2
import json
import requests


app = Flask(__name__)

Base = declarative_base()


class Admin(Base):
    __tablename__ = "admin"
    admin_id = Column(Integer, primary_key=True)
    admin_mail = Column(String(100), nullable=False)


class Television(Base):
    __tablename__ = "television"
    television_id = Column(Integer, primary_key=True)
    television_name = Column(String(100), nullable=False)
    television_admin = Column(Integer, ForeignKey('admin.admin_id'))
    television_relation = relationship(Admin)

    @property
    def serialize(self):
        return {
            'id': self.television_id,
            'name': self.television_name

        }


class Items(Base):
    __tablename__ = "items"
    item_id = Column(Integer, primary_key=True)
    item_name = Column(String(100), nullable=False)
    item_price = Column(Integer, nullable=False)
    item_brand = Column(String(100), nullable=False)
    item_image = Column(String(1000), nullable=False)
    item_image2 = Column(String(1000), nullable=False)
    item_screen_size = Column(String(100), nullable=False)
    item_display_resolution = Column(String(100), nullable=False)
    item_other_features = Column(String(100), nullable=False)
    television_id = Column(Integer, ForeignKey('television.television_id'))
    item_relation = relationship(
        Television,
        backref=backref("television", cascade="all,delete"))
    # for json

    @property
    def serialize(self):
        return {
            'id': self.item_id,
            'name': self.item_name,
            'price': self.item_price,
            'brand': self.item_brand,
            'image': self.item_image,
            'image2': self.item_image2,
            'screen_size': self.item_screen_size,
            'display_resolution': self.item_display_resolution,
            'other_features': self.item_other_features,

        }
# to connect a database engine
engine = create_engine('sqlite:///television.db')
Base.metadata.create_all(engine)
# to create a session
session = scoped_session(sessionmaker(bind=engine))

# gconnect client_id and client_data
CLIENT_DATA = json.loads(open("client_secrets.json").read())
CLIENT_ID = CLIENT_DATA["web"]['client_id']


# for login
@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # it can return the current state
    return render_template('login.html', STATE=state)


# GConnect
@app.route('/gconnect', methods=['POST', 'GET'])
def gConnect():
    if request.args.get('state') != login_session['state']:
        response.make_response(json.dumps('Invalid State paramenter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    request.get_data()
    code = request.data.decode('utf-8')

    # for obtain the authorization code then compatible with python3

    try:
        # it can update the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps("""Failed to upgrade the authorisation code"""), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Checking for access token is valid or not

    access_token = credentials.access_token
    myurl = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    # here submit the req and parse the response with python3 compatible
    header = httplib2.Http()
    result = json.loads(header.request(myurl, 'GET')[1].decode('utf-8'))

    # If access token info contains any error,it can abort

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # checking for the access token is used for correct user or not

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps(
                            """Token's user ID does not
                            match given user ID."""),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # checking for the access token is valid for this app or not

    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            """Token's client ID
            does not match app's."""),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Storing the access token in the session for later use.

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'present user is already connected.'
            ), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # here Getting user information

    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    # Add provider to login session

    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    admin_id = userID(login_session['email'])
    if not admin_id:
        admin_id = createNewUser(login_session)
    login_session['admin_id'] = admin_id
    flash("Successfull Login %s" % login_session['email'], 'success')
    return "Your account is verified Successfully"


def createNewUser(login_session):
    email = login_session['email']
    newAdmin = Admin(admin_mail=email)
    session.add(newAdmin)
    session.commit()
    admin = session.query(Admin).filter_by(admin_mail=email).first()
    admin_Id = admin.admin_id
    return admin_Id


def userID(admin_mail):
    try:
        admin = session.query(Admin).filter_by(admin_mail=admin_mail).one()
        return admin.admin_id
    except Exception as e:
        print(e)
        return None


# Gdisconnect - revoke the current user's token and reset their login session
@app.route('/gdisconnect')
def gdisconnect():
    # it can only disconnects a connected user.
    del login_session['email']
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps(
            'Current user is not connected.'
            ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    header = httplib2.Http()
    result = header.request(url, 'GET')[0]

    if result['status'] == '200':

        # Reset the user's login session.

        del login_session['access_token']
        del login_session['gplus_id']
        response = redirect(url_for('home'))
        response.headers['Content-Type'] = 'application/json'
        flash("You are successfully logout", "success")
        return response
    else:

        # the given token was invalid for whatever the reason
        response = make_response(json.dumps('Failed to revoke token for user'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/logout')
def logout():
    if 'email' in login_session:
        flash('You are logged out', "warning")
        return gdisconnect()
    flash('Your account is already signout', 'danger')
    return redirect(url_for('login'))


# JSON
@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Television).all()
    return jsonify(TV_Models=[c.serialize for c in categories])


@app.route('/category/<int:category_id>/items/JSON')
def categoryItemsJSON(category_id):
    # categories = session.query(Television).get(category_id)
    items = session.query(Items).filter_by(television_id=category_id).all()
    return jsonify(TV_model_Items=[i.serialize for i in items])


@app.route('/items/JSON')
def itemsJSON():
    items = session.query(Items).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/item/<int:id>/JSON')
def itemJSON(id):
    item = session.query(Items).get(id)
    return jsonify(Item=item.serialize)


@app.context_processor
def inject_all():
    category = session.query(Television).all()
    return dict(mycategories=category)


@app.route('/read')
def read():
    television = session.query(Items).all()
    msg = ""
    for each in television:
        msg += str(each.item_name)
    return msg


# this method shows the items which are present in the catalogue
@app.route('/')
@app.route('/home')
def home():
    items = session.query(Items).all()
    if not items:
        flash('cart was empty', 'warning')
    return render_template('display_TV_items.html', Items=items)


@app.route('/category', methods=['GET'])
def showcategory():
    if request.method == 'GET':
        category_list = session.query(Television).all()
        return render_template('display_TV_cat.html', categories=category_list)


@app.route('/all.json')
def all_json():
    rows = session.query(Items).all()
    return jsonify(Rows=[each.serialize for each in rows])


# This method is used for Add a category
@app.route('/category/new', methods=['GET', 'POST'])
def newtvcategory():
    if 'email' not in login_session:
        flash("Please login with your account", 'warning')
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('new_TV_cat.html')
    else:
        category_name = request.form['category_name']
        if category_name:
            admin = session.query(Admin).filter_by(
                admin_mail=login_session['email']
                ).one_or_none()
            if admin is None:
                flash('user is not available in the table', 'danger')
                return redirect(url_for('home'))
            admin_id = admin.admin_id
            new_television = Television(
                television_name=category_name,
                television_admin=admin_id
                )
            session.add(new_television)
            session.commit()
            flash('Your category is added successfully', 'success')
            return redirect(url_for('home'))
        else:
            flash('Your Category is not added', 'warning')
            return redirect(url_for('home'))


# This method is used for to Edit a category
@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editTVcategory(category_id):
    if 'email' not in login_session:
        flash("Please login with your account", 'warning')
        return redirect(url_for('login'))
    television = session.query(Television).filter_by(
        television_id=category_id
        ).one_or_none()
    admin = session.query(Admin).filter_by(
        admin_mail=login_session['email']
        ).one_or_none()
    if admin is None:
        flash("Incorrect user", 'danger')
        return redirect(url_for('home'))
    if television == 'None':
        flash('Category is not available', 'danger')
        return redirect(url_for('home'))
    login_admin_id = admin.admin_id
    admin_id = television.television_admin
    if login_admin_id != admin_id:
        flash('you are not allowed to edit the category', 'warning')
        return redirect(url_for('home'))

    if request.method == 'POST':
        category_name = request.form['category_name']
        television.television_name = category_name
        session.add(television)
        session.commit()
        flash('Your Category is updated', 'success')
        return redirect(url_for('home'))
    else:
        television = session.query(Television).filter_by(
            television_id=category_id
            ).one_or_none()
        return render_template(
            'edit_TV_cat.html',
            television_name=television.television_name,
            id_category=category_id, category_id=category_id)


# This method is used for to Delete a category
@app.route('/category/<int:category_id>/delete')
def deleteTVcategory(category_id):

    if 'email' not in login_session:
        flash("Please login with your account", 'warning')
        return redirect(url_for('login'))
    television = session.query(Television).filter_by(
        television_id=category_id
        ).one_or_none()
    admin = session.query(Admin).filter_by(
        admin_mail=login_session['email']
        ).one_or_none()
    if admin is None:
        flash("Incorrect user", 'danger')
        return redirect(url_for('home'))
    if television == 'None':
        flash('Category is not found', 'danger')
        return redirect(url_for('home'))
    login_admin_id = admin.admin_id
    admin_id = television.television_admin
    if login_admin_id != admin_id:
        flash('you are not allowed to delete the category', 'warning')
        return redirect(url_for('home'))
    name = television.television_name
    session.delete(television)
    session.commit()
    flash(str(name)+' is deleted ', 'success')
    return redirect(url_for('home'))


# for json
@app.route('/category/<int:category_id>/items.json')
def one_category_json(category_id):
    catsingle = session.query(Items).filter_by(television_id=category_id).all()
    return jsonify(Catsingle=[each.serialize for each in catsingle])


# used for to display an items
@app.route('/category/items')
def showTVitems():
    if request.method == 'GET':
        category_list = session.query(Items).filter_by(television_id=1).all()
    return render_template('display_TV_items.html', categories=category_list)


# This method gives the latest items present in the website
@app.route('/latestitems')
def recentitems():
    if request.method == 'GET':
        category_list = session.query(Items).all()
    return render_template('recent_items.html', categories=category_list)


# It displays the specific items in the categories
@app.route('/category/<int:category_id>/items')
def showcategoryitems(category_id):
    if request.method == 'GET':
        items = session.query(Items).filter_by(television_id=category_id).all()
    if not items:
        flash('Items are not available', 'danger')
    return render_template(
        'displayitems_incategory.html',
        Items=items, category_id=category_id)


# for item details
@app.route(
    '/category/<int:category_id>/items/<int:itemid>',
    methods=['GET', 'POST']
    )
def TVdetails(category_id, itemid):
    if request.method == 'GET':
        item = session.query(Items).filter_by(
            television_id=category_id,
            item_id=itemid
            ).one_or_none()
        return render_template(
            'TV_details.html',
            iname=item.item_name,
            iprice=item.item_price,
            ibrand=item.item_brand,
            image=item.item_image,
            image2=item.item_image2,
            isize=item.item_screen_size,
            iresolution=item.item_display_resolution,
            ifeatures=item.item_other_features
            )


# To Add an item
@app.route('/category/<int:categoryid>/items/new', methods=['GET', 'POST'])
def newTVitem(categoryid):
    if 'email' not in login_session:
        flash("will you please login with your account", 'danger')
        return redirect(url_for('login'))
    categoryname = session.query(Television).filter_by(
        television_id=categoryid
        ).one_or_none()
    admin = session.query(Admin).filter_by(
        admin_mail=login_session['email']
        ).one_or_none()
    if admin == 'None':
        flash("Incorrect user", 'warning')
        return redirect(url_for('home'))
    if not categoryname:
        flash('This category is not available in the cart', 'danger')
        return redirect(url_for('home'))

    login_admin_id = admin.admin_id
    admin_id = categoryname.television_admin

    if login_admin_id != admin_id:
        flash('you are not correct person to add the item', 'warning')
        return redirect(url_for('home'))
    if request.method == 'GET':
        return render_template(
            'add_TV_item.html',
            cat_id=categoryid, categoryName=categoryname.television_name)
    else:
        name = request.form['iname']
        image = request.form['iimage']
        image2 = request.form['image2']
        price = request.form['iprice']
        brand = request.form['ibrand']
        screen_size = request.form['isize']
        display_resolution = request.form['iresolution']
        other_features = request.form['ifeatures']

        sid = categoryid
        new_item = Items(
            item_name=name,
            item_price=price,
            item_brand=brand,
            item_image=image,
            item_image2=image2,
            item_screen_size=screen_size,
            item_display_resolution=display_resolution,
            item_other_features=other_features,
            television_id=sid
            )
        session.add(new_item)
        session.commit()
        flash(str(brand)+' is added', 'success')
        return redirect(url_for('home'))


# this method is used for to Edit an item
@app.route(
    '/category/<int:categoryid>/items/<int:itemid>/edit',
    methods=['GET', 'POST']
    )
def updateTVitem(categoryid, itemid):
    if 'email' not in login_session:
        flash("will you please login with your account", 'danger')
        return redirect(url_for('login'))
    categoryname = session.query(Television).filter_by(
        television_id=categoryid
        ).one_or_none()
    admin = session.query(Admin).filter_by(
        admin_mail=login_session['email']
        ).one_or_none()
    if admin == 'None':
        flash("Incorrect user", 'danger')
        return redirect(url_for('home'))
    if not categoryname:
        flash('This category is not available in the cart', 'danger')
        return redirect(url_for('home'))

    item = session.query(Items).filter_by(
        item_id=itemid,
        television_id=categoryid
        ).one_or_none()
    if not item:
        flash('incorrect item', 'danger')
        return redirect(url_for('home'))

    login_admin_id = admin.admin_id
    admin_id = categoryname.television_admin

    if login_admin_id != admin_id:
        flash('you are not correct person to edit the item', 'warning')
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form['iname']
        image = request.form['iimage']
        image2 = request.form['iimage2']
        price = request.form['iprice']
        brand = request.form['ibrand']
        screen_size = request.form['isize']
        display_resolution = request.form['iresolution']
        other_features = request.form['ifeatures']

        item = session.query(Items).filter_by(
            television_id=categoryid,
            item_id=itemid
            ).one_or_none()
        if item:
            item.item_name = name
            item.item_image = image
            item.item_image2 = image2
            item.item_price = price
            item.item_brand = brand
            item.item_screen_size = screen_size
            item.item_display_resolution = display_resolution
            item.item_other_features = other_features
        else:
            flash('No items here', 'danger')
            return redirect(url_for('home'))
        session.add(item)
        session.commit()
        flash(str(brand)+' is updated', 'success')
        return redirect(url_for('home'))
    else:
        edit = session.query(Items).filter_by(item_id=itemid).one_or_none()
        if edit:
            return render_template(
                'edit_TV_item.html',
                iname=edit.item_name,
                iprice=edit.item_price,
                ibrand=edit.item_brand,
                iimage=edit.item_image,
                image2=edit.item_image2,
                isize=edit.item_screen_size,
                iresolution=edit.item_display_resolution,
                ifeatures=edit.item_other_features,
                catid=categoryid,
                iid=itemid)
        else:
            return redirect(url_for('home'))


# this method is used for to delete an item
@app.route('/category/<int:categoryid>/items/<int:itemid>/delete')
def removeTVitem(categoryid, itemid):
    if 'email' not in login_session:
        flash("will you please login with your account", 'danger')
        return redirect(url_for('login'))
    categoryname = session.query(Television).filter_by(
        television_id=categoryid
        ).one_or_none()
    admin = session.query(Admin).filter_by(
        admin_mail=login_session['email']
        ).one_or_none()
    if admin == 'None':
        flash("Incorrect user", 'danger')
        return redirect(url_for('home'))
    if not categoryname:
        flash('This category is not available in the cart', 'danger')
        return redirect(url_for('home'))

    item = session.query(Items).filter_by(
        television_id=categoryid,
        item_id=itemid
        ).one_or_none()
    if not item:
        flash('Incorrect item', 'danger')
        return redirect(url_for('home'))

    login_admin_id = admin.admin_id
    admin_id = categoryname.television_admin

    if login_admin_id != admin_id:
        flash('you are not correct person to edit', 'warning')
        return redirect(url_for('home'))
    item = session.query(Items).filter_by(item_id=itemid).one_or_none()
    if item:
        brand = item.item_brand
        session.delete(item)
        session.commit()
        flash(str(brand)+' is deleted', 'success')
        return redirect(url_for('home'))
    else:
        flash('item not found', 'danger')
        return redirect(url_for('home'))


if __name__ == '__main__':
    app.secret_key = "manasa"
    app.run(debug=True, host="localhost", port=5000)
