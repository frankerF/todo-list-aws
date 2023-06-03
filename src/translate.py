import json
import decimalencoder
import todoList


def translate(event, context):
    item = todoList.get_item(event['pathParameters']['id'])
    if item:
        language = event['pathParameters']['language']
        itemTranslated = todoList.get_translate_item(item['id'], language)
        print("\nSalida de itemTranslated: " + str(itemTranslated) + "\n")
        response = {
            "statusCode": 200,
            "body": json.dumps(itemTranslated,
                               cls=decimalencoder.DecimalEncoder)
        }
    else:
        response = {
            "statusCode": 404,
            "body": ""
        }
    return response
