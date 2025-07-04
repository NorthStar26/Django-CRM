# Generated by Django 5.2.1 on 2025-07-03 13:10

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("companies", "0010_alter_companyprofile_website"),
    ]

    operations = [
        migrations.AlterField(
            model_name="companyprofile",
            name="website",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                validators=[
                    django.core.validators.URLValidator(
                        message="Website must be a valid URL starting with http:// or https://",
                        schemes=["http", "https"],
                    )
                ],
                verbose_name="Website",
            ),
        ),
    ]
