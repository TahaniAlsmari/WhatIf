from django.db import models
from django.contrib.auth.models import User


class DecisionRecord(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="decision_records"
    )

    decision_text = models.CharField(max_length=255)
    risk_level = models.CharField(max_length=50)

    alternative_decision = models.TextField(
        blank=True,
        null=True
    )

    alternative_risk = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.decision_text}"