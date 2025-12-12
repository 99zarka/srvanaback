from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0001_initial'),
        ('notifications', '0004_notification_related_dispute'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='related_review',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='reviews.review'),
        ),
    ]
