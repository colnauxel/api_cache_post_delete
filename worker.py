from flask import request
from base64 import b64encode,b64decode,decodebytes,decode
import requests
import pika
import json
import redis
import settings

redis_host = settings.REDIS_HOST
redis_port = settings.REDIS_POST
redis_password = settings.REDIS_PASSWORD

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='handel_cache', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C')

def callback(ch, method, properties, body):
    r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)
    data_json = json.loads(body)
    url = data_json['url']

    if 'expire' in data_json:
        expire = data_json['expire']
        data = requests.get(url).text
        data_byte = data.encode('utf-8')
        encode_data = b64encode(data_byte)
        r.set("msg:" + url, encode_data, ex=expire)
        print('save cache ')
    else:
        r.delete('msg:'+url)
        print('delete cache')
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='handel_cache', on_message_callback=callback)

channel.start_consuming()