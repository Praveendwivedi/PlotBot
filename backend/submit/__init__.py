import requests as urlrequests
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from pathlib import Path
import openai
from dotenv import load_dotenv

import logging

import azure.functions as func

load_dotenv()

openai.api_key = os.get_env("OPENAI_API_KEY")

try:
    cred = credentials.Certificate(Path(__file__).parent/"serviceAccountKey.json")

    app=firebase_admin.initialize_app(cred,{
        'databaseURL': os.get_env("DATABASE_URL")
    })
except:
    logging.info('error')
    app = firebase_admin.get_app()
    
    # print('c',user_ref.child('praveen98ok@gmail.com'))
ref = db.reference()
user_ref = ref.child('Users')
# logging.info(f"{app.name},{ref.child('Users').get()}")

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    text = req.params.get('text')
    if not text:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"err":"no text found"}),
                status_code=400
            )
        else:
            text = req_body.get('text')
            # return func.HttpResponse(
            #     json.dumps({"user_inf":t}),
            #     status_code=200
            # )
    text=text.strip()
    if text == '':
        return func.HttpResponse(
                json.dumps({"err":"no text found"}),
                status_code=400
            )
    # return func.HttpResponse(
    #             json.dumps({"user_info":t}),
    #             status_code=200
    #         )
    
    try:
        token = req.headers.get('Authorization')
        # logging.info(f"Header {token}")

        r = urlrequests.get("https://oauth2.googleapis.com/tokeninfo",{"id_token":token})
        user_info = r.json()
        
        if "error" in user_info:
            return func.HttpResponse(
                json.dumps(user_info),
                status_code=400
            )

        #check if application is plotbot or not
        if user_info["aud"] != '371694754584-23efcgomgom3a8hm934ogdl1tsuvqqh2.apps.googleusercontent.com':
            return func.HttpResponse(json.dumps({"err":"unauthorized"}),status_code=401)

        if user_info["sub"] and  user_info["email_verified"] == 'true':
            # print("got user", user_info)
            try:
                key = str(user_info["sub"])
                get_user_db = user_ref.child(key).get()
                get_remaining = get_user_db["remaining"]
                if get_remaining == 0:
                    return func.HttpResponse(json.dumps({"err":"maximum limit reached :("}),status_code=401)

                user_ref.child(key).update({'remaining':get_remaining-1})

                logging.info(f"calling completion text:{text}\nuser: {user_info}")

                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", 
                    messages = [{"role": "system", "content" : "you are html code generator bot."},
                                {"role": "user", "content" : text + "\ngenerate only html code using d3.js library"}]
                )
                logging.info(f"completion {completion}")
                
                try:
                    response_text = completion["choices"]
                    # logging.info(f"response_text0 {response_text}")
                    response_text = response_text[0]
                    # logging.info(f"response_text1 {response_text}")
                    response_text = response_text["message"]["content"]
                    # logging.info(f"response_text2 {response_text}")

                    response_text = response_text.split("```")
                    try:
                        if "html" in response_text[1][:4]:
                            response = response_text[1][4:]
                        else:
                            response = response_text[1]
                    except:
                        return func.HttpResponse(json.dumps({"err":"invalid request"}),status_code=400)
                except:
                    return func.HttpResponse(json.dumps({"err":"something went wrong"}),status_code=400)
                
                return func.HttpResponse(json.dumps({"remaining":get_remaining-1, "response": response}),status_code=201)

            except:
                return func.HttpResponse(json.dumps({"err":"unauthorized/invalid"}),status_code=401)
        elif user_info["email_verified"] != 'true':
            return func.HttpResponse(json.dumps({"err":"email not verified :("}),status_code=400)
        else:
            return func.HttpResponse(json.dumps({"err":"bad request buddy :("}),status_code=400)
    except:
        return func.HttpResponse(json.dumps({"err":"invalid request"}),status_code=400)

