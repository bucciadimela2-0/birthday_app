
from rest_framework import serializers

from .models import Location, Team, Employee, Absence, NewsletterLog, EmailSettings


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name", "timezone"]


class TeamSerializer(serializers.ModelSerializer):
    # Campo di sola lettura per mostrare il nome della sede senza una join manuale
    location_name = serializers.CharField(source="location.name", read_only=True)

    class Meta:
        model = Team
        fields = ["id", "name", "location", "location_name"]


class AbsenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Absence
        fields = ["id", "employee", "start_date", "end_date"]

    def validate(self, attrs):
        # Coerenza date: il vincolo è anche a livello DB, ma qui diamo
        # un errore 400 leggibile invece di un IntegrityError 500.
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and end < start:
            raise serializers.ValidationError(
                "La data di fine non può precedere quella di inizio."
            )
        return attrs


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    team_name = serializers.CharField(source="team.name", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "date_of_birth",
            "team",
            "team_name",
            "role",
            "role_display",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class NewsletterLogSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.name", read_only=True, default=None)

    class Meta:
        model = NewsletterLog
        fields = [
            "id",
            "sent_at",
            "reference_date",
            "team",
            "team_name",
            "recipients_count",
            "celebrants",
        ]


class EmailSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailSettings
        fields = [
            "birthday_subject",
            "birthday_body",
            "notify_subject",
            "notify_body",
            "leap_day_rule",
        ]


class TriggerSerializer(serializers.Serializer):
    """Input opzionale per il trigger manuale: una data per simulare un giorno."""
    date = serializers.DateField(required=False)