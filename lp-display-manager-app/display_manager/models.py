import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


def make_token(length=32):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def make_code(length=8):
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    raw = ''.join(secrets.choice(alphabet) for _ in range(length))
    return f'{raw[:4]}-{raw[4:]}'


class DisplayLayout(models.Model):
    COLUMN_RIGHT = 'right'
    COLUMN_LEFT = 'left'
    COLUMN_CHOICES = [
        (COLUMN_RIGHT, 'Miniatures à droite'),
        (COLUMN_LEFT, 'Miniatures à gauche'),
    ]

    name = models.CharField('Nom', max_length=150)
    description = models.TextField('Description', blank=True)
    column_position = models.CharField('Position colonne', max_length=10, choices=COLUMN_CHOICES, default=COLUMN_RIGHT)
    target_width = models.PositiveIntegerField('Largeur cible', default=1920)
    target_height = models.PositiveIntegerField('Hauteur cible', default=1080)
    is_active = models.BooleanField('Actif', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Layout'
        verbose_name_plural = 'Layouts'

    def __str__(self):
        return self.name

    def ensure_default_zones(self):
        defaults = [('main', 0), ('thumb1', 1), ('thumb2', 2), ('thumb3', 3)]
        for name, order in defaults:
            DisplayZone.objects.get_or_create(layout=self, name=name, defaults={'order': order})

    def duplicate(self):
        original = self
        copy = DisplayLayout.objects.create(
            name=f'{original.name} - copie',
            description=original.description,
            column_position=original.column_position,
            target_width=original.target_width,
            target_height=original.target_height,
            is_active=original.is_active,
        )
        for zone in original.zones.all():
            new_zone = DisplayZone.objects.create(layout=copy, name=zone.name, order=zone.order)
            for item in zone.items.all():
                DisplayZoneItem.objects.create(
                    zone=new_zone,
                    media=item.media,
                    order=item.order,
                    duration_seconds=item.duration_seconds,
                    is_active=item.is_active,
                )
        return copy


class DisplayZone(models.Model):
    ZONE_MAIN = 'main'
    ZONE_THUMB1 = 'thumb1'
    ZONE_THUMB2 = 'thumb2'
    ZONE_THUMB3 = 'thumb3'
    ZONE_CHOICES = [
        (ZONE_MAIN, 'Zone centrale'),
        (ZONE_THUMB1, 'Miniature 1'),
        (ZONE_THUMB2, 'Miniature 2'),
        (ZONE_THUMB3, 'Miniature 3'),
    ]

    layout = models.ForeignKey(DisplayLayout, related_name='zones', on_delete=models.CASCADE)
    name = models.CharField('Zone', max_length=20, choices=ZONE_CHOICES)
    order = models.PositiveIntegerField('Ordre', default=0)

    class Meta:
        ordering = ['order', 'name']
        unique_together = [('layout', 'name')]
        verbose_name = 'Zone'
        verbose_name_plural = 'Zones'

    def __str__(self):
        return f'{self.layout} / {self.get_name_display()}'


class DisplayMedia(models.Model):
    TYPE_IMAGE = 'image'
    TYPE_WEB = 'web'
    TYPE_CHOICES = [
        (TYPE_IMAGE, 'Image'),
        (TYPE_WEB, 'Page web'),
    ]

    name = models.CharField('Nom', max_length=150)
    media_type = models.CharField('Type', max_length=20, choices=TYPE_CHOICES)
    image = models.ImageField('Image', upload_to='display/images/', blank=True, null=True)
    web_url = models.URLField('URL web', blank=True)
    default_duration_seconds = models.PositiveIntegerField('Durée par défaut', default=15)
    is_active = models.BooleanField('Actif', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Média'
        verbose_name_plural = 'Médias'

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.media_type == self.TYPE_IMAGE and not self.image:
            raise ValidationError('Une image doit être fournie pour un média de type image.')
        if self.media_type == self.TYPE_WEB and not self.web_url:
            raise ValidationError('Une URL doit être fournie pour un média de type page web.')


class DisplayZoneItem(models.Model):
    zone = models.ForeignKey(DisplayZone, related_name='items', on_delete=models.CASCADE)
    media = models.ForeignKey(DisplayMedia, related_name='zone_items', on_delete=models.CASCADE)
    order = models.PositiveIntegerField('Ordre', default=0)
    duration_seconds = models.PositiveIntegerField('Durée', default=15)
    is_active = models.BooleanField('Actif', default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Élément de zone'
        verbose_name_plural = 'Éléments de zone'

    def __str__(self):
        return f'{self.zone} → {self.media}'


class DisplayScreen(models.Model):
    STATUS_ONLINE = 'online'
    STATUS_OFFLINE = 'offline'
    STATUS_UNKNOWN = 'unknown'
    STATUS_CHOICES = [
        (STATUS_ONLINE, 'En ligne'),
        (STATUS_OFFLINE, 'Hors ligne'),
        (STATUS_UNKNOWN, 'Inconnu'),
    ]

    name = models.CharField('Nom', max_length=150)
    location = models.CharField('Lieu', max_length=150, blank=True)
    association_code = models.CharField('Code association', max_length=16, unique=True, default=make_code)
    player_token = models.CharField('Token player', max_length=64, unique=True, default=make_token)
    active_layout = models.ForeignKey(DisplayLayout, related_name='screens', blank=True, null=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField('Adresse IP', blank=True, null=True)
    last_contact = models.DateTimeField('Dernier contact', blank=True, null=True)
    status = models.CharField('Statut', max_length=20, choices=STATUS_CHOICES, default=STATUS_UNKNOWN)
    agent_version = models.CharField('Version agent', max_length=50, blank=True)
    is_active = models.BooleanField('Actif', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Écran'
        verbose_name_plural = 'Écrans'

    def __str__(self):
        return self.name

    def compute_status(self):
        if not self.last_contact:
            return self.STATUS_UNKNOWN
        delta = timezone.now() - self.last_contact
        if delta <= timedelta(seconds=getattr(settings, 'LPDISPLAY_OFFLINE_SECONDS', 90)):
            return self.STATUS_ONLINE
        return self.STATUS_OFFLINE

    def touch(self, ip=None, agent_version=''):
        self.last_contact = timezone.now()
        if ip:
            self.ip_address = ip
        if agent_version:
            self.agent_version = agent_version
        self.status = self.STATUS_ONLINE
        self.save(update_fields=['last_contact', 'ip_address', 'agent_version', 'status'])

    def get_player_url(self):
        return reverse('display_manager:player', args=[self.player_token])


class DisplayCommand(models.Model):
    ACTION_FREEZE = 'freeze'
    ACTION_RESUME = 'resume'
    ACTION_RELOAD = 'reload'
    ACTION_CHOICES = [
        (ACTION_FREEZE, 'Figer'),
        (ACTION_RESUME, 'Reprendre'),
        (ACTION_RELOAD, 'Recharger'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_DONE = 'done'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente'),
        (STATUS_SENT, 'Envoyée'),
        (STATUS_DONE, 'Terminée'),
        (STATUS_FAILED, 'Échec'),
    ]

    screen = models.ForeignKey(DisplayScreen, related_name='commands', on_delete=models.CASCADE)
    action = models.CharField('Action', max_length=30, choices=ACTION_CHOICES)
    payload = models.JSONField('Payload', default=dict, blank=True)
    status = models.CharField('Statut', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    result = models.TextField('Résultat', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    executed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Commande player'
        verbose_name_plural = 'Commandes player'

    def __str__(self):
        return f'{self.screen} / {self.action} / {self.status}'


class DisplayQRCodeAction(models.Model):
    QR_FREEZE = 'freeze'
    QR_RESUME = 'resume'
    QR_CHOICES = [
        (QR_FREEZE, 'Figer l’affichage'),
        (QR_RESUME, 'Reprendre l’affichage'),
    ]

    name = models.CharField('Nom', max_length=150)
    token = models.CharField('Token QR', max_length=64, unique=True, default=make_token)
    action = models.CharField('Action', max_length=30, choices=QR_CHOICES)
    target_screen = models.ForeignKey(DisplayScreen, related_name='qr_actions', on_delete=models.CASCADE)
    target_zone = models.CharField('Zone cible', max_length=20, default='all')
    duration_seconds = models.PositiveIntegerField('Durée', default=60)
    is_active = models.BooleanField('Actif', default=True)
    expires_at = models.DateTimeField('Expiration', blank=True, null=True)
    use_count = models.PositiveIntegerField('Utilisations', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'QR action'
        verbose_name_plural = 'QR actions'

    def __str__(self):
        return self.name

    def is_available(self):
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() >= self.expires_at:
            return False
        return True

    def qr_url(self):
        return reverse('display_manager:qr_execute', args=[self.token])
