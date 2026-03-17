from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def websocket_push(user_id, event_type, message="", count=None, data=None):
    """
    Generic single-channel websocket push.

    event_type:
        notification
        activity_joined
        activity_updated
        qr_checked_in
        dashboard_refresh
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "websocket_event",   # consumer method name
            "event_type": event_type,    # frontend discriminator
            "message": message,
            "count": count,
            "data": data or {},
        }
    )

def push_activity_utilization(user_id, activity):
    current_participants = activity.participations.filter(
        status__in=["joined", "checked_in"]
    ).count()

    max_capacity = activity.max_capacity or 0
    utilization_percent = 0

    if max_capacity > 0:
        utilization_percent = round((current_participants / max_capacity) * 100)

    websocket_push(
        user_id=user_id,
        event_type="dashboard_utilization",
        data={
            "activity_id": activity.id,
            "current_participants": current_participants,
            "max_capacity": max_capacity,
            "utilization_percent": utilization_percent,
        }
    )