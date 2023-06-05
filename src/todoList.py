import os
import boto3
import time
import uuid
import json
import functools
from botocore.exceptions import ClientError


def get_table(dynamodb=None):
    if not dynamodb:
        # Recoge la url desde localEnvironment.json
        URL = os.environ['ENDPOINT_OVERRIDE']
        if URL:
            print('URL dynamoDB:'+URL)
            # fija el parámetro endpoint_url cuando se llame a boto3.client
            # para no tener que pasársela cada vez
            boto3.client = functools.partial(boto3.client, endpoint_url=URL)
            # fija la url cuando se llame a boto3.resource
            boto3.resource = functools.partial(boto3.resource,
                                               endpoint_url=URL)
        dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
    # fetch todo from the database
    # Recoge la tabla especificada en localEnvironment.json
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    return table


def get_item(key, dynamodb=None):
    # Obtiene la tabla "local-TodosDynamoDbTable"
    table = get_table(dynamodb)
    try:
        # Recoge el item solicitado por parámetro.
        result = table.get_item(
            Key={
                'id': key
            }
        )

    # Si casca devuelve el error.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        # Si va todo bien, devuelve el json resultante de la consulta.
        if 'Item' in result:
            return result['Item']


def get_translate_item(key, language, dynamodb=None):
    translateClient = boto3.client('translate', region_name='us-east-1')
    table = get_table(dynamodb)
    try:
        # Recoge el item solicitado por parámetro.
        result = table.get_item(
            Key={
                'id': key
            }
        )
        print("Palabra enviada a translate: " + result['Item']['text']+"\n")
        print("Parámetro language: " + language)
        itemTranslated = translateClient.translate_text(
            Text=result['Item']['text'],
            SourceLanguageCode="es",
            TargetLanguageCode=language)
        print("Después de llamar al cliente de itemTranslated\n")
    except ClientError as e:
        print("ClientError: "+str(e.response))
    else:
        print('Result translateItem:'+str(itemTranslated['TranslatedText']))
        return result


def get_items(dynamodb=None):
    table = get_table(dynamodb)
    # fetch todo from the database
    # Obtiene todos los elementos de la tabla local-TodosDynamoDbTable
    result = table.scan()
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
        # Inserta un nuevo elemento en la tabla
        table.put_item(Item=item)
        # create a response
        # Volcamos el item pasado a la base de datos.
        response = {
            "statusCode": 200,
            "body": json.dumps(item)
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
        result = table.update_item(
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
