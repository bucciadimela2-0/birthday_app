# employees/services.py
from django.core.mail import send_mail
from django.conf import settings as django_settings
from django.utils import timezone

from .models import Employee, Absence, NewsletterLog, EmailSettings


def _age_on(born, target_date):
    #Anni compiuti alla data target. Gestisce chi non ha ancora festeggiato quest'anno.
    #La soluzione più semplice è sottrarre gli anni e poi correggere se il compleanno non è ancora passato.
    return target_date.year - born.year - (
        (target_date.month, target_date.day) < (born.month, born.day)
    )


def _absent_employee_ids(target_date):
    # Restituisce un set di ID di dipendenti che sono assenti (in ferie o altro tipo di assenza) nella data target.
    return set(
        Absence.objects.filter(
            start_date__lte=target_date,
            end_date__gte=target_date,
        ).values_list("employee_id", flat=True)
    )


def send_birthday_newsletter(target_date=None):
    # Se non viene specificata, la data target è oggi (secondo il timezone della sede).
    if target_date is None:
        target_date = timezone.localdate()

    config = EmailSettings.load()
    # Per comodità, carichiamo tutti i festeggiati in un'unica query, con select_related("team") per evitare query addizionali quando accediamo a emp.team. 
    # Il metodo "celebrating" sul manager di Employee si occupa della logica di chi festeggia oggi, inclusi i casi di compleanni al 29 Febbraio.

    celebrants = list(
        Employee.objects
        .select_related("team")
        .active()
        .celebrating(target_date, config.leap_day_rule)
    )

    summary = {
        "date": target_date.isoformat(),
        "celebrants": len(celebrants),
        "birthday_emails": 0,
        "team_notifications": 0,
    }

    if not celebrants:
        return summary
    # Per evitare di inviare email a colleghi che sono in ferie, carichiamo in anticipo gli ID di tutti i dipendenti assenti oggi in un set, 
    # così da poter fare check veloci in memoria quando costruiamo la lista dei destinatari delle notifiche di team.

    absent_ids = _absent_employee_ids(target_date)

    #Fase 1: invio gli auguri di compleanno a ogni festeggiato (anche se è in ferie)
    
    for emp in celebrants:
        age = _age_on(emp.date_of_birth, target_date)
        send_mail(
            subject=config.birthday_subject.format(name=emp.first_name),
            message=config.birthday_body.format(name=emp.first_name, age=age),
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[emp.email],
        )
        summary["birthday_emails"] += 1

    # Fase 2: per ogni team con almeno un festeggiato, 
    # invio una notifica a tutti i colleghi attivi che NON festeggiano oggi e NON sono in ferie oggi.
    teams = {}
    for emp in celebrants:
        teams.setdefault(emp.team_id, []).append(emp)

    
    # Per ottimizzare, carichiamo in anticipo tutti i membri attivi di ogni team coinvolto in un'unica query,
    # organizzati in un dizionario keyed by team_id, così il loop dei destinatari
    team_ids = list(teams.keys())
    members_by_team = {tid: [] for tid in team_ids}
    for member in Employee.objects.filter(team_id__in=team_ids, is_active=True):
        members_by_team[member.team_id].append(member)

    for team_id, team_celebrants in teams.items():
        team = team_celebrants[0].team  
        celebrant_ids = {e.id for e in team_celebrants}

        # I destinatari della notifica di team sono tutti i membri attivi del team che NON festeggiano oggi (non sono nella lista dei celebranti) e NON sono in ferie oggi (non sono negli absent_ids).
        recipients = [
            m.email
            for m in members_by_team[team_id]
            if m.id not in celebrant_ids and m.id not in absent_ids
        ]

        celebrants_snapshot = [
            {"name": e.full_name, "age": _age_on(e.date_of_birth, target_date)}
            for e in team_celebrants
        ]

        if recipients:
            birthdays_text = "\n".join(
                f"- {c['name']} (turns {c['age']})"
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

        NewsletterLog.objects.create(
            reference_date=target_date,
            team=team,
            recipients_count=len(recipients),
            celebrants=celebrants_snapshot,
        )

    return summary