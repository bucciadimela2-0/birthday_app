from datetime import date as date_cls

from django.core.management.base import BaseCommand, CommandError

from employees.services import send_birthday_newsletter


class Command(BaseCommand):
    help = "Invia la newsletter compleanni per una data (default: oggi)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            type=str,
            default=None,
            help="Data da simulare in formato YYYY-MM-DD (default: oggi).",
        )

    def handle(self, *args, **options):
        raw = options["date"]
        target_date = None
        if raw:
            try:
                target_date = date_cls.fromisoformat(raw)
            except ValueError:
                raise CommandError(f"Data non valida: {raw!r}. Usa YYYY-MM-DD.")

        summary = send_birthday_newsletter(target_date)

        self.stdout.write(self.style.SUCCESS("Newsletter elaborata."))
        self.stdout.write(f"  Data:                {summary['date']}")
        self.stdout.write(f"  Festeggiati:         {summary['celebrants']}")
        self.stdout.write(f"  Mail di auguri:      {summary['birthday_emails']}")
        self.stdout.write(f"  Notifiche ai team:   {summary['team_notifications']}")