# Generated by Django 2.2.5 on 2019-09-23 22:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tom_targets', '0014_auto_20190923_1827'),
    ]

    operations = [
        migrations.AlterField(
            model_name='targetlist',
            name='modified',
            field=models.DateTimeField(auto_now=True, help_text='The time which this target list was changed in the TOM database.', verbose_name='Last Modified'),
        ),
        migrations.AlterField(
            model_name='targetname',
            name='modified',
            field=models.DateTimeField(auto_now=True, help_text='The time which this target name was changed in the TOM database.', verbose_name='Last Modified'),
        ),
    ]
