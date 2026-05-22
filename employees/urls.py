
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LocationViewSet,
    TeamViewSet,
    EmployeeViewSet,
    AbsenceViewSet,
    NewsletterLogViewSet,
    TriggerNewsletterView,
    EmailSettingsView,
)

router = DefaultRouter()
router.register(r"locations", LocationViewSet)
router.register(r"teams", TeamViewSet)
router.register(r"employees", EmployeeViewSet)
router.register(r"absences", AbsenceViewSet)
router.register(r"newsletter-logs", NewsletterLogViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("newsletter/trigger/", TriggerNewsletterView.as_view(), name="newsletter-trigger"),
    path("settings/", EmailSettingsView.as_view(), name="email-settings"),
]

