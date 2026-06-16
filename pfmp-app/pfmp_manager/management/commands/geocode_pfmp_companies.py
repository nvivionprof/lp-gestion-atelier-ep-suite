import csv
import json
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from pfmp_manager.models import Company, CompanyContact


GEOCODING_OK = 'OK'
GEOCODING_PENDING = 'A_GEOCODER'
GEOCODING_AMBIGUOUS = 'AMBIGU'
GEOCODING_FAILED = 'ECHEC'
GEOCODING_MANUAL = 'MANUEL'


def _decimal(value):
    try:
        return Decimal(str(value)).quantize(Decimal('0.000001'))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _clean_parts(*parts):
    return ' '.join(str(p or '').strip() for p in parts if str(p or '').strip())


def _company_query(company):
    # full_address contient déjà l'adresse complète lorsqu'elle vient de l'import.
    # Ne pas le concaténer avec address + CP + ville, sinon Nominatim reçoit une requête doublée.
    if company.full_address:
        return _clean_parts(company.full_address)

    return _clean_parts(
        company.address,
        company.postal_code,
        company.city,
        company.country or 'France',
    )


def _contact_query(contact):
    return _clean_parts(
        contact.personal_address,
        contact.personal_postal_code,
        contact.personal_city,
        'France',
    )


def _osm_url(query):
    return 'https://www.openstreetmap.org/search?' + urlencode({'query': query})


class Command(BaseCommand):
    help = 'Géocode les entreprises PFMP sans coordonnées GPS et, en option, les adresses personnelles de contacts autorisées pour la proximité.'

    def add_arguments(self, parser):
        parser.add_argument('--missing-only', action='store_true', help='Traiter seulement les entreprises sans latitude/longitude.')
        parser.add_argument('--retry-failed', action='store_true', help='Retraiter seulement les entreprises en statut ECHEC ou AMBIGU.')
        parser.add_argument('--force', action='store_true', help='Recalculer même si des coordonnées existent déjà.')
        parser.add_argument('--include-contacts', action='store_true', help='Géocoder aussi les contacts autorisés comme point de proximité élève.')
        parser.add_argument('--limit', type=int, default=0, help='Limiter le nombre d’éléments traités.')
        parser.add_argument('--delay', type=float, default=1.1, help='Temporisation entre deux appels au géocodeur, en secondes.')
        parser.add_argument('--timeout', type=float, default=8.0, help='Timeout HTTP du géocodeur, en secondes.')
        parser.add_argument('--dry-run', action='store_true', help='Simulation sans écriture en base.')
        parser.add_argument('--report', default='', help='Chemin CSV du rapport de géocodage.')
        parser.add_argument('--provider-url', default='https://nominatim.openstreetmap.org/search', help='URL du service de géocodage compatible Nominatim.')
        parser.add_argument('--user-agent', default='LP-Gestion-Atelier-PFMP-Manager/RC19', help='User-Agent transmis au service de géocodage.')

    def _fetch(self, query, *, provider_url, timeout, user_agent):
        params = urlencode({'q': query, 'format': 'json', 'limit': 3, 'addressdetails': 0})
        url = provider_url + ('&' if '?' in provider_url else '?') + params
        req = Request(url, headers={'User-Agent': user_agent, 'Accept': 'application/json'})
        try:
            with urlopen(req, timeout=timeout) as response:
                raw = response.read().decode('utf-8')
                return json.loads(raw), ''
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            return [], str(exc)

    def _result_to_row(self, kind, obj, query, status, message='', lat='', lon=''):
        return {
            'type': kind,
            'id': obj.pk,
            'nom': getattr(obj, 'name', None) or getattr(obj, 'full_name', ''),
            'ville': getattr(obj, 'city', None) or getattr(obj, 'personal_city', ''),
            'requete': query,
            'statut': status,
            'latitude': lat,
            'longitude': lon,
            'message': message,
        }

    def _write_report(self, path, rows):
        if not path:
            return
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['type', 'id', 'nom', 'ville', 'requete', 'statut', 'latitude', 'longitude', 'message'], delimiter=';')
            writer.writeheader()
            writer.writerows(rows)

    def _mark_company_failed(self, company, query, message, options):
        if not options['dry_run']:
            company.geocoding_status = GEOCODING_FAILED
            company.osm_search_url = _osm_url(query)
            if not company.full_address:
                company.full_address = query[:360]
            company.save(update_fields=['geocoding_status', 'osm_search_url', 'full_address', 'updated_at'])
        return self._result_to_row('entreprise', company, query, GEOCODING_FAILED, message)

    def _geocode_company(self, company, options):
        query = _company_query(company)
        if not query:
            return self._mark_company_failed(company, query, 'Adresse absente', options)

        data, err = self._fetch(query, provider_url=options['provider_url'], timeout=options['timeout'], user_agent=options['user_agent'])
        if err:
            return self._mark_company_failed(company, query, err, options)
        if not data:
            return self._mark_company_failed(company, query, 'Aucun résultat', options)

        first = data[0]
        lat = _decimal(first.get('lat'))
        lon = _decimal(first.get('lon'))
        if lat is None or lon is None:
            return self._result_to_row('entreprise', company, query, GEOCODING_FAILED, 'Coordonnées invalides')

        status = GEOCODING_AMBIGUOUS if len(data) > 1 else GEOCODING_OK
        if not options['dry_run']:
            company.latitude = lat
            company.longitude = lon
            company.geocoding_status = status
            company.osm_search_url = _osm_url(query)
            if not company.full_address:
                company.full_address = query[:360]
            company.save(update_fields=['latitude', 'longitude', 'geocoding_status', 'osm_search_url', 'full_address', 'updated_at'])
        return self._result_to_row('entreprise', company, query, status, first.get('display_name', ''), str(lat), str(lon))

    def _geocode_contact(self, contact, options):
        query = _contact_query(contact)
        if not query:
            return self._result_to_row('contact', contact, query, GEOCODING_FAILED, 'Adresse personnelle absente')

        data, err = self._fetch(query, provider_url=options['provider_url'], timeout=options['timeout'], user_agent=options['user_agent'])
        if err:
            return self._result_to_row('contact', contact, query, GEOCODING_FAILED, err)
        if not data:
            return self._result_to_row('contact', contact, query, GEOCODING_FAILED, 'Aucun résultat')

        first = data[0]
        lat = _decimal(first.get('lat'))
        lon = _decimal(first.get('lon'))
        if lat is None or lon is None:
            return self._result_to_row('contact', contact, query, GEOCODING_FAILED, 'Coordonnées invalides')

        status = GEOCODING_AMBIGUOUS if len(data) > 1 else GEOCODING_OK
        if not options['dry_run']:
            contact.personal_latitude = lat
            contact.personal_longitude = lon
            contact.save(update_fields=['personal_latitude', 'personal_longitude'])
        return self._result_to_row('contact', contact, query, status, first.get('display_name', ''), str(lat), str(lon))

    def handle(self, *args, **options):
        rows = []
        company_qs = Company.objects.exclude(status='inactive').order_by('name')

        if options['force']:
            pass
        elif options['retry_failed']:
            company_qs = company_qs.filter(geocoding_status__in=[GEOCODING_FAILED, GEOCODING_AMBIGUOUS])
        elif options['missing_only']:
            company_qs = company_qs.filter(
                Q(geocoding_status='') |
                Q(geocoding_status=GEOCODING_PENDING) |
                ((Q(latitude__isnull=True) | Q(longitude__isnull=True)) & ~Q(geocoding_status=GEOCODING_FAILED))
            )
        else:
            company_qs = company_qs.filter(
                Q(geocoding_status=GEOCODING_PENDING) |
                ((Q(latitude__isnull=True) | Q(longitude__isnull=True)) & ~Q(geocoding_status=GEOCODING_FAILED))
            )

        if options['limit'] and options['limit'] > 0:
            company_qs = company_qs[:options['limit']]

        processed = ok = ambiguous = failed = 0
        total = company_qs.count() if hasattr(company_qs, 'count') else len(company_qs)
        self.stdout.write(f'Entreprises à géocoder : {total}')

        for company in company_qs:
            if company.latitude and company.longitude and not options['force'] and options['missing_only']:
                continue
            row = self._geocode_company(company, options)
            rows.append(row)
            processed += 1
            ok += 1 if row['statut'] == GEOCODING_OK else 0
            ambiguous += 1 if row['statut'] == GEOCODING_AMBIGUOUS else 0
            failed += 1 if row['statut'] == GEOCODING_FAILED else 0
            self.stdout.write(f"{row['statut']} — {company.name} — {row['latitude']} {row['longitude']} — {row['message']}")
            if options['delay'] > 0:
                time.sleep(options['delay'])

        contact_processed = 0
        if options['include_contacts']:
            contact_qs = CompanyContact.objects.filter(active=True, use_personal_location_for_student_search=True).order_by('company__name', 'full_name')
            if not options['force']:
                contact_qs = contact_qs.filter(Q(personal_latitude__isnull=True) | Q(personal_longitude__isnull=True))
            if options['limit'] and options['limit'] > 0:
                contact_qs = contact_qs[:options['limit']]
            self.stdout.write(f'Contacts à géocoder : {contact_qs.count() if hasattr(contact_qs, "count") else len(contact_qs)}')
            for contact in contact_qs:
                row = self._geocode_contact(contact, options)
                rows.append(row)
                contact_processed += 1
                self.stdout.write(f"{row['statut']} — contact {contact.full_name} — {row['latitude']} {row['longitude']}")
                if options['delay'] > 0:
                    time.sleep(options['delay'])

        self._write_report(options['report'], rows)
        self.stdout.write('--- Synthèse géocodage PFMP ---')
        self.stdout.write(f'Entreprises traitées : {processed}')
        self.stdout.write(f'OK : {ok}')
        self.stdout.write(f'Ambiguës : {ambiguous}')
        self.stdout.write(f'Échecs : {failed}')
        self.stdout.write(f'Contacts traités : {contact_processed}')
        if options['dry_run']:
            self.stdout.write('Mode simulation : aucune écriture en base.')
        if options['report']:
            self.stdout.write(f"Rapport CSV : {options['report']}")
