from flask import Flask, redirect, url_for, session, request, render_template
from flaskext.oauth import OAuth
import json
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

@app.route('/')
def index():
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


@app.route('/login')
def login():
    return facebook.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True))

@app.route('/login/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['oauth_token'] = (resp['access_token'], '')
    me = facebook.get('/me')
    return 'Logged in as id=%s name=%s redirect=%s' % \
        (me.data['id'], me.data['name'], request.args.get('next'))

@app.route('/home')
@facebook.authorized_handler
def home(resp):
    # Home Page
    return render_template('index.html')

@app.route('/get_friends')
@facebook.authorized_handler
def ajax_friends(q):
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
@facebook.authorized_handler
def get_flame(args):
    first = request.args.get('first')
    second = request.args.get('second')
    first_name = _get_details(first)['name']
    second_name = _get_details(second)['name']
    
    flames = _flame(first_name, second_name)
	message={
		'f':'Friends for ever' ,
		'l':'True Love',
		'a':'Chup Chup ke',
		'm':'Made for each other',
		'e':'Teri kehke lunga',
	}
    return_dict = {
        'first_name': first_name,
        'second_name': second_name,
        'result': flames,
        'message': 'Teri toh lag gayi baap !',
    }
    return json.dumps(return_dict)

def _get_details(user='me'):
    me = facebook.get('/%s' % user)
    return me.data


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


if __name__ == "__main__":
    app.run()
