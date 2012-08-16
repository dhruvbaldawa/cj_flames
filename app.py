from flask import Flask, redirect, url_for, session, request, render_template
from flaskext.oauth import OAuth
import logging
import hmac
import hashlib
import base64
import json
import os
from config import *

app = Flask(__name__)
app.secret_key = 'abcdeghji'
app.debug = True
oauth = OAuth()

facebook = oauth.remote_app('facebook',
    base_url=BASE_URL,
    request_token_url=REQUEST_TOKEN_URL,
    access_token_url=ACCESS_TOKEN_URL,
    authorize_url=AUTHORIZE_URL,
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    request_token_params={'scope': 'email, user_about_me, friends_about_me, \
                                    user_photos, friends_photos'},
)

def validate_signed_fb_request(signed_request):
    """ Returns dictionary with signed request data """
    try:
        l = signed_request.split('.', 2)
        encoded_sig = str(l[0])
        payload = str(l[1])
    except IndexError:
        raise ValueError("'signed_request' malformed")
    
    sig = base64.urlsafe_b64decode(encoded_sig + "=" * ((4 - len(encoded_sig) % 4) % 4))
    data = base64.urlsafe_b64decode(payload + "=" * ((4 - len(payload) % 4) % 4))
    
    data = json.loads(data)
    
    if data.get('algorithm').upper() != 'HMAC-SHA256':
        raise ValueError("'signed_request' is using an unknown algorithm")
    else:
        expected_sig = hmac.new(CONSUMER_SECRET, msg=payload, digestmod=hashlib.sha256).digest()
    
    if sig != expected_sig:
        raise ValueError("'signed_request' signature mismatch")
    else:
        return data


@app.route('/', methods=['GET', 'POST'])
def index():
    print request.form['signed_request']
    signed_data = validate_signed_fb_request(request.form['signed_request'])
    if signed_data.has_key('oauth_token'):
        print signed_data['oauth_token']
        session['oauth_token'] = (signed_data['oauth_token'], '')
        session['user'] = signed_data['user_id']
        return redirect(url_for('home'))
    return redirect(url_for('login'))
    
def _flame(boy, girl):
    length = len(boy) + len(girl)
    f = []
    f = list('flame')
    a = list(boy)
    b = list(girl)
    length1 = []
    length1 = list(set(a) & set(b))
    length = length - (len(length1))
    pointer = 1
    pointer1 = 0
    lesser = 0
    while len(f) != 1:
        if pointer == length:
            f.remove(f[pointer1])
            lesser += 1
        pointer = pointer + 1
        pointer1 = pointer1 + 1
        if pointer > length:
            pointer=1
        if pointer1 > 4-lesser:
            pointer1=0

    return f
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    return facebook.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True))

@app.route('/login/authorized', methods=['GET', 'POST'])
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['oauth_token'] = (resp['access_token'], '')
    print session['oauth_token']
    # me = facebook.get('/me')
    #return 'Logged in as id=%s name=%s redirect=%s' % \
        #(me.data['id'], me.data['name'], request.args.get('next'))
    return redirect(url_for('home'))

@app.route('/home', methods=['GET', 'POST'])
def home():
    # Home Page
    return render_template('index.html')

@app.route('/get_friends')
def ajax_friends():
    q = request.args.get('tag')
    # FQL Query
    query = "\
    SELECT uid, name FROM user\
    WHERE strpos(lower(name), '%s') >= 0 AND\
    uid IN (SELECT uid2 FROM friend WHERE uid1 = me())\
    LIMIT 10" % q # Substitute the %s in query with 'q'
    
    friends = facebook.get('/fql?q='+query) # Query with Facebook API
    user = _get_details('me')
    
    return_friends = [{'id': user['id'], 'name': user['name']}] # Initialize an empty list
    
    # Build the list to be returned
    for friend in friends.data['data']:
        changed_friend = {'id': friend['uid'], 'name': friend['name'], 'readonly': 'true'}
        return_friends.append(changed_friend)
    
    return json.dumps(return_friends)

@app.route('/flame')
def get_flame():
    first = request.args.get('first')
    second = request.args.get('second')
    first_name = _get_details(first)['name']
    second_name = _get_details(second)['name']
    current_user = _get_details()['name']
    """
    batch_requests(('GET', '/me', None),
                   ('GET', '/first', None),
                   ('GET', '/second', None),
    )
    """
    
    flames = _flame(first_name, second_name)[0]
    flame_dict = {
        'f': 'Friends',
        'l': 'Love',
        'a': 'Affair',
        'm': 'Married',
        'e': 'Enemy',
    }
    
    message = {
        'f': 'Friends for ever' ,
        'l': 'True Love',
        'a': 'Chup Chup ke',
        'm': 'Made for each other',
        'e': 'Teri kehke lunga',
    }

    images = {
        'f': url_for('static', filename='img/f3.gif'),
        'l': url_for('static', filename='img/l2.jpg'),
        'a': url_for('static', filename='img/a1.jpg'),
        'm': url_for('static', filename='img/m1.jpg'),
        'e': url_for('static', filename='img/e1.jpg'),
    }
    
    
    thumb = {
        'f': url_for('static', filename='img/fp.gif', _external=True),
        'l': url_for('static', filename='img/lp.jpg', _external=True),
        'a': url_for('static', filename='img/ap.jpg', _external=True),
        'm': url_for('static', filename='img/mp.jpg', _external=True),
        'e': url_for('static', filename='img/ep.jpg', _external=True),
    }

    return_dict = {
        'first_name': first_name,
        'second_name': second_name,
        'current_user': current_user,
        'result': flame_dict[flames],
        'message': message[flames],
        'image': images[flames],
        'picture': thumb[flames],
    }
    return json.dumps(return_dict)
"""
def batch_requests(*args):
    request = []
    for method, relative_url, body in args:
        per_request = {}
        if method is None:
            method = 'GET'
        per_request['method'] = method
        per_request['relative_url'] = relative_url
        if body is not None:
            per_request['body'] = body
        request.append(per_request)
    
    response = facebook.post('/', data={
                                    'access_token': get_facebook_oauth_token(),
                                    'batch': json.dumps(request),},\
                )
    import pprint
    pprint.pprint(response.data)
"""   

def _get_details(user='me'):
    me = facebook.get('/%s' % user)
    return me.data


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
