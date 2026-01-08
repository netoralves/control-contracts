# Generated migration for StakeholderContrato model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0069_alter_tarefa_options_alter_sprint_data_fim_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='StakeholderContrato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('CONTRATADA', 'Contratada'), ('CONTRATANTE', 'Contratante')], max_length=20, verbose_name='Tipo de Stakeholder')),
                ('papel', models.CharField(max_length=50, verbose_name='Papel/Função')),
                ('observacoes', models.TextField(blank=True, null=True, verbose_name='Observações')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('colaborador', models.ForeignKey(blank=True, help_text='Colaborador da contratada (usado quando tipo = Contratada)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stakeholders_contrato', to='contracts.colaborador', verbose_name='Colaborador')),
                ('contrato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stakeholders', to='contracts.contrato', verbose_name='Contrato')),
                ('contato_cliente', models.ForeignKey(blank=True, help_text='Contato do cliente/contratante (usado quando tipo = Contratante)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stakeholders_contrato', to='contracts.contatocliente', verbose_name='Contato do Cliente')),
            ],
            options={
                'verbose_name': 'Stakeholder do Contrato',
                'verbose_name_plural': 'Stakeholders do Contrato',
                'ordering': ['tipo', 'papel'],
                'unique_together': {('contrato', 'tipo', 'papel')},
            },
        ),
    ]

