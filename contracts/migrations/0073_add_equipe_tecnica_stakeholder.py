# Generated migration to add Equipe Técnica fields to StakeholderContrato

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0072_remove_lead_cliente_remove_lead_gerente_comercial_and_more'),
    ]

    operations = [
        # Adicionar campos para Equipe Técnica usando RunSQL para evitar problemas
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    -- Adicionar coluna nome se não existir
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='contracts_stakeholdercontrato' AND column_name='nome'
                    ) THEN
                        ALTER TABLE contracts_stakeholdercontrato 
                        ADD COLUMN nome varchar(255) NULL;
                    END IF;
                    
                    -- Adicionar coluna email se não existir
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='contracts_stakeholdercontrato' AND column_name='email'
                    ) THEN
                        ALTER TABLE contracts_stakeholdercontrato 
                        ADD COLUMN email varchar(254) NULL;
                    END IF;
                    
                    -- Adicionar coluna telefone se não existir
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='contracts_stakeholdercontrato' AND column_name='telefone'
                    ) THEN
                        ALTER TABLE contracts_stakeholdercontrato 
                        ADD COLUMN telefone varchar(20) NULL;
                    END IF;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Remover unique_together para permitir múltiplos membros da Equipe Técnica
        migrations.RunSQL(
            sql="""
                DO $$
                DECLARE
                    constraint_name text;
                BEGIN
                    -- Encontrar e remover constraint unique_together se existir
                    SELECT conname INTO constraint_name
                    FROM pg_constraint 
                    WHERE conrelid = 'contracts_stakeholdercontrato'::regclass
                    AND conname LIKE '%contrato_id_tipo_papel%uniq'
                    LIMIT 1;
                    
                    IF constraint_name IS NOT NULL THEN
                        EXECUTE 'ALTER TABLE contracts_stakeholdercontrato DROP CONSTRAINT ' || constraint_name;
                    END IF;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Registrar campos no estado do Django (as colunas já foram criadas pelo RunSQL)
        migrations.AddField(
            model_name='stakeholdercontrato',
            name='nome',
            field=models.CharField(
                blank=True,
                help_text='Nome do membro da equipe técnica (usado quando tipo = Equipe Técnica)',
                max_length=255,
                null=True,
                verbose_name='Nome'
            ),
        ),
        migrations.AddField(
            model_name='stakeholdercontrato',
            name='email',
            field=models.EmailField(
                blank=True,
                help_text='E-mail do membro da equipe técnica (usado quando tipo = Equipe Técnica)',
                null=True,
                verbose_name='E-mail'
            ),
        ),
        migrations.AddField(
            model_name='stakeholdercontrato',
            name='telefone',
            field=models.CharField(
                blank=True,
                help_text='Telefone do membro da equipe técnica (usado quando tipo = Equipe Técnica)',
                max_length=20,
                null=True,
                verbose_name='Telefone'
            ),
        ),
    ]
