# Generated by Django 4.1 on 2022-09-20 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0004_challethouse_address_confirmationofreservation"),
    ]

    operations = [
        migrations.AddField(
            model_name="confirmationofreservation",
            name="saved_file",
            field=models.FileField(null=True, upload_to=""),
        ),
    ]
