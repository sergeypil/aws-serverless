import os
import uuid
import json
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOGGER = get_logger('ApiHandler-handler')


class ConversionEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super().default(obj)


def retrieve_cognito_details(userpool_name):
    cognito = boto3.client('cognito-idp')
    pagination_token = None

    while True:
        if pagination_token:
            response = cognito.list_user_pools(MaxResults=60, NextToken=pagination_token)
        else:
            response = cognito.list_user_pools(MaxResults=60)

        for userpool in response['UserPools']:
            if userpool['Name'] == userpool_name:
                userpool_id = userpool['Id']
                break

        pagination_token = response.get('NextToken')
        if not pagination_token:
            break

    pagination_token = None
    while True:
        if pagination_token:
            response = cognito.list_user_pool_clients(UserPoolId=userpool_id, MaxResults=60, NextToken=pagination_token)
        else:
            response = cognito.list_user_pool_clients(UserPoolId=userpool_id, MaxResults=60)

        for client in response['UserPoolClients']:
            if client['UserPoolId'] == userpool_id:
                client_id = client['ClientId']
                break

        pagination_token = response.get('NextToken')
        if not pagination_token:
            break

    return userpool_id, client_id


def handle_user_auth(resource, request_body):
    userpool_name = os.environ['BOOKING_USERPOOL']
    userpool_id, client_id = retrieve_cognito_details(userpool_name)
    cognito = boto3.client('cognito-idp')

    if resource == '/signup':
        user_data = {
            'UserPoolId': userpool_id,
            'Username': request_body['email'],
            'UserAttributes': [
                {'Name': 'given_name', 'Value': request_body['firstName']},
                {'Name': 'family_name', 'Value': request_body['lastName']},
                {'Name': 'email', 'Value': request_body['email']}
            ],
            'TemporaryPassword': request_body['password'],
            'MessageAction': 'SUPPRESS'
        }

        response = cognito.admin_create_user(**user_data)
        _LOGGER.info(f'admin_create_user response: {response}')

        password_data = {
            'UserPoolId': userpool_id,
            'Username': request_body['email'],
            'Password': request_body['password'],
            'Permanent': True
        }

        response = cognito.admin_set_user_password(**password_data)
        _LOGGER.info(f'admin_set_user_password response: {response}')

        return {'statusCode': 200, 'body': ''}
    else:
        auth_paramaters = {
            'ClientId': client_id,
            'AuthFlow': 'USER_PASSWORD_AUTH',
            'AuthParameters': {
                'USERNAME': request_body['email'],
                'PASSWORD': request_body['password']
            }
        }

        response = cognito.initiate_auth(**auth_paramaters)
        _LOGGER.info(f'initiate_auth response: {response}')
        token = response['AuthenticationResult']['IdToken']

        return {'statusCode': 200, 'body': json.dumps({'accessToken': token})}


def fetch_all_tables():
    dynamodb = boto3.resource('dynamodb')
    dynamodb_table = dynamodb.Table(os.environ['TABLES_TABLE'])
    response = dynamodb_table.scan()

    tables = response.get('Items', [])

    return {'statusCode': 200, 'body': json.dumps({'tables': tables}, cls=ConversionEncoder)}

def create_new_table(request_body):
    dynamodb = boto3.resource('dynamodb')
    dynamodb_table = dynamodb.Table(os.environ['TABLES_TABLE'])

    dynamodb_table.put_item(Item=request_body)

    return {'statusCode': 200, 'body': json.dumps({'id': request_body['id']})}


def fetch_table_by_identifier(table_id):
    dynamodb = boto3.resource('dynamodb')
    dynamodb_table = dynamodb.Table(os.environ['TABLES_TABLE'])

    _LOGGER.info(f"get_table_by_id table_id: {table_id=}")

    response = dynamodb_table.get_item(Key={'id': int(table_id)})

    table = response.get('Item', {})

    return {'statusCode': 200, 'body': json.dumps(table, cls=ConversionEncoder)}


def create_table_reservation(request_body):
    dynamodb = boto3.resource('dynamodb')
    reservations_table = dynamodb.Table(os.environ['RESERVATION_TABLE'])
    tables_table = dynamodb.Table(os.environ['TABLES_TABLE'])

    filter_cond = Attr('number').eq(request_body['tableNumber'])
    table_search_result = tables_table.scan(FilterExpression=filter_cond)

    if not table_search_result['Items']:
        return {'statusCode': 400, 'body': 'Table not found'}

    filter_cond = Attr('tableNumber').eq(request_body['tableNumber']) & Attr('date').eq(request_body['date']) & (
        Attr('slotTimeStart').between(request_body['slotTimeStart'], request_body['slotTimeEnd']) |
        Attr('slotTimeEnd').between(request_body['slotTimeStart'], request_body['slotTimeEnd'])
    )

    reservation_search_result = reservations_table.scan(FilterExpression=filter_cond)
    if reservation_search_result['Items']:
        return {'statusCode': 400, 'body': 'Conflicting reservation exists'}

    request_body['id'] = str(uuid.uuid4())

    reservations_table.put_item(Item=request_body)

    return {'statusCode': 200, 'body': json.dumps({'reservationId': request_body['id']})}


def fetch_all_reservations():
    dynamodb = boto3.resource('dynamodb')
    dynamodb_table = dynamodb.Table(os.environ['RESERVATION_TABLE'])

    response = dynamodb_table.scan()

    reservations = response.get('Items', [])

    return {'statusCode': 200, 'body': json.dumps({'reservations': reservations}, cls=ConversionEncoder)}


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        return

    def process_request(self, event, context):

        endpoint = event['resource']
        method = event['httpMethod']
        request_body = json.loads(event.get('body', '{}'))

        try:
            if endpoint in ('/signup', '/signin') and method == 'POST':
                return handle_user_auth(endpoint, request_body)
            elif endpoint == '/tables' and method == 'GET':
                return fetch_all_tables()
            elif endpoint == '/tables' and method == 'POST':
                return create_new_table(request_body)
            elif endpoint == '/tables/{tableId}' and method == 'GET':
                return fetch_table_by_identifier(event['pathParameters']['tableId'])
            elif endpoint == '/reservations' and method == 'POST':
                return create_table_reservation(request_body)
            elif endpoint == '/reservations' and method == 'GET':
                return fetch_all_reservations()
            else:
                return {'statusCode': 400, 'body': 'Unknown resource'}
        except Exception as error:
            return {'statusCode': 400, 'body': str(error)}

HANDLER = ApiHandler()


def lambda_trigger(event, context):
    return HANDLER.lambda_handler(event=event, context=context)