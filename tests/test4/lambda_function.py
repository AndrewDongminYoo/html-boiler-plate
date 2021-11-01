from requests_toolbelt.multipart import decoder
from datetime import date
import boto3.session
import pymysql
import base64
import json


def uploadToS3(body, original_file_name):
    s3 = boto3.client(
        's3',
        region_name="ap-northeast-2")
    s3.put_object(
        ACL="public-read",
        Bucket='itwassummer.shop',
        Body=body,
        Key=original_file_name,
        ContentType='images/' + original_file_name.split('.')[1]
    )
    conn = db_ops()
    cursor = conn.cursor()
    # noinspection SqlResolve
    cursor.execute("""
    create table if not exists image( 
    idx int auto_increment, 
    url varchar(200) null, 
    constraint image_pk 
    primary key (idx));""")
    # noinspection SqlResolve
    cursor.execute(f"insert into image (url) value('{original_file_name}');")
    conn.commit()


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


def response(key=None, value=None):
    if not key and value:
        return json.dumps({"message": "success"})
    return json.dumps({
        "message": "success",
        key: value
    })


def lambda_handler(event, context):
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
    if action_type == 'write':
        if event['httpMethod'] == 'OPTIONS':
            res_body = response()
        else:
            today = date.today()
            body = json.loads(event['body'])
            cursor.execute(f"""insert into board (title, content, regDate) 
            value('{body['title']}', '{body['content']}', '{today.strftime("%Y%m%d")}');""")
            conn.commit()
            res_body = response()
    elif action_type == 'list':
        query = event['queryStringParameters'].get('word')
        if not query:
            cursor.execute("select idx, title, regDate from `board`")
            result = cursor.fetchall()
        else:
            cursor.execute(f"select idx, title, regDate from `board` where title like '%{query}%'")
            result = cursor.fetchall()
        res_body = response("data", result)
    elif action_type == 'read':
        idx = event['queryStringParameters']['idx']
        cursor.execute("select * from board where idx=" + idx)
        post = cursor.fetchone()
        res_body = response("data", post)
    elif action_type == 'delete':
        idx = event['queryStringParameters']['idx']
        cursor.execute("delete from `board` where idx=" + idx)
        conn.commit()
        res_body = response()
    elif action_type == "file":
        if 'Content-Type' in event['headers']:
            content_type = event['headers']['Content-Type']
        else:
            content_type = event['headers']['content-type']
        _file = base64.b64decode(event['body']).decode('iso-8859-1')
        lst = []
        for part in decoder.MultipartDecoder(_file.encode('utf-8'), content_type).parts:
            lst.append(part.text)
        print("lst:", lst)
        decoder_file = decoder.MultipartDecoder(_file.encode('utf-8'), content_type)
        file_name = lst[1]  # 파일명은 한글이 아니어야 한다.
        uploadToS3(lst[0].encode('iso-8859-1'), file_name)
        res_body = response("file_name", file_name)

    return {
        "statusCode": 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST,GET,HEAD'
        },
        "body": res_body,
    }
