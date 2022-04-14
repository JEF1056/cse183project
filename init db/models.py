"""
This file defines the database models
"""

import datetime
from .common import db, Field, auth, T
from pydal.validators import *


def get_user_email():
    return auth.current_user.get('email') if auth.current_user else None

def get_time():
    return datetime.datetime.utcnow()

db.define_table(
    'product',
    Field('product_name', requires=IS_NOT_EMPTY()),
    Field('product_quantity', 'integer', default=0, requires=IS_INT_IN_RANGE(0, 1e6)),
    Field('product_price', 'float', default=0., requires=IS_FLOAT_IN_RANGE(0, 1e6)),
    Field('mail_order', 'boolean', default=True),
    Field('created_by', default=get_user_email),
    Field('creation_date', 'datetime', default=get_time),
)

db.product.id.readable = db.product.id.writable = False
db.product.created_by.readable = db.product.created_by.writable = False
db.product.creation_date.readable = db.product.creation_date.writable = False

db.product.product_quantity.label = T('Quantity')
db.product.product_price.label = T('Price')

### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later

db.commit()
