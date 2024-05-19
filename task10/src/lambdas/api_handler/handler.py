import os
import uuid
import json
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOGGER = get_logger('ApiHandler-handler')


class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o)
        return json.JSONEncoder.default(self, o)


def getUserPoolId(userpool_name):
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


def getAppClientId(userpool_id):
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


def userSignup(formData):
    userpool_name = os.environ['BOOKING_USERPOOL']
    userpool_id = getUserPoolId(userpool_name)
    cognito = boto3.client('cognito-idp')

    user_data = {
        'UserPoolId': userpool_id,
        'Username': formData['email'],
        'UserAttributes': [
            {'Name': 'given_name', 'Value': formData['firstName']},
            {'Name': 'family_name', 'Value': formData['lastName']},
            {'Name': 'email', 'Value': formData['email']}
        ],
        'TemporaryPassword': formData['password'],
        'MessageAction': 'SUPPRESS'
    }

    response = cognito.admin_create_user(**user_data)
    _LOGGER.info(f'admin_create_user response: {response}')

    password_data = {
        'UserPoolId': userpool_id,
        'Username': formData['email'],
        'Password': formData['password'],
        'Permanent': True
    }

    resp = cognito.admin_set_user_password(**password_data)
    _LOGGER.info(f'admin_set_user_password response: {resp}')

    return {'statusCode': 200, 'body': ''}


def userSignin(formData):
    userpool_name = os.environ['BOOKING_USERPOOL']
    userpool_id = getUserPoolId(userpool_name)
    client_id = getAppClientId(userpool_id)
    cognito = boto3.client('cognito-idp')

    auth_data = {
        'ClientId': client_id,
        'AuthFlow': 'USER_PASSWORD_AUTH',
        'AuthParameters': {
            'USERNAME': formData['email'],
            'PASSWORD': formData['password']
        }
    }

    response = cognito.initiate_auth(**auth_data)
    _LOGGER.info(f'initiate_auth response: {response}')
    access_token = response['AuthenticationResult']['IdToken']

    return {'statusCode': 200, 'body': json.dumps({'accessToken': access_token})}


def getTableList():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLES_TABLE'])
    response = table.scan()

    tables = response['Items'] if response and response.get('Items') else []

    return {'statusCode': 200, 'body': json.dumps({'tables': tables}, cls=JsonEncoder)}


def addNewTable(formData):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLES_TABLE'])
    table.put_item(Item=formData)

    return {'statusCode': 200, 'body': json.dumps({'id': formData['id']})}


def getTableById(table_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLES_TABLE'])
    _LOGGER.info(f"get_table_by_id table_id: {table_id=}")
    response = table.get_item(Key={'id': int(table_id)})

    table_data = response['Item'] if response and response.get('Item') else {}

    return {'statusCode': 200, 'body': json.dumps(table_data, cls=JsonEncoder)}


def makeReservation(formData):
    dynamodb = boto3.resource('dynamodb')
    reservations_table = dynamodb.Table(os.environ['RESERVATION_TABLE'])
    tables_table = dynamodb.Table(os.environ['TABLES_TABLE'])

    table_response = tables_table.scan(
        FilterExpression=Attr('number').eq(formData['tableNumber'])
    )
    if not table_response['Items']:
        return {'statusCode': 400, 'body': 'Table not found'}

    reservations_response = reservations_table.scan(
        FilterExpression=Attr('tableNumber').eq(formData['tableNumber']) & Attr('date').eq(formData['date']) & (
            (Attr('slotTimeStart').between(formData['slotTimeStart'], formData['slotTimeEnd'])) |
            (Attr('slotTimeEnd').between(formData['slotTimeStart'], formData['slotTimeEnd']))
        )
    )
    if reservations_response['Items']:
        return {'statusCode': 400, 'body': 'Conflicting reservation exists'}

    formData['id'] = str(uuid.uuid4())
    reservations_table.put_item(Item=formData)

    return {'statusCode': 200, 'body': json.dumps({'reservationId': formData['id']})}


def getReservationsList():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['RESERVATION_TABLE'])
    response = table.scan()

    tables = response['Items'] if response and response.get('Items') else []

    return {'statusCode': 200, 'body': json.dumps({'reservations': tables}, cls=JsonEncoder)}


class ApiHandler(AbstractLambda):

    def processRequest(self, event) -> dict:
        pass

    def requestHandler(self, event, context):

        resource = event['resource']
        http_method = event['httpMethod']
        formData = json.loads(event['body'] or '{}')

        try:
            if resource == '/signup' and http_method == 'POST':
                return userSignup(formData)
            elif resource == '/signin' and http_method == 'POST':
                return userSignin(formData)
            elif resource == '/tables' and http_method == 'GET':
                return getTableList()
            elif resource == '/tables' and http_method == 'POST':
                return addNewTable(formData)
            elif resource == '/tables/{tableId}' and http_method == 'GET':
                return getTableById(event['pathParameters']['tableId'])
            elif resource == '/reservations' and http_method == 'POST':
                return makeReservation(formData)
            elif resource == '/reservations' and http_method == 'GET':
                return getReservationsList()
            else:
                return {'statusCode': 400, 'body': 'Unknown resource'}
        except Exception as e:
            return {'statusCode': 400, 'body': str(e)}

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)