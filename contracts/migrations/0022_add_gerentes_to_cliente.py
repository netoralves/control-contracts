# Generated manually for client management

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("contracts", "0021_centrocusto_colaborador_lead_oportunidade_reclamacao_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="gerente_comercial",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"cargo__icontains": "comercial"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="clientes_comercial",
                to="contracts.colaborador",
                verbose_name="Gerente Comercial da Conta",
            ),
        ),
        migrations.AddField(
            model_name="cliente",
            name="gerente_sucessos",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"cargo__icontains": "sucessos"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="clientes_sucessos",
                to="contracts.colaborador",
                verbose_name="Gerente de Sucessos",
            ),
        ),
    ]

