# Generated by Django 2.2.14 on 2020-07-23 08:48

import django.db.models.deletion
import parler.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shuup_tasks', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tasktypetranslation',
            name='master',
            field=parler.fields.TranslationsForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='shuup_tasks.TaskType'),
        ),
    ]
