from django.core.management.base import BaseCommand
from pfmp_manager.sync import sync_users_from_lp_core, sync_formations_from_lp_core
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--force-password', action='store_true')
        parser.add_argument('--core-user-id')
    def handle(self,*args,**opts):
        f=sync_formations_from_lp_core(); u=sync_users_from_lp_core(force_password=opts['force_password'], core_user_id=opts.get('core_user_id'))
        self.stdout.write(f"Formations {f}; utilisateurs {u}")
