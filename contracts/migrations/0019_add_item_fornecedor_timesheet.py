# Generated manually for timesheet feature

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("contracts", "0018_alter_itemcontrato_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="ordemservico",
            name="item_fornecedor_consultor",
            field=models.ForeignKey(
                blank=True,
                help_text="Item de fornecedor vinculado às horas do consultor",
                limit_choices_to={"tipo": "servico"},
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="os_consultor",
                to="contracts.itemfornecedor",
                verbose_name="Item de Fornecedor (Consultor)",
            ),
        ),
        migrations.AddField(
            model_name="ordemservico",
            name="item_fornecedor_gerente",
            field=models.ForeignKey(
                blank=True,
                help_text="Item de fornecedor vinculado às horas do gerente",
                limit_choices_to={"tipo": "servico"},
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="os_gerente",
                to="contracts.itemfornecedor",
                verbose_name="Item de Fornecedor (Gerente)",
            ),
        ),
    ]

