# employees/models/settings.py
from django.db import models


class EmailSettings(models.Model):
    """Configurazione del servizio. Riga unica (pattern singleton)."""

    class LeapDayRule(models.TextChoices):
        FEB_28 = "FEB_28", "Festeggia il 28 febbraio"
        MAR_01 = "MAR_01", "Festeggia il 1 marzo"

    # -- Mail di auguri al festeggiato --
    birthday_subject = models.CharField(
        max_length=200,
        default="\U0001F382 Buon compleanno, {name}!",
    )
    birthday_body = models.TextField(
        default=(
            "Ciao {name},\n\n"
            "tutto il team ti augura un felicissimo compleanno "
            "per i tuoi {age} anni! \U0001F389\n\n"
            "Goditi la giornata!"
        ),
        help_text="Placeholder: {name}, {age}",
    )

    # -- Mail di notifica ai colleghi --
    notify_subject = models.CharField(
        max_length=200,
        default="\U0001F382 Compleanni di oggi nel team {team}",
    )
    notify_body = models.TextField(
        default=(
            "Ciao!\n\n"
            "Oggi nel team {team} si festeggia:\n"
            "{birthdays}\n\n"
            "Passa a fare gli auguri! \U0001F389"
        ),
        help_text="Placeholder: {team}, {birthdays}",
    )

    leap_day_rule = models.CharField(
        max_length=10,
        choices=LeapDayRule.choices,
        default=LeapDayRule.FEB_28,
        help_text="Quando festeggia chi e' nato il 29/02 negli anni non bisestili",
    )

    class Meta:
        verbose_name = "Email settings"
        verbose_name_plural = "Email settings"

    def __str__(self):
        return "Configurazione servizio newsletter"

    def save(self, *args, **kwargs):
        """Forza l'esistenza di una sola riga: pk fissa a 1."""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Restituisce l'unica istanza, creandola coi default se manca."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj