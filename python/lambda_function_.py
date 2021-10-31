import json
import boto3.session
import base64
import pymysql
from requests_toolbelt.multipart import decoder


def create_connection_token():
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name="ap-northeast-2"
    )
    get_secret_value_response = client.get_secret_value(
        SecretId='database-access-key'
    )
    token = get_secret_value_response['SecretString']
    return eval(token)


def db_ops():
    secrets = create_connection_token()
    try:
        connection = pymysql.connect(
            host=secrets['host'],
            user=secrets['username'],
            password=secrets['password'],
            port=secrets['port'],
            db='sparta',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    except pymysql.MySQLError as e:
        print("connection error!!")
        return e

    print("connection ok!!")
    return connection


def uploadToS3(body, original_file_name):
    s3 = boto3.client('s3')
    s3.put_object(
        ACL="public-read",
        Bucket='aws-lambda-image',
        Body=body,
        Key=original_file_name,
        ContentType='image/' + original_file_name.split('.')[1]
    )

    conn = db_ops()
    cursor = conn.cursor()
    cursor.execute("use sparta;")
    # noinspection SqlResolve
    cursor.execute(f"""
    create table if not exists image( 
    idx int auto_increment, 
    url varchar(200) null, 
    constraint image_pk 
    primary key (idx));""")
    # noinspection SqlResolve
    cursor.execute(f"insert into image (url) value('{original_file_name}');")
    conn.commit()


def lambda_handler(event, context):
    if 'Content-Type' in event['headers']:
        content_type_header = event['headers']['Content-Type']
    else:
        content_type_header = event['headers']['content-type']
    print(json.dumps(event))
    print(context)
    post_data = base64.b64decode(event['body']).decode('iso-8859-1')
    lst = []
    for part in decoder.MultipartDecoder(post_data.encode('utf-8'), content_type_header).parts:
        lst.append(part.text)
    decoder_file = decoder.MultipartDecoder(post_data.encode('utf-8'), content_type_header)
    print(decoder_file)
    file_name = lst[1]  # 파일명은 한글이 아니어야 한다.
    uploadToS3(lst[0].encode('iso-8859-1'), file_name)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "success",
        }),
    }
