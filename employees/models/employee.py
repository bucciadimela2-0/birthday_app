from django.db import models
from ..managers import EmployeeManager



class Employee(models.Model):
    class Role(models.TextChoices):
        EMPLOYEE = "EMPLOYEE", "Dipendente"
        MANAGER = "MANAGER", "Manager"
        EXECUTIVE = "EXECUTIVE", "Dirigente"
        
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField()
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE) #Non da ruolo inventato
    team = models.ForeignKey('employees.Team', on_delete=models.PROTECT, related_name='employees')
    is_active = models.BooleanField(
        default=True,
        help_text="Falso = non più in azienda o sospeso (diverso da 'in ferie')",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EmployeeManager()
    
    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Absence(models.Model):
    #Periodo di assenza di un dipendente, es. ferie, malattia, etc.
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='absences')
    start_date = models.DateField()
    end_date = models.DateField()
    

    class Meta:
        ordering = ['-start_date']
        constraints = [ #controllo che la data di fine sia dopo quella di inizio, altrimenti non ha senso
            models.CheckConstraint(
                condition = models.Q(end_date__gte=models.F('start_date')),
                name='end_date_after_start_date'    
            )
        ]

    def __str__(self):
        return f"{self.employee} | {self.start_date} → {self.end_date}"
    def covers(self, target_date):
     #Controlla se la data target è coperta dal periodo di assenza (inclusi i giorni di inizio e fine)
        return self.start_date <= target_date <= self.end_date
    