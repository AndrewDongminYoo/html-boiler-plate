import json
import boto3
import pymysql
from datetime import date


def get_secret():
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name="ap-northeast-2"
    )
    get_secret_value_response = client.get_secret_value(
        SecretId='mysql-secret'
    )
    token = get_secret_value_response['SecretString']
    return eval(token)


def db_ops():
    secrets = get_secret()
    try:
        connection = pymysql.connect(
            host=secrets['host'],
            user=secrets['username'],
            password=secrets['password'],
            db='sparta',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    except pymysql.MySQLError as e:
        print("connection error!!")
        return e

    print("connection ok!!")
    return connection


def lambda_handler(event, context):
    print(event)
    print(context)
    action_type = event['queryStringParameters']['type']
    res_body = ""
    conn = db_ops()
    cursor = conn.cursor()
    cursor.execute("use `sparta`;")
    cursor.execute(f"""
    create table if not exists board ( 
    idx int auto_increment,
    title varchar(100) null,
    content text null, 
    regDate varchar(10) null,
    constraint board_pk 
    primary key (idx));""")
    if action_type == "drop_table":
        cursor.execute("drop table if exists board;")
        conn.commit()
        res_body = "delete_many_success"
    if action_type == 'write':
        if event['httpMethod'] == 'OPTIONS':
            res_body = json.dumps({
                "message": "success",
            })
        else:
            today = date.today()
            body = json.loads(event['body'])
            # noinspection SqlResolve
            cursor.execute(f"""insert into board (title, content, regDate) 
            value('{body['title']}', '{body['content']}', '{today.strftime("%Y%m%d")}');""")
            conn.commit()
            res_body = json.dumps({
                "message": "success",
            })
    elif action_type == 'list':
        # noinspection SqlResolve
        cursor.execute("select idx, title, content, regDate from board")
        result = cursor.fetchall()
        res_body = json.dumps({
            "message": "success",
            "data": result
        })
    elif action_type == 'read':
        idx = event['queryStringParameters']['idx']
        # noinspection SqlResolve
        cursor.execute("select * from board where idx=" + idx)
        bbs = cursor.fetchone()
        res_body = json.dumps({
            "result": "success",
            "data": bbs
        })
    elif action_type == 'delete':
        idx = event['queryStringParameters']['idx']
        # noinspection SqlResolve
        cursor.execute("delete from `board` where idx="+idx)
        conn.commit()
        res_body = json.dumps({
            "message": "success",
        })

    return {
        "statusCode": 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type,x-requested-with',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET'
        },
        "body": res_body,
    }
