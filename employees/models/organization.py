from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=255, unique = True)
    timezone = models.CharField(max_length=64, default='UTC', help_text="Nome IANA, es. 'Europe/Rome', 'Asia/Tokyo'")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
    
class Team(models.Model):
    name = models.CharField(max_length=120)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='teams')
    #on_delete=models.PROTECT assicura che non si possa cancellare una location se ci sono team associati ad essa
    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint( #assicura che non ci siano due team con lo stesso nome nella stessa location
                fields=["name", "location"],
                name="unique_team_name_per_location",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.location.name})"