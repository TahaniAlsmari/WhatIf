

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DecisionRecord",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("decision_text", models.CharField(max_length=255)),
                ("risk_level", models.CharField(max_length=50)),
                ("alternative_decision", models.TextField(blank=True, null=True)),
                (
                    "alternative_risk",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
