import os
import boto3
import time
import uuid
import json
import functools
from botocore.exceptions import ClientError


def get_table(dynamodb=None):
    if not dynamodb:
        URL = os.environ['ENDPOINT_OVERRIDE'] #Recoge la url desde localEnvironment.json
        if URL:
            print('URL dynamoDB:'+URL)
            boto3.client = functools.partial(boto3.client, endpoint_url=URL) #fija el parámetro endpoint_url cuando se llame a boto3.client para no tener que pasársela cada vez
            boto3.resource = functools.partial(boto3.resource,
                                               endpoint_url=URL)  #fija la url cuando se llame a boto3.resource 
        dynamodb = boto3.resource("dynamodb")
    # fetch todo from the database
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE']) #Recoge la tabla especificada en localEnvironment.json
    return table


def get_item(key, dynamodb=None):
    table = get_table(dynamodb) #Obtiene la tabla "local-TodosDynamoDbTable"
    try: #Recoge el item solicitado por parámetro.
        result = table.get_item(
            Key={
                'id': key
            }
        )

    except ClientError as e: #Si casca devuelve el error.
        print(e.response['Error']['Message'])
    else: #Si va todo bien, devuelve el json resultante de la consulta.
        print('Result getItem:'+str(result))
        if 'Item' in result:
            return result['Item']


def get_items(dynamodb=None):
    table = get_table(dynamodb)
    # fetch todo from the database
    result = table.scan() #Obtiene todos los elementos de la tabla local-TodosDynamoDbTable
    return result['Items']


def put_item(text, dynamodb=None):
    table = get_table(dynamodb)
    timestamp = str(time.time())
    print('Table name:' + table.name)
    item = {
        'id': str(uuid.uuid1()),
        'text': text,
        'checked': False,
        'createdAt': timestamp,
        'updatedAt': timestamp,
    }
    try:
        # write the todo to the database
        table.put_item(Item=item) #Inserta un nuevo elemento en la tabla
        # create a response
        response = {
            "statusCode": 200,
            "body": json.dumps(item) #Volcamos el item pasado a la base de datos.
        }

    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response


def update_item(key, text, checked, dynamodb=None):
    table = get_table(dynamodb)
    timestamp = int(time.time() * 1000)
    # update the todo in the database
    try:
        result = table.update_item( #
            Key={
                'id': key
            },
            ExpressionAttributeNames={
              '#todo_text': 'text',
            },
            ExpressionAttributeValues={
              ':text': text,
              ':checked': checked,
              ':updatedAt': timestamp,
            },
            UpdateExpression='SET #todo_text = :text, '
                             'checked = :checked, '
                             'updatedAt = :updatedAt',
            ReturnValues='ALL_NEW',
        )

    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return result['Attributes']


def delete_item(key, dynamodb=None):
    table = get_table(dynamodb)
    # delete the todo from the database
    try:
        table.delete_item(
            Key={
                'id': key
            }
        )

    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return


def create_todo_table(dynamodb):
    # For unit testing
    tableName = os.environ['DYNAMODB_TABLE']
    print('Creating Table with name:' + tableName)
    table = dynamodb.create_table(
        TableName=tableName,
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1
        }
    )

    # Wait until the table exists.
    table.meta.client.get_waiter('table_exists').wait(TableName=tableName)
    if (table.table_status != 'ACTIVE'):
        raise AssertionError()

    return table
