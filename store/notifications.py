import firebase_admin
from firebase_admin import credentials, messaging
import os
import json

_initialized = False

def _init_firebase():
    global _initialized
    if not _initialized:
        try:
            cred_json = os.environ.get('FIREBASE_CREDENTIALS')
            if cred_json:
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
            else:
                cred_path = os.path.join(os.path.dirname(__file__), 'firebase-credentials.json')
                cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _initialized = True
        except Exception as e:
            print(f"Firebase init error: {e}")

def send_order_notification(fcm_token, title, body):
    try:
        _init_firebase()
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={'title': title, 'body': body},
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(sound='default'),
            ),
            token=fcm_token,
        )
        response = messaging.send(message)
        print(f"Notification sent: {response}")
        return response
    except Exception as e:
        print(f"Notification error: {e}")

def send_status_notification(fcm_token, order_id, status):
    messages = {
        'confirmed': ('Order Confirmed! ✅', f'Your order #{order_id} has been confirmed!'),
        'out_for_delivery': ('Out for Delivery! 🚴', f'Your order #{order_id} is on the way!'),
        'delivered': ('Order Delivered! 🎉', f'Your order #{order_id} has been delivered!'),
        'cancelled': ('Order Cancelled ❌', f'Your order #{order_id} has been cancelled.'),
    }
    if status in messages:
        title, body = messages[status]
        send_order_notification(fcm_token, title, body)
