from botocore.exceptions import ClientError
from globals import bucket_name, bucket_prefix, expense_email_verifier_agw
import json
import os
import base64
import boto3
import requests


s3_client = boto3.client("s3")


def lambda_handler(event, context):
    try:
        print(f'Incoming event: {event}')
        event_http_method = event['requestContext']['http']['method']
        print(f'Incoming API Gateway HTTP Method: {event_http_method}')
        event_path = event['requestContext']['http']['path']
        print(f'Incoming API Gateway Path: {event_path}')
        try:
            user_email = event['headers']['user-email']
            print(f'Incoming API Gateway user email: {user_email}')
            print(f'Verifying email from expense-email-verifier service')
            email_verifier_req = {"user-email": str(user_email)}
            email_verifier_resp = requests.post(url=expense_email_verifier_agw,
                                                data=json.dumps(email_verifier_req))
            if email_verifier_resp.status_code == 200:
                print('user-email verification successful')
                file_content = base64.b64decode(event['body'])
                file_name = event['headers']['file-name']
                print(f'Incoming API Gateway file name: {file_name}')
                s3_response = s3_client.put_object(Bucket=bucket_name,
                                                   Key=bucket_prefix+'/'+user_email+'/'+file_name,
                                                   Body=file_content)
                print('Returning successful response')
                msg = {"message": f"{file_name} successfully uploaded."}
                return {
                    "statusCode": 200,
                    "headers": {"content-type": "application/json"},
                    "body": json.dumps(msg)
                }
            else:
                print('user-email verification failed')
                msg = {"message": f"Unable to verify provided user-email."}
                return {
                    "statusCode": 404,
                    "headers": {"content-type": "application/json"},
                    "body": json.dumps(msg)
                }
        except KeyError as ke:
            msg = {"message": "Missing user-email, file-name in headers or file content in "
                              "request."}
            return {
                "statusCode": 400,
                "headers": {"content-type": "application/json"},
                "body": json.dumps(msg)
            }
    except (Exception, ClientError) as e:
        msg = e.response['Error']['Message']
        print(f'Exception caught: {msg}')
        return {
            "statusCode": 500,
            "headers": {"content-type": "application/json"},
            "body": json.dumps(msg)
        }


if __name__ == '__main__':
    script_dir = os.path.dirname(__file__)
    rel_path = '../events/test-agw-event.json'
    abs_file_path = os.path.join(script_dir, rel_path)
    with open(abs_file_path) as f:
        test_event = json.load(f)
        lambda_handler(test_event, None)