# scripts/setup_rbac.py
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from contracts.models import (
    Contrato,
    OrdemServico,
    OrdemFornecimento,
    Cliente,
    ItemContrato,
    ItemFornecedor,
)


def create_groups():
    models = [
        Contrato,
        OrdemServico,
        OrdemFornecimento,
        Cliente,
        ItemContrato,
        ItemFornecedor,
    ]

    # Grupos
    admin_group, _ = Group.objects.get_or_create(name="Admin")
    gerente_group, _ = Group.objects.get_or_create(name="Gerente")
    tecnico_group, _ = Group.objects.get_or_create(name="Tecnico")
    leitor_group, _ = Group.objects.get_or_create(name="Leitor")

    # Permissões comuns
    for model in models:
        ct = ContentType.objects.get_for_model(model)

        view = Permission.objects.get(codename=f"view_{model._meta.model_name}")
        add = Permission.objects.get(codename=f"add_{model._meta.model_name}")
        change = Permission.objects.get(codename=f"change_{model._meta.model_name}")
        delete = Permission.objects.get(codename=f"delete_{model._meta.model_name}")

        # Admin
        admin_group.permissions.add(view, add, change, delete)

        # Gerente
        gerente_group.permissions.add(view, add, change, delete)

        # Leitor
        leitor_group.permissions.add(view)

    # Permissão para Técnico: apenas Ordem de Serviço
    os_ct = ContentType.objects.get_for_model(OrdemServico)
    tecnico_group.permissions.add(
        Permission.objects.get(codename="view_ordemservico"),
        Permission.objects.get(codename="add_ordemservico"),
        Permission.objects.get(codename="change_ordemservico"),
        Permission.objects.get(codename="delete_ordemservico"),
    )

    print("Grupos e permissões configurados!")
