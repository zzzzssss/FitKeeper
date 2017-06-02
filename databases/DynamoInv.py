from boto3 import Session
from boto3.dynamodb.conditions import Key, Attr
import datetime
import time
import os

aws_key_filename = os.path.join(os.path.dirname(__file__), 'aws_key.txt')

with open(aws_key_filename, 'rb') as aws_file:
    lines = aws_file.readlines()
    access_key_id = lines[0].rstrip('\n')
    secret_access_key = lines[1].rstrip('\n')


def conn_dynamodb():
    session = Session(aws_access_key_id=access_key_id,
                      aws_secret_access_key=secret_access_key,
                      region_name='us-east-1')
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table('Invitation')
    return table


def put_inv_record(id, f_id):
    #datatype{ user_id:str, timestamp:int, formatted_t: str, friend_id: str, agreed:int}
    t = int(time.time())
    try:
        table = conn_dynamodb()
        table.put_item(
            Item={
                'user_id': id,
                'timestamp': t,
                'formatted_t': datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S'),
                'friend_id': f_id,
                'agreed': '0'
            }
        )
        return None
    except:
        print "[INV DB] Failed to put inv record."
        return None


def retrieve_inv_record(id):
    try:
        table = conn_dynamodb()
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(id)
        )
        items = response['Items']
        f_list_r = sorted(items, key=lambda item: item['timestamp'], reverse=True)
        return f_list_r
    except:
        print "[INV DB] Failed to retrieve inv record."
        return []


def change_request_status(id, f_id, status):
    """
    change the status between two users
    id: user id
    f_id: friend if
    status: 1 for agree, -1 for reject
    """
    try:
        table = conn_dynamodb()
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(id)
        )
        items = response['Items']
        f_list = []

        for item in items:
            if item['friend_id'] == f_id:
                f_list.append(item)
        f_list_r = sorted(f_list, key=lambda item: item['timestamp'], reverse=True)
        result = f_list_r[0]

        table.update_item(
            Key={
                'user_id': id,
                'timestamp': result['timestamp']
            },
            UpdateExpression='SET agreed = :val1',
            ExpressionAttributeValues={
                ':val1': str(status)
            }
        )
        return None
    except:
        print "[INV DB] Failed to change request status."
        return None
