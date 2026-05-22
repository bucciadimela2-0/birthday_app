
from django.core.mail import send_mail
from django.conf import settings as django_settings
from django.utils import timezone

from .models import Employee, Team, NewsletterLog, EmailSettings


def _age_on(born, target_date):
    """Anni compiuti in target_date. Gestisce il caso di chi non li ha
    ancora compiuti nell'anno (qui per costruzione è il compleanno, ma
    la formula resta corretta in generale)."""
    return target_date.year - born.year - (
        (target_date.month, target_date.day) < (born.month, born.day)
    )


def _is_on_leave(employee, target_date):
    """Il dipendente ha un'assenza che copre target_date?"""
    return employee.absences.filter(
        start_date__lte=target_date,
        end_date__gte=target_date,
    ).exists()


def send_birthday_newsletter(target_date=None):
    """
    Orchestrazione completa dell'invio del giorno.

    Restituisce un riepilogo (dict) di cosa è stato fatto, utile per
    l'endpoint di trigger e per i test.
    """
    if target_date is None:
        target_date = timezone.localdate()

    config = EmailSettings.load()

    celebrants = list(
        Employee.objects.active().celebrating(target_date, config.LeapDayRule)
    )

    summary = {
        "date": target_date.isoformat(),
        "celebrants": len(celebrants),
        "birthday_emails": 0,
        "team_notifications": 0,
    }

    if not celebrants:
        return summary

    # — Fase 1: auguri personali a ogni festeggiato (anche se in ferie) —
    for emp in celebrants:
        age = _age_on(emp.date_of_birth, target_date)
        send_mail(
            subject=config.birthday_subject.format(name=emp.first_name),
            message=config.birthday_body.format(name=emp.first_name, age=age),
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[emp.email],
        )
        summary["birthday_emails"] += 1

    # — Fase 2: notifica di riepilogo per ogni team con festeggiati —
    teams = {}
    for emp in celebrants:
        teams.setdefault(emp.team_id, []).append(emp)

    for team_id, team_celebrants in teams.items():
        team = team_celebrants[0].team

        # Destinatari: colleghi attivi del team, non festeggiati, non in ferie oggi
        celebrant_ids = {e.id for e in team_celebrants}
        recipients = []
        for colleague in team.employees.active():
            if colleague.id in celebrant_ids:
                continue
            if _is_on_leave(colleague, target_date):
                continue
            recipients.append(colleague.email)

        # Snapshot dei festeggiati per il log e per il testo
        celebrants_snapshot = [
            {"name": e.full_name, "age": _age_on(e.date_of_birth, target_date)}
            for e in team_celebrants
        ]

        if recipients:
            birthdays_text = "\n".join(
                f"- {c['name']} (compie {c['age']} anni)"
                for c in celebrants_snapshot
            )
            send_mail(
                subject=config.notify_subject.format(team=team.name),
                message=config.notify_body.format(
                    team=team.name, birthdays=birthdays_text
                ),
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
            )
            summary["team_notifications"] += 1

        # Log dell'invio per questo team (storico/monitoraggio)
        NewsletterLog.objects.create(
            reference_date=target_date,
            team=team,
            recipients_count=len(recipients),
            celebrants=celebrants_snapshot,
        )

    return summary