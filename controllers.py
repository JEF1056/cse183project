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

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_user_email
from py4web.utils.form import Form, FormStyleBulma

url_signer = URLSigner(session)

@action('index')
@action.uses(url_signer,'index.html',db, auth)
def index():
    return dict(url_signer = url_signer)

@action('back')
@action.uses(db, session, auth)
def back():
    redirect(URL('index'))

@action('second_page')  # /fixtures_example/index
@action.uses(url_signer, 'second_page.html', db, auth.user)
def second_page():
    res = []
    rows = db(db.cars.created_by).select()
    for r in rows:
        if r.car_brand not in res:
            res.append(r.car_brand)
    return dict(res=res, rows=rows, url_signer=url_signer,
                filter_url=URL('filter', signer=url_signer))


@action('add', method=["GET", "POST"])
@action.uses('add.html', db, session, auth.user, url_signer)
def add():
    # Insert form: no record= in it.
    form = Form(db.cars, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        # We simply redirect; the insertion already happened.
        redirect(URL('index'))
    # Either this is a GET request, or this is a POST but not accepted = with errors.
    return dict(form=form)


# This endpoint will be used for URLs of the form /edit/k where k is the product id.
@action('edit/<cars_id:int>', method=["GET", "POST"])
@action.uses('edit.html', db, session, auth.user, url_signer)
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
    return dict(form=form)


@action('delete/<cars_id:int>')
@action.uses(db, session, auth.user, url_signer)
def delete(cars_id=None):
    assert cars_id is not None
    db(db.cars.id == cars_id).delete()
    redirect(URL('index'))


@action('filter')
@action.uses()
def filter():
    # counter for input counts
    counter = 0
    # get params
    selected = request.params.get("s")
    if selected != "":
        counter = counter + 1
    car_model = request.params.get("car_model")
    if car_model != "":
        counter = counter + 1
    min_year = request.params.get("min_year")
    if min_year != "":
        counter = counter + 1
    max_year = request.params.get("max_year")
    if max_year != "":
        counter += 1
    min_price = request.params.get("min_price")
    if min_price != "":
        counter += 1
    max_price = request.params.get("max_price")
    if max_price != "":
        counter += 1
    min_mil = request.params.get("min_mil")
    if min_mil != "":
        counter += 1
    max_mil = request.params.get("max_mil")
    if max_mil != "":
        counter += 1

    # get all lists
    results = db(db.cars.car_brand == selected).select().as_list()
    results1 = db(db.cars.car_year >= min_year).select().as_list()
    results2 = db(db.cars.car_year <= max_year).select().as_list()
    results3 = db(db.cars.car_price >= min_price).select().as_list()
    results4 = db(db.cars.car_price <= max_price).select().as_list()
    results5 = db(db.cars.car_mileage >= min_mil).select().as_list()
    results6 = db(db.cars.car_mileage <= max_mil).select().as_list()
    final = []
    final1 = []
    final2 = []
    if car_model != "":
        results7 = db(db.cars.car_model.contains(car_model)).select().as_list()
        for h in results7:
            final.append(h)
    # print(results7)

    # list for how many times it shows
    final_count = [0] * 1000
    # all lists stored in final
    for a in results:
        final.append(a)
    for b in results1:
        final.append(b)
    for c in results2:
        final.append(c)
    for d in results3:
        final.append(d)
    for e in results4:
        final.append(e)
    for f in results5:
        final.append(f)
    for g in results6:
        final.append(g)

    # print(counter)
    # in case only one input value
    if counter == 1:
        return dict(results=final)
    # case two input value
    elif counter == 2:
        n = len(final)
        # loop to find the same list in "final"
        for x in range(0, n - 1):
            for y in range(x + 1, n):
                # found the same list
                if final[x] == final[y]:
                    # final_count[x]+=1
                    final1.append(final[x])
        # print(final1)
        return dict(results=final1)
    # case more than two input value
    else:
        n = len(final)
        # loop to find the same list in "final"
        for x in range(0, n - 1):
            for y in range(x + 1, n):
                # found the same list
                if final[x] == final[y]:
                    # mark in final_count, how many times it occurs
                    final_count[x] += 1
        # in final_count, find the counts matches the counter, append to final2
        for z in range(0, len(final_count)):
            if final_count[z] == counter - 1:
                final2.append(final[z])
        return dict(results=final2)
