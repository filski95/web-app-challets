# Generated by Django 4.1 on 2022-09-28 07:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0009_rename_rank_opinion_rating"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="challethouse",
            options={"ordering": ["house_number"]},
        ),
    ]
