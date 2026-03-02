import firebase_admin
from firebase_admin import credentials, messaging
import os
import json

if not firebase_admin._apps:
    try:
        # Railway pe environment variable se lega
        firebase_creds = os.environ.get('FIREBASE_CREDENTIALS')
        if firebase_creds:
            cred_dict = json.loads(firebase_creds)
            cred = credentials.Certificate(cred_dict)
        else:
            # Local development mein file se lega
            cred = credentials.Certificate(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'serviceAccountKey.json')
            )
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase init error: {e}")

def send_order_notification(fcm_token, title, body):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=fcm_token,
        )
        response = messaging.send(message)
        print("Notification sent:", response)
        return True
    except Exception as e:
        print("Notification error:", e)
        return False