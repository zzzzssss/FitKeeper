import flask
from flask import Flask, render_template, request, g, redirect, url_for, session, flash, jsonify
from flask_oauth import OAuth
import sqlite3 as sql
from functools import wraps
import json, datetime, os, sys, boto3
from werkzeug.utils import secure_filename
import pymysql
from datetime import datetime as dt
sys.path.append('calendar/')
sys.path.append('databases/')
sys.path.append('ml/')
sys.path.append('ses/')
from mycalendar import *
from db_funcs import *
from db_funcs_machines import *
from dynamodb import *
from recommendation import *
from ses import *
from DynamoInv import *
from boto.s3.connection import S3Connection
from boto.s3.key import Key as S3Key
from werkzeug.datastructures import FileStorage
from boto3.s3.transfer import S3Transfer 
#import transloc

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


UPLOAD_FOLDER = 'static/img/'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
GOOGLE_CLIENT_ID = '852263075688-3u85br5hvvk6ajvrafavv3lpupns3va7.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = 'l7a5ztJX5bW9iZBTq81GP-pg'
REDIRECT_URI = '/oauth2callback'
SECRET_KEY = '8(2:W\x909\x01\xb3F\xd0\x11\x85\xc56\xd1h\xf5\x1bu\r[\xab\x9f'

# AWS S3
S3_BUCKET_NAME="cloudcloud"
s3_key_filename = os.path.join(os.path.dirname(__file__)+'s3/', 's3-keys.txt')
with open(s3_key_filename) as s3_key_file:
    lines = s3_key_file.readlines()

    S3_ACCESS_KEY = lines[0].rstrip('\n').split('=')[1].rstrip()
    S3_SECRET_KEY = lines[1].rstrip('\n').split('=')[1].rstrip()

s3_client = boto3.client(
    's3',
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = SECRET_KEY

oauth = OAuth()
google = oauth.remote_app(
	'google',
	base_url='https://www.google.com/accounts/',
	authorize_url='https://accounts.google.com/o/oauth2/auth',
	request_token_url=None,
	request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/calendar',
		                'response_type': 'code'},
	access_token_url='https://accounts.google.com/o/oauth2/token',
	access_token_method='POST',
	access_token_params={'grant_type': 'authorization_code'},
	consumer_key=GOOGLE_CLIENT_ID,
	consumer_secret=GOOGLE_CLIENT_SECRET
)

# login required decorator
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            #flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap


# complete profile info required decorator
def comp_profile_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'comp_info' in session:
            print "Profile completion check passed."
            return f(*args, **kwargs)
        else:
            return redirect(url_for('comp_info'))
    return wrap


@app.route('/google',methods=['GET', 'POST'])
def g_index():
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('google_login'))

    access_token = access_token[0]  # secret = access_token[1]
    from urllib2 import Request, urlopen, URLError
    headers = {'Authorization': 'OAuth '+access_token}
    req = Request('https://www.googleapis.com/oauth2/v1/userinfo',
                  None, headers)
    # req_cal = Request('https://www.googleapis.com/calendar/v3/calendars/primary/events',
    #                   None, headers)

    try:
        res = urlopen(req)
        # res_cal = urlopen(req_cal)
        # print (res)
        # print 'res_cal: ',res_cal
    except URLError, e:
        if e.code == 401:
            # Unauthorized - bad token
            session.pop('access_token', None)
            return redirect(url_for('google_login'))
        return res.read()

    # Successful login. Extract user information
    session['logged_in'] = True
    profile = json.loads(res.read())
    print json.dumps(profile, indent=4, sort_keys=True)
    # google_calendar = json.loads(res_cal.read())
    session['profile'] = profile
    session['user_id'] = profile['id']
    session['user_email'] = profile['email']
    ses_verification(conn_ses(), profile['email'])
   
    db = get_db()   # Get Profile Database
    user_init(db, profile)   # Initialize User Profile

    # Determine if user's profile is complete
    if is_profile_complete(db, session['user_id']) is False:
        return render_template('information_submit.html')
    else:
        session['comp_info'] = True

    # query_res = read_profile(db, (profile['id'],))
    #print query_res[0]
    # FAKE DATA
    # fake_data={'family_name': 'fcsues', 'str_ctr': 40.8172, 'signup_date': datetime.date(2017, 7, 9), 'uid': '108153423178355183645', 'rating': 0, 'dob': datetime.date(2017, 4, 24), 'photo': 'https://wallpaperbrowse.com/media/images/pictures-2.jpg', 'squ_ctr': 5.0, 'bas_ctr': 0.0, 'swi_ctr': 4.5, 'rating_ctr': 0, 'addr': (3.5, 1.0), 'given_name': 'mere', 'avg_rating': 2.5, 'gender': 'male', 'lat': 3.5, 'car_ctr': -73.9417, 'lng': 1.0, 'age': 32, 'email': 'meref@gmail.com', 'name': 'mere fcsues'}
    # fake_data1={'family_name': 'brown', 'str_ctr': 40.8172, 'signup_date': datetime.date(2017, 7, 9), 'uid': '10815342317835518', 'rating': 0, 'dob': datetime.date(2017, 5, 24), 'photo': 'https://wallpaperbrowse.com/media/images/IV1fgh7G.jpg', 'squ_ctr': 5.0, 'bas_ctr': 0.0, 'swi_ctr': 4.5, 'rating_ctr': 0, 'addr': (3.5, 1.0), 'given_name': 'Robert', 'avg_rating': 2.7, 'gender': 'male', 'lat': 3.5, 'car_ctr': -73.9417, 'lng': 1.0, 'age': 22, 'email': 'robert@gmail.com', 'name': 'Robert Brown'}
    # fake_data2={'family_name': 'Robert', 'str_ctr': 40.8172, 'signup_date': datetime.date(2017, 7, 9), 'uid': '1081534231783551855555', 'rating': 0, 'dob': datetime.date(2017, 5, 27), 'photo': 'https://wallpaperbrowse.com/media/images/pexels-photo-115045.jpeg', 'squ_ctr': 5.0, 'bas_ctr': 0.0, 'swi_ctr': 4.5, 'rating_ctr': 0, 'addr': (3.5, 1.0), 'given_name': 'brown', 'avg_rating': 3, 'gender': 'male', 'lat': 3.5, 'car_ctr': -73.9417, 'lng': 1.0, 'age': 18, 'email': 'ccbrown@gmail.com', 'name': 'Robert cc Brown'}
    filtering_result = find_friends(db, session['user_id'])
    # print filtering_result
    stride_timeslots=[]
    eliptical_timeslots=[]
    strength_timeslots=[]
    db_2 = connect_db_2()


    interest = 'filter_by_cor'   # Sort by correlation by default
    if request.method == "POST":
        data = {}    
        if "timeselect" in request.form:
            try:
                start=request.form['starttime']
                print start
                end=request.form['endtime']
                print end
            except:
                return render_template('index.html', profile_htmls=filtering_result[interest], stride_timeslots=stride_timeslots,
                eliptical_timeslots=eliptical_timeslots, strength_timeslots=strength_timeslots
                )
            temp_1=find_STRIDE(db_2,start,end)
            for record in temp_1:
                data_one={}
                data_one['start_time']=record[1]
                data_one['end_time']=record[2]
                data_one['machine_number']=record[3]
                data_one['mid']=record[0]

                stride_timeslots.append(data_one)

            temp_2=find_ELIPTICAL(db_2,start,end)
            for record in temp_2:
                data_one={}
                data_one['start_time']=record[1]
                data_one['end_time']=record[2]
                data_one['machine_number']=record[3]
                data_one['mid']=record[0]

                eliptical_timeslots.append(data_one)
            
            temp_3=find_STRENGTH(db_2,start,end)
            for record in temp_3:
                data_one={}
                data_one['start_time']=record[1]
                data_one['end_time']=record[2]
                data_one['machine_number']=record[3]
                data_one['mid']=record[0]

                strength_timeslots.append(data_one)
            
            
            return render_template('index.html', profile_htmls=filtering_result[interest], stride_timeslots=stride_timeslots,
                eliptical_timeslots=eliptical_timeslots, strength_timeslots=strength_timeslots
                )

        elif "reserve_stride" in request.form:
            print request.form 
            data_1=[]
            reserved_time=request.form.keys()
            reserved_time.remove('reserve_stride')
            for ele in reserved_time:
                temp=ele.split('/')
                data_1.append(temp)
            for ttt in data_1:

                insert_machineRESERVE(db_2, session['user_id'], ttt[1], ttt[2], "stride", ttt[0])
                update_strideAVALABLE(db_2,ttt[1], ttt[2],ttt[0])

            return render_template('index.html', profile_htmls=filtering_result[interest], stride_timeslots=stride_timeslots, 
                eliptical_timeslots=eliptical_timeslots, strength_timeslots=strength_timeslots
                )

        elif "reserve_eliptical" in request.form:
            print request.form 
            data_1=[]
            reserved_time=request.form.keys()
            reserved_time.remove('reserve_eliptical')
            for ele in reserved_time:
                temp=ele.split('/')
                data_1.append(temp)
            for ttt in data_1:
                insert_machineRESERVE(db_2, session['user_id'], ttt[1], ttt[2], "eliptical", ttt[0])
                update_elipticalAVALABLE(db_2,ttt[1], ttt[2],ttt[0])

            return render_template('index.html', profile_htmls=filtering_result[interest], stride_timeslots=stride_timeslots, 
                eliptical_timeslots=eliptical_timeslots, strength_timeslots=strength_timeslots
                )
        elif "reserve_strength" in request.form:
            print request.form 
            data_1=[]
            reserved_time=request.form.keys()
            reserved_time.remove('reserve_strength')
            for ele in reserved_time:
                temp=ele.split('/')
                data_1.append(temp)
            for ttt in data_1:
                insert_machineRESERVE(db_2, session['user_id'], ttt[1], ttt[2], "strength", ttt[0])
                update_strengthAVALABLE(db_2,ttt[1], ttt[2],ttt[0])

            return render_template('index.html', profile_htmls=filtering_result[interest], stride_timeslots=stride_timeslots, 
                eliptical_timeslots=eliptical_timeslots, strength_timeslots=strength_timeslots
                )

        else:
            if (request.form):
                interest = request.form['interests']

            # return render_template('index.html', profile_htmls=filtering_result[interest], stride_timeslots=stride_timeslots, 
            #     eliptical_timeslots=eliptical_timeslots, strength_timeslots=strength_timeslots
            #     )
                

            if (request.json):
                data['email'] = request.json['email']   # Invitee's email addr
                data['uid'] = request.json['uid']   # Invitee's uid
                sender_profile = read_profile(db, [session['user_id']])[0]
                receiver_profile = read_profile(db, [data['uid']])[0]
                print "ready to send email"
                send_request(conn_ses(), session['user_email'], data['email'], session['user_id'],
                             receiver_profile['uid'], sender_profile['name'],
                             receiver_profile['given_name'])
                put_inv_record(session['user_id'], data['uid'])   # Write invitation record to INV DB
                print data
                return jsonify(data)

    return render_template('index.html', profile_htmls=filtering_result[interest], stride_timeslots=stride_timeslots, 
                eliptical_timeslots=eliptical_timeslots, strength_timeslots=strength_timeslots
                )


######## Google Authorization Functions #############
@app.route('/google_login')
def google_login():
    callback=url_for('authorized', _external=True)
    return google.authorize(callback=callback)

@app.route(REDIRECT_URI)
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    session['access_token'] = access_token, ''
    return redirect(url_for('g_index'))

@google.tokengetter
def get_access_token():
    return session.get('access_token')
#####################################################


@app.route('/welcome')
def welcome():
    return render_template('welcome.html') 


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    user_password = False

    if request.method == 'POST':

        # db = get_db()
        # cur=db.cursor()
        # cur.execute("select * from Users")
        # rows= cur.fetchall();
        #
        # for row in rows:
        #     if request.form['username'] == row[2] and request.form['password'] == row[3]:
        #        user_password = True

        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            user_password = True

        if user_password:
            session['logged_in'] = True
            #flash('You were logged in.')
            return redirect(url_for('index'))

        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)


@app.route('/edit')
@login_required
@comp_profile_required
def edit():
    db = get_db()
    profile = read_profile(db, [session['user_id']])[0]
    print profile
    return render_template('edit_information.html', profile=profile) 



@app.route('/thankyou', methods=['POST'])
@login_required
def thankyou():
    """
    Receive info from page "information_submit.html",
    Update user's profile.
    'POST' method.
    """

    db = get_db()
    invitor_uid = '***'
    invitee_uid = '***'
    accept_idc = False   # Accept indicator

    # Parse request.form(an 'ImmutableMultiDict' Object)
    for key in request.form.keys():
        temp = key.split('/')
        if temp[0] == 'accept':
            accept_idc = True
        if temp[0] == 'invitor':
            invitor_uid = temp[1]
        if temp[0] == 'acceptor':
            invitee_uid = temp[1]

    print 'invitor_uid:', invitor_uid
    print 'invitee_uid:', invitee_uid

    profile = []
    # profile = read_profile(db, [session['user_id']])[0]

    

    if request.method=="POST":
        
        print "[THANKYOU] request.method == 'POST'"
        if accept_idc:
            print "Invitation accepted."
            # Invitation accepted
            rate_table = conn_rate_table()
            # update inv table 
            change_request_status(invitor_uid, invitee_uid, 1)
            write_rate_record(rate_table, invitor_uid, invitee_uid)
        else:
            print "Invitation declined."
            # update inv table
            change_request_status(invitor_uid, invitee_uid, -1)
            pass

        print request.form
	profile = read_profile(db, [invitee_uid])[0]
        return render_template('thankyou.html', profile=profile)

    #query_res = read_profile(db, (session['user_id'],))

    return render_template('thankyou.html',profile=profile)


# @app.route('/accept_invitation2', methods=['POST', "GET"])
# def accept_invitation2():
#     fake_data={'family_name': 'fcsues', 'str_ctr': 40.8172, 'signup_date': datetime.date(2017, 7, 9), 'uid': '108153423178355183645', 'rating': 0, 'dob': datetime.date(2017, 4, 24), 'photo': 'https://wallpaperbrowse.com/media/images/pictures-2.jpg', 'squ_ctr': 5.0, 'bas_ctr': 0.0, 'swi_ctr': 4.5, 'rating_ctr': 0, 'addr': (3.5, 1.0), 'given_name': 'mere', 'avg_rating': 2.5, 'gender': 'male', 'lat': 3.5, 'car_ctr': -73.9417, 'lng': 1.0, 'age': 32, 'email': 'meref@gmail.com', 'name': 'mere fcsues'}
#     fake_data1={'family_name': 'brown', 'str_ctr': 40.8172, 'signup_date': datetime.date(2017, 7, 9), 'uid': '10815342317835518', 'rating': 0, 'dob': datetime.date(2017, 5, 24), 'photo': 'https://wallpaperbrowse.com/media/images/IV1fgh7G.jpg', 'squ_ctr': 5.0, 'bas_ctr': 0.0, 'swi_ctr': 4.5, 'rating_ctr': 0, 'addr': (3.5, 1.0), 'given_name': 'Robert', 'avg_rating': 2.7, 'gender': 'male', 'lat': 3.5, 'car_ctr': -73.9417, 'lng': 1.0, 'age': 22, 'email': 'robert@gmail.com', 'name': 'Robert Brown'}
#     #fake_data2={'family_name': 'Robert', 'str_ctr': 40.8172, 'signup_date': datetime.date(2017, 7, 9), 'uid': '1081534231783551855555', 'rating': 0, 'dob': datetime.date(2017, 5, 27), 'photo': 'https://wallpaperbrowse.com/media/images/pexels-photo-115045.jpeg', 'squ_ctr': 5.0, 'bas_ctr': 0.0, 'swi_ctr': 4.5, 'rating_ctr': 0, 'addr': (3.5, 1.0), 'given_name': 'brown', 'avg_rating': 3, 'gender': 'male', 'lat': 3.5, 'car_ctr': -73.9417, 'lng': 1.0, 'age': 18, 'email': 'ccbrown@gmail.com', 'name': 'Robert cc Brown'}
#     data_f=[]
#     data_f.append(fake_data)

    
#     invitor=fake_data 
#     acceptor=fake_data1
    
#     return render_template('accept/accept_invitation.html', profiles=data_f, invitor=invitor, acceptor=acceptor) 


@app.route('/emailinv/<string:invitor_uid>/<string:invitee_uid>')
def accept_invitation(invitor_uid, invitee_uid):
    """
    URL for accepting invitation.
    Parse invitor_uid & invitee_uid from URL.
    Append invitation records(A->B & B->A) to DynamoDB.
    """
    db = get_db()
    invitor_profile = read_profile(db, [invitor_uid])[0]
    invitee_profile = read_profile(db, [invitee_uid])[0]

    return render_template('accept/accept_invitation.html', profiles=[invitor_profile],
                           invitor=invitor_profile, acceptor=invitee_profile)


@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    session.pop('logged_in', None)
    session.pop('profile', None)
    session.pop('calendar', None)
    session.pop('comp_info', None)
    session.pop('user_email', None)
    flash('You were logged out.')
    return redirect(url_for('welcome'))


def get_db():
    """
    Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'mysql_db'):
        g.mysql_db = connect_db()
    return g.mysql_db


@app.teardown_appcontext
def close_connection(exception):
    """
    Closes the database again at the end of the request.
    """
    if hasattr(g, 'mysql_db'):
        g.mysql_db.close()


@app.route('/', methods=['GET', 'POST'])
#@login_required
#@comp_profile_required
def index():
    return redirect(url_for('login'))

    #return render_template('index.html')


@app.route('/friends', methods=['GET', 'POST'])
@login_required
@comp_profile_required
def friends():
    """
    Recommend workout partners to user using K-means.
    Then, sort recommendation result based on
    all "filtering" attributes.
    """
    user_id = session['user_id']   # Current user's id
    db = get_db()
    rate_table = conn_rate_table()

    star_mark = None
    if request.method == "POST":
        try:
            uidstring = request.form.keys()[0]
            ratee_uid = uidstring.split("/")[0]
            star_mark = request.form[uidstring]
            rate = float(star_mark)
            # Update Profile DB
            update_records(db, ratee_uid, rating_ctr=1, rating=rate)
            # Update Rating DB
            remove_rate_record(rate_table, user_id, ratee_uid)
            print rate
        except:
            print "User did not rate before pressing 'Submit' button."

    records = query_rate_record(rate_table, user_id)
    partner_uids = []
    profiles = []
    for record in records:
        partner_uid = record['partner']
        timestamp = record['timestamp']
        profile = read_profile(db, [partner_uid])[0]
        profile['acc_timestamp'] = timestamp
        profiles.append(profile)

    # fake_data={'family_name': 'fcsues', 'str_ctr': 40.8172, 'signup_date': datetime.date(2017, 7, 9), 'uid': '108153423178355183645', 'rating': 0, 'dob': datetime.date(2017, 4, 24), 'photo': 'https://wallpaperbrowse.com/media/images/pictures-2.jpg', 'squ_ctr': 5.0, 'bas_ctr': 0.0, 'swi_ctr': 4.5, 'rating_ctr': 0, 'addr': (3.5, 1.0), 'given_name': 'mere', 'avg_rating': 2.5, 'gender': 'male', 'lat': 3.5, 'car_ctr': -73.9417, 'lng': 1.0, 'age': 32, 'email': 'meref@gmail.com', 'name': 'mere fcsues'}
    # fake_data1={'family_name': 'brown', 'str_ctr': 40.8172, 'signup_date': datetime.date(2017, 7, 9), 'uid': '10815342317835518', 'rating': 0, 'dob': datetime.date(2017, 5, 24), 'photo': 'https://wallpaperbrowse.com/media/images/IV1fgh7G.jpg', 'squ_ctr': 5.0, 'bas_ctr': 0.0, 'swi_ctr': 4.5, 'rating_ctr': 0, 'addr': (3.5, 1.0), 'given_name': 'Robert', 'avg_rating': 2.7, 'gender': 'male', 'lat': 3.5, 'car_ctr': -73.9417, 'lng': 1.0, 'age': 22, 'email': 'robert@gmail.com', 'name': 'Robert Brown'}
    # fake_data2={'family_name': 'Robert', 'str_ctr': 40.8172, 'signup_date': datetime.date(2017, 7, 9), 'uid': '1081534231783551855555', 'rating': 0, 'dob': datetime.date(2017, 5, 27), 'photo': 'https://wallpaperbrowse.com/media/images/pexels-photo-115045.jpeg', 'squ_ctr': 5.0, 'bas_ctr': 0.0, 'swi_ctr': 4.5, 'rating_ctr': 0, 'addr': (3.5, 1.0), 'given_name': 'brown', 'avg_rating': 3, 'gender': 'male', 'lat': 3.5, 'car_ctr': -73.9417, 'lng': 1.0, 'age': 18, 'email': 'ccbrown@gmail.com', 'name': 'Robert cc Brown'}
    # data_f=[]
    # data_f.append(fake_data)
    # data_f.append(fake_data1)
    # data_f.append(fake_data2)

    return render_template('friends/friends_index.html', profiles=profiles)



@app.route('/reservation', methods=['GET', 'POST'])
@login_required
@comp_profile_required
def reservation():
    uid = session['user_id']
    db = get_db()
    db_2 = connect_db_2()
    if request.method == 'POST':
        if "editinfo" in request.form:
            fn = request.form['yourfirstname'].title()
            ln = request.form['yourlastname'].title()
            address = request.form['youraddress']
            print address
            latlng = address.strip('()').split()
            lat, lng = latlng[0], latlng[1]
            gender = request.form['gender']
            birthdate = request.form['yourdate']
            db = get_db()
            update_profile_rsv(db, uid, fn, ln,
                               gender, lat, lng, birthdate)
            return redirect(url_for('reservation'))

        if "form1" in request.form:
            print "get self rating updated scores"
            bas = float(request.form["basketballrating"])
            swi = float(request.form["swimmingrating"])
            stre = float(request.form["strengthrating"])
            car = float(request.form["cardiorating"])
            squ = float(request.form["squashrating"])
            update_scores(db, uid, bas, stre, car, swi, squ)
            return redirect(url_for('reservation'))

        if "deletereservation" in request.form:
            # print request.form
            data_1=[]
            reserved_time=request.form.keys()
            reserved_time.remove('deletereservation')
            for ele in reserved_time:
                temp=ele.split('/')
                data_1.append(temp)
            print data_1
            delete_machineRESERVE(db_2, uid, data_1[0][1], data_1[0][2], data_1[0][0])
            if 'stride' in data_1[0]:
                cancel_strideAVALABLE(db_2,data_1[0][1], data_1[0][2],data_1[0][0])
            if 'eliptical' in data_1[0]:
                cancel_elipticalAVALABLE(db_2,data_1[0][1], data_1[0][2],data_1[0][0])
            if 'strength' in data_1[0]:
                cancel_strengthAVALABLE(db_2,data_1[0][1], data_1[0][2],data_1[0][0])

        # check if the post request has the file part
        elif 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        else:
            file = request.files['file']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            elif file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                path = os.path.join(app.config['UPLOAD_FOLDER'])
                print path
                f = path + filename
                data = open(f, 'rb')

                # s3_client = boto3.client(
                #     's3',
                #     aws_access_key_id=ACCESS_KEY,
                #     aws_secret_access_key=SECRET_KEY,

                # )
                #s3 = boto3.resource('s3')
                #s3.create_bucket(Bucket='cloudcloud')
                #s3.Object(BUCKET_NAME, filename).put(Body=open(f, 'rb'), ACL='public-read')

                transfer = S3Transfer(s3_client)
                transfer.upload_file(f, S3_BUCKET_NAME, filename)
                response = s3_client.put_object_acl(ACL='public-read',
                                        Bucket=S3_BUCKET_NAME, Key=filename)
                newfilename = "https://s3.amazonaws.com/cloudcloud/"+filename
                update_photo(db, uid, newfilename)   # Update photo URL
                return redirect(url_for('reservation',filename=newfilename))

    # 'GET' method. 
    query_res = read_profile(db, (uid,))

    print query_res[0]

    # All invitataions sent by current user
    inv_rows = []
    inv_records = retrieve_inv_record(uid)
    for record in inv_records:
        d = {}
        invitee_uid = record['friend_id']
        invitee_profile = read_profile(db, [invitee_uid])[0]
        invitee_fn, invitee_ln = invitee_profile['given_name'], invitee_profile['family_name']
        inv_time = record['formatted_t']
        if record['agreed'] == '1':
            inv_status = 'Agreed'
        elif record['agreed'] == '0':
            inv_status = 'Pending'
        else:
            inv_status = 'Declined'
        d['first_name'] = invitee_fn
        d['last_name'] = invitee_ln
        d['sent_time'] = inv_time
        d['inv_status'] = inv_status
        inv_rows.append(d)

    
    reservation_records = find_machineRESERVE(db_2, uid)

    return render_template('reservations/reservation_index.html', profile=query_res[0], rows=reservation_records, 
                           inv_rows=inv_rows)



@app.route('/buslist', methods=['GET', 'POST'])
@login_required
@comp_profile_required
def buslist2():
    bus_line = None
    time1 = None
    time2 = None
    if request.method == 'POST':
        try:
            bus_line = request.form['bus_line']
            time1 = request.form['time1']
            time2 = request.form['time2']
        except:
            return render_template("buslist/index.html", rows=[])

    db = get_db()
    result = find_bus(db, bus_line, time1, time2)
    return render_template("buslist/index.html", rows=result)


@app.route('/comp_info')
@login_required
def comp_info():
    """
    information_submit.html: 
        page of supplementing user's profile.
    """
    ses_verification(conn_ses(), session['user_email'])  # Send verification email
    return render_template('information_submit.html')


@app.route('/post', methods=['POST'])
@login_required
def supplement_profile():
    """
    Receive info from page "information_submit.html",
    Update user's profile.
    'POST' method.
    """

    fn = request.form['yourfirstname'].title()   # title(): Uppercase the first letter
    ln = request.form['yourlastname'].title()
    address = request.form['youraddress']
    gender = request.form['gender']
    birthdate = request.form['yourdate']
    # Self-ratings
    bas_ctr = request.form['yourbasketball']
    str_ctr = request.form['yourstrength']
    car_ctr = request.form['yourcardio']
    swi_ctr = request.form['yourswimming']
    squ_ctr = request.form['yoursquash']
    # Extract lat & lng from 'address'
    latlng = address.strip('()').split()
    lat, lng = latlng[0], latlng[1]

    # Update profile database
    db = get_db()
    update_profile(db, session['user_id'], fn, ln, bas_ctr, str_ctr,
                   car_ctr, swi_ctr, squ_ctr, 
                   gender, lat, lng, birthdate)
    if is_profile_complete(db, session['user_id']):
        session['comp_info'] = True
    #query_res = read_profile(db, (session['user_id'],))

    return render_template('form_action.html',fn=fn)
    
    #return render_template('index.html',profile_html=query_res[0],selected=interest)


@app.route('/sendinv/<invitee_id>')
# @login_required
def send_invitation(invitee_id):
    """
    Send an invitation to 'invitee'
    using AWS SES service.
    """
    # db = get_db()
    # invitee_email = get_user_email(db, invitee_id)
    # send_request(conn=conn_ses(), source=session['user_email'],
    #              to_address=invitee_email, 
    #              reply_addresses=session['user_email'])
    print invitee_id
    return None


@app.route('/***', methods=['POST'])
@login_required
def to_rating_page():
    """
    Find all users that the current user need
    to rate (by querying DynamoDB),
    render the rating page, and send users' info
    to frontend.
    """
    records = query_inv_record(session['user_id'])
    if len(records) == 0:
        # No users need to rate. 
        # return render_template()
        pass

    uid_list = []
    for record in records:
        uid_list.append(record['partner'])

    db = get_db()
    profiles = read_profile(db, uid_list)
    return render_template('***.html', profiles=profiles)



@app.route('/rate', methods=['GET', 'POST'])
def rate_partner():
    """
    Rate partners. 
    """
    db = get_db()
    ##### DATA NEEDED ######
    # 1. ratee's id
    # 2. ratee's rating
    ratee_id = '1'
    ratee_rating = 5.0
    ########################
    update_records(db=db, uid=ratee_id, rating=ratee_rating,
                   rating_ctr=1)
    return None


if __name__ == '__main__':
    #app.run(debug=True, host='0.0.0.0')
    app.run(debug=True)

