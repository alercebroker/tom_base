# Generated by Django 2.2.2 on 2019-07-01 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tom_alerts', '0002_auto_20190626_2135'),
    ]

    operations = [
        migrations.AlterField(
            model_name='brokerquery',
            name='modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
