import os
import sys
import json

from flask import Flask
from flask import request, Response
from pymongo import MongoClient
import goslate
import requests
import unirest
import urllib

gs = goslate.Goslate()

app = Flask(__name__)

if 'MONGOLAB_URI' in os.environ:
    mongo_client = MongoClient("ds031661.mongolab.com",31661)
    db = mongo_client.heroku_app33149566
    db.authenticate("linguini", "linguini")
else:
    mongo_client = MongoClient("mongodb://localhost:27017")
    #mongo_client = MongoClient(host="mongodb://heroku_app33149566:15u1snfd9f34rjsvi18s08rngv@ds031661.mongolab.com:31661")
    db = mongo_client["linguini"]
    #db = mongo_client["heroku_app33149566"]

@app.route('/')
def hello():
    return "Linguini"

@app.route('/search')
def search():
    query = request.args.get('q')
    start = query.title()
    end = start[:-1] + chr(ord(start[-1]) + 1)
    query = {'name': {'$gte': start, '$lt': end}}
    result = json.dumps(list(db.Users.find(query,{'_id':0})))
    return Response(result, mimetype='application/json')

@app.route('/login/', methods=['POST',])
def login():
    login_data = request.get_json()
    user_data['lang'] = login_data['lang']
    user_data['name'] = login_data['name'].title()
    user_data['id'] = login_data['id']

    user = db.Users.find_one({'id':user_data['id']})
    if not user:
        db.Users.insert(user_data)
    else:
        db.Users.update({'id': user['id']}, {'$set':{'lang':user['lang']}})
    return "Success"

def _translate(message, to_language):
    payload = {"message":message, "lang": to_language}
    headers = {'content-type': 'application/json'}
    if 'MONGOLAB_URI' in os.environ:
        r = requests.post("https://mashapelinguini.herokuapp.com/translate/", data=json.dumps(payload), headers=headers)
    else:
        r = requests.post("http://localhost:4000/translate/", data=json.dumps(payload), headers=headers)
    translated_text = json.loads(r.text)['text']
    return translated_text

def _publish(to, message):
    message = urllib.quote(message.encode('utf8'))
    response = requests.get('https://pubnub-pubnub.p.mashape.com/publish/pub-c-287cdce8-3958-499e-82c8-85c830e981b0/sub-c-c44a92f0-98df-11e4-91be-02ee2ddab7fe/0/{}/0/"{}"'.format(to,message),
        headers={"X-Mashape-Key": "c9eRe8ZTI5mshmGeJvK8Z0iawkx6p1xhUY7jsn8pKuG9mOWMOS"}
    )

@app.route('/publish/', methods=['POST',])
def publish():
    data = request.get_json()
    to = db.Users.find_one({'id':data['to']})
    final_message = json.dumps({'message':_translate(data['message'], to['lang']),'from':data['from'], 'name':to['name']})
    #print final_message
    #_publish(to['id'], final_message)
    _publish(data['to'], final_message)
    return "Success"

@app.route("/translate/", methods=['POST'])
def translate():
    data = request.get_json()
    message = data['message']
    to_language = data['lang']
    translated_text = gs.translate(message, to_language)
    data = {'text': translated_text}
    serialized = json.dumps(data)
    return Response(serialized, mimetype='application/json')
#app.debug=True
#if 'MONGOLAB_URI' not in os.environ:
#app.run(host="0.0.0.0",port=int(sys.argv[1]))