# Generated manually to fix foreign key constraint

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("contracts", "0073_add_equipe_tecnica_stakeholder"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Dropar a constraint existente
            ALTER TABLE contracts_tarefa 
            DROP CONSTRAINT contracts_tarefa_projeto_id_c35b2c07_fk_contracts_projeto_id;
            
            -- Recriar a constraint com CASCADE
            ALTER TABLE contracts_tarefa 
            ADD CONSTRAINT contracts_tarefa_projeto_id_c35b2c07_fk_contracts_projeto_id 
            FOREIGN KEY (projeto_id) 
            REFERENCES contracts_projeto(id) 
            ON DELETE CASCADE;
            """,
            reverse_sql="""
            -- Reverter para NO ACTION (caso necessário)
            ALTER TABLE contracts_tarefa 
            DROP CONSTRAINT IF EXISTS contracts_tarefa_projeto_id_c35b2c07_fk_contracts_projeto_id;
            
            ALTER TABLE contracts_tarefa 
            ADD CONSTRAINT contracts_tarefa_projeto_id_c35b2c07_fk_contracts_projeto_id 
            FOREIGN KEY (projeto_id) 
            REFERENCES contracts_projeto(id) 
            ON DELETE NO ACTION;
            """,
        ),
    ]

