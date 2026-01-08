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
    # Item Contrato - Edição e Detalhes (usado na aba do contrato)
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
    # Customer Success - Tickets de Contato
    path(
        "customer-success/",
        views.customer_success_list,
        name="customer_success_list",
    ),
    path(
        "customer-success/novo/",
        views.customer_success_criar_ticket,
        name="customer_success_criar_ticket",
    ),
    path(
        "customer-success/<int:pk>/",
        views.customer_success_detail,
        name="customer_success_detail",
    ),
    path(
        "customer-success/<int:pk>/excluir/",
        views.customer_success_delete,
        name="customer_success_delete",
    ),
    # Endpoints API dinâmicos
    path(
        "api/contratos_por_cliente/",
        views.api_contratos_por_cliente,
        name="api_contratos_por_cliente",
    ),
    path(
        "api/projetos_por_contrato/",
        views.api_projetos_por_contrato,
        name="api_projetos_por_contrato",
    ),
    path(
        "api/sprints_por_projeto/",
        views.api_sprints_por_projeto,
        name="api_sprints_por_projeto",
    ),
    path(
        "api/ordens_servico_por_contrato/",
        views.api_ordens_servico_por_contrato,
        name="api_ordens_servico_por_contrato",
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
    path(
        "api/item_contrato/<int:item_id>/saldo/",
        views.api_item_contrato_saldo,
        name="api_item_contrato_saldo",
    ),
    path(
        "api/item_contrato/<int:item_id>/valor/",
        views.api_item_contrato_valor,
        name="api_item_contrato_valor",
    ),
    path(
        "api/item_fornecedor/<int:item_id>/valor/",
        views.api_item_fornecedor_valor,
        name="api_item_fornecedor_valor",
    ),
    path(
        "api/itens_fornecedor_servico_por_contrato/",
        views.api_itens_fornecedor_servico_por_contrato,
        name="api_itens_fornecedor_servico_por_contrato",
    ),
    # Gestão de Clientes - Colaboradores
    path("colaboradores/", views.colaborador_list, name="colaborador_list"),
    path("colaboradores/novo/", views.colaborador_create, name="colaborador_create"),
    path("colaboradores/<int:pk>/", views.colaborador_detail, name="colaborador_detail"),
    path("colaboradores/<int:pk>/editar/", views.colaborador_update, name="colaborador_update"),
    path("colaboradores/<int:pk>/password/", views.colaborador_password_change, name="colaborador_password_change"),
    # Grupos
    path("grupos/", views.grupo_list, name="grupo_list"),
    path("grupos/novo/", views.grupo_create, name="grupo_create"),
    path("grupos/<int:pk>/", views.grupo_detail, name="grupo_detail"),
    path("grupos/<int:pk>/editar/", views.grupo_update, name="grupo_update"),
    path("grupos/<int:pk>/excluir/", views.grupo_delete, name="grupo_delete"),
    # Gestão de Contratos e OF - SLAs
    path("slas/", views.sla_list, name="sla_list"),
    path("slas/novo/", views.sla_create, name="sla_create"),
    path("slas/<int:pk>/", views.sla_detail, name="sla_detail"),
    path("slas/<int:pk>/editar/", views.sla_update, name="sla_update"),
    # Gestão de Contratos e OF - Fila de Faturamento
    path("fila-faturamento/", views.fila_faturamento, name="fila_faturamento"),
    path("fila-faturamento/os/<int:pk>/marcar-faturada/", views.marcar_os_faturada, name="marcar_os_faturada"),
    path("fila-faturamento/of/<int:pk>/marcar-faturada/", views.marcar_of_faturada, name="marcar_of_faturada"),
    # Gestão de OS com Tarefas
    path("ordensservico/<int:os_id>/tarefas/novo/", views.tarefa_os_create, name="tarefa_os_create"),
    path("ordensservico/<int:os_id>/tarefas/<int:tarefa_id>/editar/", views.tarefa_os_update, name="tarefa_os_update"),
    path("tarefas/<int:tarefa_id>/lancamentos/novo/", views.lancamento_hora_create, name="lancamento_hora_create"),
    path("lancamentos/<int:lancamento_id>/editar/", views.lancamento_hora_update, name="lancamento_hora_update"),
    path("lancamentos/<int:lancamento_id>/excluir/", views.lancamento_hora_delete, name="lancamento_hora_delete"),
    # Gestão Ágil de Projetos
    path("projetos/", views.projeto_list, name="projeto_list"),
    path("projetos/novo/", views.projeto_create, name="projeto_create"),
    path("projetos/<int:pk>/", views.projeto_detail, name="projeto_detail"),
    path("projetos/<int:pk>/editar/", views.projeto_update, name="projeto_update"),
    path("projetos/<int:pk>/excluir/", views.projeto_delete, name="projeto_delete"),
    path("contratos/<int:contrato_id>/backlog/", views.backlog_gerenciar, name="backlog_gerenciar"),
    path("contratos/<int:contrato_id>/backlog/criar/", views.backlog_create_ajax, name="backlog_create_ajax"),
    path("backlog/<int:backlog_id>/excluir/", views.backlog_delete_ajax, name="backlog_delete_ajax"),
    path("backlog/<int:backlog_id>/converter-projeto/", views.backlog_converter_projeto, name="backlog_converter_projeto"),
    path("backlog/<int:backlog_id>/converter-projeto-ajax/", views.backlog_converter_projeto_ajax, name="backlog_converter_projeto_ajax"),
    path("projetos/<int:projeto_id>/sprints/novo/", views.sprint_create, name="sprint_create"),
    path("projetos/<int:projeto_id>/sprints/<int:sprint_id>/", views.sprint_detail, name="sprint_detail"),
    path("projetos/<int:projeto_id>/sprints/<int:sprint_id>/editar/", views.sprint_update, name="sprint_update"),
    path("projetos/<int:projeto_id>/sprints/<int:sprint_id>/fechar/", views.sprint_fechar, name="sprint_fechar"),
    path("projetos/<int:projeto_id>/sprints/<int:sprint_id>/excluir/", views.sprint_delete, name="sprint_delete"),
    path("projetos/<int:projeto_id>/sprints/<int:sprint_id>/tarefas/<int:tarefa_id>/mover/", views.tarefa_mover_sprint, name="tarefa_mover_sprint"),
    path("projetos/<int:projeto_id>/sprints/<int:sprint_id>/tarefas/<int:tarefa_id>/remover/", views.tarefa_remover_sprint, name="tarefa_remover_sprint"),
    path("projetos/<int:projeto_id>/tarefas/nova/", views.tarefa_projeto_create, name="tarefa_projeto_create"),
    path("projetos/<int:projeto_id>/tarefas/<int:tarefa_id>/", views.tarefa_projeto_detail, name="tarefa_projeto_detail"),
    path("projetos/<int:projeto_id>/tarefas/<int:tarefa_id>/editar/", views.tarefa_projeto_update, name="tarefa_projeto_update"),
    path("projetos/<int:projeto_id>/tarefas/<int:tarefa_id>/excluir/", views.tarefa_projeto_delete, name="tarefa_projeto_delete"),
    
    # Gestão de Contratos (unificado - todos os regimes: Lei 14.133, Lei 13.303 e Privado)
    path("gestao-contratos/", views.gestao_contratos_list, name="gestao_contratos_list"),
    path("gestao-contratos/novo/", views.gestao_contratos_create, name="gestao_contratos_create"),
    path("gestao-contratos/<int:pk>/", views.gestao_contratos_detail, name="gestao_contratos_detail"),
    path("gestao-contratos/<int:pk>/editar/", views.gestao_contratos_update, name="gestao_contratos_update"),
    path("gestao-contratos/<int:pk>/excluir/", views.gestao_contratos_delete, name="gestao_contratos_delete"),
    
    path("gestao-contratos/<int:contrato_id>/termos-aditivos/novo/", views.termo_aditivo_create, name="termo_aditivo_create"),
    path("gestao-contratos/<int:contrato_id>/termos-aditivos/<int:pk>/editar/", views.termo_aditivo_update, name="termo_aditivo_update"),
    path("gestao-contratos/<int:contrato_id>/termos-aditivos/<int:pk>/excluir/", views.termo_aditivo_delete, name="termo_aditivo_delete"),
    
    # Stakeholder Contrato
    path("stakeholder/<int:contrato_id>/criar/", views.stakeholder_contrato_create, name="stakeholder_contrato_create"),
    path("stakeholder/<int:pk>/editar/", views.stakeholder_contrato_update, name="stakeholder_contrato_update"),
    path("stakeholder/<int:pk>/excluir/", views.stakeholder_contrato_delete, name="stakeholder_contrato_delete"),
    
    # Timesheet
    path("timesheet/", views.timesheet_list, name="timesheet_list"),
    path("timesheet/tarefa/<int:tarefa_id>/", views.timesheet_tarefa_detail, name="timesheet_tarefa_detail"),
    path("timesheet/tarefa/<int:tarefa_id>/lancar/", views.timesheet_lancar_horas, name="timesheet_lancar_horas"),
    path("timesheet/lancamento/<int:lancamento_id>/editar/", views.timesheet_editar_lancamento, name="timesheet_editar_lancamento"),
    path("timesheet/lancamento/<int:lancamento_id>/excluir/", views.timesheet_excluir_lancamento, name="timesheet_excluir_lancamento"),
    path("timesheet/planilha/", views.timesheet_planilha, name="timesheet_planilha"),
    path("timesheet/planilha/salvar/", views.timesheet_planilha_salvar, name="timesheet_planilha_salvar"),
    path("timesheet/planilha/excluir/<int:lancamento_id>/", views.timesheet_planilha_excluir, name="timesheet_planilha_excluir"),
    path("timesheet/exportar/", views.timesheet_exportar, name="timesheet_exportar"),
    path("timesheet/importar/", views.timesheet_importar, name="timesheet_importar"),
    path("api/tarefas_por_sprint/", views.api_tarefas_por_sprint, name="api_tarefas_por_sprint"),
    
    # Análise de Contratos com IA
    path("ia-contratos/", views.documento_contrato_list, name="documento_contrato_list"),
    path("ia-contratos/upload/", views.documento_contrato_upload, name="documento_contrato_upload"),
    path("ia-contratos/<int:pk>/", views.documento_contrato_detail, name="documento_contrato_detail"),
    path("ia-contratos/<int:pk>/analisar/", views.documento_contrato_analisar, name="documento_contrato_analisar"),
    path("ia-contratos/<int:pk>/criar-registros/", views.documento_contrato_criar_registros, name="documento_contrato_criar_registros"),
    path("ia-contratos/<int:pk>/excluir/", views.documento_contrato_delete, name="documento_contrato_delete"),
    path("ia-contratos/documento/<int:pk>/download/", views.documento_contrato_download, name="documento_contrato_download"),
    
    # Planos de Trabalho
    path("projetos/<int:projeto_id>/plano-trabalho/gerar/", views.plano_trabalho_gerar, name="plano_trabalho_gerar"),
    path("plano-trabalho/<int:pk>/", views.plano_trabalho_detail, name="plano_trabalho_detail"),
    path("plano-trabalho/<int:pk>/editar/", views.plano_trabalho_update, name="plano_trabalho_update"),
    path("plano-trabalho/<int:pk>/aprovar/", views.plano_trabalho_aprovar, name="plano_trabalho_aprovar"),
    path("plano-trabalho/<int:pk>/rejeitar/", views.plano_trabalho_rejeitar, name="plano_trabalho_rejeitar"),
    path("plano-trabalho/<int:pk>/exportar-pdf/", views.plano_trabalho_exportar_pdf, name="plano_trabalho_exportar_pdf"),
]
