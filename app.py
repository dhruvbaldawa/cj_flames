from flask import Flask, redirect, url_for, session, request
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
    me = facebook.get('/me')
    return _get_friends('me')


def _get_friends(user):
    """Helper function to get all the friends"""
    query = "/%s/friends" % user
    friends = facebook.get(query)
    friends_list = []
    """
    if 'next' in friends.data['paging']:
        friends = facebook.get()
        friends_list.extend(friends.data)
    """
    return json.dumps(friends)

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


if __name__ == "__main__":
    app.run()
