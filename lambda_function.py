import json
import boto3.session
import pymysql
import datetime


def get_secret():
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name="us-east-1"
    )
    get_secret_value_response = client.get_secret_value(
        SecretId='database-access-key'
    )
    token = get_secret_value_response['SecretString']
    return eval(token)


def db_ops():
    secrets = get_secret()
    print(secrets['host'])
    try:
        connection = pymysql.connect(
            host=secrets['host'],
            user=secrets['username'],
            password=secrets['password'],
            port=secrets['port'],
            database='sparta',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    except pymysql.MySQLError as e:
        print("connection error!!", e)
        return
    except pymysql.OperationalError as e:
        print("operational error!!", e)
        return

    print("connection ok!!")
    return connection


def lambda_handler(event, context):
    print(json.dumps(event))
    body = json.loads(event['body'])
    print(body)
    print(context)
    conn = db_ops()
    cursor = conn.cursor()
    cursor.execute(f"insert into `board` (title, content) values ('{body['title']}', '{body['content']}');")
    conn.commit()
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "success",
            "rows": conn.affected_rows()
        })
    }


if __name__ == '__main__':
    while True:
        try:
            result = lambda_handler({"body": "{\"title\": \"this is title\", \"content\": \"this is content\"}"}, None)
            print(result, datetime.datetime.utcnow())
        except AttributeError:
            print()