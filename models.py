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


def get_time():
    return datetime.datetime.utcnow()

# db.define_table(
#     'user',
#     Field('name'),
#     Field('user_email', default=get_user_email())
# )
db.define_table(
    'images',
    # Field('cars_id', 'reference cars'),
    Field('owner', default=get_user_email),
    Field('file_name'),
    Field('file_type'),
    Field('file_date'),
    Field('file_path'),
    Field('file_size', 'integer'),
    Field('confirmed', 'boolean', default=False),
)

db.define_table(
    'cars',
    Field('car_brand', requires=IS_NOT_EMPTY()),
    Field('car_model', requires=IS_NOT_EMPTY()),
    Field('car_year', 'integer', default=0, requires=IS_INT_IN_RANGE(1886, todays_date.year + 1)),
    Field('car_price', 'float', default=0.00, requires=IS_FLOAT_IN_RANGE(0, 1e6)),
    Field('car_mileage','integer',default=0,requires=IS_INT_IN_RANGE(0,1000000)),
    Field('car_description', 'text', requires=IS_NOT_EMPTY(), maxsize=2048),
    Field('car_picture', 'upload', 'reference images', label="Car Picture"),
    Field('created_by', default=get_user_email),
    Field('creation_date', 'datetime', default=get_time),
)

db.cars.id.readable = db.cars.id.writable = False
db.cars.created_by.readable = db.cars.created_by.writable = False
db.cars.creation_date.readable = db.cars.creation_date.writable = False


### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later

db.commit()
