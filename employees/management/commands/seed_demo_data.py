
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from employees.models import (
    Location, Team, Employee, Absence, EmailSettings, NewsletterLog,
)


class Command(BaseCommand):
    help = "Popola il database con dati di esempio per la demo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Svuota i dati esistenti prima di inserire i nuovi.",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Svuoto i dati esistenti...")
            NewsletterLog.objects.all().delete()
            Absence.objects.all().delete()
            Employee.objects.all().delete()
            Team.objects.all().delete()
            Location.objects.all().delete()

        today = timezone.localdate()

        def born_years_ago(years):
            """Data di nascita che cade OGGI, `years` anni fa.
            Gestisce il 29/02: se oggi non esiste in quell'anno, ripiega."""
            try:
                return today.replace(year=today.year - years)
            except ValueError:
                return today.replace(year=today.year - years, day=28)

        # -- Sedi --
        milano = Location.objects.create(name="Milano", timezone="Europe/Rome")
        tokyo = Location.objects.create(name="Tokyo", timezone="Asia/Tokyo")
        ny = Location.objects.create(name="New York", timezone="America/New_York")

        # -- Team --
        eng = Team.objects.create(name="Engineering", location=milano)
        sales = Team.objects.create(name="Sales", location=milano)
        design = Team.objects.create(name="Design", location=milano)
        ops = Team.objects.create(name="Operations", location=tokyo)
        support = Team.objects.create(name="Support", location=ny)
        finance = Team.objects.create(name="Finance", location=ny)

        E = Employee.Role.EMPLOYEE
        M = Employee.Role.MANAGER
        X = Employee.Role.EXECUTIVE

        employees = [
            # Engineering: 2 festeggiano OGGI
            Employee(first_name="Lucia", last_name="Bianchi", email="lucia@example.com",
                     date_of_birth=born_years_ago(34), team=eng, role=M),
            Employee(first_name="Mario", last_name="Rossi", email="mario@example.com",
                     date_of_birth=born_years_ago(29), team=eng, role=E),
            Employee(first_name="Anna", last_name="Verdi", email="anna@example.com",
                     date_of_birth=date(1995, 7, 10), team=eng, role=E),
            Employee(first_name="Paolo", last_name="Neri", email="paolo@example.com",
                     date_of_birth=date(1988, 11, 3), team=eng, role=E),
            Employee(first_name="Elena", last_name="Fontana", email="elena@example.com",
                     date_of_birth=date(1993, 3, 27), team=eng, role=E),
            Employee(first_name="Marco", last_name="Inattivo", email="marco@example.com",
                     date_of_birth=date(1991, 1, 1), team=eng, role=E, is_active=False),

            # Sales: include il caso 29/02
            Employee(first_name="Giada", last_name="Leap", email="giada@example.com",
                     date_of_birth=date(1992, 2, 29), team=sales, role=E),
            Employee(first_name="Sara", last_name="Conti", email="sara@example.com",
                     date_of_birth=date(1990, 5, 21), team=sales, role=M),
            Employee(first_name="Luca", last_name="Moretti", email="luca@example.com",
                     date_of_birth=date(1987, 8, 8), team=sales, role=E),
            Employee(first_name="Chiara", last_name="Galli", email="chiara@example.com",
                     date_of_birth=date(1996, 12, 1), team=sales, role=E),

            # Design: un festeggiato OGGI, da solo nel team
            Employee(first_name="Davide", last_name="Sole", email="davide@example.com",
                     date_of_birth=born_years_ago(40), team=design, role=M),

            # Operations (Tokyo)
            Employee(first_name="Kenji", last_name="Tanaka", email="kenji@example.com",
                     date_of_birth=date(1985, 9, 14), team=ops, role=X),
            Employee(first_name="Yuki", last_name="Sato", email="yuki@example.com",
                     date_of_birth=date(1994, 4, 2), team=ops, role=E),
            Employee(first_name="Haru", last_name="Ito", email="haru@example.com",
                     date_of_birth=date(1991, 6, 18), team=ops, role=E),

            # Support (New York)
            Employee(first_name="John", last_name="Smith", email="john@example.com",
                     date_of_birth=date(1989, 10, 30), team=support, role=M),
            Employee(first_name="Emily", last_name="Davis", email="emily@example.com",
                     date_of_birth=date(1997, 2, 14), team=support, role=E),

            # Finance (New York): un festeggiato OGGI + un collega
            Employee(first_name="Robert", last_name="Brown", email="robert@example.com",
                     date_of_birth=born_years_ago(45), team=finance, role=X),
            Employee(first_name="Olivia", last_name="Wilson", email="olivia@example.com",
                     date_of_birth=date(1992, 1, 25), team=finance, role=E),
        ]
        Employee.objects.bulk_create(employees)

        # -- Assenze che coprono OGGI --
        paolo = Employee.objects.get(email="paolo@example.com")
        Absence.objects.create(
            employee=paolo,
            start_date=today - timedelta(days=3),
            end_date=today + timedelta(days=4),
        )
        robert = Employee.objects.get(email="robert@example.com")
        Absence.objects.create(
            employee=robert,
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=6),
        )

        # -- Configurazione di default --
        EmailSettings.load()

        self.stdout.write(self.style.SUCCESS(
            f"Dati demo creati: {Employee.objects.count()} dipendenti, "
            f"{Team.objects.count()} team, {Location.objects.count()} sedi. "
            f"Oggi e' {today.isoformat()}. Festeggiano: Lucia, Mario (Engineering), "
            f"Davide (Design, da solo), Robert (Finance, in ferie ma riceve auguri)."
        ))