import firebase_admin
from firebase_admin import credentials, messaging
import os

if not firebase_admin._apps:
    cred = credentials.Certificate(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'serviceAccountKey.json')
    )
    firebase_admin.initialize_app(cred)

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