from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from system_manager.models import (
    EducationalSystem,
    SystemEquipment,
    SystemUser,
    TemporarySystemPermission,
)
from system_manager.permissions import can_edit_systems


@override_settings(FORCE_SCRIPT_NAME=None)
class HierarchyEquipmentTests(TestCase):
    def setUp(self):
        self.root = EducationalSystem.objects.create(
            code='SYS-ROOT',
            designation='Système principal',
        )
        self.child = EducationalSystem.objects.create(
            code='SYS-SUB',
            designation='Sous-système',
            parent_system=self.root,
        )
        self.admin = SystemUser.objects.create(
            code='ADMIN',
            username='admin',
            role_principal='admin',
            active=True,
        )
        session = self.client.session
        session['system_user_id'] = self.admin.pk
        session.save()

    def test_documentation_owner(self):
        self.assertEqual(self.child.documentation_system, self.root)

    def test_nested_child_rejected(self):
        nested = EducationalSystem(
            code='NESTED',
            designation='Niveau interdit',
            parent_system=self.child,
        )
        with self.assertRaises(ValidationError):
            nested.full_clean()

    def test_equipment_code_generation(self):
        first = SystemEquipment.objects.create(
            systeme=self.child,
            designation='Capteur',
        )
        second = SystemEquipment.objects.create(
            systeme=self.child,
            designation='Capteur',
        )
        self.assertNotEqual(first.code, second.code)

    def test_parent_permission_applies_to_child(self):
        user = SystemUser.objects.create(
            code='ELEVE',
            username='eleve',
            role_principal='eleve',
            active=True,
        )
        permission = TemporarySystemPermission.objects.create(
            user=user,
            date_debut=timezone.now() - timedelta(hours=1),
            date_fin=timezone.now() + timedelta(hours=1),
            can_edit=True,
            active=True,
        )
        permission.systems.add(self.root)
        self.assertTrue(can_edit_systems(user, self.child))

    def test_child_document_add_redirects_to_parent(self):
        # Le client Django appelle la route interne, sans le préfixe
        # public /system retiré en production par Nginx.
        response = self.client.get(
            f'/systemes/{self.child.pk}/documents/ajouter/'
        )
        self.assertRedirects(
            response,
            reverse('system_document_add', args=[self.root.pk]),
            fetch_redirect_response=False,
        )
