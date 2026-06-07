from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse
import qrcode
from inventory.models import Equipment, Person


class Command(BaseCommand):
    help = 'Génère des QR codes PNG pour matériels et personnes dans media/qrcodes.'

    def handle(self, *args, **options):
        out_dir = Path(settings.MEDIA_ROOT) / 'qrcodes'
        out_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for eq in Equipment.objects.all():
            payload = f"{settings.TOOLMAG_PUBLIC_BASE_URL}{reverse('user_inventory_auto', kwargs={'code': eq.code})}"
            img = qrcode.make(payload)
            img.save(out_dir / f'{eq.code}.png')
            count += 1
        for person in Person.objects.all():
            payload = f'TOOLMAG:{person.role.upper()}:{person.code}'
            img = qrcode.make(payload)
            img.save(out_dir / f'{person.code}.png')
            count += 1
        self.stdout.write(self.style.SUCCESS(f'{count} QR codes générés dans {out_dir}'))
