# employees/tests/test_api.py
from datetime import date

from django.test import TestCase

from employees.models import Location, Team, Employee, EmailSettings


class ApiSmokeTests(TestCase):
    #test di base per verificare che le API siano raggiungibili e funzionino a grandi linee (status code, struttura della risposta, ecc.)

    @classmethod
    def setUpTestData(cls):
        loc = Location.objects.create(name="Milan", timezone="Europe/Rome")
        cls.team = Team.objects.create(name="Engineering", location=loc)
        cls.emp = Employee.objects.create(
            first_name="Lucia", last_name="B", email="lucia@x.com",
            date_of_birth=date(1990, 2, 28), team=cls.team,
        )
        # Un altro nato il 29 Febbraio, per testare l'endpoint "celebrating_today" in un giorno non bisestile
        cls.leap = Employee.objects.create(
            first_name="Giada", last_name="L", email="giada@x.com",
            date_of_birth=date(1992, 2, 29), team=cls.team,
        )
        EmailSettings.load()

    def test_list_employees(self):
        # Verifica che l'endpoint di listing degli impiegati sia raggiungibile e restituisca 200 OK
        resp = self.client.get("/api/employees/")
        self.assertEqual(resp.status_code, 200)

    def test_create_employee(self):
        # Verifica che sia possibile creare un nuovo impiegato tramite POST e che venga effettivamente creato nel database
        payload = {
            "first_name": "New", "last_name": "Guy",
            "email": "new@x.com", "date_of_birth": "1999-01-01",
            "team": self.team.id,
        }
        resp = self.client.post("/api/employees/", payload, content_type="application/json")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Employee.objects.filter(email="new@x.com").exists())

    def test_update_employee(self):
        # Verifica che sia possibile aggiornare un impiegato esistente tramite PATCH e che le modifiche vengano salvate
        resp = self.client.patch(
            f"/api/employees/{self.emp.id}/",
            {"first_name": "Lucy"}, content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.emp.refresh_from_db()
        self.assertEqual(self.emp.first_name, "Lucy")

    def test_celebrating_today_leap_year_case(self):
        # Verifica che l'endpoint "celebrating_today" restituisca correttamente sia chi è nato il 28 Febbraio che chi è nato il 29 Febbraio quando la data richiesta è il 28 Febbraio di un anno non bisestile
        resp = self.client.get("/api/employees/celebrating_today/?date=2025-02-28")
        self.assertEqual(resp.status_code, 200)
        names = [e["first_name"] for e in resp.json()]
        self.assertIn("Giada", names)
        self.assertIn("Lucia", names)

    def test_trigger_newsletter(self):
        # Verifica che l'endpoint per triggerare la newsletter sia raggiungibile e restituisca 200 OK, e che la risposta contenga la chiave "celebrants" (anche se non testiamo il contenuto esatto in questo smoke test)
        resp = self.client.post(
            "/api/newsletter/trigger/",
            {"date": "2025-02-28"}, content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("celebrants", resp.json())

    def test_settings_get_and_put(self):
        # Verifica che sia possibile ottenere le impostazioni via GET e aggiornarle via PUT, e che le modifiche vengano effettivamente salvate
        resp = self.client.get("/api/settings/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("leap_day_rule", resp.json())

        resp = self.client.put(
            "/api/settings/",
            {"leap_day_rule": "MAR_01"}, content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(EmailSettings.load().leap_day_rule, "MAR_01")

    def test_newsletter_logs_are_read_only(self):
        # Verifica che l'endpoint dei log della newsletter sia read-only (non accetti POST)
        resp = self.client.post("/api/newsletter-logs/", {}, content_type="application/json")
        self.assertEqual(resp.status_code, 405)