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
from yatl.helpers import A
from pydal.validators import *

from py4web import action, request, abort, redirect, URL
from py4web.utils.url_signer import URLSigner
from py4web.utils.form import Form, FormStyleBulma

from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash, Field
from .models import get_user_email, get_user, get_last_name, get_first_name
from pgeocode import GeoDistance

url_signer = URLSigner(session)

ID = None


@action('index')  # /fixtures_example/index
@action.uses(url_signer, 'index.html', db, auth)
def index():
    return dict(url_signer=url_signer)


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
                filter_url=URL('filter', signer=url_signer),
                load_cars=URL('load_cars', signer=url_signer),
                )


@action('add')
@action.uses('add.html', auth.user, session)
def add():
    return dict(
        add_car_url=URL('add_car', signer=url_signer),
        # load_cars_info=URL('load_cars_info', signer=url_signer),
        upload_pic_url=URL('upload_pic', signer=url_signer)
    )


@action('add_car', method="POST")
@action.uses(db, auth.user, session, url_signer.verify())
def add_car():
    # redirect(URL('upload_image.html'))
    print("here")
    id = db.cars.insert(
        car_brand=request.json.get('car_brand'),
        car_model=request.json.get('car_model'),
        car_year=request.json.get('car_year'),
        car_price=request.json.get('car_price'),
        car_mileage=request.json.get('car_mileage'),
        car_description=request.json.get('car_description'),
        car_picture=request.json.get('car_picture'),
        car_city=request.json.get('car_city'),
        car_zip=request.json.get('car_zip'),
    )
    # redirect(URL('upload_image'))
    ID = id
    return dict(
        id=id,
    )
    # load_cars_info=URL('load_cars_info', signer=url_signer),
    # upload_pic_url=URL('upload_pic', signer=url_signer))


@action('upload_image')
@action.uses('upload_image.html', auth.user, session)
def upload_image():
    return dict(
        load_cars_info=URL('load_cars_info', signer=url_signer),
        upload_pic_url=URL('upload_pic', signer=url_signer),
    )


@action('upload_pic', method="POST")
@action.uses(url_signer.verify(), db, 'second_page.html')
def upload_pic():
    cars_id = request.json.get("cars_id")
    car_picture = request.json.get("car_picture")

    db(db.cars.id == cars_id).update(car_picture=car_picture)
    return "gg"


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
        redirect(URL('`second_page`'))
    # Edit form: it has record=
    form = Form(db.cars, record=p, deletable=False, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        # The update already happened!
        redirect(URL('post_your_car'))
    return dict(form=form)


@action('delete/<cars_id:int>')
@action.uses(db, session, auth.user, url_signer)
def delete(cars_id=None):
    assert cars_id is not None
    db(db.cars.id == cars_id).delete()
    redirect(URL('post_your_car'))


@action('load_cars')
@action.uses(db, session)
def load_cars():
    rows = [{i:dict(row)[i] for i in dict(row) if i not in ["update_record", "delete_record", "marked_by"]} for row in db(db.cars).select()]
    marked_by = {}
    for row in db(db.marked_by).select():
        if row["cars_id"] in marked_by:
            marked_by[row["cars_id"]].append(row["users"])
        else:
            marked_by[row["cars_id"]] = [row["users"]]
    
    for i, row in enumerate(rows):
        marked_list=[]
        if row["id"] in marked_by:
            marked_list = marked_by[row["id"]]
        rows[i].update(dict(marked_by=marked_list))
        
    return dict(results=rows, current_user=get_user_email())


@action('load_cars_info')
@action.uses(db)
def load_cars_info():
    cars = db(db.cars.id == ID).select()
    print("cars ", cars)
    return dict(
        cars=cars
    )


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
    car_city = request.params.get("city")
    car_range = request.params.get("range")
    if car_range != "" and car_city != "":
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
    final = []
    final1 = []
    final2 = []
    all_car = db(db.cars.created_by).select()
    dist = GeoDistance('us')
    for x in all_car:
        cal_distence = dist.query_postal_code(car_city,x.car_city)
        if car_range != "":
            if cal_distence*0.621371 <= int(car_range):
                y = db(db.cars.car_city == x.car_city).select().as_list()
                for a in y:
                    final.append(a)
    # get all lists
    results = db(db.cars.car_brand == selected).select().as_list()
    results1 = db(db.cars.car_year >= min_year).select().as_list()
    results2 = db(db.cars.car_year <= max_year).select().as_list()
    results3 = db(db.cars.car_price >= min_price).select().as_list()
    results4 = db(db.cars.car_price <= max_price).select().as_list()
    results5 = db(db.cars.car_mileage >= min_mil).select().as_list()
    results6 = db(db.cars.car_mileage <= max_mil).select().as_list()

    if car_model != "":
        results7 = db(db.cars.car_model.contains(car_model)).select().as_list()
        for h in results7:
            final.append(h)
    # print(results7)

    # list for how many times it shows
    final_count = [0] * 10000
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


@action('add_bookmark/<cars_id:int>', method=["GET", "POST"])
@action.uses('add_bookmark.html', db, session, auth.user, url_signer)
def add_bookmark(cars_id=None):
    assert cars_id is not None
    p = list(car for car in db(db.marked_by.users == get_user_email()).select() if car["cars_id"] == cars_id)
    if not p:
        db.marked_by.insert(
            cars_id=cars_id,
            users=get_user_email()
        )
    redirect(URL('my_bookmarks'))

@action('remove_bookmark/<cars_id:int>', method=["GET", "POST"])
@action.uses('add_bookmark.html', db, session, auth.user, url_signer)
def add_bookmark(cars_id=None):
    assert cars_id is not None
    p = list(car["id"] for car in db(db.marked_by.users == get_user_email()).select() if car["cars_id"] == cars_id)
    print(p)
    for i in range(len(p)):
        db(db.marked_by.id == p[i]).delete()
    redirect(URL('my_bookmarks'))


@action('my_bookmarks/', method=["GET", "POST"])
@action.uses('my_bookmarks.html', db, session, auth.user, url_signer)
def my_bookmarks():
    return {"load_bookmarks": URL("load_bookmarks")}

@action('load_bookmarks')
@action.uses(db, session)
def load_bookmarks():
    final22 = []
    rows = db(db.cars.created_by).select().as_list()
    for row in rows:
        s = db(db.marked_by.cars_id == row['id']).select()
        for r in s:
            if r['users'] == get_user_email():
                final22.append(row)
    return dict(results=final22)

# TODO Just a blank page
@action('car_description_page')
@action.uses(url_signer, 'car_description_page.html', db, auth.user)
def car_description_page():
    return dict(url_signer=url_signer)


# TODO Still in progress
@action('post_your_car')
@action.uses(url_signer, 'post_your_car.html', db, auth.user)
def post_your_car():
    res = []
    rows = db(db.cars.created_by).select()
    for r in rows:
        if r.car_brand not in res:
            res.append(r.car_brand)

    first_name = get_first_name()
    last_name = get_last_name()

    return dict(res=res, rows=rows, first_name=first_name, last_name=last_name, url_signer=url_signer, )


# TODO not finished yet
# ---------------------------------  For feedback page use: ---------------------------------
@action('feedback')
@action.uses('feedback.html', db, auth, auth.user, url_signer)
def chat_page():
    return dict(
        user_email=get_user_email(),
        load_posts_url=URL('load_posts', signer=url_signer),
        add_post_url=URL('add_post', signer=url_signer),
        delete_post_url=URL('delete_post', signer=url_signer),
        get_likes_url=URL('get_likes', signer=url_signer),
        set_like_url=URL('set_like', signer=url_signer),
        get_likers_url=URL('get_likers', signer=url_signer),
    )


# load posts
@action('load_posts')
@action.uses(url_signer.verify(), db)
def load_posts():
    rows = db(db.posts).select().as_list()
    return dict(rows=rows)


# add posts
@action('add_post', method="POST")
@action.uses(url_signer.verify(), db, auth.user)
def add_post():
    id = db.posts.insert(
        post=request.json.get('post'),
    )
    # get the name of the author
    r = db(db.auth_user.email == get_user_email()).select().first()
    first_name = r.first_name
    last_name = r.last_name
    user_email = get_user_email()
    return dict(id=id, first_name=first_name, last_name=last_name, user_email=user_email)


@action('delete_post')
@action.uses(url_signer.verify(), db)
def delete_post():
    id = request.params.get('id')
    assert id is not None
    db(db.posts.id == id).delete()
    return "ok"


@action('get_likes')
@action.uses(url_signer.verify(), db, auth.user)
def get_likes():
    post_id = request.params.get('post_id')
    row = db((db.likes.post == post_id) &
             (db.likes.user == get_user())).select().first()
    like = row.like if row is not None else 0
    dislike = row.dislike if row is not None else 0
    return dict(like=like, dislike=dislike)


@action('set_like', method='POST')
@action.uses(url_signer.verify(), db, auth.user)
def set_like():
    post_id = request.json.get('post_id')
    like = request.json.get('like')
    dislike = request.json.get('dislike')
    assert post_id is not None and like is not None
    db.likes.update_or_insert(
        ((db.likes.post == post_id) & (db.likes.user == get_user())),
        post=post_id,
        user=get_user(),
        like=like,
        dislike=dislike
    )
    return "ok"


@action('get_likers')
@action.uses(url_signer.verify(), db)
def get_likers():
    post_id = request.params.get('post_id')
    like_list = ""
    likes = db((db.likes.post == post_id) & (db.likes.like == True)).select()
    for row in likes:
        like_list += row.user.first_name + " " + row.user.last_name
        if (row == likes[-1]):
            break
        else:
            like_list += ", "

    dislike_list = ""
    dislikes = db((db.likes.post == post_id) & (db.likes.dislike == True)).select()
    for row in dislikes:
        dislike_list += row.user.first_name + " " + row.user.last_name
        if (row == dislikes[-1]):
            break
        else:
            dislike_list += ", "

    final_sentence = ""
    if like_list != "":
        final_sentence += "Liked by " + like_list
    if dislike_list != "":
        if like_list != "":
            final_sentence += ", Disliked by " + dislike_list
        else:
            final_sentence += "Disliked by " + dislike_list
    return dict(final_sentence=final_sentence)
# --------------------------------- End feedback page ---------------------------------
