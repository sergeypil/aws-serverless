import os
import uuid
import json
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOGGER = get_logger('ApiHandler-handler')

class Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o)
        return json.JSONEncoder.default(self, o)

def fetch_cognito_userpool_id(userpool_name):
    cognito = boto3.client('cognito-idp')
    next_token = None
    while True:
        if next_token:
            response = cognito.list_user_pools(MaxResults=60, NextToken=next_token)
        else:
            response = cognito.list_user_pools(MaxResults=60)

        for client in response['UserPools']:
            if client['Name'] == userpool_name:
                return client['Id']

        next_token = response.get('NextToken')
        if not next_token:
            break
    raise Exception('Cannot find UserPoolId')

def fetch_cognito_app_client_id(userpool_id):
    cognito = boto3.client('cognito-idp')
    next_token = None

    while True:
        if next_token:
            response = cognito.list_user_pool_clients(
                UserPoolId=userpool_id, MaxResults=60, NextToken=next_token
            )
        else:
            response = cognito.list_user_pool_clients(UserPoolId=userpool_id, MaxResults=60)

        _LOGGER.info(f'list_user_pool_clients response: {response}')

        for client in response['UserPoolClients']:
            if client['UserPoolId'] == userpool_id:
                return client['ClientId']

        next_token = response.get('NextToken')
        if not next_token:
            break

    raise Exception('Cannot find ClientId')

def signup_user(body):
    userpool_name = os.environ['BOOKING_USERPOOL']
    userpool_id = fetch_cognito_userpool_id(userpool_name)
    cognito = boto3.client('cognito-idp')

    user_data = {
        'UserPoolId': userpool_id,
        'Username': body['email'],
        'UserAttributes': [
            {'Name': 'given_name', 'Value': body['firstName']},
            {'Name': 'family_name', 'Value': body['lastName']},
            {'Name': 'email', 'Value': body['email']}
        ],
        'TemporaryPassword': body['password'],
        'MessageAction': 'SUPPRESS'
    }

    response = cognito.admin_create_user(**user_data)
    _LOGGER.info(f'admin_create_user response: {response}')

    password_data = {
        'UserPoolId': userpool_id,
        'Username': body['email'],
        'Password': body['password'],
        'Permanent': True
    }

    resp = cognito.admin_set_user_password(**password_data)
    _LOGGER.info(f'admin_set_user_password response: {resp}')

    return {'statusCode': 200, 'body': ''}

def signin_user(body):
    userpool_name = os.environ['BOOKING_USERPOOL']
    userpool_id = fetch_cognito_userpool_id(userpool_name)
    client_id = fetch_cognito_app_client_id(userpool_id)
    cognito = boto3.client('cognito-idp')

    auth_data = {
        'ClientId': client_id,
        'AuthFlow': 'USER_PASSWORD_AUTH',
        'AuthParameters': {
            'USERNAME': body['email'],
            'PASSWORD': body['password']
        }
    }

    response = cognito.initiate_auth(**auth_data)
    _LOGGER.info(f'initiate_auth response: {response}')
    access_token = response['AuthenticationResult']['IdToken']

    return {'statusCode': 200, 'body': json.dumps({'accessToken': access_token})}

def create_table(body):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLES_TABLE'])
    table.put_item(Item=body)

    return {'statusCode': 200, 'body': json.dumps({'id': body['id']})}


def fetch_tables():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLES_TABLE'])
    response = table.scan()

    tables = response['Items'] if response and response.get('Items') else []

    return {'statusCode': 200, 'body': json.dumps({'tables': tables}, cls=Encoder)}

def fetch_table_by_id(table_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLES_TABLE'])
    _LOGGER.info(f"get_table_by_id table_id: {table_id=}")
    response = table.get_item(Key={'id': int(table_id)})

    table_data = response['Item'] if response and response.get('Item') else {}

    return {'statusCode': 200, 'body': json.dumps(table_data, cls=Encoder)}

def create_reservation(body):
    dynamodb = boto3.resource('dynamodb')
    reservations_table = dynamodb.Table(os.environ['RESERVATION_TABLE'])
    tables_table = dynamodb.Table(os.environ['TABLES_TABLE'])

    table_response = tables_table.scan(
        FilterExpression=Attr('number').eq(body['tableNumber'])
    )
    if not table_response['Items']:
        return {'statusCode': 400, 'body': 'Table not found'}

    reservations_response = reservations_table.scan(
        FilterExpression=Attr('tableNumber').eq(body['tableNumber']) & Attr('date').eq(body['date']) & (
            (Attr('slotTimeStart').between(body['slotTimeStart'], body['slotTimeEnd'])) |
            (Attr('slotTimeEnd').between(body['slotTimeStart'], body['slotTimeEnd']))
        )
    )
    if reservations_response['Items']:
        return {'statusCode': 400, 'body': 'Conflicting reservation exists'}

    body['id'] = str(uuid.uuid4())
    reservations_table.put_item(Item=body)

    return {'statusCode': 200, 'body': json.dumps({'reservationId': body['id']})}

def fetch_reservations():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['RESERVATION_TABLE'])
    response = table.scan()

    tables = response['Items'] if response and response.get('Items') else []

    return {'statusCode': 200, 'body': json.dumps({'reservations': tables}, cls=Encoder)}

class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass

    def handle_request(self, event, context):

        resource = event['resource']
        http_method = event['httpMethod']
        body = json.loads(event['body'] or '{}')

        try:
            if resource == '/signup' and http_method == 'POST':
                return signup_user(body)
            elif resource == '/signin' and http_method == 'POST':
                return signin_user(body)
            elif resource == '/tables' and http_method == 'GET':
                return fetch_tables()
            elif resource == '/tables' and http_method == 'POST':
                return create_table(body)
            elif resource == '/tables/{tableId}' and http_method == 'GET':
                return fetch_table_by_id(event['pathParameters']['tableId'])
            elif resource == '/reservations' and http_method == 'POST':
                return create_reservation(body)
            elif resource == '/reservations' and http_method == 'GET':
                return fetch_reservations()
            else:
                return {'statusCode': 400, 'body': 'Unknown resource'}
        except Exception as e:
            return {'statusCode': 400, 'body': str(e)}

HANDLER = ApiHandler()

def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)