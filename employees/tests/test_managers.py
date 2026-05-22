# employees/tests/test_managers.py
from datetime import date

from django.test import TestCase

from employees.models import Location, Team, Employee


class CelebratingOnTests(TestCase):
    """Birthday detection logic, focused on the Feb 29 edge case."""

    @classmethod
    def setUpTestData(cls):
        loc = Location.objects.create(name="Milan", timezone="Europe/Rome")
        cls.team = Team.objects.create(name="Engineering", location=loc)

        
        #Nato il 28 Febbraio
        
        cls.feb28 = Employee.objects.create(
            first_name="Lucia", last_name="B", email="lucia@x.com",
            date_of_birth=date(1990, 2, 28), team=cls.team,
        )
        # Nato il 29 Febbraio (1992 è bisestile, data valida)
        
        cls.feb29 = Employee.objects.create(
            first_name="Mario", last_name="R", email="mario@x.com",
            date_of_birth=date(1992, 2, 29), team=cls.team,
        )
        # Nato in un giorno qualsiasi
        
        cls.july = Employee.objects.create(
            first_name="Anna", last_name="V", email="anna@x.com",
            date_of_birth=date(1995, 7, 10), team=cls.team,
        )
        # Inattivo, nato il 28 Febbraio: non deve mai comparire
     
        cls.inactive = Employee.objects.create(
            first_name="Marco", last_name="I", email="marco@x.com",
            date_of_birth=date(1991, 2, 28), team=cls.team, is_active=False,
        )

    def _names(self, qs):
        return sorted(e.first_name for e in qs)

    # --- Caso ordinario ---

    def test_ordinary_day_match(self):
        qs = Employee.objects.active().celebrating(date(2025, 7, 10))
        self.assertEqual(self._names(qs), ["Anna"])

    def test_no_one_celebrating(self):
        qs = Employee.objects.active().celebrating(date(2025, 6, 1))
        self.assertEqual(list(qs), [])

  #-- Gli inattivi sono esclusi ---

    def test_inactive_never_included(self):
        # Feb 28, 2024 (leap year): only Lucia, NOT Marco (inactive)
        qs = Employee.objects.active().celebrating(date(2024, 2, 28))
        self.assertEqual(self._names(qs), ["Lucia"])

    #-- Feb 29 in un anno BISIESTILE: tutti nel loro giorno effettivo ---

    def test_leap_year_feb28_only_those_born_28(self):
        qs = Employee.objects.active().celebrating(date(2024, 2, 28))
        self.assertEqual(self._names(qs), ["Lucia"])

    def test_leap_year_feb29_only_those_born_29(self):
        qs = Employee.objects.active().celebrating(date(2024, 2, 29))
        self.assertEqual(self._names(qs), ["Mario"])

  #-- Feb 29 in un anno NON-bisestile, regola FEB_28 (default) ---
    def test_non_leap_feb28_also_includes_those_born_29(self):
        # 2025 non è bisestile: il 28 Febbraio celebrano sia Lucia (28) che Mario (29)
        qs = Employee.objects.active().celebrating(date(2025, 2, 28), "FEB_28")
        self.assertEqual(self._names(qs), ["Lucia", "Mario"])

    def test_non_leap_feb28_with_mar01_rule_excludes_29(self):
      # Con la regola MAR_01, chi è nato il 29 Febbraio celebra il 1 Marzo, non il 28
        qs = Employee.objects.active().celebrating(date(2025, 2, 28), "MAR_01")
        self.assertEqual(self._names(qs), ["Lucia"])

    def test_non_leap_mar01_with_mar01_rule_includes_29(self):
        ## Con la regola MAR_01, chi è nato il 29 Febbraio celebra il 1 Marzo
        qs = Employee.objects.active().celebrating(date(2025, 3, 1), "MAR_01")
        self.assertEqual(self._names(qs), ["Mario"])

    def test_non_leap_mar01_with_feb28_rule_excludes_29(self):
        # Con la regola FEB_28, il 1 Marzo non deve includere chi è nato il 29 Febbraio
        
        qs = Employee.objects.active().celebrating(date(2025, 3, 1), "FEB_28")
        self.assertEqual(self._names(qs), [])