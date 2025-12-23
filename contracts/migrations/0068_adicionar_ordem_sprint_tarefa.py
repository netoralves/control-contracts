# Generated manually on 2025-12-19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contracts", "0067_remover_bilhetavel_os"),
    ]

    operations = [
        migrations.AddField(
            model_name="tarefa",
            name="ordem_sprint",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Ordem de exibição da tarefa dentro da sprint (0 = primeiro)",
                verbose_name="Ordem na Sprint",
            ),
        ),
    ]

