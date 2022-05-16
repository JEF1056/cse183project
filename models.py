"""
This file defines the database models
"""

import datetime
from .common import db, Field, auth, T
from pydal.validators import *
from datetime import date

# Citations: https://www.geeksforgeeks.org/python-program-to-print-current-year-month-and-day/
todays_date = date.today()


def get_user_email():
    return auth.current_user.get('email') if auth.current_user else None

def get_first_name():
    return auth.current_user.get('first_name') if auth.current_user else None

def get_last_name():
    return auth.current_user.get('last_name') if auth.current_user else None

def get_user():
    return auth.current_user.get('id') if auth.current_user else None

def get_time():
    return datetime.datetime.utcnow()


db.define_table(
    'cars',
    Field('car_brand', requires=IS_NOT_EMPTY()),
    Field('car_model', requires=IS_NOT_EMPTY()),
    Field('car_year', 'integer', default=0, requires=IS_INT_IN_RANGE(1886, todays_date.year + 1)),
    Field('car_price', 'float', default=0.00, requires=IS_FLOAT_IN_RANGE(0, 1e6)),
    Field('car_mileage', 'integer', default=0, requires=IS_INT_IN_RANGE(0, 1000000)),
    Field('car_description', 'text', requires=IS_LENGTH(maxsize=2048)),
    Field('car_picture'),
    Field('created_by', default=get_user_email),
    Field('creation_date', 'datetime', default=get_time),
)

db.define_table(
    'marked_by',
    Field('cars_id', 'reference cars'),
    Field('users'),
)

# For chat page use
db.define_table('posts',
                Field('first_name', default=get_first_name),
                Field('last_name', default=get_last_name),
                Field('user_email', default=get_user_email),
                Field('post')
                )

db.define_table('likes',
                Field('post', 'reference posts'),
                Field('like', 'boolean'),
                Field('dislike', 'boolean'),
                Field('user', 'reference auth_user', default=get_user)
)
# End use for chat page

db.cars.id.readable = db.cars.id.writable = False
db.cars.created_by.readable = db.cars.created_by.writable = False
db.cars.creation_date.readable = db.cars.creation_date.writable = False
db.marked_by.cars_id.readable = db.marked_by.cars_id.writable = False

### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later

db.commit()
