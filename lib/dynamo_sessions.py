import os
import time

import boto3

from boto3.dynamodb.conditions import Key, Attr
import botocore.exceptions

import logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

def get_session_table():
    dynamodb = boto3.resource('dynamodb')
    return dynamodb.Table(os.getenv('SESSION_TABLE'))

def create(d):
    get_session_table().put_item(Item=d)
    LOGGER.debug("Created session {0} for account {1}, queue={2}".format(d['sessionId'],d['accountId'],d['sqsUrl']))
    return d


def destroy(account_id, session_id):
    get_session_table().delete_item(Key={'accountId':account_id,
                                         'sessionId':session_id})

def lookup(account_id, user_id=None, session_id=None):
    expires_filter = Attr('expires').gte(int(time.time()))
    q = {'Select': 'ALL_ATTRIBUTES',
         'FilterExpression': expires_filter}
    if session_id is None:
        q['KeyConditionExpression'] = Key('accountId').eq(account_id)
        if user_id is not None:
            q['FilterExpression'] = Attr('userId').eq(user_id) & expires_filter
    else:
        q['KeyConditionExpression'] = Key('accountId').eq(account_id) & Key('sessionId').eq(session_id)
    return collect_results(get_session_table().query,q)


def get_all_sessions():
    q = {'Select': 'ALL_ATTRIBUTES',
         'FilterExpression': Attr('expires').gte(int(time.time()))}
    return collect_results(get_session_table().scan,q)

def get_all_sqs_urls():
    q = {'Select': 'SELECTED_ATTRIBUTES',
         'AttributesToGet': ['sqsUrl']}
    return collect_results(get_session_table().scan,q)


def collect_results(table_f,qp):
    items = []
    while True:
        r = table_f(**qp)
        items.extend(r['Items'])
        lek = r.get('LastEvaluatedKey')
        if lek is None or lek=='':
            break
        qp['ExclusiveStartKey'] = lek
    return items

