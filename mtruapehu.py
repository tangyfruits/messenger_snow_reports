import os
import sys
import json
import urllib2
import requests
import random
from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "This page acts as a Webhook for the Ruapehu Bot on Facebook", 200


@app.route('/', methods=['POST'])
def webhook():
    whakapapa = ["Happy Valley","Te Heuheu Valley","Waterfall","The Pinnacles","Far West T Bar","West Ridge Far West"]
    turoa = ["Alpine Meadows","Blyth Flats","Nga Waiheke","Giant Cafe","Highnoon Top"]
    # endpoint for processing incoming messaging even
    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):  # someone sent us a message
                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text
                    if messaging_event.get("payload" ) == 'DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_PREVIOUS':  # payloads
                        pass
                    send_ruapehu_template(sender_id, message_text, whakapapa)

    return "ok", 200
 
def send_ruapehu_photos(recipient_id, message_text, skifield):


    for webcam in whakapapa:
        mtruapehu = "https://webcams.mtruapehu.com/" + webcam + "/latest.jpg"
        params = {
            "access_token": os.environ["PAGE_ACCESS_TOKEN"]
        }
        headers = {
            "Content-Type": "application/json"
        }
        
        data = json.dumps({
            "recipient": {
                "id": recipient_id
            },
         "message":{
            "attachment":{
                "type":"image",
                    "payload":{
                        "url": mtruapehu,
                                }
                        }
                    }
        }
        )
        r = requests.post("https://graph.facebook.com/v2.10/me/messages", params=params, headers=headers, data=data)
        if r.status_code != 200:
            log(r.status_code)
            log(r.text)

def send_ruapehu_template(recipient_id, message_text, skifield):

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message":{ 
            "attachment":{ 
                "type":"template",
                "payload":{ 
                    "template_type":"generic",
                    "elements":[ 
                    ]
                }
            }
        }
    }
    )
    for webcam in skifield:
        data = data['message']['attachment']['payload']['elements'][0].append(create_generic_template(webcam))

    r = requests.post("https://graph.facebook.com/v2.10/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def create_generic_template(webcam):
    return { 
        "title": webcam,
        "image_url": build_url(webcam),
        "default_action":{ 
            "type":"web_url",
            "url": build_url(webcam),
            "webview_height_ratio":"tall"
        },
        "buttons":[ 
            { 
                "type":"web_url",
                "url":"https://www.mtruapehu.com/whakapapa/report",
                "title":"View Full Report"
            },
            { 
                "type":"postback",
                "title":"Turoa",
                "payload":"DEVELOPER_DEFINED_PAYLOAD"
            }
        ]
    }

def build_url(webcam):
    return "https://webcams.mtruapehu.com/" + webcam.lower().replace(" ", "") +"/latest.jpg"


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True) #take this out in prod
