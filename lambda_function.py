import json
import boto3
import string
import random
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('UrlShortenerTable')  # change to your table name if different

# CORS headers reused for every response
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
}


def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def lambda_handler(event, context):
    # Lambda Function URLs use a different event shape than API Gateway.
    # Function URL: event['requestContext']['http']['method'] and event['rawPath']
    # API Gateway (older style): event['httpMethod'] and event['path']
    http_method = (
        event.get('requestContext', {}).get('http', {}).get('method')
        or event.get('httpMethod')
    )
    path = event.get('rawPath') or event.get('path', '/')

    # Handle CORS preflight
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': ''
        }

    # POST / -> create a short URL
    if http_method == 'POST':
        return create_short_url(event)

    # GET /{code} -> redirect to the original URL
    if http_method == 'GET' and path and path != '/':
        code = path.lstrip('/')
        return redirect_short_url(code)

    return {
        'statusCode': 400,
        'headers': CORS_HEADERS,
        'body': json.dumps({'error': 'Unsupported request'})
    }


def create_short_url(event):
    try:
        body = json.loads(event.get('body') or '{}')
        long_url = body.get('url')

        if not long_url:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Missing "url" in request body'})
            }

        # generate a short code, retry on the rare collision
        short_code = generate_short_code()
        for _ in range(5):
            existing = table.get_item(Key={'shortCode': short_code}).get('Item')
            if not existing:
                break
            short_code = generate_short_code()

        table.put_item(Item={
            'shortCode': short_code,
            'longUrl': long_url
        })

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({'shortCode': short_code})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': str(e)})
        }


def redirect_short_url(code):
    try:
        item = table.get_item(Key={'shortCode': code}).get('Item')

        if not item:
            return {
                'statusCode': 404,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Short URL not found'})
            }

        return {
            'statusCode': 302,
            'headers': {
                **CORS_HEADERS,
                'Location': item['longUrl']
            },
            'body': ''
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': str(e)})
        }
