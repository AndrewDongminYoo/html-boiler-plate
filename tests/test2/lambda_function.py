import json
import boto3
import pymysql
import datetime


def db_ops():
    try:
        connection = pymysql.connect(
            host='rds-database-mysql-for-lambda.cb0wnv8kcyrj.ap-northeast-2.rds.amazonaws.com',
            user='admin',
            password='F*f#e8so7jn(k&86r{12ve%U61O=S8:A',
            port=3306,
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
    cursor.execute("use `sparta`;")
    # noinspection SqlResolve
    cursor.execute("alter table `board` add reg_Date datetime null;")
    # noinspection SqlResolve
    cursor.execute(f"""insert into `board` (title, content) values ('{body["title"]}', '{body["content"]}');""")
    conn.commit()
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "success",
            "rows": conn.affected_rows()
        })
    }


if __name__ == '__main__':
    try:
        result = lambda_handler({"body": "{\"title\": \"this is title\", \"content\": \"this is content\"}"}, None)
        print(result, datetime.datetime.utcnow())
    except AttributeError:
        print()
