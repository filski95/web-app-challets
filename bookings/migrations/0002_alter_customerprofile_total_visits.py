# Generated by Django 4.1 on 2022-08-17 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customerprofile",
            name="total_visits",
            field=models.SmallIntegerField(
                default=0, verbose_name="Number of visits so far"
            ),
        ),
    ]