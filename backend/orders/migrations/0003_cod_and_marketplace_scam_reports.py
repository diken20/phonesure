from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0002_alter_order_status'),
        ('phones', '0003_phone_review_note_phone_reviewed_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.AddField(
            model_name='order', name='payment_method',
            field=models.CharField(choices=[('esewa', 'eSewa'), ('cod', 'Cash on delivery')], default='esewa', max_length=12),
        ),
        migrations.AlterField(
            model_name='order', name='status',
            field=models.CharField(choices=[('pending', 'Waiting for payment'), ('paid', 'Paid'), ('review', 'Needs review (paid, phone no longer available)'), ('cancelled', 'Cancelled'), ('refunded', 'Refunded'), ('cod_pending', 'Cash on delivery - awaiting delivery')], default='pending', max_length=10),
        ),
        migrations.AlterField(
            model_name='problemreport', name='category',
            field=models.CharField(choices=[('not_as_described', 'Not as described'), ('scam', 'Suspected scam or fake listing'), ('battery', 'Battery problem'), ('screen_or_body', 'Screen or body damage'), ('not_working', 'Not working properly'), ('missing_items', 'Missing box, charger or bill'), ('other', 'Other')], max_length=20),
        ),
        migrations.AlterField(
            model_name='problemreport', name='item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='problems', to='orders.orderitem'),
        ),
        migrations.AddField(
            model_name='problemreport', name='phone',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='scam_reports', to='phones.phone'),
        ),
    ]
