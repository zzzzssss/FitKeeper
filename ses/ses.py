import boto.ses
import json, os


aws_key_filename = os.path.join(os.path.dirname(__file__), 'aws_key.txt')

APP_URL_HEADER = 'http://ec2-52-23-169-34.compute-1.amazonaws.com:5000/emailinv/'

with open(aws_key_filename, 'rb') as aws_file:
    lines = aws_file.readlines()
    access_key_id = lines[0].rstrip('\n')
    secret_access_key = lines[1].rstrip('\n')


# Connect to Amazon AWS
def conn_ses():
    """
    Connect to ses.
    """
    conn = boto.ses.connect_to_region("us-east-1",
            aws_access_key_id = access_key_id,
            aws_secret_access_key = secret_access_key)
    return conn


def verify_email(conn, email_addr='yc3313@columbia.edu'):
    # verify an email address
    conn.verify_email_address(email_addr)
    return None

'''
# list the addresses that are currently verified
addr_list = []
res = conn.list_verified_email_addresses()
temp = res['ListVerifiedEmailAddressesResponse']['ListVerifiedEmailAddressesResult']['VerifiedEmailAddresses']
for addr in temp:
    addr_list.append(str(addr))
# print addr_list
'''

def is_email_verified(conn, user_email):
    """
    Determine if user's email varified by AWS.
    """
    addr_list = []
    res = conn.list_verified_email_addresses()
    temp = res['ListVerifiedEmailAddressesResponse']['ListVerifiedEmailAddressesResult']['VerifiedEmailAddresses']
    for addr in temp:
        addr_list.append(str(addr))

    return True if user_email in addr_list else False


def ses_verification(conn, user_email):
    if not is_email_verified(conn, user_email):
        verify_email(conn, user_email)
        print "[SES] Sent SES Verification."
    else:
        print "[SES] This email address has been verified."
    return None


def send_request(conn,
                 source='yc2763@nyu.edu',
                 to_address='yc3313@columbia.edu',
                 sender_id='1010',
                 receiver_id='0101',
                 sender_name='aa',
                 receiver_name='bb',
                 ):
    # send formatted message
    link = APP_URL_HEADER + sender_id + '/' + receiver_id
    text_body = 'Hi,'+receiver_name+'\n'+'\n'+"		I'm "+sender_name+','+' I want to make friend with you!'+'\n'+'\n'+\
                '		If you agree, please click the following link:'+'\n'+'\n'+'		'+link
    try:
        conn.send_email(source=source,
                        to_addresses=to_address,
                        reply_addresses=source,
                        subject='You have a friend request @FitKeeper!',
                        body=text_body,
                        format='text')
        print "[SES] Sent an invitation request."
    except boto.ses.exceptions.SESAddressNotVerifiedError:
        print "[SES] Email Address not varified. Failed to send."
    return None
