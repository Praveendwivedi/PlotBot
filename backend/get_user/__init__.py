import requests as urlrequests
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from pathlib import Path
from dotenv import load_dotenv
import os
import logging

import azure.functions as func


load_dotenv()

try:
    cred = credentials.Certificate(Path(__file__).parent/"serviceAccountKey.json")

    app=firebase_admin.initialize_app(cred,{
        'databaseURL': os.get_env("DATABASE_URL")
    })
except:
    logging.info('error')
    app = firebase_admin.get_app()
    

ref = db.reference()
user_ref = ref.child('Users')
# logging.info(f"{app.name},{ref.child('Users').get()}")

def main(req: func.HttpRequest) -> func.HttpResponse:
    # logging.info('Python HTTP trigger function processed a request.')
    try:
        token = req.headers.get('Authorization')
        # logging.info(f"Header {token}")

        r = urlrequests.get("https://oauth2.googleapis.com/tokeninfo",{"id_token":token})
        user_info = r.json()
        logging.info(f"user info {user_info}")
        if "error" in user_info:
            return func.HttpResponse(
                json.dumps(user_info),
                status_code=400
            )

        if user_info["aud"] != '371694754584-23efcgomgom3a8hm934ogdl1tsuvqqh2.apps.googleusercontent.com':
            return func.HttpResponse(json.dumps({"err":"unauthorized"}),status_code=401)

        if user_info["sub"] and  user_info["email_verified"] == 'true':
            # print("got user", user_info)
            try:
                key = str(user_info["sub"])
                get_user_db = user_ref.child(key).get()
                get_remaining = get_user_db["remaining"]
                user={}
                user["email"]=user_info["email"]
                user["name"]=user_info["name"]
                # get_user_db.update({'remaining':get_remaining-1})
                return func.HttpResponse(json.dumps({"is_new":0,"remaining":get_remaining,"user":user }),status_code=201)
            except:
                key = str(user_info["sub"])
                jsond = {}
                jsond[key] = {'remaining': 3, 'trial': 'true', 'name': user_info["name"], 'email': user_info["email"]}
                # print(jsond,json.dumps(jsond))
                user_ref.update(jsond)
                # user_ref.update({user_info["email"] : {'remaining': "'3'", 'trial': '"true"'}})
                # print('set')
                user={}
                user["email"]=user_info["email"]
                user["name"]=user_info["name"]
                return func.HttpResponse(json.dumps({"is_new":1,"remaining":3,"user":user }),status_code=201)
        elif user_info["email_verified"] != 'true':
            return func.HttpResponse(json.dumps({"err":"email not verified :("}),status_code=400)
        else:
            return func.HttpResponse(json.dumps({"err":"bad request buddy :("}),status_code=400)
    except:
        return func.HttpResponse(json.dumps({"err":"invalid request"}),status_code=400)

    # return func.HttpResponse(json.dumps({"err":"something not right"}),status_code=500)

