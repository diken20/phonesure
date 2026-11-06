from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0003_cod_and_marketplace_scam_reports"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Waiting for payment"),
                    ("paid", "Paid"),
                    ("review", "Needs review (paid, phone no longer available)"),
                    ("cancelled", "Cancelled"),
                    ("refunded", "Refunded"),
                    ("cod_pending", "Cash on delivery - awaiting delivery"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
