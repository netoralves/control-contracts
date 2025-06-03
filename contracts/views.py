from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, FileResponse
from django.contrib import messages
from django.db.models import Q, Sum, Value, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.utils.encoding import smart_str
from django.views.decorators.http import require_GET
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now
from django.utils.timezone import is_aware
from pandas._libs.tslibs.nattype import NaTType
from datetime import datetime


import csv, os, json, io
import pandas as pd

from .models import (
    Cliente,
    Contrato,
    ItemContrato,
    ItemFornecedor,
    OrdemFornecimento,
    OrdemServico,
    ImportExportLog,
)
from .forms import (
    ClienteForm,
    ContratoForm,
    ItemContratoForm,
    ItemFornecedorForm,
    OrdemFornecimentoForm,
    OrdemServicoForm,
)
from .utils import map_tipo_item_contrato_para_fornecedor


# Controle de Login
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("dashboard")
    if request.method == "POST":
        messages.error(request, "Usuário ou senha inválidos.")

    return render(request, "contracts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


# Dashboard
@login_required
def dashboard(request):
    total_clientes = Cliente.objects.count()
    contratos_ativos = Contrato.objects.filter(situacao="Ativo").count()

    valor_total_contratos = (
        ItemContrato.objects.aggregate(
            total=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("quantidade") * F("valor_unitario"),
                        output_field=DecimalField(max_digits=20, decimal_places=2),
                    )
                ),
                Value(0, output_field=DecimalField(max_digits=20, decimal_places=2)),
            )
        )["total"]
        or 0
    )

    valor_faturado_os = (
        OrdemServico.objects.aggregate(
            total=Coalesce(
                Sum("valor_total"),
                Value(0, output_field=DecimalField(max_digits=20, decimal_places=2)),
            )
        )["total"]
        or 0
    )

    valor_faturado_of = (
        OrdemFornecimento.objects.aggregate(
            total=Coalesce(
                Sum("valor_total"),
                Value(0, output_field=DecimalField(max_digits=20, decimal_places=2)),
            )
        )["total"]
        or 0
    )

    valor_total_faturado = valor_faturado_os + valor_faturado_of

    grafico_faturamento = json.dumps(
        {
            "labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
            "datasets": [
                {
                    "label": "Faturamento",
                    "data": [0, 0, 0, 0, 0, 0],
                    "backgroundColor": "rgba(54, 162, 235, 0.6)",
                }
            ],
        },
        cls=DjangoJSONEncoder,
    )

    grafico_contratos_por_cliente = json.dumps(
        {
            "labels": ["Sem Dados"],
            "datasets": [
                {
                    "label": "Contratos",
                    "data": [1],
                    "backgroundColor": ["rgba(255, 99, 132, 0.6)"],
                }
            ],
        },
        cls=DjangoJSONEncoder,
    )

    context = {
        "total_clientes": total_clientes,
        "contratos_ativos": contratos_ativos,
        "valor_total_contratos": valor_total_contratos,
        "valor_total_faturado": valor_total_faturado,
        "grafico_faturamento": grafico_faturamento,
        "grafico_contratos_por_cliente": grafico_contratos_por_cliente,
    }
    return render(request, "contracts/dashboard.html", context)


# Controle de Permissões
def group_required(*group_names):
    def in_groups(user):
        return user.is_authenticated and (
            bool(user.groups.filter(name__in=group_names)) or user.is_superuser
        )

    return user_passes_test(in_groups)


# APIs para carregamento dinâmico
@require_GET
def api_contratos_por_cliente(request):
    cliente_id = request.GET.get("cliente_id")
    if not cliente_id:
        return JsonResponse({"error": "Cliente não informado."}, status=400)

    contratos = Contrato.objects.filter(cliente_id=cliente_id)
    data = [{"id": c.id, "numero": c.numero_contrato} for c in contratos]
    return JsonResponse({"contratos": data})


@require_GET
def api_itens_contrato_por_contrato(request):
    contrato_id = request.GET.get("contrato_id")
    tipos = request.GET.get("tipo", "").split(",")
    itens = []

    if contrato_id:
        queryset = ItemContrato.objects.filter(contrato_id=contrato_id, tipo__in=tipos)

        for item in queryset:
            itens.append(
                {
                    "id": item.id,
                    "descricao": f"{item.numero_item} - {item.descricao}",
                    "valor_unitario": float(item.valor_unitario),
                }
            )

    return JsonResponse({"itens_contrato": itens})


@require_GET
def api_itens_fornecedor_por_item_contrato(request):
    contrato_id = request.GET.get("contrato")
    item_contrato_id = request.GET.get("item_contrato")

    if not contrato_id or not item_contrato_id:
        return JsonResponse([], safe=False)

    try:
        contrato = Contrato.objects.get(id=contrato_id)
        item_contrato = ItemContrato.objects.get(id=item_contrato_id)
    except (Contrato.DoesNotExist, ItemContrato.DoesNotExist):
        return JsonResponse([], safe=False)

    tipo_item = map_tipo_item_contrato_para_fornecedor(item_contrato.tipo)
    if not tipo_item:
        return JsonResponse([], safe=False)

    fornecedores = [f.upper() for f in contrato.fornecedores]
    itens = ItemFornecedor.objects.filter(
        tipo=tipo_item, fornecedor__in=fornecedores
    ).values("id", "descricao")
    return JsonResponse(list(itens), safe=False)


@require_GET
def api_itens_fornecedor_por_contrato(request):
    contrato_id = request.GET.get("contrato_id")

    if not contrato_id:
        return JsonResponse({"itens_contrato": []})

    try:
        contrato = Contrato.objects.get(id=contrato_id)
    except Contrato.DoesNotExist:
        return JsonResponse({"itens_contrato": []})

    itens = contrato.itens.filter(tipo__in=["servico", "treinamento"]).values(
        "id", "descricao"
    )
    return JsonResponse({"itens_contrato": list(itens)})


# Cliente - Listagem com filtros e paginação
@group_required("Admin", "Gerente", "Leitor")
def cliente_list(request):
    clientes = Cliente.objects.all()

    nome = request.GET.get("nome")
    cidade = request.GET.get("cidade")
    estado = request.GET.get("estado")
    ativo = request.GET.get("ativo")

    if nome:
        clientes = clientes.filter(nome_razao_social__icontains=nome)
    if cidade:
        clientes = clientes.filter(cidade__icontains=cidade)
    if estado:
        clientes = clientes.filter(estado__icontains=estado)
    if ativo == "ativo":
        clientes = clientes.filter(ativo=True)
    elif ativo == "inativo":
        clientes = clientes.filter(ativo=False)

    paginator = Paginator(clientes, 10)
    page = request.GET.get("page")
    clientes_page = paginator.get_page(page)

    return render(request, "cliente/list.html", {"clientes": clientes_page})


# Cliente - Criar
@group_required("Admin", "Gerente")
def cliente_create(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("cliente_list")
    else:
        form = ClienteForm()
    return render(request, "cliente/form.html", {"form": form})


# Cliente - Editar
@group_required("Admin", "Gerente")
def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect("cliente_list")
    else:
        form = ClienteForm(instance=cliente)
    return render(request, "cliente/form.html", {"form": form})


# Cliente - Detalhar
@group_required("Admin", "Gerente", "Leitor")
def cliente_detail(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, "cliente/detail.html", {"cliente": cliente})


# Cliente - Deletar
@group_required("Admin", "Gerente")
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        cliente.delete()
        return redirect("cliente_list")
    return render(request, "cliente/confirm_delete.html", {"cliente": cliente})


# Cliente - Exportação CSV
@group_required("Admin", "Gerente")
def export_clientes_csv(request):
    clientes = Cliente.objects.all()

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="clientes.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "ID",
            "Razão Social",
            "Nome Fantasia",
            "Tipo Cliente",
            "Tipo Pessoa",
            "CNPJ/CPF",
            "Natureza Jurídica",
            "Inscrição Estadual",
            "Inscrição Municipal",
            "Endereço",
            "Número",
            "Complemento",
            "Bairro",
            "Cidade",
            "Estado",
            "CEP",
            "País",
            "Nome Responsável",
            "Cargo Responsável",
            "Telefone Contato",
            "Email Contato",
            "Ativo",
        ]
    )

    for cliente in clientes:
        writer.writerow(
            [
                cliente.id,
                cliente.nome_razao_social,
                cliente.nome_fantasia,
                cliente.tipo_cliente,
                cliente.tipo_pessoa,
                cliente.cnpj_cpf,
                cliente.natureza_juridica,
                cliente.inscricao_estadual,
                cliente.inscricao_municipal,
                cliente.endereco,
                cliente.numero,
                cliente.complemento,
                cliente.bairro,
                cliente.cidade,
                cliente.estado,
                cliente.cep,
                cliente.pais,
                cliente.nome_responsavel,
                cliente.cargo_responsavel,
                cliente.telefone_contato,
                cliente.email_contato,
                "Ativo" if cliente.ativo else "Inativo",
            ]
        )

    return response


# Contrato - Filtros inteligentes
def get_contratos_queryset(request):
    contratos = Contrato.objects.all()

    cliente = request.GET.get("cliente")
    numero = request.GET.get("numero")
    situacao = request.GET.get("situacao")
    fornecedor = request.GET.get("fornecedor")

    if cliente:
        contratos = contratos.filter(
            Q(cliente__nome_razao_social__icontains=cliente)
            | Q(cliente__nome_fantasia__icontains=cliente)
        )

    if numero:
        contratos = contratos.filter(numero_contrato__icontains=numero)

    if situacao:
        contratos = contratos.filter(situacao=situacao)

    if fornecedor:
        contratos = contratos.filter(fornecedores__icontains=fornecedor)

    return contratos.order_by("-data_assinatura")


# Contrato - Listar
@group_required("Admin", "Gerente", "Leitor")
def contrato_list(request):
    contratos = get_contratos_queryset(request)

    paginator = Paginator(contratos, 10)
    page = request.GET.get("page")
    contratos_page = paginator.get_page(page)

    fornecedores_pre_definidos = [
        "iB Services",
        "MVC Security",
        "Red Hat",
        "CyberArk",
        "Trend Micro",
        "Fortinet",
        "Ridge Security",
        "Thales",
        "Viewtinet",
        "Outro Fornecedor",
    ]
    fornecedores_db = ItemFornecedor.objects.values_list(
        "fornecedor", flat=True
    ).distinct()
    fornecedores_lista = sorted(
        set(list(fornecedores_pre_definidos) + list(fornecedores_db))
    )

    return render(
        request,
        "contrato/list.html",
        {"contratos": contratos_page, "fornecedores_lista": fornecedores_lista},
    )


# Contrato - Detalhar
@group_required("Admin", "Gerente", "Leitor")
def contrato_detail(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk)
    return render(request, "contrato/detail.html", {"contrato": contrato})


# Contrato - Criar
@group_required("Admin", "Gerente")
def contrato_create(request):
    if request.method == "POST":
        form = ContratoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("contrato_list")
    else:
        form = ContratoForm()
    return render(request, "contrato/form.html", {"form": form})


# Contrato - Editar
@group_required("Admin", "Gerente")
def contrato_update(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk)
    if request.method == "POST":
        form = ContratoForm(request.POST, instance=contrato)
        if form.is_valid():
            form.save()
            return redirect("contrato_list")
    else:
        form = ContratoForm(instance=contrato)
    return render(request, "contrato/form.html", {"form": form})


# Contrato - Deletar
@group_required("Admin", "Gerente")
def contrato_delete(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk)
    if request.method == "POST":
        contrato.delete()
        return redirect("contrato_list")
    return render(request, "contrato/confirm_delete.html", {"object": contrato})


# Contrato - Exportação CSV
@group_required("Admin", "Gerente")
def export_contratos_csv(request):
    contratos = get_contratos_queryset(request)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="contratos.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "ID",
            "Número Contrato",
            "Cliente",
            "Data Assinatura",
            "Data Fim",
            "Vigência (Meses)",
            "Fornecedores",
            "Valor Total (R$)",
            "Situação",
        ]
    )

    for contrato in contratos:
        writer.writerow(
            [
                contrato.id,
                contrato.numero_contrato,
                contrato.cliente.nome_fantasia or contrato.cliente.nome_razao_social,
                contrato.data_assinatura,
                contrato.data_fim,
                contrato.vigencia,
                ", ".join(contrato.fornecedores),
                float(contrato.valor_global),
                contrato.situacao,
            ]
        )

    return response


# Item de Contrato - Listar com filtros, ordenação e paginação
@group_required("Admin", "Gerente", "Leitor")
def itemcontrato_list(request):
    itens = ItemContrato.objects.all()

    contrato = request.GET.get("contrato")
    tipo = request.GET.get("tipo")
    numero = request.GET.get("numero")
    vigencia = request.GET.get("vigencia_produto")
    lote = request.GET.get("lote")

    if contrato:
        itens = itens.filter(
            Q(contrato__numero_contrato__icontains=contrato)
            | Q(contrato__cliente__nome_razao_social__icontains=contrato)
            | Q(contrato__cliente__nome_fantasia__icontains=contrato)
        )

    if tipo:
        itens = itens.filter(tipo=tipo)

    if numero:
        itens = itens.filter(numero_item__icontains=numero)

    if vigencia:
        itens = itens.filter(vigencia_produto=vigencia)

    if lote:
        itens = itens.filter(lote=lote)

    itens = itens.order_by("contrato__numero_contrato", "lote", "numero_item")

    paginator = Paginator(itens, 10)
    page = request.GET.get("page")
    itens_page = paginator.get_page(page)

    return render(request, "item_contrato/list.html", {"itens": itens_page})


# Item de Contrato - Criar
@group_required("Admin", "Gerente")
def itemcontrato_create(request):
    if request.method == "POST":
        form = ItemContratoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("item_contrato_list")
    else:
        form = ItemContratoForm()
    return render(request, "item_contrato/form.html", {"form": form})


# Item de Contrato - Editar
@group_required("Admin", "Gerente")
def itemcontrato_update(request, pk):
    item = get_object_or_404(ItemContrato, pk=pk)
    if request.method == "POST":
        form = ItemContratoForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect("item_contrato_list")
    else:
        form = ItemContratoForm(instance=item)
    return render(request, "item_contrato/form.html", {"form": form})


# Item de Contrato - Detalhar
@group_required("Admin", "Gerente", "Leitor")
def itemcontrato_detail(request, pk):
    item = get_object_or_404(ItemContrato, pk=pk)
    return render(request, "item_contrato/detail.html", {"item": item})


# Item de Contrato - Deletar
@group_required("Admin", "Gerente")
def itemcontrato_delete(request, pk):
    item = get_object_or_404(ItemContrato, pk=pk)
    if request.method == "POST":
        item.delete()
        return redirect("item_contrato_list")
    return render(request, "item_contrato/confirm_delete.html", {"object": item})


# Item de Contrato - Exportação CSV
@group_required("Admin", "Gerente")
def export_item_contrato_csv(request):
    itens = ItemContrato.objects.all()

    contrato = request.GET.get("contrato")
    tipo = request.GET.get("tipo")
    numero = request.GET.get("numero")
    vigencia = request.GET.get("vigencia_produto")
    lote = request.GET.get("lote")

    if contrato:
        itens = itens.filter(
            Q(contrato__numero_contrato__icontains=contrato)
            | Q(contrato__cliente__nome_razao_social__icontains=contrato)
            | Q(contrato__cliente__nome_fantasia__icontains=contrato)
        )

    if tipo:
        itens = itens.filter(tipo=tipo)

    if numero:
        itens = itens.filter(numero_item__icontains=numero)

    if vigencia:
        itens = itens.filter(vigencia_produto=vigencia)

    if lote:
        itens = itens.filter(lote=lote)

    itens = itens.order_by("contrato__numero_contrato", "lote", "numero_item")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="itens_contrato.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "ID",
            "Lote",
            "Número Item",
            "Contrato",
            "Cliente",
            "Descrição",
            "Tipo",
            "Unidade",
            "Quantidade Contratada",
            "Quantidade Consumida",
            "Saldo de Quantidade",
            "Valor Unitário (R$)",
            "Valor Total (R$)",
            "Valor Faturado (R$)",
            "Valor Saldo (R$)",
            "Vigência do Produto (meses)",
        ]
    )

    for item in itens:
        writer.writerow(
            [
                item.id,
                item.lote,
                item.numero_item,
                item.contrato.numero_contrato,
                item.contrato.cliente.nome_fantasia
                or item.contrato.cliente.nome_razao_social,
                item.descricao,
                item.tipo,
                item.unidade,
                item.quantidade,
                item.quantidade_consumida,
                item.saldo_quantidade,
                float(item.valor_unitario),
                float(item.valor_total),
                float(item.valor_faturado),
                float(item.valor_saldo),
                item.vigencia_produto if item.vigencia_produto else "",
            ]
        )

    return response


# Item de Fornecedor - Listar com filtros e paginação
@group_required("Admin", "Gerente", "Leitor")
def itemfornecedor_list(request):
    itens = ItemFornecedor.objects.all()

    fornecedor = request.GET.get("fornecedor")
    tipo = request.GET.get("tipo")

    if fornecedor:
        itens = itens.filter(fornecedor=fornecedor)

    if tipo:
        itens = itens.filter(tipo=tipo)

    paginator = Paginator(itens, 10)
    page = request.GET.get("page")
    itens_page = paginator.get_page(page)

    context = {"itens": itens_page, "fornecedor": fornecedor, "tipo": tipo}
    return render(request, "item_fornecedor/list.html", context)


# Item de Fornecedor - Detalhar
@group_required("Admin", "Gerente", "Leitor")
def itemfornecedor_detail(request, pk):
    item = get_object_or_404(ItemFornecedor, pk=pk)
    return render(request, "item_fornecedor/detail.html", {"item": item})


# Item de Fornecedor - Criar
@group_required("Admin", "Gerente")
def itemfornecedor_create(request):
    if request.method == "POST":
        form = ItemFornecedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("item_fornecedor_list")
    else:
        form = ItemFornecedorForm()
    return render(request, "item_fornecedor/form.html", {"form": form})


# Item de Fornecedor - Editar
@group_required("Admin", "Gerente")
def itemfornecedor_update(request, pk):
    item = get_object_or_404(ItemFornecedor, pk=pk)
    if request.method == "POST":
        form = ItemFornecedorForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect("item_fornecedor_list")
    else:
        form = ItemFornecedorForm(instance=item)
    return render(request, "item_fornecedor/form.html", {"form": form})


# Item de Fornecedor - Deletar
@group_required("Admin", "Gerente")
def itemfornecedor_delete(request, pk):
    item = get_object_or_404(ItemFornecedor, pk=pk)
    if request.method == "POST":
        item.delete()
        return redirect("item_fornecedor_list")
    return render(request, "item_fornecedor/confirm_delete.html", {"object": item})


# Item de Fornecedor - Exportação CSV
@group_required("Admin", "Gerente")
def export_item_fornecedor_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="itens_fornecedor.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "ID",
            "Fornecedor",
            "Outro Fornecedor",
            "Tipo",
            "SKU",
            "Descrição",
            "Unidade",
            "Valor Unitário",
            "Observações",
        ]
    )

    itens = ItemFornecedor.objects.all()
    for item in itens:
        writer.writerow(
            [
                item.id,
                item.fornecedor,
                item.outro_fornecedor if item.fornecedor == "Outro Fornecedor" else "",
                item.tipo,
                item.sku,
                item.descricao,
                item.unidade,
                f"{item.valor_unitario:.2f}".replace(".", ","),
                item.observacoes or "",
            ]
        )

    return response


# Todas as colunas disponíveis
colunas = [
    {"id": "numero", "label": "Número"},
    {"id": "cliente", "label": "Cliente"},
    {"id": "contrato", "label": "Contrato"},
    {"id": "itemcontrato", "label": "Item Contrato"},
    {"id": "itemfornecedor", "label": "Item Fornecedor"},
    {"id": "unidade", "label": "Unidade"},
    {"id": "quantidade", "label": "Quantidade"},
    {"id": "vigencia_produto", "label": "Vigência do Produto (meses)"},
    {"id": "valor_unitario", "label": "Valor Unitário"},
    {"id": "valor_total", "label": "Valor Total"},
    {"id": "data_ativacao", "label": "Data Ativação"},
    {"id": "data_faturamento", "label": "Data Faturamento"},
    {"id": "observacoes", "label": "Observações"},
    {"id": "status", "label": "Status"},
]


# Ordem de Fornecimento - Listar
@group_required("Admin", "Gerente", "Leitor")
def ordemfornecimento_list(request):
    ordens = OrdemFornecimento.objects.all()

    # Filtros
    numero = request.GET.get("numero")
    cliente = request.GET.get("cliente")
    status = request.GET.get("status")

    if numero:
        ordens = ordens.filter(numero_of__icontains=numero)
    if cliente:
        ordens = ordens.filter(cliente__nome_fantasia__icontains=cliente)
    if status:
        ordens = ordens.filter(status=status)

    context = {
        "ordens": ordens,
        "colunas": colunas,
    }
    return render(request, "ordem_fornecimento/list.html", context)


# Ordem de Fornecimento - Detalhar
@group_required("Admin", "Gerente", "Leitor")
def ordemfornecimento_detail(request, pk):
    ordem = get_object_or_404(OrdemFornecimento, pk=pk)
    return render(request, "ordem_fornecimento/detail.html", {"ordem": ordem})


# Ordem de Fornecimento - Criar
@group_required("Admin", "Gerente")
def ordemfornecimento_create(request):
    if request.method == "POST":
        form = OrdemFornecimentoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ordem de Fornecimento criada com sucesso.")
            return redirect("ordem_fornecimento_list")
    else:
        form = OrdemFornecimentoForm()
    return render(request, "ordem_fornecimento/form.html", {"form": form})


# Ordem de Fornecimento - Editar
@group_required("Admin", "Gerente")
def ordemfornecimento_update(request, pk):
    ordem = get_object_or_404(OrdemFornecimento, pk=pk)
    if request.method == "POST":
        form = OrdemFornecimentoForm(request.POST, instance=ordem)
        if form.is_valid():
            form.save()
            messages.success(request, "Ordem de Fornecimento atualizada com sucesso.")
            return redirect("ordem_fornecimento_list")
    else:
        form = OrdemFornecimentoForm(instance=ordem)
    return render(request, "ordem_fornecimento/form.html", {"form": form})


# Ordem de Fornecimento - Deletar
@group_required("Admin", "Gerente")
def ordemfornecimento_delete(request, pk):
    ordem = get_object_or_404(OrdemFornecimento, pk=pk)
    if request.method == "POST":
        ordem.delete()
        messages.success(request, "Ordem de Fornecimento excluída com sucesso.")
        return redirect("ordem_fornecimento_list")
    return render(request, "ordem_fornecimento/confirm_delete.html", {"ordem": ordem})


# Ordem de Fornecimento - Exportação CSV
@group_required("Admin", "Gerente", "Leitor")
def export_ordemfornecimento_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="ordens_fornecimento.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "ID",
            "Número OF",
            "Número OF Cliente",
            "Cliente",
            "Contrato",
            "Item do Contrato",
            "Item do Fornecedor",
            "Unidade",
            "Quantidade",
            "Vigência Produto",
            "Valor Unitário",
            "Valor Total",
            "Status",
            "Data Ativação",
            "Data Faturamento",
            "Observações",
            "Criado em",
            "Atualizado em",
        ]
    )

    ordens = OrdemFornecimento.objects.all()

    for ordem in ordens:
        writer.writerow(
            [
                ordem.id,
                smart_str(ordem.numero_of),
                smart_str(ordem.numero_of_cliente),
                smart_str(ordem.cliente.nome_fantasia),
                smart_str(ordem.contrato.numero),
                smart_str(ordem.item_contrato.descricao),
                smart_str(ordem.item_fornecedor.descricao),
                smart_str(ordem.unidade),
                ordem.quantidade,
                ordem.vigencia_produto,
                ordem.valor_unitario,
                ordem.valor_total,
                ordem.get_status_display(),
                ordem.data_ativacao.strftime("%d/%m/%Y") if ordem.data_ativacao else "",
                (
                    ordem.data_faturamento.strftime("%d/%m/%Y")
                    if ordem.data_faturamento
                    else ""
                ),
                smart_str(ordem.observacoes),
                (
                    ordem.criado_em.strftime("%d/%m/%Y %H:%M:%S")
                    if ordem.criado_em
                    else ""
                ),
                (
                    ordem.atualizado_em.strftime("%d/%m/%Y %H:%M:%S")
                    if ordem.atualizado_em
                    else ""
                ),
            ]
        )

    return response


# Ordem de Serviço - Listar com filtros e paginação
@group_required("Admin", "Gerente", "Técnico")
def ordemservico_list(request):
    ordens = OrdemServico.objects.all()

    numero = request.GET.get("numero")
    cliente = request.GET.get("cliente")
    status = request.GET.get("status")

    if numero:
        ordens = ordens.filter(numero_os__icontains=numero)

    if cliente:
        ordens = ordens.filter(cliente__nome_fantasia__icontains=cliente)

    if status:
        ordens = ordens.filter(status=status)

    paginator = Paginator(ordens.order_by("-data_inicio"), 10)
    page = request.GET.get("page")
    ordens_page = paginator.get_page(page)

    colunas = [
        {"id": "numero", "label": "Número OS"},
        {"id": "numero_cliente", "label": "Número OS Cliente"},
        {"id": "cliente", "label": "Cliente"},
        {"id": "contrato", "label": "Contrato"},
        {"id": "itemcontrato", "label": "Item do Contrato"},
        {"id": "itemfornecedor", "label": "Item do Fornecedor"},
        {"id": "unidade", "label": "Unidade"},
        {"id": "quantidade", "label": "Quantidade"},
        {"id": "valor_unitario", "label": "Valor Unitário"},
        {"id": "valor_total", "label": "Valor Total"},
        {"id": "gerente_projetos", "label": "Gerente de Projetos"},
        {"id": "consultor_tecnico", "label": "Consultor Técnico"},
        {"id": "data_inicio", "label": "Data Início"},
        {"id": "hora_inicio", "label": "Hora Início"},
        {"id": "data_termino", "label": "Data Término"},
        {"id": "hora_termino", "label": "Hora Término"},
        {"id": "status", "label": "Status"},
        {"id": "data_emissao_trd", "label": "Data Emissão TRD"},
        {"id": "data_faturamento", "label": "Data Faturamento"},
        {"id": "horas_consultor", "label": "Horas Consultor"},
        {"id": "horas_gerente", "label": "Horas Gerente"},
        {"id": "horas_totais", "label": "Horas Totais"},
    ]

    context = {
        "ordens": ordens_page,
        "colunas": colunas,
        "filtro_numero": numero or "",
        "filtro_cliente": cliente or "",
        "filtro_status": status or "",
    }
    return render(request, "ordem_servico/list.html", context)


# Ordem de Serviço - Detalhar
@group_required("Admin", "Gerente", "Técnico")
def ordemservico_detail(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    return render(request, "ordem_servico/detail.html", {"ordem": ordem})


# Ordem de Serviço - Criar
@group_required("Admin", "Gerente")
def ordemservico_create(request):
    contrato_id = request.GET.get("contrato")
    if request.method == "POST":
        form = OrdemServicoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("ordem_servico_list")
    else:
        form = OrdemServicoForm(initial={"contrato": contrato_id})
    return render(request, "ordem_servico/form.html", {"form": form})


# Ordem de Serviço - Editar
@group_required("Admin", "Gerente")
def ordemservico_update(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)

    if request.method == "POST":
        form = OrdemServicoForm(request.POST, instance=ordem)
        if form.is_valid():
            form.save()
            return redirect("ordem_servico_list")
    else:
        form = OrdemServicoForm(instance=ordem)

    return render(request, "ordem_servico/form.html", {"form": form})


# Ordem de Serviço - Deletar
@group_required("Admin", "Gerente")
def ordemservico_delete(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    if request.method == "POST":
        ordem.delete()
        return redirect("ordem_servico_list")
    return render(request, "ordem_servico/confirm_delete.html", {"object": ordem})


# Ordem de Serviço - Exportação CSV
@group_required("Admin", "Gerente", "Técnico")
def export_ordemservico_csv(request):
    ordens = OrdemServico.objects.all()

    contrato = request.GET.get("contrato")
    cliente = request.GET.get("cliente")
    status = request.GET.get("status")

    if contrato:
        ordens = ordens.filter(contrato__numero_contrato__icontains=contrato)

    if cliente:
        ordens = ordens.filter(cliente__nome_fantasia__icontains=cliente)

    if status:
        ordens = ordens.filter(status=status)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="ordens_servico.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "ID",
            "Número OS",
            "Número OS Cliente",
            "Cliente",
            "Contrato",
            "Item Contrato",
            "Item Fornecedor",
            "Quantidade",
            "Valor Unitário (R$)",
            "Valor Total (R$)",
            "Status",
            "Data Início",
            "Hora Início",
            "Data Término",
            "Hora Término",
            "Data Emissão TRD",
            "Data Faturamento",
        ]
    )

    for ordem in ordens:
        writer.writerow(
            [
                ordem.id,
                ordem.numero_os,
                ordem.numero_os_cliente,
                ordem.cliente.nome_fantasia,
                ordem.contrato.numero_contrato,
                ordem.item_contrato.descricao,
                ordem.item_fornecedor.descricao,
                ordem.quantidade,
                float(ordem.valor_unitario),
                float(ordem.valor_total),
                ordem.get_status_display(),
                ordem.data_inicio,
                ordem.hora_inicio,
                ordem.data_termino or "",
                ordem.hora_termino or "",
                ordem.data_emissao_trd or "",
                ordem.data_faturamento or "",
            ]
        )

    return response


@require_http_methods(["GET", "POST"])
def import_export_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        try:
            excel_file = pd.ExcelFile(file)

            # Clientes
            Cliente.objects.all().delete()
            df_clientes = pd.read_excel(excel_file, sheet_name="Clientes")
            for _, row in df_clientes.iterrows():
                Cliente.objects.create(**row.to_dict())

            # Contratos
            Contrato.objects.all().delete()
            df_contratos = pd.read_excel(excel_file, sheet_name="Contratos")
            for _, row in df_contratos.iterrows():
                cliente = Cliente.objects.get(id=row["cliente_id"])
                fornecedores = (
                    eval(row["fornecedores"])
                    if isinstance(row["fornecedores"], str)
                    else []
                )
                Contrato.objects.create(
                    cliente=cliente,
                    numero=row["numero"],
                    data_assinatura=row["data_assinatura"],
                    data_fim=row["data_fim"],
                    valor_total=row["valor_total"],
                    situacao=row["situacao"],
                    fornecedores=fornecedores,
                )

            # Itens de Contrato
            ItemContrato.objects.all().delete()
            df_itens_contrato = pd.read_excel(excel_file, sheet_name="ItensContrato")
            for _, row in df_itens_contrato.iterrows():
                contrato = Contrato.objects.get(id=row["contrato_id"])
                ItemContrato.objects.create(
                    contrato=contrato, **row.drop("contrato_id").to_dict()
                )

            # Itens de Fornecedor
            ItemFornecedor.objects.all().delete()
            df_itens_fornecedor = pd.read_excel(
                excel_file, sheet_name="ItensFornecedor"
            )
            for _, row in df_itens_fornecedor.iterrows():
                ItemFornecedor.objects.create(**row.to_dict())

            # Ordens de Serviço
            OrdemServico.objects.all().delete()
            df_os = pd.read_excel(excel_file, sheet_name="OrdensServico")
            for _, row in df_os.iterrows():
                OrdemServico.objects.create(**row.to_dict())

            # Ordens de Fornecimento
            OrdemFornecimento.objects.all().delete()
            df_of = pd.read_excel(excel_file, sheet_name="OrdensFornecimento")
            for _, row in df_of.iterrows():
                OrdemFornecimento.objects.create(**row.to_dict())

            messages.success(request, "Dados importados com sucesso!")
        except Exception as e:
            messages.error(request, f"Erro na importação: {str(e)}")

        return redirect("import_export_view")

    return render(request, "import_export/import_export.html")


def export_excel_view(request):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine="openpyxl")

    models_and_sheets = [
        (Cliente, "Clientes"),
        (Contrato, "Contratos"),
        (ItemContrato, "ItensContrato"),
        (ItemFornecedor, "ItensFornecedor"),
        (OrdemFornecimento, "OrdensFornecimento"),
        (OrdemServico, "OrdensServico"),
    ]

    for model, sheet_name in models_and_sheets:
        queryset = model.objects.all().values()
        df = pd.DataFrame.from_records(queryset)
        df = clean_datetimes(df)
        df.to_excel(writer, sheet_name=sheet_name, index=False)

    writer.close()
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        "attachment; filename=ControleContratos_Exportado.xlsx"
    )
    return response


def clean_datetimes(df):
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].apply(
                lambda x: (
                    x.replace(tzinfo=None)
                    if isinstance(x, datetime) and is_aware(x)
                    else x
                )
            )
        elif df[col].dtype == "object":
            # Tenta converter strings para datetime e remover fuso se necessário
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                df[col] = df[col].apply(
                    lambda x: (
                        x.replace(tzinfo=None)
                        if isinstance(x, datetime) and is_aware(x)
                        else x
                    )
                )
            except Exception:
                pass
    return df


# Visualizar Logs de Importação e Exportação
@group_required("Admin", "Gerente")
def logs_import_export(request):
    logs = ImportExportLog.objects.order_by("-data")
    return render(request, "import_export/import_export_logs.html", {"logs": logs})
