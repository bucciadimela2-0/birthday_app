
from datetime import date, timedelta

from django.test import TestCase
from django.core import mail

from employees.models import (
    Location, Team, Employee, Absence, NewsletterLog, EmailSettings,
)
from employees.services import send_birthday_newsletter


class SendNewsletterTests(TestCase):
   

    def setUp(self):
        loc = Location.objects.create(name="Milan", timezone="Europe/Rome")
        self.team = Team.objects.create(name="Engineering", location=loc)
        self.day = date(2025, 6, 15)  # an ordinary day, not leap-sensitive

        #Festeggia oggi
        self.birthday = Employee.objects.create(
            first_name="Lucia", last_name="B", email="lucia@x.com",
            date_of_birth=date(1990, 6, 15), team=self.team,
        )
        # Colleghi che NON festeggiano oggi
        self.coll_a = Employee.objects.create(
            first_name="Anna", last_name="V", email="anna@x.com",
            date_of_birth=date(1995, 1, 1), team=self.team,
        )
        self.coll_b = Employee.objects.create(
            first_name="Paolo", last_name="N", email="paolo@x.com",
            date_of_birth=date(1988, 3, 3), team=self.team,
        )
        EmailSettings.load()
        mail.outbox = []

    def _recipients(self):
        # Tutti i destinatari di ogni email inviata, appiattiti in un'unica lista
        out = []
        for m in mail.outbox:
            out.extend(m.to)
        return out

    def test_celebrant_gets_their_own_birthday_email(self):
        send_birthday_newsletter(self.day)
       # C'è un'email il cui unico destinatario è il festeggiato
        wishes = [m for m in mail.outbox if m.to == ["lucia@x.com"]]
        self.assertEqual(len(wishes), 1)

    def test_celebrant_excluded_from_team_notification(self):
        send_birthday_newsletter(self.day)
        # Trova l'email di notifica (quella indirizzata ai colleghi)
        notifications = [m for m in mail.outbox if "anna@x.com" in m.to]
        self.assertEqual(len(notifications), 1)
        # Il festeggiato NON deve essere tra i destinatari della notifica
        self.assertNotIn("lucia@x.com", notifications[0].to)

    def test_colleague_on_leave_excluded_from_notification(self):
        # Paolo è in ferie nel giorno target
        Absence.objects.create(
            employee=self.coll_b,
            start_date=self.day - timedelta(days=1),
            end_date=self.day + timedelta(days=1),
        )
        send_birthday_newsletter(self.day)
        self.assertNotIn("paolo@x.com", self._recipients())
        # Anna, invece, non è in ferie e riceve la notifica
        self.assertIn("anna@x.com", self._recipients())

    def test_celebrant_on_leave_still_gets_wishes(self):
        #Lucia festeggia E è in ferie: gli auguri arrivano comunque
        
        Absence.objects.create(
            employee=self.birthday,
            start_date=self.day - timedelta(days=1),
            end_date=self.day + timedelta(days=1),
        )
        send_birthday_newsletter(self.day)
        self.assertIn("lucia@x.com", self._recipients())

    def test_no_celebrants_no_email(self):
        summary = send_birthday_newsletter(date(2025, 9, 9))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(summary["celebrants"], 0)

    def test_team_with_only_celebrant_sends_no_notification(self):
        # Un team il cui unico membro è il festeggiato: nessuna notifica
       
        loc2 = Location.objects.create(name="Rome", timezone="Europe/Rome")
        solo_team = Team.objects.create(name="Solo", location=loc2)
        Employee.objects.create(
            first_name="Davide", last_name="S", email="davide@x.com",
            date_of_birth=date(1985, 6, 15), team=solo_team,
        )
        send_birthday_newsletter(self.day)
        # Davide riceve i suoi auguri ma nessuna notifica è indirizzata a lui
     
        davide_mails = [m for m in mail.outbox if m.to == ["davide@x.com"]]
        self.assertEqual(len(davide_mails), 1)

    def test_log_is_created(self):
        send_birthday_newsletter(self.day)
        self.assertTrue(NewsletterLog.objects.filter(reference_date=self.day).exists())
        log = NewsletterLog.objects.get(reference_date=self.day, team=self.team)
       # I nomi dei festeggiati devono essere correttamente registrati nel log
        names = [c["name"] for c in log.celebrants]
        self.assertIn("Lucia B", names)

    def test_summary_counts(self):
        summary = send_birthday_newsletter(self.day)
        self.assertEqual(summary["celebrants"], 1)
        self.assertEqual(summary["birthday_emails"], 1)
        self.assertEqual(summary["team_notifications"], 1)