from django.urls import path

from django.contrib import admin
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # Cliente
    path("clientes/", views.cliente_list, name="cliente_list"),
    path("clientes/novo/", views.cliente_create, name="cliente_create"),
    path("clientes/<int:pk>/", views.cliente_detail, name="cliente_detail"),
    path("clientes/<int:pk>/editar/", views.cliente_update, name="cliente_update"),
    path("clientes/<int:pk>/excluir/", views.cliente_delete, name="cliente_delete"),
    path("clientes/export/csv/", views.export_clientes_csv, name="export_clientes_csv"),
    # Contrato
    path("contratos/", views.contrato_list, name="contrato_list"),
    path("contratos/novo/", views.contrato_create, name="contrato_create"),
    path("contratos/<int:pk>/", views.contrato_detail, name="contrato_detail"),
    path("contratos/<int:pk>/editar/", views.contrato_update, name="contrato_update"),
    path("contratos/<int:pk>/excluir/", views.contrato_delete, name="contrato_delete"),
    path(
        "contratos/export/csv/", views.export_contratos_csv, name="export_contratos_csv"
    ),
    # Item Contrato
    path("itenscontrato/", views.itemcontrato_list, name="item_contrato_list"),
    path("itenscontrato/novo/", views.itemcontrato_create, name="item_contrato_create"),
    path(
        "itenscontrato/<int:pk>/",
        views.itemcontrato_detail,
        name="item_contrato_detail",
    ),
    path(
        "itenscontrato/<int:pk>/editar/",
        views.itemcontrato_update,
        name="item_contrato_update",
    ),
    path(
        "itenscontrato/<int:pk>/excluir/",
        views.itemcontrato_delete,
        name="item_contrato_delete",
    ),
    path(
        "itemcontrato/export/csv/",
        views.export_item_contrato_csv,
        name="export_item_contrato_csv",
    ),
    # Item Fornecedor
    path("itensfornecedor/", views.itemfornecedor_list, name="item_fornecedor_list"),
    path(
        "itensfornecedor/novo/",
        views.itemfornecedor_create,
        name="item_fornecedor_create",
    ),
    path(
        "itensfornecedor/<int:pk>/",
        views.itemfornecedor_detail,
        name="item_fornecedor_detail",
    ),
    path(
        "itensfornecedor/<int:pk>/editar/",
        views.itemfornecedor_update,
        name="item_fornecedor_update",
    ),
    path(
        "itensfornecedor/<int:pk>/excluir/",
        views.itemfornecedor_delete,
        name="item_fornecedor_delete",
    ),
    path(
        "itensfornecedor/export/",
        views.export_item_fornecedor_csv,
        name="export_item_fornecedor_csv",
    ),
    # Ordem de Fornecimento
    path(
        "ordensfornecimento/",
        views.ordemfornecimento_list,
        name="ordem_fornecimento_list",
    ),
    path(
        "ordensfornecimento/novo/",
        views.ordemfornecimento_create,
        name="ordem_fornecimento_create",
    ),
    path(
        "ordensfornecimento/<int:pk>/",
        views.ordemfornecimento_detail,
        name="ordem_fornecimento_detail",
    ),
    path(
        "ordensfornecimento/<int:pk>/editar/",
        views.ordemfornecimento_update,
        name="ordem_fornecimento_update",
    ),
    path(
        "ordensfornecimento/<int:pk>/excluir/",
        views.ordemfornecimento_delete,
        name="ordem_fornecimento_delete",
    ),
    path(
        "ordensfornecimento/export/csv/",
        views.export_ordemfornecimento_csv,
        name="export_ordem_fornecimento_csv",
    ),
    # Ordem de Serviço
    path("ordensservico/", views.ordemservico_list, name="ordem_servico_list"),
    path("ordensservico/novo/", views.ordemservico_create, name="ordem_servico_create"),
    path(
        "ordensservico/<int:pk>/",
        views.ordemservico_detail,
        name="ordem_servico_detail",
    ),
    path(
        "ordensservico/<int:pk>/editar/",
        views.ordemservico_update,
        name="ordem_servico_update",
    ),
    path(
        "ordensservico/<int:pk>/excluir/",
        views.ordemservico_delete,
        name="ordem_servico_delete",
    ),
    path(
        "ordensservico/export/csv/",
        views.export_ordemservico_csv,
        name="export_ordem_servico_csv",
    ),
    # import-export
    path("import-export/", views.import_export_view, name="import_export"),
    path("export-excel/", views.export_excel_view, name="export_excel"),
    path("logs/", views.logs_import_export, name="logs_import_export"),
    # Endpoints API dinâmicos
    path(
        "api/contratos_por_cliente/",
        views.api_contratos_por_cliente,
        name="api_contratos_por_cliente",
    ),
    path(
        "api/itenscontrato/",
        views.api_itens_contrato_por_contrato,
        name="api_itens_contrato_por_contrato",
    ),
    path(
        "api/itensfornecedor/",
        views.api_itens_fornecedor_por_contrato,
        name="api_itens_fornecedor_por_contrato",
    ),
    path(
        "api/itens_contrato_por_contrato/",
        views.api_itens_contrato_por_contrato,
        name="api_itens_contrato_por_contrato",
    ),
    path(
        "api/itens_fornecedor_por_item_contrato/",
        views.api_itens_fornecedor_por_item_contrato,
        name="api_itens_fornecedor_por_item_contrato",
    ),
]
