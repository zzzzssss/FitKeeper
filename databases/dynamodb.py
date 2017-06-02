import boto, datetime, os, datetime
import boto.dynamodb2
from boto.dynamodb2.exceptions import ItemNotFound
from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey

# Resourse Filename
aws_identity_filename = os.path.join(os.path.dirname(__file__), 'aws_identity.txt')
# Rate Table name
DYNAMODB_TABLE_NAME = 'GymPlanner'

# Read aws_identity.txt file
with open(aws_identity_filename, 'rb') as aws_file:
    content = aws_file.readlines()
    a_k = content[0].rstrip('\n').split()[2]
    a_s = content[1].rstrip('\n').split()[2]
    aws_file.close()


# Use cognito to setup identity
def conn_rate_table():
    """
    Connect to rate table.
    """
    client_dynamo = boto.dynamodb2.connect_to_region(
        'us-east-1',
        aws_access_key_id=a_k,
        aws_secret_access_key=a_s)

    # Connect to Table "GymPlanner"
    mytable = Table(DYNAMODB_TABLE_NAME, connection=client_dynamo)
    return mytable


def write_rate_record(mytable, uid_1, uid_2):
    """
    Write invitation record to DynamoDB.
    uid: Partition Key
    partner: Value
    """
    d = {}
    d2 = {}
    now = datetime.datetime.now().isoformat()

    d['uid'] = uid_1
    d['timestamp'] = now
    d['partner'] = uid_2

    d2['uid'] = uid_2
    d2['timestamp'] = now
    d2['partner'] = uid_1
    try:
        mytable.put_item(d, overwrite=True)
        mytable.put_item(d2, overwrite=True)
    except:
        print "[RATE DB] Write rate record failed."
    return None


def query_rate_record(mytable, uid):
    """
    Get all invitation records (for rating purposes).
    If no records, return an empty list.
    """
    try:
        records = mytable.query_2(uid__eq=uid)
    except:
        print "[RATE DB] Failed to query rate record."
        return []
    res = []
    for record in records:
        d = {}
        d['uid'] = record['uid']
        d['timestamp'] = record['timestamp']
        d['partner'] = record['partner']
        res.append(d)
    
    return res 


def remove_rate_record(mytable, uid, partner_uid):
    """
    After each rating process, remove corresponding
    rate record.
    """
    try:
        records = mytable.query_2(uid__eq=uid)
        for record in records:
            if record['partner'] == partner_uid:
                record.delete()
                print "[Rate Table] Successfully Delete."
                return None
        print "[Rate Table] No deletion happened."
        return None
    except:
        print "[RATE DB] Remove rate record failed."
        return None

##############  K-Means  ################
def conn_u_table():
    """
    Connect to 'GymPlanner_User' Table.
    """
    client_dynamo = boto.dynamodb2.connect_to_region(
        'us-east-1',
        aws_access_key_id=a_k,
        aws_secret_access_key=a_s)

    # Connect to Table
    mytable = Table('GymPlanner_User', connection=client_dynamo)
    return mytable


def conn_c_table():
    """
    Connect to 'GymPlanner_Cluster' Table.
    """
    client_dynamo = boto.dynamodb2.connect_to_region(
        'us-east-1',
        aws_access_key_id=a_k,
        aws_secret_access_key=a_s)

    # Connect to Table
    mytable = Table('GymPlanner_Cluster', connection=client_dynamo)
    return mytable


def write_to_kmeans_users(g):
    """
    Write Data to K-means users.
    """
    table = conn_u_table()
    try:
        for k, v in g.items():
            d = {}
            d['uid'] = k
            d['cid'] = str(v)
            table.put_item(d, overwrite=True)
    except:
        print "[KMEANS USER TABLE] Write failed."

    return None


def write_to_kmeans_cluster(ggm):
    """
    Write Data to K-means clusters.
    """
    table = conn_c_table()
    try:
        for k, v in ggm.items():
            d = {}
            d['cid'] = k
            d['uid'] = v
            table.put_item(d, overwrite=True)
    except:
        print "[KMEANS CLUSTER TABLE] Write failed."

    return None


def query_neighbors(uid):
    """
    Get IDs of all users of user's cluster.
    Input:
        uid: user's id
    Return:
        A list of ids (except current user's id)
    """
    # Connect table
    ut = conn_u_table()
    ct = conn_c_table()

    cluster_idx = ut.get_item(uid=uid)['cid']
    neighbors = ct.get_item(cid=cluster_idx)['uid']
    return [u for u in neighbors if u != uid]
#####################################################


if __name__ == '__main__':
    today = datetime.datetime.today()
    timestamp = str(today.year) + '-' + str(today.month) + '-' + str(today.day) \
                + ' ' + str(today.hour) + ':' + str(today.minute) + \
                str(today.second)
    uid = '1'
    partners = ['2', '3', '4', '5']
    d = {}
    d['uid'] = uid
    d['timestamp'] = timestamp
    d['partners'] = partners

    # write_dynamo(d)
    print query_dynamo('1')
