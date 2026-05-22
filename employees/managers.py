import calendar
from django.db import models

class EmployeeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True  )
    def celebrating(self, target_date, leap_day_rule = "FEB_28" ):
        #Restituisce i dipendenti che festeggiano il compleanno nella data target
        match = models.Q(
            date_of_birth__month=target_date.month,
            date_of_birth__day=target_date.day,
        )
    #Gestione dei nati il 29 febbraio negli anni non bisestili, in base alla regola scelta (leap_day_rule)
        if not calendar.isleap(target_date.year) and target_date.month == 2 and target_date.day == 28:
            if leap_day_rule == "FEB_28":
                match |= models.Q(date_of_birth__month=2, date_of_birth__day=29) #Includi i nati il 29 febbraio se la regola è di festeggiarli il 28 febbraio negli anni non bisestili
        elif not calendar.isleap(target_date.year) and target_date.month == 3 and target_date.day == 1:
            if leap_day_rule == "MAR_01":
                match |= models.Q(date_of_birth__month=2, date_of_birth__day=29) #Includi i nati il 29 febbraio se la regola è di festeggiarli il 1° marzo negli anni non bisestili           
        return self.filter(match) #Applica il filtro combinato per mese e giorno (e eventuale regola per i nati il 29 febbraio)
    
class EmployeeManager(models.Manager):
    def get_queryset(self):
        return EmployeeQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def celebrating(self, target_date, leap_day_rule = "FEB_28" ):
        return self.get_queryset().celebrating(target_date, leap_day_rule)