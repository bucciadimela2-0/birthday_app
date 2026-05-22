from django.db import models
from django.core.exceptions import ValidationError 
from .organization import Team
class NewsletterLog(models.Model):
    

    sent_at = models.DateTimeField(auto_now_add=True)
    reference_date = models.DateField(
        help_text="La data 'di calendario' per cui è stata generata la newsletter",
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True, #In caso di cancellazione del team, manteniamo il log ma senza riferimento al team specifico
        related_name="newsletter_logs",
    )
    recipients_count = models.PositiveIntegerField(default=0)
    celebrants = models.JSONField(
        default=list,
        help_text="Snapshot dei festeggiati inclusi: [{name, age}, ...]",
    )

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.reference_date} · {self.team} · {self.recipients_count} dest."