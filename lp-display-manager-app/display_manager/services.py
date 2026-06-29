from django.utils import timezone

from .models import DisplayCommand, DisplayQRCodeAction


def build_manifest(screen, request=None):
    layout = screen.active_layout
    if not layout:
        return {
            'screen': {'name': screen.name, 'token': screen.player_token},
            'layout': None,
            'zones': {},
        }

    zones = {}
    for zone in layout.zones.prefetch_related('items__media').all():
        zone_items = []
        for item in zone.items.filter(is_active=True, media__is_active=True).order_by('order', 'id'):
            media = item.media
            payload = {
                'id': media.id,
                'name': media.name,
                'type': media.media_type,
                'duration': item.duration_seconds or media.default_duration_seconds,
            }
            if media.media_type == 'image' and media.image:
                url = media.image.url
                payload['url'] = request.build_absolute_uri(url) if request else url
            elif media.media_type == 'web':
                payload['url'] = media.web_url
            zone_items.append(payload)
        zones[zone.name] = zone_items

    return {
        'screen': {'name': screen.name, 'token': screen.player_token},
        'layout': {
            'id': layout.id,
            'name': layout.name,
            'column_position': layout.column_position,
            'target_width': layout.target_width,
            'target_height': layout.target_height,
        },
        'zones': zones,
        'generated_at': timezone.now().isoformat(),
    }


def execute_qr_action(qr_action: DisplayQRCodeAction):
    if not qr_action.is_available():
        return None

    payload = {'target': qr_action.target_zone or 'all'}
    if qr_action.action == DisplayQRCodeAction.QR_FREEZE:
        payload['duration'] = qr_action.duration_seconds
        action = DisplayCommand.ACTION_FREEZE
    elif qr_action.action == DisplayQRCodeAction.QR_RESUME:
        action = DisplayCommand.ACTION_RESUME
    else:
        action = qr_action.action

    command = DisplayCommand.objects.create(
        screen=qr_action.target_screen,
        action=action,
        payload=payload,
    )
    qr_action.use_count += 1
    qr_action.save(update_fields=['use_count'])
    return command
