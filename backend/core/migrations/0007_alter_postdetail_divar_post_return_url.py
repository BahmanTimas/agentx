# Generated by Django 5.1.2 on 2024-10-29 22:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_rename_response_chatcompletionhistory_result'),
    ]

    operations = [
        migrations.AlterField(
            model_name='postdetail',
            name='divar_post_return_url',
            field=models.TextField(),
        ),
    ]