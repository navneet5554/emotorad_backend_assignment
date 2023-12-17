
from flask import Flask, jsonify, request
import jwt
import redis
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nopasswordfornow'
app.config['MQTT_BROKER'] = 'emqx'  # Replace with your MQTT broker address

redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

def generate_token(email):
    expiration_time = datetime.utcnow() + timedelta(minutes=5)
    payload = {'email': email, 'exp': expiration_time}
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token') 

def on_publish(client, userdata, mid):
    print("Message Published")   

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("speed_topic")  # Replace with the MQTT topic you want to subscribe to

def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic}: {msg.payload.decode('utf-8')}")

    # Store the received message in Redis
    store_in_redis(msg.payload.decode('utf-8'))

def store_in_redis(data):
    # Connect to Redis
    redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

    # Store data in Redis
    redis_client.set('speed', data)    

    
@app.route('/', methods=['POST'])
def generate_token_endpoint():
    try:
        data = request.get_json()
        email = data.get('email')

        # Check if the email is badly formatted or empty
        if not email or '@' not in email:
            raise ValueError('Invalid email format')

        # Generate and return a token
        token = generate_token(email)
        print("token_generator")
        return jsonify({'token': token})

    except Exception as e:
        return jsonify({'error': str(e)}), 400

mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.on_publish = on_publish
mqtt_client.connect(app.config['MQTT_BROKER'], 1883, 60)
mqtt_client.subscribe('speed_topic', qos=1)
mqtt_client.loop_start()

@app.route('/', methods=['GET'])
def get_latest_speed():
    try:
        # Get the token from the request header
        token = request.headers.get('Authorization')
        if not token:
            raise ValueError('Token is missing')

        # Verify the token
        payload = verify_token(token)

        # Check if there is data stored in Redis
        latest_speed = redis_client.get('speed')
        if not latest_speed:
            raise ValueError('No data stored in Redis')

        return jsonify({'speed': latest_speed.decode('utf-8')})

    except ValueError as e:
        return jsonify({'error': str(e)}), 400  


@app.route('/push_data', methods=['POST'])
def push_data():
    try:
        # Get the token from the request header
        token = request.headers.get('Authorization')
        if not token:
            raise ValueError('Token is missing')

        # Verify the token
        verify_token(token)

        # Get speed from the request data
        data = request.get_json()
        speed = data.get('speed')
        if speed is None:
            raise ValueError('Speed is missing')

        # Publish speed to the MQTT topic
        mqtt_client.publish('speed_topic', str(speed), qos=1)

        return jsonify({'message': 'Speed data published to MQTT'})

    except ValueError as e:
        return jsonify({'error': str(e)}), 400              

if __name__ == '__main__':
    app.run(debug=True, port=4000, host='0.0.0.0')
