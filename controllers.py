"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""
import os
import datetime
import json
import traceback
import uuid

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_user_email
from py4web.utils.form import Form, FormStyleBulma

from nqgcs import NQGCS
from .gcs_url import gcs_url
from .settings import APP_FOLDER

url_signer = URLSigner(session)

BUCKET = '/car_pictures'

GCS_KEY_PATH = os.path.join(APP_FOLDER, 'private/gcs_keys.json')
with open(GCS_KEY_PATH) as gcs_key_f:
    GCS_KEYS = json.load(gcs_key_f)

gcs = NQGCS(json_key_path=GCS_KEY_PATH)

@action('index') # /fixtures_example/index
@action.uses('index.html', db, auth.user, url_signer)
def index():
    rows = db(db.cars.created_by).select()
    return dict(
        rows=rows,
        #  url_signer=url_signer,
        add_car_url = URL('add_car', signer=url_signer),
        # file_info_url = URL('file_info', signer=url_signer),
        # obtain_gcs_url = URL('obtain_gcs', signer=url_signer),
        # notify_url = URL('notify_upload', signer=url_signer),
        # delete_url = URL('notify_delete', signer=url_signer),
        )

@action('add_car', method=["GET", "POST"])
@action.uses('add.html', db, session, auth.user)
def add_car():
    # id = db.cars.insert(
    #     car_brand=request.json.get('car_brand'),
    #     car_model=request.json.get('car_model'),
    #     car_year=request.json.get('car_year'),
    #     car_price=request.json.get('car_price'),
    #     car_mileage=request.json.get('car_milage'),
    #     car_description=request.json.get('car_description')
    # )
    # Insert form: no record= in it.
    # form = Form(db.cars, csrf_session=session, formstyle=FormStyleBulma)
    # if form.accepted:
        # We simply redirect; the insertion already happened.
    # redirect(URL('index'))
    # Either this is a GET request, or this is a POST but not accepted = with errors.
    return dict(
        id=id,
        # file_info_url = URL('file_info', signer=url_signer),
        # obtain_gcs_url = URL('obtain_gcs', signer=url_signer),
        # notify_url = URL('notify_upload', signer=url_signer),
        # delete_url = URL('notify_delete', signer=url_signer),
        )

# This endpoint will be used for URLs of the form /edit/k where k is the product id.
@action('edit/<cars_id:int>', method=["GET", "POST"])
@action.uses('edit.html', db, session, auth.user)
def edit(cars_id=None):
    assert cars_id is not None
    # We read the product being edited from the db.
    # p = db(db.product.id == product_id).select().first()
    p = db.cars[cars_id]
    if p is None:
        # Nothing found to be edited!
        redirect(URL('index'))
    # Edit form: it has record=
    form = Form(db.cars, record=p, deletable=False, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        # The update already happened!
        redirect(URL('index'))
    return dict(form=form,
            file_info_url = URL('file_info', signer=url_signer),
            obtain_gcs_url = URL('obtain_gcs', signer=url_signer),
            notify_url = URL('notify_upload', signer=url_signer),
            delete_url = URL('notify_delete', signer=url_signer),
            )

@action('delete/<cars_id:int>')
@action.uses(db, session, auth.user)
def delete(cars_id=None):
    assert cars_id is not None
    db(db.cars.id == cars_id).delete()
    redirect(URL('index'))

@action('file_info')
@action.uses(url_signer.verify(), db)
def file_info():
    """Returns to the web app the information about the file currently
    uploaded, if any, so that the user can download it or replace it with
    another file if desired."""
    
    row = db(db.images.owner == get_user_email()).select().first()
    # The file is present if the row is not None, and if the upload was
    # confirmed.  Otherwise, the file has not been confirmed as uploaded,
    # and should be deleted.
    if row is not None and not row.confirmed:
        # We need to try to delete the old file content.
        delete_path(row.file_path)
        row.delete_record()
        row = {}
    if row is None:
        # There is no file.
        row = {}
    file_path = row.get('file_path')
    return dict(
        file_name=row.get('file_name'),
        file_type=row.get('file_type'),
        file_date=row.get('file_date'),
        file_size=row.get('file_size'),
        file_path=file_path,
        download_url=None if file_path is None else gcs_url(GCS_KEYS, file_path),
        # These two could be controlled to get other things done.
        upload_enabled=True,
        download_enabled=True,
    )

@action('obtain_gcs', method="POST")
@action.uses(url_signer.verify(), db)
def obtain_gcs():
    
    verb = request.json.get("action")
    if verb == "PUT":
        mimetype = request.json.get("mimetype", "")
        file_name = request.json.get("file_name")
        extension = os.path.splitext(file_name)[1]

        file_path = BUCKET + "/" + str(uuid.uuid1()) + extension

        mark_possible_upload(file_path)
        upload_url = gcs_url(GCS_KEYS, file_path, verb="PUT", 
                                        content_type=mimetype)

        return dict(
            signed_url=upload_url,
            file_path=file_path
        )
    elif verb in ["GET", "DELETE"]:
        file_path = request.json.get("file_path")
        if file_path is not None:
            r = db(db.images.file_path == file_path).select().first()
            if r is not None and r.owner == get_user_email():
                delete_url = gcs_url(GCS_KEYS, file_path, verb="DELETE")
                return dict(signed_url=delete_url)
        return dict(signer_url=None)

@action('notify_upload', method="POST")
@action.uses(url_signer.verify(), db)
def notify_upload():
    file_type = request.json.get("file_type")
    file_name = request.json.get("file_name")
    file_path = request.json.get("file_path")
    file_size = request.json.get("file_size")

    print("File was uploaded:", file_path, file_name, file_type)

    rows = db(db.images.owner == get_user_email()).select()
    for r in rows:
        if r.file_path != file_path:
            delete_path(r.file_path)

    d = datetime.datetime.utcnow()
    db.images.update_or_insert(
        ((db.images.owner == get_user_email()) &
         (db.images.file_path == file_path)),
        owner=get_user_email(),
        file_path=file_path,
        file_name=file_name,
        file_type=file_type,
        file_date=d,
        file_size=file_size,
        confirmed=True,
    )
    # Returns the file information.
    return dict(
        download_url=gcs_url(GCS_KEYS, file_path, verb='GET'),
        file_date=d,
    )

@action('notify_delete', method="POST")
@action.uses(url_signer.verify(), db)
def notify_delete():
    file_path = request.json.get("file_path")

    db((db.images.owner == get_user_email()) & 
        (db.images.file_path == file_path)).delete()
    
    return dict()

def delete_path(file_path):

    try: 
        bucket, id = os.path.split(file_path)
        gcs.delete(bucket[1:], id)
    except:
        pass

def delete_previous_uploads():
    """Deletes all previous uploads for a user, to be ready to upload a new file."""
    previous = db(db.images.owner == get_user_email()).select()
    for p in previous:
        # There should be only one, but let's delete them all.
        delete_path(p.file_path)
    db(db.images.owner == get_user_email()).delete()

def mark_possible_upload(file_path):
    """Marks that a file might be uploaded next."""
    delete_previous_uploads()
    db.images.insert(
        owner=get_user_email(),
        file_path=file_path,
        confirmed=False,
    )   