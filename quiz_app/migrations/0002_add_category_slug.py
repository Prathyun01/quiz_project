from django.db import migrations, models
from django.utils.text import slugify

def add_slugs_to_existing_categories(apps, schema_editor):
    Category = apps.get_model('quiz_app', 'Category')
    for category in Category.objects.all():
        if not category.slug:
            category.slug = slugify(category.name)
            category.save()

def reverse_add_slugs(apps, schema_editor):
    # Reverse operation - just pass
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('quiz_app', '0001_initial'),  # Adjust this to your last migration
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='slug',
            field=models.SlugField(unique=True, null=True),
        ),
        migrations.RunPython(add_slugs_to_existing_categories, reverse_add_slugs),
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(unique=True),
        ),
    ]
