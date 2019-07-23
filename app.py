from flask import Flask,render_template, request
from flask_restful import Resource, Api,reqparse
import requests
from functools import wraps
from base64 import b64encode,b64decode,decodebytes,decode
import redis
import settings
import pika
import json



app = Flask(__name__)
api = Api(app)
parser = reqparse.RequestParser()

app.config['SECRET_KEY'] = settings.SECRET_KEY
# Config Redis
redis_host = settings.REDIS_HOST
redis_port = settings.REDIS_POST
redis_password = settings.REDIS_PASSWORD

@app.route('/')
def index():
    return render_template('home.html')
@app.route("/page1")
def page1():
    return render_template('page1.html')

@app.route('/xc/<page>', methods = ["GET"])
def change_page(page):
    r = redis.StrictRedis(host = redis_host,
                          port = redis_port,
                          password=redis_password,
                          decode_responses=True)
    if r.exists('msg:'+page):
        print("existed!")
        d=r.get("msg:"+page)
        d_b=d.encode('utf-8')
        decode_d = decodebytes(d_b)
        da = decode_d.decode()
        return da
    data = requests.get('http://'+settings.HOST+":"+settings.PORT+page).text
    data_byte = data.encode('utf-8')
    encode_data = b64encode(data_byte)
    print('not existed!')
    save_redis = r.set("msg:"+page, encode_data, ex = 2*60)
    return data


# check auth
def auth(f):
    @wraps(f)
    def check(*args, **kwargs):
        if 'token' in request.headers:
            return f(*args, **kwargs)
        return {"msg":"Auth failed "}
    return check
# api_restful
class handel_cache(Resource):
    @auth
    def post(self):
        data_json = request.get_json()
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='handel_cache', durable=True)
        message = json.dumps(data_json)
        print(data_json)
        channel.basic_publish(
            exchange='',
            routing_key='handel_cache',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
            ))
        connection.close()
        return 'save cache'

    @auth
    def delete(self):
        data_json = request.get_json()
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='handel_cache', durable=True)
        message = json.dumps(data_json)
        print(data_json)
        channel.basic_publish(
            exchange='',
            routing_key='handel_cache',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))
        connection.close()
        return 'delete cache'

api.add_resource(handel_cache,'/handel_cache/')
if __name__ == '__main__':
    app.run(host =settings.HOST,
            port = settings.PORT,
            debug=True)