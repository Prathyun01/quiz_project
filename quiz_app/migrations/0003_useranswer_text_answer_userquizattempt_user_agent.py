# Generated by Django 4.2.7 on 2025-07-23 09:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz_app", "0002_add_category_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="useranswer",
            name="text_answer",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="userquizattempt",
            name="user_agent",
            field=models.TextField(blank=True, default=""),
        ),
    ]
