# Generated by Django 5.2 on 2025-06-04 11:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academic', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='classroom',
            old_name='created_by',
            new_name='teacher',
        ),
    ]
