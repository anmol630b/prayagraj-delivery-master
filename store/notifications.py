import firebase_admin
from firebase_admin import credentials, messaging
import os

# Firebase initialize karo
def _init_firebase():
    if not firebase_admin._apps:
        cred_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'serviceAccountKey.json')
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

def send_notification(fcm_token, title, body, data=None):
    try:
        _init_firebase()
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=fcm_token,
        )
        messaging.send(message)
        return True
    except Exception as e:
        print(f"Notification error: {e}")
        return False

def send_order_notification(user, order_id, status):
    try:
        from .models import FCMToken
        tokens = FCMToken.objects.filter(user=user)
        
        messages = {
            'pending': ('🛒 Order Mila!', f'Order #{order_id} mil gaya! Jaldi deliver karenge.'),
            'confirmed': ('✅ Order Confirm!', f'Order #{order_id} confirm ho gaya!'),
            'out_for_delivery': ('🚚 Delivery Pe Hai!', f'Order #{order_id} raaste mein hai!'),
            'delivered': ('🎉 Deliver Ho Gaya!', f'Order #{order_id} deliver ho gaya! Kaisa laga?'),
            'cancelled': ('❌ Order Cancel', f'Order #{order_id} cancel ho gaya.'),
        }
        
        title, body = messages.get(status, ('📦 Order Update', f'Order #{order_id} update hua!'))
        
        for token in tokens:
            send_notification(token.token, title, body, {'order_id': str(order_id), 'status': status})
    except Exception as e:
        print(f"Order notification error: {e}")
