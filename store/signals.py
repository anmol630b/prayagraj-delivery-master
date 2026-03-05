from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, FCMToken
from .notifications import send_status_notification

@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, created, **kwargs):
    if created:
        return
    try:
        fcm = FCMToken.objects.filter(user=instance.user).last()
        if fcm:
            send_status_notification(fcm.token, instance.id, instance.status)
    except Exception as e:
        print(f"Signal error: {e}")
