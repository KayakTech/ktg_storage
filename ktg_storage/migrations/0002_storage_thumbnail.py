# Generated by Django 4.2.5 on 2024-12-02 22:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ktg_storage', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='storage',
            name='thumbnail',
            field=models.URLField(blank=True, null=True),
        ),
    ]
