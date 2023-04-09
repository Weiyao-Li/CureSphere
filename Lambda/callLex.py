import boto3


def lambda_handler(event, context):
    client = boto3.client('lexv2-runtime')
    msg_from_user = event['messages'][0]['unstructured']['text']
    print(f"Message from frontend: {msg_from_user}")
    response = client.recognize_text(
        botId='NYYWX0VKMQ',  # MODIFY HERE
        botAliasId='TSTALIASID',  # MODIFY HERE
        localeId='en_US',
        sessionId='testuser',
        text=msg_from_user)

    msg_from_lex = response.get('messages', [])
    if msg_from_lex:
        resp = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'messages': [
                {'type': 'unstructured',
                 'unstructured': {
                     'id': 'string',
                     'text': msg_from_lex[0]['content'],
                     'timestamp': 'string'
                 }}
            ]
        }
    return resp
