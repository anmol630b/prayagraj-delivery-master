import requests
import os

def send_order_notification(fcm_token, title, body):
    try:
        server_key = os.environ.get('FCM_SERVER_KEY', '')
        if not server_key:
            print("FCM_SERVER_KEY not set!")
            return
        
        headers = {
            'Authorization': f'key={server_key}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'to': fcm_token,
            'notification': {
                'title': title,
                'body': body,
                'sound': 'default',
                'badge': '1',
            },
            'data': {
                'title': title,
                'body': body,
                'click_action': 'FLUTTER_NOTIFICATION_CLICK',
            }
        }
        
        response = requests.post(
            'https://fcm.googleapis.com/fcm/send',
            json=payload,
            headers=headers
        )
        print(f"FCM Response: {response.status_code} - {response.text}")
        return response.json()
    except Exception as e:
        print(f"Notification error: {e}")

def send_status_notification(fcm_token, order_id, status):
    messages = {
        'confirmed': ('Order Confirmed! ✅', f'Order #{order_id} has been confirmed!'),
        'out_for_delivery': ('Out for Delivery! 🚴', f'Order #{order_id} is on the way!'),
        'delivered': ('Order Delivered! 🎉', f'Order #{order_id} has been delivered!'),
        'cancelled': ('Order Cancelled ❌', f'Order #{order_id} has been cancelled.'),
    }
    if status in messages:
        title, body = messages[status]
        send_order_notification(fcm_token, title, body)
