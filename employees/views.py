
from datetime import date as date_cls

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Location, Team, Employee, Absence, NewsletterLog, EmailSettings
from .serializer import (
    LocationSerializer,
    TeamSerializer,
    EmployeeSerializer,
    AbsenceSerializer,
    NewsletterLogSerializer,
    EmailSettingsSerializer,
    TriggerSerializer,
)
from .services import send_birthday_newsletter


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.select_related("location").all()
    serializer_class = TeamSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    #CRUD completo anagrafica dipendenti.
    queryset = Employee.objects.select_related("team").all()
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Filtri opzionali via querystring, es. ?is_active=true&team=3
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ("1", "true", "yes"))
        team_id = self.request.query_params.get("team")
        if team_id:
            qs = qs.filter(team_id=team_id)
        return qs

    @action(detail=False, methods=["get"])
    def celebrating_today(self, request):
        #chi festeggia oggi (o in ?date=YYYY-MM-DD).
        target = request.query_params.get("date")
        target_date = date_cls.fromisoformat(target) if target else None
        from django.utils import timezone
        if target_date is None:
            target_date = timezone.localdate()
        config = EmailSettings.load()
        qs = Employee.objects.active().celebrating(target_date, config.leap_day_rule)
        return Response(EmployeeSerializer(qs, many=True).data)


class AbsenceViewSet(viewsets.ModelViewSet):
    # CRUD completo per gestire le assenze 
    queryset = Absence.objects.select_related("employee").all()
    serializer_class = AbsenceSerializer


class NewsletterLogViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    #Storico invii: sola lettura (i log si creano solo via servizio).
    
    queryset = NewsletterLog.objects.select_related("team").all()
    serializer_class = NewsletterLogSerializer


class TriggerNewsletterView(APIView):
   
#Trigger manuale dell'invio. POST opzionale con {"date": "YYYY-MM-DD"} per specificare la data target (default: oggi).
# Restituisce un summary di cosa è successo (quanti email sono state inviate, ecc.) per comodità di debug e test.
    def post(self, request):
        serializer = TriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_date = serializer.validated_data.get("date")
        summary = send_birthday_newsletter(target_date)
        return Response(summary, status=status.HTTP_200_OK)


class EmailSettingsView(APIView):
    
    #Configurazione del servizio (singleton): GET per leggere, PUT per aggiornare. 
    

    def get(self, request):
        config = EmailSettings.load()
        return Response(EmailSettingsSerializer(config).data)

    def put(self, request):
        config = EmailSettings.load()
        serializer = EmailSettingsSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)