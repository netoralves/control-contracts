from django.contrib import admin
from .models import (
    Cliente,
    Contrato,
    ItemContrato,
    ItemFornecedor,
    OrdemFornecimento,
    OrdemServico,
)
from babel.numbers import format_currency


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        "nome_razao_social",
        "nome_fantasia",
        "tipo_cliente",
        "cnpj_cpf",
        "cidade",
        "estado",
        "ativo",
    )
    search_fields = (
        "nome_razao_social",
        "nome_fantasia",
        "cnpj_cpf",
        "cidade",
        "estado",
    )
    list_filter = ("tipo_cliente", "tipo_pessoa", "estado", "ativo")
    ordering = ("nome_razao_social",)


@admin.register(ItemFornecedor)
class ItemFornecedorAdmin(admin.ModelAdmin):
    list_display = (
        "descricao",
        "fornecedor",
        "tipo",
        "sku",
        "unidade",
        "valor_unitario",
    )
    search_fields = ("descricao", "sku", "fornecedor")
    list_filter = ("fornecedor", "tipo")
    ordering = ["descricao"]

    def nome_fornecedor(self, obj):
        return obj.nome_fornecedor()

    nome_fornecedor.short_description = "Fornecedor"


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_contrato",
        "cliente",
        "data_assinatura",
        "data_fim",
        "vigencia",
        "valor_total_display",
    )
    search_fields = (
        "numero_contrato",
        "cliente__nome_razao_social",
        "cliente__nome_fantasia",
    )
    list_filter = ("vigencia", "data_assinatura")
    ordering = ("-data_assinatura",)

    def valor_total_display(self, obj):
        return f"R$ {obj.valor_total:,.2f}"

    valor_total_display.short_description = "Valor Total"


@admin.register(ItemContrato)
class ItemContratoAdmin(admin.ModelAdmin):
    list_display = [
        "numero_item",
        "descricao_curta",
        "tipo",
        "quantidade",
        "saldo_quantidade_inicial",
        "get_saldo_quantidade_atual_display",
        "valor_unitario",
        "valor_total",
        "get_saldo_disponivel_formatado_display",
        "contrato",
        "lote",
    ]
    list_filter = ("contrato", "tipo", "lote")
    search_fields = ("numero_item", "descricao", "contrato__numero_contrato")
    readonly_fields = ("valor_total", "saldo_quantidade_inicial", "saldo_disponivel", "saldo_disponivel_formatado") # Campos calculados
    
    fieldsets = (
        (None, {
            'fields': ('contrato', 'lote', 'numero_item', 'descricao', 'tipo')
        }),
        ('Quantidades e Valores', {
            'fields': ('unidade', 'quantidade', 'valor_unitario', 'valor_total', 
                       'saldo_quantidade_inicial', 'quantidade_consumida', 'saldo_quantidade_atual',
                       'saldo_disponivel', 'saldo_disponivel_formatado')
        }),
        ('Vigência (para Produtos)', {
            'fields': ('vigencia_produto',),
            'classes': ('collapse',), # Opcional, para agrupar
        }),
    )    

    def descricao_curta(self, obj):
        return (obj.descricao[:75] + '...') if len(obj.descricao) > 75 else obj.descricao
    descricao_curta.short_description = 'Descrição'

    def get_saldo_quantidade_atual_display(self, obj):
        return obj.saldo_quantidade_atual # A propriedade já calcula
    get_saldo_quantidade_atual_display.short_description = 'Saldo Qtd. Atual' # Nome da coluna no admin

    def get_saldo_disponivel_formatado_display(self, obj):
        return obj.saldo_disponivel_formatado # A propriedade já formata
    get_saldo_disponivel_formatado_display.short_description = 'Saldo R$ Disponível'

@admin.register(OrdemFornecimento)
class OrdemFornecimentoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_of",
        "cliente",
        "contrato",
        "item_contrato",
        "quantidade",
        "status",
        "data_ativacao",
        "data_faturamento",
        "valor_total_display",
    )
    search_fields = (
        "numero",
        "contrato__numero_contrato",
        "cliente__nome_razao_social",
    )
    list_filter = ("status", "data_ativacao", "data_faturamento")
    ordering = ("-data_ativacao",)

    def valor_unitario_formatado(self, obj):
        return format_currency(obj.valor_unitario, "BRL", locale="pt_BR")

    valor_unitario_formatado.short_description = "Valor Unitário"

    def valor_total_formatado(self, obj):
        return format_currency(obj.valor_total, "BRL", locale="pt_BR")

    valor_total_formatado.short_description = "Valor Total"

    def valor_total_display(self, obj):
        return (
            f"R$ {obj.valor_total:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    valor_total_display.short_description = "Valor Total"


@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_os",
        "cliente",
        "contrato",
        "item_contrato",
        "status",
        "data_inicio",
        "data_termino",
        "data_faturamento",
    )

    search_fields = (
        "numero_os",
        "numero_os_cliente",
        "contrato__numero_contrato",
        "cliente__nome_razao_social",
        "cliente__nome_fantasia",
    )

    list_filter = (
        "status",
        "data_inicio",
        "data_termino",
        "data_faturamento",
    )

    ordering = ("-data_inicio",)
