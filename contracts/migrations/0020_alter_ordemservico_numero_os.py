# Generated manually for auto-generated OS number

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contracts", "0019_add_item_fornecedor_timesheet"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ordemservico",
            name="numero_os",
            field=models.CharField(blank=True, editable=False, max_length=20, unique=True),
        ),
    ]

