from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from system_manager.forms import EducationalSystemForm
from system_manager.models import (
    DocumentCategory,
    EducationalSystem,
    SystemDocument,
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
        self.grandchild = EducationalSystem.objects.create(
            code='SYS-SUB-02',
            designation='Sous-système niveau 2',
            parent_system=self.child,
        )
        self.sibling = EducationalSystem.objects.create(
            code='SYS-SIBLING',
            designation='Système frère',
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

    def test_recursive_hierarchy_is_allowed(self):
        self.assertEqual(self.grandchild.parent_system, self.child)
        self.assertEqual(
            [system.pk for system in self.grandchild.get_ancestor_chain(include_self=True)],
            [self.root.pk, self.child.pk, self.grandchild.pk],
        )

    def test_cycle_is_rejected(self):
        self.root.parent_system = self.grandchild
        with self.assertRaises(ValidationError):
            self.root.full_clean()

    def test_parent_form_excludes_self_and_descendants(self):
        form = EducationalSystemForm(instance=self.child)
        parent_ids = set(form.fields['parent_system'].queryset.values_list('pk', flat=True))
        self.assertIn(self.root.pk, parent_ids)
        self.assertNotIn(self.child.pk, parent_ids)
        self.assertNotIn(self.grandchild.pk, parent_ids)

    def test_equipment_code_generation(self):
        first = SystemEquipment.objects.create(
            systeme=self.grandchild,
            designation='Capteur',
        )
        second = SystemEquipment.objects.create(
            systeme=self.grandchild,
            designation='Capteur',
        )
        self.assertNotEqual(first.code, second.code)

    def test_parent_permission_applies_to_all_descendants(self):
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
        self.assertTrue(can_edit_systems(user, self.grandchild))

    def test_child_document_is_saved_locally(self):
        response = self.client.post(
            f'/systemes/{self.child.pk}/documents/ajouter/',
            {
                'titre': 'Document local enfant',
                'type_document': 'lien',
                'url': 'https://example.com/document-enfant',
                'visible_students': 'on',
                'actif': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        document = SystemDocument.objects.get(titre='Document local enfant')
        self.assertEqual(document.systeme, self.child)

    def test_descendant_sees_ancestors_and_local_not_sibling(self):
        category = (
            DocumentCategory.objects.filter(
                active=True,
                parent__isnull=True,
                section_code='03',
            )
            .order_by('ordre', 'code')
            .first()
        )
        if category is None:
            category = DocumentCategory.objects.create(
                code='TEST_DOCS',
                nom='Documents de test',
                section_code='03',
                ordre=1,
                active=True,
            )

        SystemDocument.objects.create(
            systeme=self.root,
            categorie=category,
            titre='Document racine visible',
            type_document='lien',
            url='https://example.com/root',
        )
        SystemDocument.objects.create(
            systeme=self.child,
            categorie=category,
            titre='Document parent visible',
            type_document='lien',
            url='https://example.com/child',
        )
        SystemDocument.objects.create(
            systeme=self.grandchild,
            categorie=category,
            titre='Document local visible',
            type_document='lien',
            url='https://example.com/grandchild',
        )
        SystemDocument.objects.create(
            systeme=self.sibling,
            categorie=category,
            titre='Document frère invisible',
            type_document='lien',
            url='https://example.com/sibling',
        )

        response = self.client.get(
            f'/systemes/{self.grandchild.pk}/'
        )
        self.assertEqual(response.status_code, 200)

        section = next(
            row
            for row in response.context['docs_sections']
            if (
                row[0].pk == category.pk
                or any(
                    child_category.pk == category.pk
                    for child_category, *_ in row[1]
                )
            )
        )

        context_titles = {
            document.titre
            for _cat, documents, _has_docs in section[1]
            for document in documents
        }
        context_titles.update(
            document.titre for document in section[2]
        )

        self.assertIn('Document racine visible', context_titles)
        self.assertIn('Document parent visible', context_titles)
        self.assertIn('Document local visible', context_titles)
        self.assertNotIn('Document frère invisible', context_titles)
        self.assertTrue(section[3])

        self.assertContains(response, 'Document racine visible')
        self.assertContains(response, 'Document parent visible')
        self.assertContains(response, 'Document local visible')
        self.assertNotContains(response, 'Document frère invisible')
