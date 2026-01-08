from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, datetime, time, date
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, F, FloatField, ExpressionWrapper, Value, DecimalField
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
from django.contrib.auth.models import User
import os
import uuid

from .constants import FORNECEDORES_MAP, TIPOS_ITEM_FORNECEDOR_CHOICES


class Cliente(models.Model):
    TIPO_CLIENTE = [("publico", "Público"), ("privado", "Privado")]
    TIPO_PESSOA = [("fisica", "Física"), ("juridica", "Jurídica")]

    nome_razao_social = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True)
    tipo_cliente = models.CharField(max_length=10, choices=TIPO_CLIENTE)
    tipo_pessoa = models.CharField(max_length=10, choices=TIPO_PESSOA)
    cnpj_cpf = models.CharField(max_length=18, unique=True)
    natureza_juridica = models.CharField(max_length=100, blank=True, null=True)
    inscricao_estadual = models.CharField(max_length=50, blank=True, null=True)
    inscricao_municipal = models.CharField(max_length=50, blank=True, null=True)
    endereco = models.CharField(max_length=255)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    cep = models.CharField(max_length=10)
    pais = models.CharField(max_length=50, default="Brasil")
    nome_responsavel = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nome do Responsável")
    cargo_responsavel = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cargo do Responsável")
    telefone_contato = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone de Contato")
    email_contato = models.EmailField(blank=True, null=True, verbose_name="E-mail de Contato")
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateField(auto_now_add=True)
    
    # Novos campos para Gestão de Clientes
    gerente_comercial = models.ForeignKey(
        "Colaborador",
        on_delete=models.SET_NULL,
        related_name="clientes_comercial",
        blank=True,
        null=True,
        verbose_name="Gerente Comercial da Conta",
        limit_choices_to={"cargo__icontains": "comercial"}
    )
    gerente_sucessos = models.ForeignKey(
        "Colaborador",
        on_delete=models.SET_NULL,
        related_name="clientes_sucessos",
        blank=True,
        null=True,
        verbose_name="Gerente de Sucessos",
        limit_choices_to={"cargo__icontains": "sucessos"}
    )

    def __str__(self):
        return self.nome_fantasia or self.nome_razao_social


class ContatoCliente(models.Model):
    """Contatos do cliente - permite múltiplos contatos por cliente"""
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="contatos",
        verbose_name="Cliente"
    )
    nome = models.CharField(
        max_length=100,
        verbose_name="Nome"
    )
    email = models.EmailField(
        verbose_name="E-mail"
    )
    telefone = models.CharField(
        max_length=20,
        verbose_name="Telefone"
    )
    funcao = models.CharField(
        max_length=100,
        verbose_name="Função",
        blank=True,
        null=True
    )
    principal = models.BooleanField(
        default=False,
        verbose_name="Contato Principal",
        help_text="Marcar como contato principal do cliente"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    class Meta:
        verbose_name = "Contato do Cliente"
        verbose_name_plural = "Contatos do Cliente"
        ordering = ["-principal", "nome"]

    def __str__(self):
        return f"{self.nome} - {self.email} ({self.cliente.nome_razao_social})"


class ItemFornecedor(models.Model):
    FORNECEDORES_CHOICES = [
        ("iB Services", "iB Services"),
        ("MVC Security", "MVC Security"),
        ("Red Hat", "Red Hat"),
        ("CyberArk", "CyberArk"),
        ("Trend Micro", "Trend Micro"),
        ("Fortinet", "Fortinet"),
        ("Ridge Security", "Ridge Security"),
        ("Thales", "Thales"),
        ("Viewtinet", "Viewtinet"),
        ("Outro Fornecedor", "Outro Fornecedor"),
    ]

    fornecedor = models.CharField(
        max_length=100,
        choices=FORNECEDORES_CHOICES,
        default="iB Services",
        verbose_name="Fornecedor",
    )
    outro_fornecedor = models.CharField(max_length=100, blank=True, null=True)
    tipo = models.CharField(
        max_length=30, 
        choices=TIPOS_ITEM_FORNECEDOR_CHOICES,
        verbose_name="Tipo"
    )
    sku = models.CharField(max_length=100)
    descricao = models.TextField()
    unidade = models.CharField(max_length=50)
    valor_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    observacoes = models.TextField(blank=True, null=True)

    @property
    def nome_fornecedor(self):
        if self.fornecedor == "Outro Fornecedor" and self.outro_fornecedor:
            return self.outro_fornecedor
        return self.fornecedor

    def __str__(self):
        return f"{self.sku} - {self.descricao} ({self.nome_fornecedor})"

    def save(self, *args, **kwargs):
        self.fornecedor = self.fornecedor.strip().upper()
        super().save(*args, **kwargs)


class RegimeLegal(models.TextChoices):
    """Regime legal do contrato - Leis brasileiras"""
    LEI_14133 = "LEI_14133", "Lei 14.133/2021 (Licitações e Contratos)"
    LEI_13303 = "LEI_13303", "Lei 13.303/2016 (Estatuto Jurídico da Empresa Pública)"
    PRIVADO = "PRIVADO", "Contrato Privado"


class TipoTermoAditivo(models.TextChoices):
    """Tipos de termo aditivo"""
    PRORROGACAO = "PRORROGACAO", "Prorrogação"
    VALOR = "VALOR", "Aditivo de Valor"
    REEQUILIBRIO = "REEQUILIBRIO", "Reequilíbrio Econômico-Financeiro"


class Contrato(models.Model):
    VIGENCIA_CHOICES = [(12, "12 meses"), (24, "24 meses"), (36, "36 meses"), (48, "48 meses"), (60, "60 meses"), (120, "120 meses")]

    class OrigemContrato(models.TextChoices):
        # Administração Pública - Lei 14.133/21
        LIC_14133_PROPRIA = "LIC_14133_PROPRIA", "Licitação própria (Lei 14.133)"
        ARP_GERENCIADOR = "ARP_GERENCIADOR", "Ata de Registro de Preços – órgão gerenciador"
        ARP_PARTICIPANTE = "ARP_PARTICIPANTE", "Ata de Registro de Preços – órgão participante"
        ARP_ADESAO_CARONA = "ARP_ADESAO_CARONA", "Adesão tardia (carona) a ARP"
        DISPENSA_14133 = "DISPENSA_14133", "Dispensa de licitação (Lei 14.133)"
        INEXIGIBILIDADE_14133 = "INEXIGIBILIDADE_14133", "Inexigibilidade de licitação (Lei 14.133)"

        # Empresas Estatais – Lei 13.303/16
        LIC_13303_PROPRIA = "LIC_13303_PROPRIA", "Licitação própria (Lei 13.303)"
        CONTR_ESTATAL_DIRETA = "CONTR_ESTATAL_DIRETA", "Contratação direta (Lei 13.303)"

        # Setor Privado / Híbrido
        RFP_PRIVADA = "RFP_PRIVADA", "RFP (setor privado)"
        RFQ_PRIVADA = "RFQ_PRIVADA", "Cotação / RFQ (setor privado)"
        NEGOCIACAO_DIRETA_PRIVADA = "NEGOCIACAO_DIRETA_PRIVADA", "Negociação direta (setor privado)"
        FRAMEWORK_PRIVADO = "FRAMEWORK_PRIVADO", "Contrato derivado de Master/Framework"

        OUTRO = "OUTRO", "Outro"

    cliente = models.ForeignKey(
        "Cliente", on_delete=models.CASCADE, related_name="contratos"
    )

    numero_contrato = models.CharField(
        "Número do Contrato", max_length=100, unique=True
    )
    ata_registro_preco = models.CharField("ARP", max_length=100, blank=True, null=True)
    pregao_eletronico = models.CharField(
        "Pregão Eletrônico", max_length=100, blank=True, null=True
    )
    processo = models.CharField("Processo", max_length=100, blank=True, null=True)
    termo_referencia = models.CharField(
        "Termo de Referência (TR)", max_length=100, blank=True, null=True
    )
    
    # Campos adicionais para licitações
    modalidade_licitacao = models.CharField(
        "Modalidade de Licitação",
        max_length=100,
        blank=True,
        null=True,
        help_text="Ex: Pregão Eletrônico, Tomada de Preços, Concorrência, Dispensa, Inexigibilidade"
    )
    numero_edital = models.CharField(
        "Número do Edital",
        max_length=100,
        blank=True,
        null=True,
        help_text="Número do edital de licitação"
    )
    
    # Campos adicionais para ARPs
    orgao_gerenciador_arp = models.CharField(
        "Órgão Gerenciador da ARP",
        max_length=255,
        blank=True,
        null=True,
        help_text="Nome do órgão que gerenciou a Ata de Registro de Preços"
    )
    
    # Campos adicionais para contratos privados
    numero_rfp_rfq = models.CharField(
        "Número do RFP/RFQ",
        max_length=100,
        blank=True,
        null=True,
        help_text="Número do RFP (Request for Proposal) ou RFQ (Request for Quotation)"
    )
    
    objeto = models.TextField(
        "Objeto do Contrato",
        blank=True,
        null=True,
        help_text="Descrição do objeto do contrato"
    )

    # Origem do contrato (licitação própria, ARP, RFP, dispensa, etc.)
    origem_contrato = models.CharField(
        "Origem do Contrato",
        max_length=40,
        choices=OrigemContrato.choices,
        default=OrigemContrato.RFP_PRIVADA,
        help_text="Identifica se o contrato veio de licitação própria, ARP, RFP, dispensa, inexigibilidade, etc."
    )

    origem_contrato_detalhe = models.CharField(
        "Detalhe da Origem (opcional)",
        max_length=255,
        blank=True,
        null=True,
        help_text="Informações complementares sobre a origem (ex: nº do edital, fundamento legal específico, descrição livre)."
    )

    origem_contrato_justificativa_ia = models.TextField(
        "Justificativa da Origem (IA)",
        blank=True,
        null=True,
        help_text="Resumo gerado pela IA explicando por que esta origem foi identificada."
    )

    origem_contrato_confianca_ia = models.DecimalField(
        "Confiança da Origem (IA)",
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Score de confiança da IA para a origem identificada (0–1, ex: 0.85)."
    )

    # Campos unificados de Contratos Públicos
    regime_legal = models.CharField(
        "Regime Legal",
        max_length=20,
        choices=RegimeLegal.choices,
        default=RegimeLegal.PRIVADO,
        help_text="Regime legal aplicável ao contrato"
    )
    valor_inicial = models.DecimalField(
        "Valor Inicial",
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,  # Calculado automaticamente como soma dos valores totais dos itens
        help_text="Valor inicial do contrato em R$ (calculado automaticamente)"
    )

    vigencia = models.IntegerField("Vigência Original (meses)", choices=VIGENCIA_CHOICES)
    data_assinatura = models.DateField("Data de Assinatura/Início")
    # data_fim agora é calculado - mantido para compatibilidade mas não editável diretamente
    data_fim = models.DateField("Data de Fim", blank=True, null=True, editable=False)

    fornecedores = models.JSONField("Fornecedores", default=list, blank=True)
    
    gerente_contrato = models.ForeignKey(
        "Colaborador",
        on_delete=models.SET_NULL,
        related_name="contratos_gerenciados",
        blank=True,
        null=True,
        verbose_name="Gerente do Contrato",
        limit_choices_to={"cargo__icontains": "gerente"}
    )

    situacao = models.CharField(
        "Situação",
        max_length=20,
        choices=[("Ativo", "Ativo"), ("Inativo", "Inativo")],
        default="Ativo",
        blank=True,  # Permitir blank pois é calculado automaticamente no save()
    )
    valor_global = models.DecimalField(
        max_digits=14, decimal_places=2, editable=False, default=0
    )

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"

    # ==================== COMPUTED FIELDS (Regra de Ouro) ====================
    
    @property
    def data_fim_atual(self):
        """
        Data de fim atual calculada automaticamente (NUNCA editável diretamente)
        data_assinatura + vigencia_original + soma(meses_acrescimo dos aditivos)
        """
        if not self.data_assinatura:
            return None
        
        meses_totais = self.vigencia or 0
        # Somar meses de acréscimo de todos os aditivos de prorrogação
        if self.pk:  # Só se já foi salvo
            meses_totais += sum(
                aditivo.meses_acrescimo or 0
                for aditivo in self.termos_aditivos.filter(tipo=TipoTermoAditivo.PRORROGACAO)
            )
        
        return self.data_assinatura + relativedelta(months=meses_totais)

    @property
    def valor_atual(self):
        """
        Valor atual calculado automaticamente
        valor_inicial + soma(valor_acrescimo dos aditivos)
        """
        valor = self.valor_inicial or Decimal('0.00')
        if self.pk:  # Só se já foi salvo
            valor += sum(
                aditivo.valor_acrescimo or Decimal('0.00')
                for aditivo in self.termos_aditivos.filter(
                    tipo__in=[TipoTermoAditivo.VALOR, TipoTermoAditivo.REEQUILIBRIO]
                )
            )
        return valor

    @property
    def vigencia_total_meses(self):
        """Vigência total em meses (original + aditivos)"""
        meses = self.vigencia or 0
        if self.pk:
            meses += sum(
                aditivo.meses_acrescimo or 0
                for aditivo in self.termos_aditivos.filter(tipo=TipoTermoAditivo.PRORROGACAO)
            )
        return meses

    @property
    def renovacao_pendente(self):
        """
        Retorna True se a renovação está pendente (data_fim_atual - hoje <= 90 dias)
        """
        if not self.data_fim_atual:
            return False
        
        dias_restantes = (self.data_fim_atual - timezone.now().date()).days
        return 0 < dias_restantes <= 90

    @property
    def dias_para_vencimento(self):
        """Retorna o número de dias para o vencimento do contrato"""
        if not self.data_fim_atual:
            return None
        return (self.data_fim_atual - timezone.now().date()).days

    # ==================== FIM COMPUTED FIELDS ====================

    @property
    def calcular_valor_global(self):
        total = self.itens.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F("quantidade") * F("valor_unitario"), output_field=FloatField()
                )
            )
        )["total"]
        return total or 0

    @property
    def fornecedores_formatados(self):
        return [FORNECEDORES_MAP.get(f.upper(), f.title()) for f in self.fornecedores]

    def get_valor_total_itens(self):
        total = self.itens.aggregate(
            total=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("quantidade") * F("valor_unitario"),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    )
                ),
                Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2)),
            )
        )["total"]
        return total or Decimal("0.00")

    def get_valor_total_faturado_os(self):
        from .models import OrdemServico

        return (
            OrdemServico.objects.filter(contrato=self, status="faturada").aggregate(
                total=Coalesce(
                    Sum("valor_total"),
                    Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2)),
                )
            )["total"]
            or Decimal("0.00")
        )

    def get_valor_total_faturado_of(self):
        from .models import OrdemFornecimento

        return (
            OrdemFornecimento.objects.filter(contrato=self, status="faturada").aggregate(
                total=Coalesce(
                    Sum("valor_total"),
                    Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2)),
                )
            )["total"]
            or Decimal("0.00")
        )

    def get_valor_total_faturado(self):
        return self.get_valor_total_faturado_os() + self.get_valor_total_faturado_of()

    def get_valor_total_nao_faturado(self):
        total = self.get_valor_total_itens()
        faturado = self.get_valor_total_faturado()
        nao = total - faturado
        return nao if nao > Decimal("0.00") else Decimal("0.00")

    def atualizar_data_fim(self):
        """Atualiza o campo data_fim com base nos aditivos"""
        self.data_fim = self.data_fim_atual
        self.save(update_fields=["data_fim", "situacao"])

    def save(self, *args, **kwargs):
        # ✅ Normaliza fornecedores (UPPER)
        if self.fornecedores:
            self.fornecedores = [f.strip().upper() for f in self.fornecedores]

        # 🗓️ Calcula a data de fim (inicial, sem aditivos)
        if self.data_assinatura and self.vigencia:
            # Se é novo ou não tem aditivos, usa cálculo simples
            if not self.pk:
                self.data_fim = self.data_assinatura + relativedelta(months=self.vigencia)
            else:
                # Se já existe, usa o cálculo que considera aditivos
                self.data_fim = self.data_fim_atual

        # 🔄 Atualiza situação
        if self.data_fim:
            self.situacao = (
                "Ativo" if self.data_fim >= timezone.now().date() else "Inativo"
            )

        # 🚩 Primeiro save (precisa da PK para calcular valor_inicial dos itens)
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # 💰 Calcula valor_inicial como soma dos valores totais dos itens do contrato
        if self.pk:  # Só calcular se já tem PK (itens precisam do contrato salvo)
            self._atualizar_valor_inicial()

    def _atualizar_valor_inicial(self):
        """
        Método interno para atualizar valor_inicial e valor_global
        baseado na soma dos valores totais dos itens do contrato
        """
        valor_inicial_calculado = self.get_valor_total_itens()
        valor_global_calculado = self.calcular_valor_global
        
        # Atualizar usando update() para evitar recursão no save()
        update_fields = []
        if self.valor_inicial != valor_inicial_calculado:
            update_fields.append('valor_inicial')
        if self.valor_global != valor_global_calculado:
            update_fields.append('valor_global')
        
        if update_fields:
            # Atualizar valores no objeto em memória
            self.valor_inicial = valor_inicial_calculado
            self.valor_global = valor_global_calculado
            # Salvar apenas os campos que mudaram
            Contrato.objects.filter(pk=self.pk).update(
                **{field: getattr(self, field) for field in update_fields}
            )

    def __str__(self):
        return f"Contrato {self.numero_contrato} - {self.cliente}"


class TermoAditivo(models.Model):
    """
    Termos aditivos aos contratos
    Conforme Leis 14.133/2021 e 13.303/2016
    """
    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.CASCADE,
        related_name="termos_aditivos",
        verbose_name="Contrato",
        help_text="Contrato ao qual o termo aditivo se refere"
    )
    numero_termo = models.CharField(
        max_length=100,
        verbose_name="Número do Termo Aditivo",
        help_text="Número oficial do termo aditivo"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoTermoAditivo.choices,
        verbose_name="Tipo",
        help_text="Tipo de termo aditivo"
    )
    meses_acrescimo = models.IntegerField(
        default=0,
        verbose_name="Meses de Acréscimo",
        help_text="Meses adicionais de vigência (apenas para prorrogação)"
    )
    valor_acrescimo = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Valor de Acréscimo",
        help_text="Valor adicional em R$ (apenas para aditivos de valor ou reequilíbrio)"
    )
    data_assinatura = models.DateField(
        verbose_name="Data de Assinatura",
        help_text="Data de assinatura do termo aditivo"
    )
    justificativa = models.TextField(
        verbose_name="Justificativa",
        help_text="Justificativa para o termo aditivo",
        blank=True,
        null=True
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Termo Aditivo"
        verbose_name_plural = "Termos Aditivos"
        ordering = ["-data_assinatura"]
        unique_together = [["contrato", "numero_termo"]]

    def __str__(self):
        return f"{self.numero_termo} - {self.get_tipo_display()}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Atualiza a data_fim do contrato após salvar o aditivo
        self.contrato.atualizar_data_fim()

    def delete(self, *args, **kwargs):
        contrato = self.contrato
        super().delete(*args, **kwargs)
        # Atualiza a data_fim do contrato após deletar o aditivo
        contrato.atualizar_data_fim()


from .constants import TIPOS_ITEM_CONTRATO_CHOICES, TIPOS_SERVICO_TREINAMENTO_CONST, TIPOS_PRODUTO_CONST, VIGENCIA_PRODUTO_CHOICES_CONT
from django.db import models
from django.db.models import Sum, F, Value, DecimalField # Adicionado DecimalField aqui
from django.db.models.functions import Coalesce
from django.contrib.humanize.templatetags.humanize import intcomma
from datetime import date

# Importar as constantes do seu arquivo constants.py
from .constants import (
    TIPOS_ITEM_CONTRATO_CHOICES, 
    TIPOS_SERVICO_TREINAMENTO_CONST, 
    TIPOS_PRODUTO_CONST,
    VIGENCIA_PRODUTO_CHOICES_CONT,
    TIPOS_OF_ITEM_CONTRATO,
    TIPOS_OS_ITEM_CONTRATO,
    TIPOS_PRODUTO_NFE,
    TIPOS_SERVICO_NFSE,
    TIPOS_FORNECEDOR_OF_EQUIPAMENTO_SW,
    TIPOS_FORNECEDOR_OF_SOLUCAO,
    TIPOS_FORNECEDOR_OS_SERVICO,
    TIPOS_FORNECEDOR_OS_TREINAMENTO,
)

class ItemContrato(models.Model):
    # Usar as constantes importadas
    TIPOS_SERVICO_TREINAMENTO = TIPOS_SERVICO_TREINAMENTO_CONST
    TIPOS_PRODUTO = TIPOS_PRODUTO_CONST
    # VIGENCIA_PRODUTO_CHOICES já está no campo abaixo, usando a constante importada

    contrato = models.ForeignKey(
        "Contrato", on_delete=models.CASCADE, related_name="itens"
    )
    lote = models.PositiveIntegerField(
        verbose_name="Lote", help_text="Número do lote (Ex.: 1, 2, 3)", default=1
    )
    numero_item = models.CharField(max_length=50, verbose_name="Número do Item")
    descricao = models.TextField(verbose_name="Descrição")
    tipo = models.CharField(
        max_length=30, 
        choices=TIPOS_ITEM_CONTRATO_CHOICES, # Usando a constante importada
        verbose_name="Tipo de Item"
    )
    unidade = models.CharField(max_length=50, verbose_name="Unidade")
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantidade Total")
    
    saldo_quantidade_inicial = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, editable=False, verbose_name="Saldo Inicial de Quantidade"
    )
    valor_unitario = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Unitário")
    valor_total = models.DecimalField(
        max_digits=14, decimal_places=2, editable=False, default=0, verbose_name="Valor Total do Item"
    )
    vigencia_produto = models.IntegerField(
        choices=VIGENCIA_PRODUTO_CHOICES_CONT, # Usando a constante importada
        blank=True, null=True, verbose_name="Vigência do Produto (meses)"
    )

    class Meta:
        unique_together = ("contrato", "lote", "numero_item")
        verbose_name = "Item de Contrato"
        verbose_name_plural = "Itens de Contrato"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.saldo_quantidade_inicial = self.quantidade
        self.valor_total = (self.quantidade or 0) * (self.valor_unitario or 0)
        super().save(*args, **kwargs)
        # Atualizar valor_inicial do contrato após salvar o item
        if self.contrato and self.contrato.pk:
            self.contrato._atualizar_valor_inicial()

    def __str__(self):
        # Tentativa de obter o número do contrato de forma segura
        numero_contrato_str = self.contrato.numero_contrato if self.contrato else "N/A"
        return f"Item {self.numero_item} - {self.descricao[:30]}... ({numero_contrato_str})"

    def get_valor_total_faturado_os(self):
        from .models import OrdemServico # Movido para dentro para evitar importação circular se necessário
        if not hasattr(self, 'ordemservico'): # related_name para OrdemServico->ItemContrato
            return DecimalField().to_python(0)
            
        total_faturado = self.ordemservico.filter(status="faturada").aggregate(
            total=Coalesce(Sum(F('valor_unitario') * F('quantidade')), Value(0), output_field=DecimalField())
        )['total']
        return total_faturado

    def get_valor_total_faturado_of(self):
        from .models import OrdemFornecimento # Movido para dentro para evitar importação circular se necessário
        if not hasattr(self, 'ordemfornecimento'): # related_name para OrdemFornecimento->ItemContrato
            return DecimalField().to_python(0)

        total_faturado = self.ordemfornecimento.filter(status="faturada").aggregate(
            total=Coalesce(Sum(F('valor_unitario') * F('quantidade')), Value(0), output_field=DecimalField())
        )['total']
        return total_faturado

    @property
    def quantidade_consumida(self):
        from .models import OrdemServico, OrdemFornecimento
        total = 0
        if self.tipo in self.TIPOS_SERVICO_TREINAMENTO:
            total = OrdemServico.objects.filter(
                item_contrato=self, status="faturada" 
            ).aggregate(total_consumido=Coalesce(Sum("quantidade"), Value(0), output_field=DecimalField()))["total_consumido"]
        elif self.tipo in self.TIPOS_PRODUTO:
            total = OrdemFornecimento.objects.filter(
                item_contrato=self, status="faturada"
            ).aggregate(total_consumido=Coalesce(Sum("quantidade"), Value(0), output_field=DecimalField()))["total_consumido"]
        return total or 0
    quantidade_consumida.fget.short_description = "Qtd. Consumida"


    @property
    def saldo_quantidade_atual(self):
        return (self.quantidade or 0) - self.quantidade_consumida
    saldo_quantidade_atual.fget.short_description = "Saldo Qtd. Atual"

    @property
    def valor_consumido_calculado(self):
        return self.quantidade_consumida * (self.valor_unitario or 0)
    valor_consumido_calculado.fget.short_description = "Valor Consumido (Calc.)"

    @property
    def saldo_disponivel(self):
        """Calcula o saldo disponível em VALOR MONETÁRIO para este item de contrato."""
        if self.valor_total is None:
            return DecimalField().to_python(0) # Retorna Decimal(0) se valor_total for None

        valor_faturado_total = DecimalField().to_python(0)
        if self.tipo in self.TIPOS_SERVICO_TREINAMENTO:
            valor_faturado_total = self.get_valor_total_faturado_os()
        elif self.tipo in self.TIPOS_PRODUTO:
            valor_faturado_total = self.get_valor_total_faturado_of()
        
        return self.valor_total - valor_faturado_total
    saldo_disponivel.fget.short_description = "Saldo Disponível (R$)"

    @property
    def saldo_disponivel_formatado(self):
        """Retorna o saldo disponível formatado como moeda (R$)."""
        saldo = self.saldo_disponivel
        if saldo is not None:
            return f"R$ {intcomma(saldo.quantize(DecimalField(max_digits=14, decimal_places=2).to_python('0.01')))}"
        return "N/A"
    saldo_disponivel_formatado.fget.short_description = "Saldo R$ Formatado"

    @property
    def valor_faturado_original_prop(self): # Renomeado para clareza e evitar conflito
        return self.quantidade_consumida * (self.valor_unitario or 0)
    valor_faturado_original_prop.fget.short_description = "Valor Faturado (Prop.)"

    @property
    def valor_saldo_original_prop(self): # Renomeado para clareza e evitar conflito
        return self.saldo_quantidade_atual * (self.valor_unitario or 0)
    valor_saldo_original_prop.fget.short_description = "Valor Saldo Qtd. (Prop.)"
    
    def vigencia_restante(self):
        from .models import OrdemFornecimento # Movido para dentro para evitar importação circular se necessário
        if self.tipo in self.TIPOS_PRODUTO and self.vigencia_produto:
            if not hasattr(self, 'ordemfornecimento'):
                 return self.vigencia_produto # Ou None, dependendo da lógica desejada

            ativacoes = self.ordemfornecimento.filter(
                status="faturada", data_ativacao__isnull=False
            ).values_list("data_ativacao", flat=True)
            
            if not ativacoes:
                return self.vigencia_produto

            hoje = date.today()
            restantes = []

            for data_ativacao_item in ativacoes:
                if data_ativacao_item:
                    meses_utilizados = (
                        (hoje.year - data_ativacao_item.year) * 12 + hoje.month - data_ativacao_item.month
                    )
                    if hoje.day < data_ativacao_item.day and hoje.year == data_ativacao_item.year and hoje.month == data_ativacao_item.month:
                         meses_utilizados -=1
                    
                    restante = self.vigencia_produto - meses_utilizados # Não arredondar aqui para manter precisão decimal
                    restantes.append(max(restante, 0))

            return min(restantes) if restantes else self.vigencia_produto
        return None
    vigencia_restante.short_description = "Vigência Restante (meses)"


from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class ItemFornecedorOF(models.Model):
    """Modelo intermediário para relacionar múltiplos itens de fornecedor com uma OF"""
    ordem_fornecimento = models.ForeignKey(
        "OrdemFornecimento",
        on_delete=models.CASCADE,
        related_name="itens_fornecedor",
        verbose_name="Ordem de Fornecimento"
    )
    item_fornecedor = models.ForeignKey(
        "ItemFornecedor",
        on_delete=models.PROTECT,
        verbose_name="Item de Fornecedor"
    )
    quantidade = models.PositiveIntegerField(
        verbose_name="Quantidade",
        default=1
    )
    valor_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor Unitário"
    )
    valor_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Valor Total",
        editable=False
    )
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordem",
        help_text="Ordem de exibição do item"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item de Fornecedor da OF"
        verbose_name_plural = "Itens de Fornecedor da OF"
        ordering = ["ordem", "id"]

    def __str__(self):
        return f"{self.ordem_fornecimento.numero_of} - {self.item_fornecedor.descricao}"

    def save(self, *args, **kwargs):
        self.valor_total = self.valor_unitario * self.quantidade
        super().save(*args, **kwargs)


class OrdemFornecimento(models.Model):
    STATUS_ABERTA = "aberta"
    STATUS_EXECUCAO = "execucao"
    STATUS_FINALIZADA = "finalizada"
    STATUS_FATURADA = "faturada"

    STATUS_CHOICES = [
        (STATUS_ABERTA, "Aberta"),
        (STATUS_EXECUCAO, "Em execução"),
        (STATUS_FINALIZADA, "Finalizada"),
        (STATUS_FATURADA, "Faturada"),
    ]

    numero_of = models.CharField(
        max_length=20, unique=True, blank=True, editable=False, verbose_name="Número da OF"
    )
    numero_of_cliente = models.CharField(
        max_length=100, verbose_name="Número da OF do Cliente", blank=True, null=True
    )
    cliente = models.ForeignKey("Cliente", on_delete=models.PROTECT)
    contrato = models.ForeignKey("Contrato", on_delete=models.PROTECT)
    item_contrato = models.ForeignKey(
        "ItemContrato",
        limit_choices_to={"tipo__in": TIPOS_OF_ITEM_CONTRATO},
        on_delete=models.PROTECT,
        verbose_name="Item do Contrato"
    )

    unidade = models.CharField(max_length=20, verbose_name="Unidade", default="Licença")
    quantidade = models.PositiveIntegerField(verbose_name="Quantidade")
    vigencia_produto = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Vigência do Produto (meses)"
    )
    valor_unitario = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Valor Unitário"
    )
    valor_total = models.DecimalField(
        max_digits=14, 
        decimal_places=2,
        verbose_name="Valor Total"
    )
    
    # Flag para faturamento separado (HW/SW)
    faturamento_separado = models.BooleanField(
        default=False,
        verbose_name="Faturamento Separado (HW/SW)",
        help_text="Se habilitado, permite fracionar o valor em NF-e (HW) e NFS-e (SW)"
    )
    valor_hw = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor HW (NF-e)",
        help_text="Valor para faturamento como produto (NF-e)"
    )
    valor_sw = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor SW (NFS-e)",
        help_text="Valor para faturamento como serviço (NFS-e)"
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_ABERTA
    )
    data_ativacao = models.DateField(blank=True, null=True)
    data_faturamento = models.DateField(blank=True, null=True)

    observacoes = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ordem de Fornecimento"
        verbose_name_plural = "Ordens de Fornecimento"
        ordering = ["-criado_em"]

    def __str__(self):
        return self.numero_of

    def clean(self):
        # Validar tipo de item de contrato
        if self.item_contrato.tipo not in TIPOS_OF_ITEM_CONTRATO:
            raise ValidationError(
                f"Item do contrato deve ser de um dos tipos permitidos para OF: {', '.join(TIPOS_OF_ITEM_CONTRATO)}."
            )

        # Validar faturamento separado apenas para Equipamento com SW embarcado
        if self.faturamento_separado and self.item_contrato.tipo != "equipamento_sw_embarcado":
            raise ValidationError(
                "Faturamento separado (HW/SW) só é permitido para itens do tipo 'Equipamento com SW embarcado'."
            )

        # Validar valores de faturamento separado
        if self.faturamento_separado:
            if not self.valor_hw or not self.valor_sw:
                raise ValidationError(
                    "Quando o faturamento separado está habilitado, os valores HW e SW devem ser informados."
                )
            if (self.valor_hw + self.valor_sw) != self.valor_total:
                raise ValidationError(
                    f"A soma dos valores HW ({self.valor_hw}) e SW ({self.valor_sw}) deve ser igual ao valor total ({self.valor_total})."
                )

        # Validar quantidade disponível
        total_consumido = sum(
            of.quantidade
            for of in OrdemFornecimento.objects.filter(
                item_contrato=self.item_contrato
            ).exclude(pk=self.pk if self.pk else None)
        )

        saldo_disponivel = self.item_contrato.quantidade - total_consumido

        if self.quantidade > saldo_disponivel:
            raise ValidationError(
                f"A quantidade ({self.quantidade}) excede o saldo disponível ({saldo_disponivel})."
            )

    def gerar_numero_of(self):
        """Gera o número da OF no formato 0001/2025 de forma incremental por ano"""
        from datetime import date
        
        # Usar data de criação ou data atual para determinar o ano
        ano = timezone.now().year
        
        # Buscar todas as OF do ano e extrair o maior número sequencial
        of_do_ano = OrdemFornecimento.objects.filter(
            numero_of__endswith=f"/{ano}"
        )
        
        # Se estiver editando, excluir a própria OF da busca
        if self.pk:
            of_do_ano = of_do_ano.exclude(pk=self.pk)
        
        # Encontrar o maior número sequencial
        maior_numero = 0
        for of in of_do_ano:
            try:
                num = int(of.numero_of.split('/')[0])
                if num > maior_numero:
                    maior_numero = num
            except (ValueError, IndexError):
                continue
        
        # Incrementar para o próximo número
        numero_sequencial = maior_numero + 1
        
        # Formatar com 4 dígitos: 0001, 0002, etc.
        numero_formatado = f"{numero_sequencial:04d}/{ano}"
        
        return numero_formatado

    def save(self, *args, **kwargs):
        # Gerar número da OF automaticamente se não existir (apenas na criação)
        if not self.numero_of:
            self.numero_of = self.gerar_numero_of()
        
        # Atualização automática de campos derivados
        self.unidade = self.item_contrato.unidade
        self.vigencia_produto = self.item_contrato.vigencia_produto
        self.valor_unitario = self.item_contrato.valor_unitario
        self.valor_total = self.valor_unitario * self.quantidade

        # Se faturamento separado não estiver habilitado, limpar valores HW/SW
        if not self.faturamento_separado:
            self.valor_hw = None
            self.valor_sw = None

        # Preenchimento das datas baseado no status
        if self.status == self.STATUS_FINALIZADA and not self.data_ativacao:
            self.data_ativacao = timezone.now().date()

        if self.status == self.STATUS_FATURADA and not self.data_faturamento:
            self.data_faturamento = timezone.now().date()

        super().save(*args, **kwargs)
    
    @property
    def tipo_documento_fiscal(self):
        """Retorna o tipo de documento fiscal baseado no tipo de item de contrato"""
        if self.item_contrato.tipo in TIPOS_PRODUTO_NFE:
            return "NF-e"  # Nota Fiscal Eletrônica (produto)
        elif self.item_contrato.tipo in TIPOS_SERVICO_NFSE:
            return "NFS-e"  # Nota Fiscal de Serviços Eletrônica (serviço)
        return None
    
    @property
    def precisa_faturamento_separado(self):
        """Verifica se precisa de faturamento separado baseado no tipo de item"""
        return self.item_contrato.tipo == "equipamento_sw_embarcado"

    @property
    def vigencia_restante(self):
        if self.item_contrato.vigencia_produto and self.data_ativacao:
            delta = timezone.now().date() - self.data_ativacao
            meses_decorridos = delta.days // 30
            return max(self.item_contrato.vigencia_produto - meses_decorridos, 0)
        return None


class ItemFornecedorOS(models.Model):
    """Modelo intermediário para relacionar múltiplos itens de fornecedor com uma OS"""
    ordem_servico = models.ForeignKey(
        "OrdemServico",
        on_delete=models.CASCADE,
        related_name="itens_fornecedor",
        verbose_name="Ordem de Serviço"
    )
    item_fornecedor = models.ForeignKey(
        "ItemFornecedor",
        on_delete=models.PROTECT,
        verbose_name="Item de Fornecedor"
    )
    quantidade = models.PositiveIntegerField(
        verbose_name="Quantidade",
        default=1
    )
    valor_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor Unitário"
    )
    valor_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Valor Total",
        editable=False
    )
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordem",
        help_text="Ordem de exibição do item"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item de Fornecedor da OS"
        verbose_name_plural = "Itens de Fornecedor da OS"
        ordering = ["ordem", "id"]

    def __str__(self):
        return f"{self.ordem_servico.numero_os} - {self.item_fornecedor.descricao}"

    def save(self, *args, **kwargs):
        self.valor_total = self.valor_unitario * self.quantidade
        super().save(*args, **kwargs)


class OrdemServico(models.Model):
    STATUS_CHOICES = [
        ("aberta", "Aberta"),
        ("execucao", "Em execução"),
        ("finalizada", "Finalizada"),
        ("faturada", "Faturada"),
    ]

    numero_os = models.CharField(max_length=20, unique=True, blank=True, editable=False)
    numero_os_cliente = models.CharField(max_length=50, blank=True, null=True)

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE)
    projeto = models.ForeignKey(
        "Projeto",
        on_delete=models.CASCADE,
        related_name="ordens_servico",
        verbose_name="Projeto",
        help_text="Projeto ao qual a OS está vinculada",
        blank=True,
        null=True  # Temporariamente nullable para migração
    )
    item_contrato = models.ForeignKey(
        ItemContrato,
        on_delete=models.CASCADE,
        limit_choices_to={"tipo__in": TIPOS_OS_ITEM_CONTRATO},
        verbose_name="Item do Contrato"
    )
    
    # Itens de fornecedor para timesheet (mantidos para compatibilidade)
    item_fornecedor_consultor = models.ForeignKey(
        ItemFornecedor,
        on_delete=models.PROTECT,
        related_name="os_consultor",
        blank=True,
        null=True,
        verbose_name="Item de Fornecedor (Consultor)",
        help_text="Item de fornecedor vinculado às horas do consultor",
        limit_choices_to={"tipo__in": ["servico", "treinamento"]}
    )
    item_fornecedor_gerente = models.ForeignKey(
        ItemFornecedor,
        on_delete=models.PROTECT,
        related_name="os_gerente",
        blank=True,
        null=True,
        verbose_name="Item de Fornecedor (Gerente)",
        help_text="Item de fornecedor vinculado às horas do gerente",
        limit_choices_to={"tipo__in": ["servico", "treinamento"]}
    )

    gerente_projetos = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Gerente de Projetos"
    )
    consultor_tecnico = models.CharField(max_length=100, blank=True, null=True)

    unidade = models.CharField(max_length=50, editable=False, default="Horas")
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)

    valor_unitario = models.DecimalField(
        max_digits=12, decimal_places=2, editable=False, default=0
    )
    valor_total = models.DecimalField(
        max_digits=14, decimal_places=2, editable=False, default=0
    )

    data_inicio = models.DateField()
    hora_inicio = models.TimeField(default="09:00:00")

    data_termino = models.DateField(blank=True, null=True)
    hora_termino = models.TimeField(default="19:00:00")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Aberta")

    data_emissao_trd = models.DateField(blank=True, null=True)
    data_faturamento = models.DateField(blank=True, null=True)

    tipo_os = models.CharField(max_length=20, editable=False, default="Serviço")

    horas_consultor = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True
    )
    horas_gerente = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True
    )
    horas_totais = models.DecimalField(
        max_digits=6, decimal_places=2, editable=False, default=0
    )
    
    # Campos para planejado x realizado
    horas_planejadas = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        editable=False,
        verbose_name="Horas Planejadas",
        help_text="Total de horas planejadas para a OS (igual à quantidade total da OS)"
    )
    horas_realizadas = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        editable=False,
        verbose_name="Horas Realizadas",
        help_text="Total de horas realizadas (calculado automaticamente das tarefas)"
    )

    class Meta:
        unique_together = ("numero_os", "contrato")

    def __str__(self):
        return f"{self.numero_os} - {self.cliente.nome_fantasia}"
    
    def clean(self):
        """Validações para OrdemServico"""
        # Validar tipo de item de contrato
        if self.item_contrato.tipo not in TIPOS_OS_ITEM_CONTRATO:
            raise ValidationError(
                f"Item do contrato deve ser de um dos tipos permitidos para OS: {', '.join(TIPOS_OS_ITEM_CONTRATO)}."
            )
        
        # Validar quantidade disponível
        from django.db.models import Sum, Value
        from django.db.models.functions import Coalesce
        
        total_consumido = OrdemServico.objects.filter(
            item_contrato=self.item_contrato
        ).exclude(pk=self.pk if self.pk else None).aggregate(
            total=Coalesce(Sum("quantidade"), Value(0))
        )["total"] or 0
        
        saldo_disponivel = self.item_contrato.quantidade - total_consumido
        
        if self.quantidade > saldo_disponivel:
            raise ValidationError(
                f"A quantidade ({self.quantidade}) excede o saldo disponível ({saldo_disponivel})."
            )
    
    @property
    def tipo_documento_fiscal(self):
        """OS sempre gera NFS-e (Nota Fiscal de Serviços Eletrônica)"""
        return "NFS-e"
    
    @property
    def custo_consultor(self):
        """Calcula o custo total das horas do consultor"""
        if self.item_fornecedor_consultor and self.horas_consultor:
            return self.horas_consultor * self.item_fornecedor_consultor.valor_unitario
        return Decimal('0.00')
    
    @property
    def custo_gerente(self):
        """Calcula o custo total das horas do gerente"""
        if self.item_fornecedor_gerente and self.horas_gerente:
            return self.horas_gerente * self.item_fornecedor_gerente.valor_unitario
        return Decimal('0.00')
    
    @property
    def custo_total_os(self):
        """Custo total da OS (consultor + gerente)"""
        return self.custo_consultor + self.custo_gerente
    
    @property
    def receita_prevista(self):
        """Receita prevista da OS (valor do item do contrato × quantidade)"""
        if self.item_contrato and self.quantidade:
            return self.item_contrato.valor_unitario * self.quantidade
        return Decimal('0.00')
    
    @property
    def impostos(self):
        """15% de impostos sobre a receita prevista"""
        return self.receita_prevista * Decimal('0.15')
    
    @property
    def royalties(self):
        """12% de royalties sobre a receita prevista"""
        return self.receita_prevista * Decimal('0.12')
    
    @property
    def margem_contribuicao(self):
        """Margem de contribuição = Receita - Impostos - Royalties - Custo Total"""
        return self.receita_prevista - self.impostos - self.royalties - self.custo_total_os
    
    @property
    def percentual_margem(self):
        """Percentual da margem de contribuição sobre a receita prevista"""
        if self.receita_prevista > 0:
            return (self.margem_contribuicao / self.receita_prevista) * 100
        return Decimal('0.00')
    
    @property
    def is_exequivel(self):
        """Verifica se a OS é exequível (margem >= 20%)"""
        return self.percentual_margem >= Decimal('20.00')
    
    def calcular_horas_tarefas(self):
        """
        Calcula horas realizadas baseado nos lançamentos de horas das tarefas vinculadas.
        Horas planejadas = quantidade total da OS (já definido no save).
        Horas realizadas = soma de todos os lançamentos de horas das tarefas vinculadas à OS.
        """
        from django.db.models import Sum, Value, DecimalField, Q
        from django.db.models.functions import Coalesce
        
        # Horas realizadas = soma de todos os lançamentos de horas das tarefas vinculadas à OS
        # Buscar todas as tarefas vinculadas à OS (através da sprint ou diretamente)
        tarefas_os = self.tarefas.all()
        
        # Se a OS tem uma sprint vinculada, buscar também tarefas da sprint
        if hasattr(self, 'sprint') and self.sprint:
            tarefas_sprint = self.sprint.tarefas.all()
            # Combinar tarefas diretas e tarefas da sprint
            from django.db.models import Q
            todas_tarefas = Tarefa.objects.filter(
                Q(ordem_servico=self) | Q(sprint=self.sprint)
            ).distinct()
        else:
            todas_tarefas = tarefas_os
        
        # Calcular horas realizadas: soma de todos os lançamentos de horas
        horas_realizadas_total = Decimal('0.00')
        for tarefa in todas_tarefas:
            horas_tarefa = tarefa.lancamentos_horas.aggregate(
                total=Coalesce(
                    Sum('horas_trabalhadas'),
                    Value(Decimal('0.00')),
                    output_field=DecimalField()
                )
            )['total'] or Decimal('0.00')
            horas_realizadas_total += horas_tarefa
        
        self.horas_realizadas = horas_realizadas_total
        self.save(update_fields=['horas_realizadas'])
    
    @property
    def diferenca_horas(self):
        """Diferença entre horas planejadas e realizadas"""
        return self.horas_realizadas - self.horas_planejadas
    
    @property
    def percentual_execucao(self):
        """Percentual de execução (realizado / planejado)"""
        if self.horas_planejadas > 0:
            return (self.horas_realizadas / self.horas_planejadas) * 100
        return Decimal('0.00')
    
    @property
    def horas_realizadas_consultor(self):
        """Total de horas realizadas pelo consultor (lançamentos de horas em tarefas onde ele é responsável)"""
        from django.db.models import Sum, Value, DecimalField, Q
        from django.db.models.functions import Coalesce
        
        # Buscar tarefas vinculadas à OS onde o consultor é responsável
        tarefas_consultor = self.tarefas.filter(
            responsavel__cargo__icontains="consultor"
        )
        
        # Se há sprint vinculada, incluir tarefas da sprint também
        if hasattr(self, 'sprint') and self.sprint:
            tarefas_sprint_consultor = self.sprint.tarefas.filter(
                responsavel__cargo__icontains="consultor"
            )
            todas_tarefas_consultor = (tarefas_consultor | tarefas_sprint_consultor).distinct()
        else:
            todas_tarefas_consultor = tarefas_consultor
        
        horas_total = Decimal('0.00')
        for tarefa in todas_tarefas_consultor:
            if tarefa.responsavel:
                horas = tarefa.lancamentos_horas.filter(
                    colaborador=tarefa.responsavel
                ).aggregate(
                    total=Coalesce(
                        Sum('horas_trabalhadas'),
                        Value(Decimal('0.00')),
                        output_field=DecimalField()
                    )
                )['total'] or Decimal('0.00')
                horas_total += horas
        
        return horas_total
    
    @property
    def horas_realizadas_gerente(self):
        """Total de horas realizadas pelo gerente (lançamentos de horas em tarefas de gestão)"""
        from django.db.models import Sum, Value, DecimalField, Q
        from django.db.models.functions import Coalesce
        
        # Buscar tarefas vinculadas à OS onde o gerente é responsável (tarefas de gestão)
        tarefas_gerente = self.tarefas.filter(
            responsavel__cargo__icontains="gerente"
        )
        
        # Se há sprint vinculada, incluir tarefas da sprint também
        if hasattr(self, 'sprint') and self.sprint:
            tarefas_sprint_gerente = self.sprint.tarefas.filter(
                responsavel__cargo__icontains="gerente"
            )
            todas_tarefas_gerente = (tarefas_gerente | tarefas_sprint_gerente).distinct()
        else:
            todas_tarefas_gerente = tarefas_gerente
        
        horas_total = Decimal('0.00')
        for tarefa in todas_tarefas_gerente:
            if tarefa.responsavel:
                horas = tarefa.lancamentos_horas.filter(
                    colaborador=tarefa.responsavel
                ).aggregate(
                    total=Coalesce(
                        Sum('horas_trabalhadas'),
                        Value(Decimal('0.00')),
                        output_field=DecimalField()
                    )
                )['total'] or Decimal('0.00')
                horas_total += horas
        
        return horas_total
    
    @property
    def diferenca_horas_consultor(self):
        """Diferença entre horas planejadas e realizadas do consultor"""
        return self.horas_realizadas_consultor - (self.horas_consultor or Decimal('0.00'))
    
    @property
    def diferenca_horas_gerente(self):
        """Diferença entre horas planejadas e realizadas do gerente"""
        return self.horas_realizadas_gerente - (self.horas_gerente or Decimal('0.00'))

    def gerar_numero_os(self):
        """Gera o número da OS no formato 0001/2025 de forma incremental por ano"""
        from datetime import date
        from django.db.models import Max
        
        # Usar data_inicio para determinar o ano, ou data atual se não houver
        ano = self.data_inicio.year if self.data_inicio else date.today().year
        
        # Buscar todas as OS do ano e extrair o maior número sequencial
        os_do_ano = OrdemServico.objects.filter(
            numero_os__endswith=f"/{ano}"
        )
        
        # Se estiver editando, excluir a própria OS da busca
        if self.pk:
            os_do_ano = os_do_ano.exclude(pk=self.pk)
        
        # Encontrar o maior número sequencial
        maior_numero = 0
        for os in os_do_ano:
            try:
                num = int(os.numero_os.split('/')[0])
                if num > maior_numero:
                    maior_numero = num
            except (ValueError, IndexError):
                continue
        
        # Incrementar para o próximo número
        numero_sequencial = maior_numero + 1
        
        # Formatar com 4 dígitos: 0001, 0002, etc.
        numero_formatado = f"{numero_sequencial:04d}/{ano}"
        
        return numero_formatado

    def clean(self):
        """Validação de exequibilidade da OS"""
        super().clean()
        
        # Validar exequibilidade apenas se todos os campos necessários estiverem preenchidos
        if (self.item_contrato and self.quantidade and 
            self.item_fornecedor_consultor and self.item_fornecedor_gerente and
            self.horas_consultor and self.horas_gerente and
            self.receita_prevista > 0):
            
            if not self.is_exequivel:
                raise ValidationError(
                    f"A OS não é exequível. Margem de contribuição ({self.percentual_margem:.2f}%) "
                    f"é menor que o mínimo exigido (20%). "
                    f"Margem atual: R$ {self.margem_contribuicao:.2f}"
                )

    def save(self, *args, **kwargs):
        is_update = self.pk is not None
        old_instance = None

        if is_update:
            old_instance = OrdemServico.objects.get(pk=self.pk)

        # Gerar número da OS automaticamente se não existir (apenas na criação)
        if not self.numero_os:
            if self.data_inicio:
                self.numero_os = self.gerar_numero_os()
            else:
                # Se não houver data_inicio, usar data atual
                from datetime import date
                self.numero_os = self.gerar_numero_os()

        # Definir unidade e valor unitário (apenas se item_contrato mudou ou na criação)
        if self.item_contrato:
            # Só atualizar se for nova OS ou se o item_contrato mudou
            if not is_update or (old_instance and old_instance.item_contrato != self.item_contrato):
                self.unidade = self.item_contrato.unidade
                self.valor_unitario = self.item_contrato.valor_unitario
            # Sempre recalcular valor_total baseado na quantidade atual
            if self.quantidade:
                self.valor_total = self.quantidade * self.valor_unitario

        # Definir Tipo OS automaticamente
        self.tipo_os = self.item_contrato.tipo

        # Calcular Horas Totais se for do tipo Serviço
        if self.tipo_os == "Serviço":
            self.horas_totais = (self.horas_consultor or 0) + (self.horas_gerente or 0)
        else:
            self.horas_totais = 0
        
        # Horas planejadas = quantidade total da OS (conceito original)
        if self.quantidade:
            self.horas_planejadas = self.quantidade
        
        # Calcular horas planejadas e realizadas baseado nas tarefas (após salvar)
        # Isso será feito em um signal ou método separado para evitar referência circular

        # Calcular Data e Hora de Término
        if self.data_inicio and self.hora_inicio and self.horas_totais > 0:
            self.data_termino, self.hora_termino = self.calcula_termino()

        # Gerar data_emissao_trd se status for finalizada
        if self.status == "finalizada" and not self.data_emissao_trd:
            self.data_emissao_trd = timezone.now().date()

        # Gerar data_faturamento se status for faturada
        if self.status == "faturada" and not self.data_faturamento:
            self.data_faturamento = timezone.now().date()

        # Obter valores anteriores antes de salvar (para sincronização com Sprint)
        old_data_inicio = None
        old_data_termino = None
        old_status = None
        if self.pk:
            try:
                old_instance = OrdemServico.objects.get(pk=self.pk)
                old_data_inicio = old_instance.data_inicio
                old_data_termino = old_instance.data_termino
                old_status = old_instance.status
            except OrdemServico.DoesNotExist:
                pass

        super().save(*args, **kwargs)
        
        # Sincronizar datas, status e gerente de projetos com a Sprint vinculada (após salvar)
        # Usar try/except para evitar erro se não houver sprint vinculada
        try:
            sprint = self.sprint
            if sprint:
                sprint_updated = False
                update_fields = []
                
                # Sincronizar datas: OS → Sprint
                if old_data_inicio != self.data_inicio:
                    sprint.data_inicio = self.data_inicio
                    update_fields.append('data_inicio')
                    sprint_updated = True
                
                if old_data_termino != self.data_termino:
                    sprint.data_fim = self.data_termino
                    update_fields.append('data_fim')
                    sprint_updated = True
                
                # Sincronizar gerente de projetos: Projeto → OS (via Sprint)
                # O gerente está no Projeto, não na Sprint
                if sprint.projeto.gerente_projeto:
                    gerente_nome = str(sprint.projeto.gerente_projeto)
                    if self.gerente_projetos != gerente_nome:
                        self.gerente_projetos = gerente_nome
                        # Não precisa adicionar ao update_fields pois já está sendo salvo
                
                # Sincronizar status: OS → Sprint
                if old_status != self.status:
                    sprint.status = self.status
                    update_fields.append('status')
                    sprint_updated = True
                
                # Salvar a Sprint se houver alterações
                if sprint_updated and update_fields:
                    sprint.save(update_fields=update_fields)
        except AttributeError:
            # Não há sprint vinculada, não fazer nada
            pass

        if self.status == "faturada":
            if not is_update or (old_instance and old_instance.status != "faturada"):
                # Cria feedback automaticamente para Customer Success
                from .models import FeedbackSprintOS
                if not FeedbackSprintOS.objects.filter(sprint=self).exists():
                    FeedbackSprintOS.objects.create(
                        sprint=self,
                        cliente=self.projeto.contrato.cliente if self.projeto and self.projeto.contrato else None,
                        contrato=self.projeto.contrato if self.projeto and self.projeto.contrato else None,
                        projeto=self.projeto,
                        status='pendente'
                    )
                item = self.item_contrato

    def calcula_termino(self):
        """
        Calcula a data e hora de término da OS com base em horário útil:
        Segunda a Sexta, das 09h-12h e 14h-19h
        """
        horas_restantes = float(self.horas_totais)
        data = self.data_inicio
        hora = self.hora_inicio

        while horas_restantes > 0:
            if self.eh_dia_util(data):
                inicio_periodo, fim_periodo = self.periodo_do_dia(hora)

                horas_disponiveis = (
                    datetime.combine(date.min, fim_periodo)
                    - datetime.combine(date.min, hora)
                ).seconds / 3600
                if horas_disponiveis <= 0:
                    # Avança para o próximo dia útil
                    data += timedelta(days=1)
                    hora = time(9, 0)
                    continue

                horas_trabalhadas = min(horas_restantes, horas_disponiveis)
                hora = (
                    datetime.combine(date.min, hora)
                    + timedelta(hours=horas_trabalhadas)
                ).time()

                horas_restantes -= horas_trabalhadas
                if horas_restantes > 0:
                    data += timedelta(days=1)
                    hora = time(9, 0)
            else:
                data += timedelta(days=1)
                hora = time(9, 0)

        return data, hora

    def eh_dia_util(self, data):
        return data.weekday() < 5  # 0 = segunda, 4 = sexta

    def periodo_do_dia(self, hora_atual):
        if hora_atual < time(12, 0):
            return hora_atual, time(12, 0)
        elif hora_atual < time(14, 0):
            return time(14, 0), time(19, 0)
        elif hora_atual < time(19, 0):
            return hora_atual, time(19, 0)
        else:
            return time(9, 0), time(12, 0)


class ImportExportLog(models.Model):
    TIPOS = [("import", "Importação"), ("export", "Exportação")]
    STATUS = [("success", "Sucesso"), ("error", "Erro")]

    data = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    arquivo = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS)
    mensagem = models.TextField()

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.data.strftime('%d/%m/%Y %H:%M')}"


# ========== NOVOS MODELOS PARA REPAGINAÇÃO DO SISTEMA ==========

class Colaborador(models.Model):
    """Modelo para representar colaboradores da empresa"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="colaborador",
        verbose_name="Usuário"
    )
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    email = models.EmailField(verbose_name="E-mail")
    telefone = models.CharField(max_length=20, blank=True, null=True)
    cargo = models.CharField(max_length=100, verbose_name="Cargo")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Colaborador"
        verbose_name_plural = "Colaboradores"
        ordering = ["nome_completo"]
    
    def __str__(self):
        return f"{self.nome_completo} - {self.cargo}"


# Adicionar campos gerente_comercial e gerente_sucessos ao modelo Cliente
# Isso será feito via migration para evitar referência circular
# Por enquanto, vamos adicionar os campos diretamente usando referência por string


class FeedbackSprintOS(models.Model):
    """
    Ticket de contato e feedback do cliente sobre sprints/OS
    Vinculado a Customer Success
    """
    MOTIVADOR_CHOICES = [
        ('voluntario_cs', 'Contato Proativo'),
        ('solicitacao_comercial', 'Contato Reativo'),
        ('feedback_servico', 'Obter Feedback do Serviço Prestado (Automático)'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente de Contato'),
        ('em_contato', 'Em Contato'),
        ('respondido', 'Feedback Recebido'),
        ('concluido', 'Concluído'),
    ]
    
    NOTA_CHOICES = [
        (0, '0 - Muito Improvável'),
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
        (6, '6'),
        (7, '7'),
        (8, '8'),
        (9, '9'),
        (10, '10 - Muito Provável'),
    ]
    
    SATISFACAO_CHOICES = [
        (0, '0 - Muito Insatisfeito'),
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
        (6, '6'),
        (7, '7'),
        (8, '8'),
        (9, '9'),
        (10, '10 - Muito Satisfeito'),
    ]
    
    numero_ticket = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Número do Ticket",
        help_text="Número único identificador do ticket"
    )
    
    sprint = models.ForeignKey(
        'Sprint',
        on_delete=models.CASCADE,
        related_name='feedbacks',
        blank=True,
        null=True,
        verbose_name="Sprint"
    )
    ordem_servico = models.ForeignKey(
        'OrdemServico',
        on_delete=models.CASCADE,
        related_name='feedbacks',
        blank=True,
        null=True,
        verbose_name="Ordem de Serviço"
    )
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.CASCADE,
        related_name='feedbacks_sprint_os',
        verbose_name="Cliente"
    )
    contrato = models.ForeignKey(
        'Contrato',
        on_delete=models.CASCADE,
        related_name='feedbacks_sprint_os',
        verbose_name="Contrato"
    )
    projeto = models.ForeignKey(
        'Projeto',
        on_delete=models.CASCADE,
        related_name='feedbacks_sprint_os',
        blank=True,
        null=True,
        verbose_name="Projeto"
    )
    motivador_contato = models.CharField(
        max_length=30,
        choices=MOTIVADOR_CHOICES,
        default='feedback_servico',
        verbose_name="Motivador do Contato"
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name="Status"
    )
    # Questionário NPS - Pergunta Principal (obrigatória para cálculo do NPS)
    pergunta_nps = models.IntegerField(
        choices=NOTA_CHOICES,
        blank=True,
        null=True,
        verbose_name="Pergunta NPS: Recomendação",
        help_text="Em uma escala de 0 a 10, qual a probabilidade de você recomendar nossos serviços a um amigo ou colega? (0-10)"
    )
    # Perguntas complementares de satisfação (não entram no cálculo do NPS)
    pergunta_satisfacao_qualidade = models.IntegerField(
        choices=SATISFACAO_CHOICES,
        blank=True,
        null=True,
        verbose_name="Satisfação: Qualidade do Serviço",
        help_text="Em uma escala de 0 a 10, como você avalia a qualidade do serviço prestado? (0-10)"
    )
    pergunta_satisfacao_prazos = models.IntegerField(
        choices=SATISFACAO_CHOICES,
        blank=True,
        null=True,
        verbose_name="Satisfação: Cumprimento de Prazos",
        help_text="Em uma escala de 0 a 10, como você avalia o cumprimento dos prazos estabelecidos? (0-10)"
    )
    pergunta_satisfacao_comunicacao = models.IntegerField(
        choices=SATISFACAO_CHOICES,
        blank=True,
        null=True,
        verbose_name="Satisfação: Comunicação e Atendimento",
        help_text="Em uma escala de 0 a 10, como você avalia a comunicação e o atendimento recebido? (0-10)"
    )
    # Campo aberto para elogios/críticas
    elogios_criticas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Elogios ou Críticas",
        help_text="Compartilhe elogios, críticas ou sugestões de melhoria"
    )
    gerente_sucessos = models.ForeignKey(
        'Colaborador',
        on_delete=models.SET_NULL,
        related_name='feedbacks_gerenciados',
        blank=True,
        null=True,
        verbose_name="Gerente de Customer Success"
    )
    data_contato = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data do Contato"
    )
    data_resposta = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data da Resposta"
    )
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações Internas"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Ticket de Contato - Customer Success"
        verbose_name_plural = "Tickets de Contato - Customer Success"
        ordering = ['-criado_em']
    
    @property
    def nps_categoria(self):
        """Categoriza o cliente conforme NPS padrão baseado na pergunta principal:
        - Detratores: 0-6
        - Neutros/Passivos: 7-8
        - Promotores: 9-10
        
        O NPS é calculado APENAS com base na pergunta principal de recomendação.
        """
        if self.pergunta_nps is None:
            return None
        
        if self.pergunta_nps >= 9:
            return 'Promotor'
        elif self.pergunta_nps >= 7:
            return 'Neutro'
        else:  # 0-6
            return 'Detrator'
    
    @property
    def nps_score(self):
        """Calcula o NPS (Net Promoter Score) individual para este ticket.
        
        O NPS tradicional é calculado sobre um conjunto de respostas:
        NPS = % Promotores - % Detratores
        
        Para um único ticket, retorna o valor individual:
        - 100 se for Promotor (9-10)
        - 0 se for Neutro (7-8)
        - -100 se for Detrator (0-6)
        
        Para calcular o NPS agregado de múltiplos tickets, use o método de classe
        calcular_nps_agregado().
        """
        categoria = self.nps_categoria
        if categoria is None:
            return None
        if categoria == 'Promotor':
            return 100
        elif categoria == 'Neutro':
            return 0
        else:  # Detrator
            return -100
    
    @property
    def satisfacao_media(self):
        """Calcula a média das perguntas complementares de satisfação (não NPS)"""
        notas = []
        if self.pergunta_satisfacao_qualidade is not None:
            notas.append(self.pergunta_satisfacao_qualidade)
        if self.pergunta_satisfacao_prazos is not None:
            notas.append(self.pergunta_satisfacao_prazos)
        if self.pergunta_satisfacao_comunicacao is not None:
            notas.append(self.pergunta_satisfacao_comunicacao)
        
        if notas:
            return sum(notas) / len(notas)
        return None
    
    @classmethod
    def calcular_nps_agregado(cls, queryset=None):
        """Calcula o NPS agregado conforme fórmula padrão: % Promotores - % Detratores
        
        Args:
            queryset: QuerySet de FeedbackSprintOS. Se None, calcula sobre todos.
        
        Returns:
            dict com:
            - nps: valor do NPS (de -100 a 100)
            - total_respostas: total de tickets com resposta NPS
            - promotores: quantidade e percentual
            - neutros: quantidade e percentual
            - detratores: quantidade e percentual
        """
        if queryset is None:
            queryset = cls.objects.all()
        
        # Filtrar apenas tickets com resposta NPS
        tickets_com_nps = queryset.exclude(pergunta_nps__isnull=True)
        total = tickets_com_nps.count()
        
        if total == 0:
            return {
                'nps': None,
                'total_respostas': 0,
                'promotores': {'quantidade': 0, 'percentual': 0},
                'neutros': {'quantidade': 0, 'percentual': 0},
                'detratores': {'quantidade': 0, 'percentual': 0},
            }
        
        promotores = tickets_com_nps.filter(pergunta_nps__gte=9).count()
        neutros = tickets_com_nps.filter(pergunta_nps__in=[7, 8]).count()
        detratores = tickets_com_nps.filter(pergunta_nps__lte=6).count()
        
        percentual_promotores = (promotores / total) * 100
        percentual_detratores = (detratores / total) * 100
        
        nps = percentual_promotores - percentual_detratores
        
        return {
            'nps': round(nps, 2),
            'total_respostas': total,
            'promotores': {
                'quantidade': promotores,
                'percentual': round(percentual_promotores, 2)
            },
            'neutros': {
                'quantidade': neutros,
                'percentual': round((neutros / total) * 100, 2)
            },
            'detratores': {
                'quantidade': detratores,
                'percentual': round(percentual_detratores, 2)
            },
        }
    
    def gerar_numero_ticket(self):
        """Gera um número único para o ticket baseado na OS ou Sprint
        
        Regras:
        - Tickets automáticos (OS finalizada/faturada): TKT-OS-{numero_os}
        - Tickets manuais com Sprint: TKT-SPRINT-{sprint_id}
        - Tickets manuais sem Sprint: TKT-MANUAL-{ano}-{sequencial}
        """
        from django.db.models import Max
        from datetime import datetime
        
        # Determinar o prefixo baseado na vinculação
        if self.ordem_servico:
            # Ticket automático vinculado à OS (quando OS é finalizada/faturada)
            # Formato: TKT-OS-{numero_os}
            numero_os_limpo = self.ordem_servico.numero_os.replace('/', '-').replace(' ', '')
            prefixo = f"TKT-OS-{numero_os_limpo}"
        elif self.sprint:
            # Ticket manual vinculado à Sprint
            # Formato: TKT-SPRINT-{sprint_id}
            prefixo = f"TKT-SPRINT-{self.sprint.id}"
        else:
            # Ticket manual sem vinculação específica (sem Sprint nem OS)
            # Formato: TKT-MANUAL-{ano}-{sequencial}
            ano = datetime.now().year
            # Buscar o último número do ano
            ultimo_ticket = FeedbackSprintOS.objects.filter(
                numero_ticket__startswith=f"TKT-MANUAL-{ano}"
            ).aggregate(Max('numero_ticket'))
            
            if ultimo_ticket['numero_ticket__max']:
                # Extrair o número do último ticket
                try:
                    ultimo_num = int(ultimo_ticket['numero_ticket__max'].split('-')[-1])
                    novo_num = ultimo_num + 1
                except (ValueError, IndexError):
                    novo_num = 1
            else:
                novo_num = 1
            
            prefixo = f"TKT-MANUAL-{ano}-{novo_num:04d}"
        
        return prefixo
    
    def save(self, *args, **kwargs):
        """Gera o número do ticket automaticamente se não existir"""
        from datetime import datetime
        
        if not self.numero_ticket:
            # Tentar gerar o número
            numero_gerado = self.gerar_numero_ticket()
            
            # Verificar se já existe (caso raro de colisão)
            contador = 1
            numero_final = numero_gerado
            while FeedbackSprintOS.objects.filter(numero_ticket=numero_final).exclude(pk=self.pk if self.pk else None).exists():
                if self.ordem_servico:
                    numero_final = f"{numero_gerado}-{contador}"
                elif self.sprint:
                    numero_final = f"{numero_gerado}-{contador}"
                else:
                    # Para tickets manuais, incrementar o número
                    ano = datetime.now().year
                    try:
                        base_num = int(numero_gerado.split('-')[-1])
                        novo_num = base_num + contador
                    except (ValueError, IndexError):
                        novo_num = contador
                    numero_final = f"TKT-MANUAL-{ano}-{novo_num:04d}"
                contador += 1
                # Proteção contra loop infinito
                if contador > 1000:
                    raise ValueError("Não foi possível gerar um número único para o ticket")
            
            self.numero_ticket = numero_final
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        numero = self.numero_ticket or "Sem número"
        if self.sprint:
            sprint_os = f"Sprint {self.sprint.nome}"
        elif self.ordem_servico:
            sprint_os = f"OS {self.ordem_servico.numero_os}"
        else:
            sprint_os = "Ticket Manual"
        return f"{numero} - {sprint_os} - {self.cliente}"


class SLA(models.Model):
    """SLAs (Service Level Agreements) vinculados a contratos"""
    TIPO_CHOICES = [
        ("disponibilidade", "Disponibilidade"),
        ("tempo_resposta", "Tempo de Resposta"),
        ("resolucao", "Tempo de Resolução"),
        ("atendimento", "Atendimento"),
        ("outro", "Outro"),
    ]
    
    contrato = models.ForeignKey(
        "Contrato",
        on_delete=models.CASCADE,
        related_name="slas",
        verbose_name="Contrato"
    )
    titulo = models.CharField(max_length=255, verbose_name="Título do SLA")
    descricao = models.TextField(verbose_name="Descrição")
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de SLA"
    )
    meta = models.CharField(
        max_length=100,
        verbose_name="Meta",
        help_text="Ex: 99.9% de disponibilidade, 4 horas de resposta"
    )
    valor_penalidade = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor da Penalidade (R$)"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(blank=True, null=True, verbose_name="Data de Fim")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "SLA"
        verbose_name_plural = "SLAs"
        ordering = ["-criado_em"]
    
    def __str__(self):
        return f"{self.titulo} - {self.contrato.numero_contrato}"


class CentroCusto(models.Model):
    """Centro de custo para horas não faturadas (ociosidade)"""
    nome = models.CharField(max_length=255, verbose_name="Nome do Centro de Custo")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código",
        help_text="Código único do centro de custo"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Centro de Custo"
        verbose_name_plural = "Centros de Custo"
        ordering = ["nome"]
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"


# ========== GESTÃO ÁGIL DE PROJETOS ==========

class Projeto(models.Model):
    """Projetos vinculados a contratos - Um contrato pode ter vários projetos"""
    STATUS_CHOICES = [
        ("planejamento", "Planejamento"),
        ("em_andamento", "Em Andamento"),
        ("pausado", "Pausado"),
        ("concluido", "Concluído"),
        ("cancelado", "Cancelado"),
    ]
    
    contrato = models.ForeignKey(
        "Contrato",
        on_delete=models.CASCADE,
        related_name="projetos",
        verbose_name="Contrato",
        help_text="Contrato ao qual o projeto pertence"
    )
    backlog_origem = models.ForeignKey(
        "Backlog",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="projetos_gerados",
        verbose_name="Backlog de Origem",
        help_text="Backlog que originou este projeto"
    )
    item_contrato = models.ForeignKey(
        "ItemContrato",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="projetos",
        verbose_name="Item do Contrato",
        help_text="Item do contrato vinculado ao projeto (apenas Serviço ou Treinamento)",
        limit_choices_to={"tipo__in": TIPOS_OS_ITEM_CONTRATO}
    )
    nome = models.CharField(max_length=255, verbose_name="Nome do Projeto")
    descricao = models.TextField(verbose_name="Descrição", blank=True, null=True)
    gerente_projeto = models.ForeignKey(
        "Colaborador",
        on_delete=models.SET_NULL,
        related_name="projetos_gerenciados",
        blank=True,
        null=True,
        verbose_name="Gerente de Projeto",
        limit_choices_to={"cargo__icontains": "gerente"}
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="planejamento",
        verbose_name="Status"
    )
    # Datas serão sincronizadas com o contrato
    data_inicio = models.DateField(verbose_name="Data de Início", editable=False)
    data_fim_prevista = models.DateField(verbose_name="Data de Fim Prevista", editable=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"
        ordering = ["-criado_em"]
    
    def __str__(self):
        return f"{self.nome} - {self.contrato.numero_contrato}"
    
    def save(self, *args, **kwargs):
        """Sincroniza datas com o contrato"""
        if self.contrato:
            # Sincronizar datas com o contrato
            if self.contrato.data_assinatura:
                self.data_inicio = self.contrato.data_assinatura
            if self.contrato.data_fim_atual:
                self.data_fim_prevista = self.contrato.data_fim_atual
        super().save(*args, **kwargs)
    
    @property
    def total_tarefas_backlog(self):
        """Total de tarefas no backlog do projeto (tarefas sem sprint atribuída que pertencem ao projeto)"""
        from .models import Tarefa
        # Tarefas sem sprint que foram criadas no contexto do projeto
        # Busca tarefas que estão em sprints do projeto mas sem sprint atribuída (não deveria acontecer)
        # Ou tarefas que estão no backlog do contrato mas podem ser atribuídas ao projeto
        # Por enquanto, vamos buscar tarefas sem sprint que podem ser atribuídas a sprints do projeto
        return Tarefa.objects.filter(
            sprint__isnull=True,
            backlog__contrato=self.contrato
        ).count()
    
    @property
    def tarefas_backlog_projeto(self):
        """Tarefas no backlog do projeto (sem sprint atribuída, que podem ser atribuídas a sprints do projeto)"""
        from .models import Tarefa
        # Tarefas sem sprint que pertencem ao backlog do contrato
        # Essas tarefas podem ser atribuídas a sprints do projeto
        return Tarefa.objects.filter(
            sprint__isnull=True,
            backlog__contrato=self.contrato
        )
    
    @property
    def horas_previstas_os(self):
        """Total de horas previstas na OS vinculada ao projeto"""
        from decimal import Decimal
        ordem_servico = self.ordens_servico.filter(status__in=['aberta', 'execucao']).first()
        if ordem_servico:
            return ordem_servico.horas_planejadas or Decimal('0.00')
        return Decimal('0.00')
    
    @property
    def horas_executadas_projeto(self):
        """Total de horas executadas no projeto (horas lançadas em tarefas concluídas e bilhetáveis)"""
        from .models import Tarefa, LancamentoHora
        from decimal import Decimal
        
        # Buscar todas as tarefas concluídas do projeto que são bilhetáveis
        tarefas_concluidas = Tarefa.objects.filter(
            sprint__projeto=self,
            status_sprint='concluida',
            bilhetavel_os=True
        )
        
        # Somar horas lançadas para essas tarefas
        total_horas = Decimal('0.00')
        for tarefa in tarefas_concluidas:
            lancamentos = LancamentoHora.objects.filter(
                tarefa=tarefa,
                faturavel=True
            )
            for lancamento in lancamentos:
                if lancamento.tempo_gasto:
                    total_horas += Decimal(str(lancamento.tempo_gasto))
        
        return total_horas
    
    @property
    def total_sprints(self):
        """Total de sprints do projeto"""
        return self.sprints.count()
    
    @property
    def sprints_ativas(self):
        """Sprints ativas do projeto"""
        return self.sprints.filter(status="ativa").count()


class Backlog(models.Model):
    """Backlog do contrato - Lista de pendências que podem virar projetos"""
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("em_analise", "Em Análise"),
        ("convertido_projeto", "Convertido em Projeto"),
        ("arquivado", "Arquivado"),
    ]
    
    contrato = models.ForeignKey(
        "Contrato",
        on_delete=models.CASCADE,
        related_name="backlogs",
        verbose_name="Contrato",
        help_text="Contrato ao qual o backlog pertence",
        blank=True,
        null=True  # Temporariamente nullable para migração
    )
    titulo = models.CharField(
        max_length=255,
        verbose_name="Título",
        help_text="Título ou descrição do backlog",
        blank=True,
        null=True  # Temporariamente nullable para migração
    )
    descricao = models.TextField(
        verbose_name="Descrição",
        blank=True,
        null=True,
        help_text="Descrição detalhada do backlog"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pendente",
        verbose_name="Status"
    )
    prioridade = models.CharField(
        max_length=20,
        choices=[("baixa", "Baixa"), ("media", "Média"), ("alta", "Alta"), ("critica", "Crítica")],
        default="media",
        verbose_name="Prioridade"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Backlog"
        verbose_name_plural = "Backlogs"
        ordering = ["-prioridade", "-criado_em"]
    
    def __str__(self):
        if self.contrato:
            return f"Backlog - {self.titulo} ({self.contrato.numero_contrato})"
        else:
            return f"Backlog - {self.titulo or 'Sem título'}"
    
    def converter_para_projeto(self, nome_projeto, descricao_projeto=None, gerente_projeto=None, item_contrato=None):
        """
        Converte o backlog em um projeto e cria OS automaticamente
        
        Args:
            nome_projeto: Nome do projeto a ser criado
            descricao_projeto: Descrição do projeto (opcional)
            gerente_projeto: Instância de Colaborador para ser o gerente (opcional)
            item_contrato: Instância de ItemContrato (opcional, apenas Serviço ou Treinamento)
        """
        from .models import OrdemServico, ItemContrato
        from decimal import Decimal
        
        # Buscar item do contrato se não fornecido
        if not item_contrato:
            # Buscar primeiro item do tipo Serviço ou Treinamento do contrato
            item_contrato = ItemContrato.objects.filter(
                contrato=self.contrato,
                tipo__in=['servico', 'treinamento']
            ).first()
        
        projeto = Projeto.objects.create(
            contrato=self.contrato,
            backlog_origem=self,
            nome=nome_projeto,
            descricao=descricao_projeto or self.descricao,
            gerente_projeto=gerente_projeto,  # Colaborador ou None
            item_contrato=item_contrato,
            data_inicio=self.contrato.data_assinatura or timezone.now().date(),
            data_fim_prevista=self.contrato.data_fim_atual or timezone.now().date(),
            status="planejamento"
        )
        
        # Criar OS automaticamente vinculada ao projeto
        if item_contrato:
            # Gerar número da OS
            ano = timezone.now().year
            ultima_os = OrdemServico.objects.filter(
                numero_os__startswith=f"OS-{ano}"
            ).order_by('-numero_os').first()
            
            if ultima_os:
                try:
                    ultimo_num = int(ultima_os.numero_os.split('/')[0].split('-')[-1])
                    novo_num = ultimo_num + 1
                except (ValueError, IndexError):
                    novo_num = 1
            else:
                novo_num = 1
            
            numero_os = f"OS-{novo_num:04d}/{ano}"
            
            # Criar OS vinculada ao projeto
            ordem_servico = OrdemServico.objects.create(
                numero_os=numero_os,
                cliente=self.contrato.cliente,
                contrato=self.contrato,
                projeto=projeto,
                item_contrato=item_contrato,
                quantidade=Decimal('0.00'),  # Será atualizado com o plano de trabalho
                data_inicio=projeto.data_inicio,
                status="aberta"
            )
        
        self.status = "convertido_projeto"
        self.save()
        return projeto


class Sprint(models.Model):
    """Sprints do projeto - Ciclos de desenvolvimento"""
    STATUS_CHOICES = [
        ("aberta", "Aberta"),
        ("execucao", "Em Execução"),
        ("finalizada", "Finalizada"),
        ("faturada", "Faturada"),
    ]
    
    projeto = models.ForeignKey(
        "Projeto",
        on_delete=models.CASCADE,
        related_name="sprints",
        verbose_name="Projeto"
    )
    nome = models.CharField(max_length=255, verbose_name="Nome da Sprint")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="aberta",
        verbose_name="Status"
    )
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(verbose_name="Data de Fim")
    ordem_servico = models.OneToOneField(
        "OrdemServico",
        on_delete=models.CASCADE,
        related_name="sprint",
        blank=True,
        null=True,
        verbose_name="Ordem de Serviço",
        help_text="OS vinculada à sprint (criada automaticamente se não existir)"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Sprint"
        verbose_name_plural = "Sprints"
        ordering = ["-data_inicio"]
    
    def __str__(self):
        return f"{self.nome} - {self.projeto.nome}"
    
    def save(self, *args, **kwargs):
        """Cria OS automaticamente se não existir e sincroniza status com OS"""
        if not self.pk:  # Apenas na criação
            self.status = "aberta"
            # Se não há OS vinculada, criar automaticamente
            if not self.ordem_servico:
                from .models import OrdemServico, ItemContrato, ItemFornecedor
                from decimal import Decimal
                
                # Buscar o primeiro item de contrato do tipo serviço
                item_contrato = ItemContrato.objects.filter(
                    contrato=self.projeto.contrato,
                    tipo__in=["servico", "treinamento", "consultoria"]
                ).first()
                
                # Se não houver item de contrato de serviço, buscar qualquer item do contrato
                if not item_contrato:
                    item_contrato = ItemContrato.objects.filter(
                        contrato=self.projeto.contrato
                    ).first()
                
                # Buscar o primeiro item de fornecedor do tipo serviço
                item_fornecedor = ItemFornecedor.objects.filter(
                    tipo="servico"
                ).first()
                
                # Se não houver item de fornecedor de serviço, buscar qualquer item de fornecedor
                if not item_fornecedor:
                    item_fornecedor = ItemFornecedor.objects.first()
                
                # Se ainda não houver item_contrato ou item_fornecedor, não criar a OS
                if not item_contrato or not item_fornecedor:
                    raise ValueError(
                        "Não é possível criar a OS automaticamente: "
                        "é necessário ter pelo menos um Item de Contrato e um Item de Fornecedor cadastrados."
                    )
                
                # Obter nome do gerente de projetos do Projeto (não da Sprint)
                # O gerente está vinculado ao Projeto, não à Sprint
                gerente_nome = str(self.projeto.gerente_projeto) if self.projeto.gerente_projeto else None
                
                os = OrdemServico.objects.create(
                    cliente=self.projeto.contrato.cliente,
                    contrato=self.projeto.contrato,
                    item_contrato=item_contrato,
                    item_fornecedor=item_fornecedor,
                    data_inicio=self.data_inicio,
                    data_termino=self.data_fim,
                    quantidade=Decimal('0.00'),  # Será atualizado quando as tarefas forem adicionadas
                    status="aberta",
                    gerente_projetos=gerente_nome,  # Sincronizar com o gerente do Projeto
                )
                self.ordem_servico = os
        
        # Obter valores anteriores antes de salvar (para sincronização com OS)
        old_data_inicio = None
        old_data_fim = None
        old_status = None
        if self.pk:
            try:
                old_instance = Sprint.objects.get(pk=self.pk)
                old_data_inicio = old_instance.data_inicio
                old_data_fim = old_instance.data_fim
                old_status = old_instance.status
            except Sprint.DoesNotExist:
                pass
        
        # Salvar a Sprint primeiro para garantir que tenha PK
        super().save(*args, **kwargs)
        
        # Sincronizar datas, status e gerente de projetos com a OS vinculada (após salvar para garantir que a Sprint tenha PK)
        if self.ordem_servico:
            os_updated = False
            update_fields = []
            
            # Sincronizar datas: Sprint → OS
            if old_data_inicio != self.data_inicio:
                self.ordem_servico.data_inicio = self.data_inicio
                update_fields.append('data_inicio')
                os_updated = True
            
            if old_data_fim != self.data_fim:
                self.ordem_servico.data_termino = self.data_fim
                update_fields.append('data_termino')
                os_updated = True
            
            # Sincronizar gerente de projetos: Projeto → OS (via Sprint)
            # O gerente está no Projeto, não na Sprint
            if self.projeto.gerente_projeto:
                gerente_nome = str(self.projeto.gerente_projeto)
                if self.ordem_servico.gerente_projetos != gerente_nome:
                    self.ordem_servico.gerente_projetos = gerente_nome
                    update_fields.append('gerente_projetos')
                    os_updated = True
            
            # Sincronizar status: Sprint → OS
            if old_status != self.status:
                self.ordem_servico.status = self.status
                update_fields.append('status')
                
                # Aplicar regras de datas conforme o status (mesmas regras da OS)
                if self.status == "finalizada" and not self.ordem_servico.data_emissao_trd:
                    from django.utils import timezone
                    self.ordem_servico.data_emissao_trd = timezone.now().date()
                    update_fields.append('data_emissao_trd')
                
                if self.status == "faturada" and not self.ordem_servico.data_faturamento:
                    from django.utils import timezone
                    self.ordem_servico.data_faturamento = timezone.now().date()
                    update_fields.append('data_faturamento')
                
                os_updated = True
            
            # Salvar a OS se houver alterações
            if os_updated and update_fields:
                self.ordem_servico.save(update_fields=update_fields)
    
    @property
    def total_tarefas(self):
        """Total de tarefas na sprint"""
        return self.tarefas.count()
    
    @property
    def tarefas_concluidas(self):
        """Tarefas concluídas na sprint"""
        return self.tarefas.filter(status_sprint="finalizada").count()
    
    @property
    def percentual_conclusao(self):
        """Percentual de conclusão da sprint"""
        if self.total_tarefas > 0:
            return (self.tarefas_concluidas / self.total_tarefas) * 100
        return Decimal('0.00')


class Tarefa(models.Model):
    """Tarefas vinculadas ou não a Ordens de Serviço"""
    # Status para tarefas em sprint
    STATUS_SPRINT_CHOICES = [
        ("nao_iniciada", "Não Iniciada"),
        ("em_execucao", "Em Execução"),
        ("finalizada", "Finalizada"),
    ]
    
    # Status geral (para tarefas não em sprint)
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("em_andamento", "Em Andamento"),
        ("pausada", "Pausada"),
        ("concluida", "Concluída"),
        ("cancelada", "Cancelada"),
    ]
    
    PRIORIDADE_CHOICES = [
        ("baixa", "Baixa"),
        ("media", "Média"),
        ("alta", "Alta"),
    ]
    
    titulo = models.CharField(max_length=255, verbose_name="Nome da Tarefa")
    descricao = models.TextField(verbose_name="Descrição")
    backlog = models.ForeignKey(
        "Backlog",
        on_delete=models.CASCADE,
        related_name="tarefas",
        blank=True,
        null=True,
        verbose_name="Backlog",
        help_text="Tarefa no backlog do projeto (alocação automática)"
    )
    sprint = models.ForeignKey(
        "Sprint",
        on_delete=models.SET_NULL,
        related_name="tarefas",
        blank=True,
        null=True,
        verbose_name="Sprint",
        help_text="Tarefa movida para sprint"
    )
    ordem_servico = models.ForeignKey(
        "OrdemServico",
        on_delete=models.CASCADE,
        related_name="tarefas",
        blank=True,
        null=True,
        verbose_name="Ordem de Serviço",
        help_text="Opcional: vincular a uma OS para horas faturadas (vinculada ao projeto)"
    )
    bilhetavel_os = models.BooleanField(
        default=True,
        verbose_name="Bilhetável na OS",
        help_text="Se marcado, as horas desta tarefa serão contabilizadas na OS do projeto"
    )
    responsavel = models.ForeignKey(
        "Colaborador",
        on_delete=models.SET_NULL,
        related_name="tarefas",
        blank=True,
        null=True,
        verbose_name="Responsável",
        help_text="Consultor Técnico ou Gerente de Projetos"
    )
    # Status específico para tarefas em sprint
    status_sprint = models.CharField(
        max_length=20,
        choices=STATUS_SPRINT_CHOICES,
        blank=True,
        null=True,
        verbose_name="Status (Sprint)",
        help_text="Status quando a tarefa está em uma sprint"
    )
    # Status geral (para tarefas não em sprint)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pendente",
        verbose_name="Status"
    )
    prioridade = models.CharField(
        max_length=20,
        choices=PRIORIDADE_CHOICES,
        default="media",
        verbose_name="Prioridade"
    )
    data_inicio_prevista = models.DateTimeField(verbose_name="Data/Hora de Início Planejado")
    data_termino_prevista = models.DateTimeField(verbose_name="Data/Hora de Término Planejado", help_text="Não pode ser maior que a data de fim da sprint")
    data_inicio_real = models.DateTimeField(blank=True, null=True, verbose_name="Data/Hora de Início Real", editable=False)
    data_termino_real = models.DateTimeField(blank=True, null=True, verbose_name="Data/Hora de Término Real", editable=False)
    horas_planejadas = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name="Horas Planejadas"
    )
    horas_consumidas = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        editable=False,
        verbose_name="Horas Consumidas",
        help_text="Calculado automaticamente baseado em lançamentos de horas"
    )
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tarefa"
        verbose_name_plural = "Tarefas"
        ordering = ["-criado_em"]
    
    def __str__(self):
        return f"{self.titulo} - {self.responsavel.nome_completo if self.responsavel else 'Sem responsável'}"
    
    def calcular_horas_dias_uteis(self, datetime_inicio, datetime_termino):
        """
        Calcula horas baseado em dias úteis (segunda a sexta)
        Horário: 09:00 às 12:00 e 14:00 às 19:00
        Considera também as horas específicas de início e término
        """
        from datetime import datetime, timedelta, time
        from decimal import Decimal
        
        if not datetime_inicio or not datetime_termino:
            return Decimal('0.00')
        
        # Converter para datetime se necessário
        if isinstance(datetime_inicio, str):
            datetime_inicio = datetime.fromisoformat(datetime_inicio.replace('Z', '+00:00'))
        if isinstance(datetime_termino, str):
            datetime_termino = datetime.fromisoformat(datetime_termino.replace('Z', '+00:00'))
        
        # Extrair data e hora
        data_inicio = datetime_inicio.date() if isinstance(datetime_inicio, datetime) else datetime_inicio
        hora_inicio = datetime_inicio.time() if isinstance(datetime_inicio, datetime) else time(9, 0)
        data_termino = datetime_termino.date() if isinstance(datetime_termino, datetime) else datetime_termino
        hora_termino = datetime_termino.time() if isinstance(datetime_termino, datetime) else time(19, 0)
        
        # Horário de trabalho: 09:00-12:00 (3h) e 14:00-19:00 (5h) = 8h por dia útil
        hora_inicio_trabalho = time(9, 0)  # 09:00
        hora_fim_manha = time(12, 0)  # 12:00
        hora_inicio_tarde = time(14, 0)  # 14:00
        hora_fim_trabalho = time(19, 0)  # 19:00
        
        total_horas = Decimal('0.00')
        data_atual = data_inicio
        
        while data_atual <= data_termino:
            # Verificar se é dia útil (segunda a sexta, 0-4)
            if data_atual.weekday() < 5:
                # Primeiro dia: calcular horas do início até o fim do dia
                if data_atual == data_inicio:
                    horas_dia = Decimal('0.00')
                    
                    # Manhã: 09:00-12:00
                    if hora_inicio <= hora_fim_manha:
                        inicio_manha = max(hora_inicio, hora_inicio_trabalho)
                        if inicio_manha < hora_fim_manha:
                            diff_manha = datetime.combine(data_atual, hora_fim_manha) - datetime.combine(data_atual, inicio_manha)
                            horas_dia += Decimal(str(diff_manha.total_seconds() / 3600))
                    
                    # Tarde: 14:00-19:00
                    # Se a hora de início está antes do almoço, considerar toda a tarde
                    if hora_inicio < hora_fim_manha or (hora_inicio >= hora_inicio_tarde and data_atual == data_termino):
                        inicio_tarde = hora_inicio_tarde
                        fim_tarde = hora_termino if (data_atual == data_termino and hora_termino >= hora_inicio_tarde) else hora_fim_trabalho
                        if inicio_tarde < fim_tarde:
                            diff_tarde = datetime.combine(data_atual, fim_tarde) - datetime.combine(data_atual, inicio_tarde)
                            horas_dia += Decimal(str(diff_tarde.total_seconds() / 3600))
                    elif hora_inicio >= hora_inicio_tarde:
                        # Se começa na tarde do primeiro dia
                        fim_tarde = hora_termino if data_atual == data_termino else hora_fim_trabalho
                        if hora_inicio < fim_tarde:
                            diff_tarde = datetime.combine(data_atual, fim_tarde) - datetime.combine(data_atual, hora_inicio)
                            horas_dia += Decimal(str(diff_tarde.total_seconds() / 3600))
                    
                    total_horas += horas_dia
                # Último dia: calcular horas do início do dia até o término
                elif data_atual == data_termino:
                    horas_dia = Decimal('0.00')
                    
                    # Manhã: 09:00-12:00
                    if hora_termino >= hora_inicio_trabalho and hora_termino <= hora_fim_manha:
                        inicio_manha = hora_inicio_trabalho
                        fim_manha = min(hora_termino, hora_fim_manha)
                        if inicio_manha < fim_manha:
                            diff_manha = datetime.combine(data_atual, fim_manha) - datetime.combine(data_atual, inicio_manha)
                            horas_dia += Decimal(str(diff_manha.total_seconds() / 3600))
                    elif hora_termino > hora_fim_manha:
                        # Incluir toda a manhã
                        diff_manha = datetime.combine(data_atual, hora_fim_manha) - datetime.combine(data_atual, hora_inicio_trabalho)
                        horas_dia += Decimal(str(diff_manha.total_seconds() / 3600))
                    
                    # Tarde: 14:00-19:00
                    if hora_termino >= hora_inicio_tarde:
                        inicio_tarde = hora_inicio_tarde
                        fim_tarde = min(hora_termino, hora_fim_trabalho)
                        if inicio_tarde < fim_tarde:
                            diff_tarde = datetime.combine(data_atual, fim_tarde) - datetime.combine(data_atual, inicio_tarde)
                            horas_dia += Decimal(str(diff_tarde.total_seconds() / 3600))
                    
                    total_horas += horas_dia
                # Dias intermediários: 8 horas completas
                else:
                    total_horas += Decimal('8.00')
            
            data_atual += timedelta(days=1)
        
        return total_horas
    
    def is_tarefa_gestao_projetos(self):
        """Verifica se a tarefa é de gestão de projetos (responsável é o gerente do projeto)"""
        if not self.sprint or not self.responsavel:
            return False
        
        # Verificar se o responsável é o gerente do projeto
        if self.sprint.projeto.gerente_projeto:
            return self.responsavel == self.sprint.projeto.gerente_projeto
        return False
    
    def clean(self):
        """Validações de datas e horas"""
        from django.core.exceptions import ValidationError
        from decimal import Decimal
        from datetime import datetime, time
        
        # Validação: data início não pode ser maior que data término
        if self.data_inicio_prevista and self.data_termino_prevista:
            if self.data_inicio_prevista > self.data_termino_prevista:
                raise ValidationError({
                    'data_termino_prevista': 'A data/hora de término não pode ser anterior à data/hora de início.'
                })
        
        # Validação: data início e fim da tarefa devem estar dentro do período da sprint
        from django.utils import timezone as tz
        
        if self.sprint and self.data_inicio_prevista:
            # Converter data_inicio da sprint para datetime se necessário
            if isinstance(self.sprint.data_inicio, datetime):
                data_inicio_sprint = self.sprint.data_inicio
            else:
                data_inicio_sprint = datetime.combine(self.sprint.data_inicio, time.min)
                # Tornar timezone-aware se o data_inicio_prevista for aware
                if tz.is_aware(self.data_inicio_prevista):
                    data_inicio_sprint = tz.make_aware(data_inicio_sprint)
            
            # Validar que a data de início não é anterior à data de início da sprint
            if self.data_inicio_prevista < data_inicio_sprint:
                raise ValidationError({
                    'data_inicio_prevista': f'A data/hora de início deve ser maior ou igual à data de início da sprint ({self.sprint.data_inicio.strftime("%d/%m/%Y")}).'
                })
        
        if self.sprint and self.data_termino_prevista:
            # Converter data_fim da sprint para datetime se necessário
            if isinstance(self.sprint.data_fim, datetime):
                data_fim_sprint = self.sprint.data_fim
            else:
                data_fim_sprint = datetime.combine(self.sprint.data_fim, time(23, 59, 59))
                # Tornar timezone-aware se o data_termino_prevista for aware
                if tz.is_aware(self.data_termino_prevista):
                    data_fim_sprint = tz.make_aware(data_fim_sprint)
            
            # Validar que a data de término não é posterior à data de fim da sprint
            if self.data_termino_prevista > data_fim_sprint:
                raise ValidationError({
                    'data_termino_prevista': f'A data/hora de término deve ser menor ou igual à data de fim da sprint ({self.sprint.data_fim.strftime("%d/%m/%Y")}).'
                })
        
        # Validação de horas planejadas para tarefas do consultor
        if self.sprint and self.sprint.ordem_servico and not self.is_tarefa_gestao_projetos():
            os = self.sprint.ordem_servico
            horas_consultor_os = os.horas_consultor or Decimal('0.00')
            
            # Calcular horas planejadas baseado nas datas/horas
            if self.data_inicio_prevista and self.data_termino_prevista:
                horas_calculadas = self.calcular_horas_dias_uteis(
                    self.data_inicio_prevista,
                    self.data_termino_prevista
                )
                
                # Verificar se as horas calculadas não excedem o total da OS
                if horas_calculadas > horas_consultor_os:
                    raise ValidationError({
                        'data_termino_prevista': f'As horas planejadas ({horas_calculadas}h) excedem o total de horas do consultor na OS ({horas_consultor_os}h).'
                    })
                
                # Verificar soma de todas as tarefas do consultor (exceto esta)
                # Usar self.__class__ para evitar referência circular
                outras_tarefas_consultor = self.__class__.objects.filter(
                    sprint=self.sprint,
                    ordem_servico=os
                ).exclude(pk=self.pk if self.pk else None)
                
                # Filtrar apenas tarefas que não são de gestão de projetos
                outras_tarefas_consultor = [
                    t for t in outras_tarefas_consultor 
                    if not t.is_tarefa_gestao_projetos()
                ]
                
                total_horas_outras = sum(
                    t.horas_planejadas for t in outras_tarefas_consultor
                )
                
                total_horas_todas = total_horas_outras + horas_calculadas
                
                if total_horas_todas > horas_consultor_os:
                    raise ValidationError({
                        'data_termino_prevista': f'A soma das horas planejadas de todas as tarefas do consultor ({total_horas_todas}h) excede o total de horas do consultor na OS ({horas_consultor_os}h).'
                    })
    
    def save(self, *args, **kwargs):
        """Alocação automática no backlog e cálculo de horas planejadas"""
        from decimal import Decimal
        
        # Se a tarefa está em sprint, atualizar status_sprint
        if self.sprint:
            if not self.status_sprint:
                self.status_sprint = "nao_iniciada"
        else:
            self.status_sprint = None
        
        # Calcular horas planejadas
        if self.is_tarefa_gestao_projetos():
            # Tarefa de gestão de projetos: 25% da soma de todas as horas das tarefas de consultor na sprint
            if self.sprint:
                # Calcular total de horas de todas as tarefas de consultor na sprint (excluindo a própria tarefa de gestão)
                tarefas_consultor = self.sprint.tarefas.exclude(titulo__icontains="gestão").exclude(titulo__icontains="gerente").exclude(pk=self.pk if self.pk else None)
                total_horas_consultor = sum(t.horas_planejadas for t in tarefas_consultor if t.horas_planejadas) or Decimal('0.00')
                self.horas_planejadas = total_horas_consultor * Decimal('0.25')
                # Data de início e término igual à da sprint
                if self.sprint:
                    from datetime import datetime, time
                    from django.utils import timezone as tz
                    
                    # Converter datas da sprint para datetime se necessário
                    if isinstance(self.sprint.data_inicio, datetime):
                        self.data_inicio_prevista = self.sprint.data_inicio
                    else:
                        data_inicio = datetime.combine(self.sprint.data_inicio, time.min)
                        # Tornar timezone-aware se necessário (verificar se já existe um valor aware)
                        if hasattr(self, '_state') and self._state.adding:
                            # Nova tarefa: verificar se outras tarefas da sprint são aware
                            outras_tarefas = self.sprint.tarefas.exclude(pk=self.pk if self.pk else None).first()
                            if outras_tarefas and outras_tarefas.data_inicio_prevista and tz.is_aware(outras_tarefas.data_inicio_prevista):
                                data_inicio = tz.make_aware(data_inicio)
                        elif self.data_inicio_prevista and tz.is_aware(self.data_inicio_prevista):
                            data_inicio = tz.make_aware(data_inicio)
                        self.data_inicio_prevista = data_inicio
                    
                    if isinstance(self.sprint.data_fim, datetime):
                        self.data_termino_prevista = self.sprint.data_fim
                    else:
                        data_termino = datetime.combine(self.sprint.data_fim, time(23, 59, 59))
                        # Tornar timezone-aware se necessário
                        if hasattr(self, '_state') and self._state.adding:
                            # Nova tarefa: verificar se outras tarefas da sprint são aware
                            outras_tarefas = self.sprint.tarefas.exclude(pk=self.pk if self.pk else None).first()
                            if outras_tarefas and outras_tarefas.data_termino_prevista and tz.is_aware(outras_tarefas.data_termino_prevista):
                                data_termino = tz.make_aware(data_termino)
                        elif self.data_termino_prevista and tz.is_aware(self.data_termino_prevista):
                            data_termino = tz.make_aware(data_termino)
                        self.data_termino_prevista = data_termino
        else:
            # Tarefa do consultor: calcular baseado em datas/horas e dias úteis
            if self.data_inicio_prevista and self.data_termino_prevista:
                # Calcular automaticamente, mas permitir edição manual
                horas_calculadas = self.calcular_horas_dias_uteis(
                    self.data_inicio_prevista,
                    self.data_termino_prevista
                )
                # Só atualizar se não foi preenchido manualmente ou se é nova tarefa
                # Para edição, manter o valor existente se já foi preenchido
                if not self.pk:
                    # Nova tarefa: usar valor calculado
                    self.horas_planejadas = horas_calculadas
                elif self.horas_planejadas == 0:
                    # Tarefa existente sem horas: usar valor calculado
                    self.horas_planejadas = horas_calculadas
                # Se horas_planejadas já tem valor, manter (editável pelo usuário)
        
        super().save(*args, **kwargs)
    
    @property
    def horas_restantes(self):
        """Horas restantes para conclusão"""
        return max(self.horas_planejadas - self.horas_consumidas, Decimal('0.00'))
    
    @property
    def percentual_conclusao(self):
        """Percentual de conclusão baseado em horas"""
        if self.horas_planejadas > 0:
            return (self.horas_consumidas / self.horas_planejadas) * 100
        return Decimal('0.00')
    
    @property
    def is_faturada(self):
        """Verifica se a tarefa está vinculada a uma OS (horas faturadas)"""
        return self.ordem_servico is not None
    
    @property
    def status_display(self):
        """Retorna o status correto baseado se está em sprint ou não"""
        if self.sprint and self.status_sprint:
            return self.get_status_sprint_display()
        return self.get_status_display()
    
    @property
    def status_display(self):
        """Retorna o status correto baseado se está em sprint ou não"""
        if self.sprint and self.status_sprint:
            return self.get_status_sprint_display()
        return self.get_status_display()


class LancamentoHora(models.Model):
    """Lançamentos de horas para tarefas"""
    tarefa = models.ForeignKey(
        "Tarefa",
        on_delete=models.CASCADE,
        related_name="lancamentos_horas",
        verbose_name="Tarefa",
        blank=True,
        null=True
    )
    colaborador = models.ForeignKey(
        "Colaborador",
        on_delete=models.CASCADE,
        related_name="lancamentos_horas",
        verbose_name="Colaborador"
    )
    data = models.DateField(verbose_name="Data")
    hora_inicio = models.TimeField(verbose_name="Hora de Início")
    hora_termino = models.TimeField(verbose_name="Hora de Término")
    horas_trabalhadas = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        editable=False,
        verbose_name="Horas Trabalhadas"
    )
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição do Trabalho")
    faturavel = models.BooleanField(default=True, verbose_name="Faturável")
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Lançamento de Hora"
        verbose_name_plural = "Lançamentos de Horas"
        ordering = ["-data", "-hora_inicio"]
    
    def save(self, *args, **kwargs):
        # Calcular horas trabalhadas automaticamente
        if self.hora_inicio and self.hora_termino:
            inicio = datetime.combine(self.data, self.hora_inicio)
            termino = datetime.combine(self.data, self.hora_termino)
            if termino < inicio:
                # Se termino for menor que inicio, assumir que passou da meia-noite
                termino += timedelta(days=1)
            diferenca = termino - inicio
            self.horas_trabalhadas = Decimal(str(diferenca.total_seconds() / 3600))
        
        super().save(*args, **kwargs)
        
        # Atualizar horas consumidas da tarefa
        if self.tarefa:
            total_horas = self.tarefa.lancamentos_horas.aggregate(
                total=Sum('horas_trabalhadas')
            )['total'] or Decimal('0.00')
            self.tarefa.horas_consumidas = total_horas
            self.tarefa.save(update_fields=['horas_consumidas'])
    
    def __str__(self):
        return f"{self.colaborador.nome_completo} - {self.data} - {self.horas_trabalhadas}h"


class AnaliseContrato(models.Model):
    """
    Modelo para agrupar múltiplos documentos em uma única análise
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente de Análise'),
        ('processando', 'Processando'),
        ('analisado', 'Analisado'),
        ('erro', 'Erro na Análise'),
        ('revisado', 'Revisado pelo Usuário'),
    ]
    
    nome = models.CharField(
        max_length=255, 
        verbose_name="Nome da Análise",
        help_text="Ex: Análise Contrato 009/2025 - CNPQ"
    )
    texto_consolidado = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Texto Consolidado",
        help_text="Texto extraído de todos os documentos combinados"
    )
    dados_extraidos = models.JSONField(
        blank=True, 
        null=True, 
        verbose_name="Dados Extraídos pela IA"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pendente',
        verbose_name="Status"
    )
    mensagem_erro = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Mensagem de Erro"
    )
    
    # Relacionamentos opcionais (preenchidos após criação)
    contrato_gerado = models.ForeignKey(
        'Contrato',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='analises_origem',
        verbose_name="Contrato Gerado/Vinculado"
    )
    cliente_gerado = models.ForeignKey(
        'Cliente',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='analises_origem',
        verbose_name="Cliente Gerado/Vinculado"
    )
    
    # Metadados
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Criado por"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Análise de Contrato"
        verbose_name_plural = "Análises de Contratos"
        ordering = ["-criado_em"]
    
    def __str__(self):
        return f"{self.nome} - {self.get_status_display()}"


def documento_contrato_upload_to(instance, filename):
    """
    Função para gerar o caminho de upload do arquivo, encurtando nomes muito longos.
    Mantém a extensão original e adiciona um hash para garantir unicidade.
    """
    # Extrai a extensão do arquivo
    ext = os.path.splitext(filename)[1].lower()
    
    # Remove caracteres especiais e espaços do nome base
    nome_base = os.path.splitext(filename)[0]
    # Remove caracteres especiais, mantém apenas alfanuméricos, espaços, hífens e underscores
    nome_base = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in nome_base)
    # Remove espaços múltiplos
    nome_base = '_'.join(nome_base.split())
    
    # Limita o tamanho do nome base a 100 caracteres
    if len(nome_base) > 100:
        nome_base = nome_base[:100]
    
    # Gera um hash único para garantir unicidade
    hash_unico = str(uuid.uuid4())[:8]
    
    # Monta o nome final: nome_base_hash.extensao
    nome_final = f"{nome_base}_{hash_unico}{ext}"
    
    # Retorna o caminho completo com data
    return f"documentos_contratos/{timezone.now().year}/{timezone.now().month:02d}/{nome_final}"


class DocumentoContrato(models.Model):
    """
    Modelo para armazenar documentos individuais de contrato para análise por IA.
    Suporta: Contratos, Editais, ETPs, TRs, ARPs, Propostas, Termos Aditivos
    """
    TIPO_DOCUMENTO_CHOICES = [
        ('contrato', 'Contrato'),
        ('edital', 'Edital de Licitação'),
        ('etp', 'Estudo Técnico Preliminar (ETP)'),
        ('tr', 'Termo de Referência (TR)'),
        ('arp', 'Ata de Registro de Preços (ARP)'),
        ('proposta', 'Proposta Comercial'),
        ('termo_aditivo', 'Termo Aditivo'),
        ('outro', 'Outro Documento'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente de Análise'),
        ('processando', 'Processando'),
        ('analisado', 'Analisado'),
        ('erro', 'Erro na Análise'),
    ]
    
    analise = models.ForeignKey(
        'AnaliseContrato',
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name="Análise",
        blank=True,
        null=True,
        help_text="Análise à qual este documento pertence"
    )
    nome = models.CharField(max_length=255, verbose_name="Nome do Documento")
    tipo_documento = models.CharField(
        max_length=20, 
        choices=TIPO_DOCUMENTO_CHOICES, 
        default='contrato',
        verbose_name="Tipo de Documento"
    )
    arquivo = models.FileField(
        upload_to=documento_contrato_upload_to,
        max_length=500,
        verbose_name="Arquivo"
    )
    texto_extraido = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Texto Extraído"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pendente',
        verbose_name="Status"
    )
    mensagem_erro = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Mensagem de Erro"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Documento de Contrato"
        verbose_name_plural = "Documentos de Contratos"
        ordering = ["analise", "tipo_documento", "nome"]
    
    def __str__(self):
        return f"{self.nome} ({self.get_tipo_documento_display()})"
    
    @property
    def extensao_arquivo(self):
        if self.arquivo:
            return self.arquivo.name.split('.')[-1].lower()
        return None


class PlanoTrabalho(models.Model):
    """
    Plano de trabalho completo gerado pela IA para um projeto
    Um projeto tem um plano de trabalho (1:1)
    """
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('pendente_aprovacao', 'Pendente de Aprovação'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('em_execucao', 'Em Execução'),
        ('concluido', 'Concluído'),
    ]
    
    projeto = models.OneToOneField(
        'Projeto',
        on_delete=models.CASCADE,
        related_name='plano_trabalho',
        verbose_name="Projeto",
        help_text="Projeto ao qual o plano de trabalho pertence",
        blank=True,
        null=True  # Temporariamente nullable para migração
    )
    fornecedor = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Fornecedor",
        help_text="Fornecedor principal do projeto (para definir modelo de exportação)"
    )
    
    # Resumo e análise
    resumo_contrato = models.TextField(
        verbose_name="Resumo do Contrato",
        help_text="Resumo executivo do contrato gerado pela IA"
    )
    pontos_atencao = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Pontos de Atenção",
        help_text="Lista de pontos críticos identificados"
    )
    
    # Processo de execução
    processo_execucao = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Processo de Execução",
        help_text="Etapas do processo de execução do contrato"
    )
    
    # Cronograma
    data_inicio_prevista = models.DateField(
        verbose_name="Data de Início Prevista"
    )
    data_fim_prevista = models.DateField(
        verbose_name="Data de Fim Prevista"
    )
    cronograma_detalhado = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Cronograma Detalhado",
        help_text="Cronograma com marcos e entregas"
    )
    
    # Plano de comunicação
    plano_comunicacao = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Plano de Comunicação",
        help_text="Estrutura de comunicação e stakeholders"
    )
    
    # Status report
    template_status_report = models.TextField(
        blank=True,
        null=True,
        verbose_name="Template de Status Report",
        help_text="Template para relatórios de status"
    )
    frequencia_status_report = models.CharField(
        max_length=50,
        default='semanal',
        verbose_name="Frequência do Status Report",
        help_text="Ex: semanal, quinzenal, mensal"
    )
    
    # Status e aprovação
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='rascunho',
        verbose_name="Status"
    )
    aprovado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='planos_aprovados',
        verbose_name="Aprovado por"
    )
    data_aprovacao = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data de Aprovação"
    )
    observacoes_aprovacao = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações da Aprovação"
    )
    
    # Metadados
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='planos_criados',
        verbose_name="Criado por"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plano de Trabalho"
        verbose_name_plural = "Planos de Trabalho"
        ordering = ["-criado_em"]
    
    def __str__(self):
        return f"Plano de Trabalho - {self.projeto.nome}"
    
    def aprovar(self, usuario, observacoes=None):
        """Aprova o plano de trabalho"""
        self.status = 'aprovado'
        self.aprovado_por = usuario
        self.data_aprovacao = timezone.now()
        if observacoes:
            self.observacoes_aprovacao = observacoes
        self.save()


class SLAImportante(models.Model):
    """
    SLAs críticos identificados pela IA com alertas configurados
    """
    PRIORIDADE_CHOICES = [
        ('critica', 'Crítica'),
        ('alta', 'Alta'),
        ('media', 'Média'),
        ('baixa', 'Baixa'),
    ]
    
    contrato = models.ForeignKey(
        'Contrato',
        on_delete=models.CASCADE,
        related_name='slas_importantes',
        verbose_name="Contrato"
    )
    sla = models.ForeignKey(
        'SLA',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='slas_importantes',
        verbose_name="SLA Vinculado"
    )
    
    nome = models.CharField(max_length=255, verbose_name="Nome do SLA")
    descricao = models.TextField(verbose_name="Descrição")
    tempo_resposta_horas = models.IntegerField(verbose_name="Tempo de Resposta (horas)")
    tempo_solucao_horas = models.IntegerField(verbose_name="Tempo de Solução (horas)")
    prioridade = models.CharField(
        max_length=20,
        choices=PRIORIDADE_CHOICES,
        default='media',
        verbose_name="Prioridade"
    )
    
    # Alertas
    alerta_antes_horas = models.IntegerField(
        default=24,
        verbose_name="Alerta Antes (horas)",
        help_text="Horas antes do prazo para enviar alerta"
    )
    alerta_ativo = models.BooleanField(
        default=True,
        verbose_name="Alerta Ativo"
    )
    
    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "SLA Importante"
        verbose_name_plural = "SLAs Importantes"
        ordering = ["prioridade", "tempo_resposta_horas"]
    
    def __str__(self):
        return f"{self.nome} - {self.contrato.numero_contrato}"


class QuadroPenalizacao(models.Model):
    """
    Quadro de penalizações e glosas para SLAs
    """
    sla_importante = models.ForeignKey(
        SLAImportante,
        on_delete=models.CASCADE,
        related_name='penalizacoes',
        verbose_name="SLA Importante"
    )
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('penalizacao', 'Penalização'),
            ('glosa', 'Glosa'),
            ('multa', 'Multa'),
        ],
        verbose_name="Tipo"
    )
    percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Percentual (%)",
        help_text="Percentual aplicado sobre o valor do contrato/item"
    )
    valor_fixo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor Fixo (R$)",
        help_text="Valor fixo em R$ (opcional)"
    )
    condicao_aplicacao = models.TextField(
        verbose_name="Condição de Aplicação",
        help_text="Descrição de quando esta penalização/glosa se aplica"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Quadro de Penalização/Glosa"
        verbose_name_plural = "Quadros de Penalizações/Glosas"
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.descricao}"


class MatrizRACI(models.Model):
    """
    Matriz RACI para o projeto/contrato
    """
    contrato = models.ForeignKey(
        'Contrato',
        on_delete=models.CASCADE,
        related_name='matriz_raci',
        verbose_name="Contrato"
    )
    atividade = models.CharField(max_length=255, verbose_name="Atividade")
    responsavel = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Responsável (R)",
        help_text="Quem executa a atividade"
    )
    aprovador = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Aprovador (A)",
        help_text="Quem aprova a atividade"
    )
    consultado = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Consultado (C)",
        help_text="Quem é consultado (separado por vírgula)"
    )
    informado = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Informado (I)",
        help_text="Quem é informado (separado por vírgula)"
    )
    fase = models.CharField(
        max_length=50,
        choices=[
            ('planejamento', 'Planejamento'),
            ('implantacao', 'Implantação'),
            ('execucao', 'Execução'),
            ('suporte', 'Suporte/Sustentação'),
        ],
        verbose_name="Fase"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Matriz RACI"
        verbose_name_plural = "Matriz RACI"
        ordering = ['fase', 'atividade']
    
    def __str__(self):
        return f"{self.atividade} - {self.get_fase_display()}"


class ClausulaCritica(models.Model):
    """
    Cláusulas críticas identificadas no contrato
    """
    contrato = models.ForeignKey(
        'Contrato',
        on_delete=models.CASCADE,
        related_name='clausulas_criticas',
        verbose_name="Contrato"
    )
    titulo = models.CharField(max_length=255, verbose_name="Título")
    numero_clausula = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Número da Cláusula"
    )
    descricao = models.TextField(verbose_name="Descrição")
    impacto = models.CharField(
        max_length=20,
        choices=[
            ('critico', 'Crítico'),
            ('alto', 'Alto'),
            ('medio', 'Médio'),
        ],
        default='medio',
        verbose_name="Impacto"
    )
    acao_necessaria = models.TextField(
        verbose_name="Ação Necessária",
        help_text="Ações que devem ser tomadas para cumprir ou mitigar riscos"
    )
    prazo_atencao = models.DateField(
        blank=True,
        null=True,
        verbose_name="Prazo para Atenção",
        help_text="Data limite para tomar ação"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cláusula Crítica"
        verbose_name_plural = "Cláusulas Críticas"
        ordering = ['impacto', 'prazo_atencao']


# ==================== SIGNALS ====================

@receiver(post_save, sender=ItemContrato)
def atualizar_valor_inicial_contrato_save(sender, instance, **kwargs):
    """
    Atualiza o valor_inicial do contrato quando um item é salvo
    """
    if instance.contrato and instance.contrato.pk:
        instance.contrato._atualizar_valor_inicial()


@receiver(post_delete, sender=ItemContrato)
def atualizar_valor_inicial_contrato_delete(sender, instance, **kwargs):
    """
    Atualiza o valor_inicial do contrato quando um item é deletado
    """
    if instance.contrato and instance.contrato.pk:
        instance.contrato._atualizar_valor_inicial()


class StakeholderContrato(models.Model):
    """
    Stakeholders do contrato (pessoas chave da contratada e contratante)
    """
    class TipoStakeholder(models.TextChoices):
        CONTRATADA = "CONTRATADA", "Contratada"
        CONTRATANTE = "CONTRATANTE", "Contratante"
    
    class PapelContratada(models.TextChoices):
        PREPOSTO = "PREPOSTO", "Preposto"
        PREPOSTO_SUBSTITUTO = "PREPOSTO_SUBSTITUTO", "Preposto Substituto"
        CS = "CS", "CS (Customer Success)"
        GERENTE_CONTRATO = "GERENTE_CONTRATO", "Gerente do Contrato"
        GERENTE_PROJETO = "GERENTE_PROJETO", "Gerente do Projeto"
        GERENTE_SUBSTITUTO = "GERENTE_SUBSTITUTO", "Gerente Substituto"
        GERENTE_COMERCIAL = "GERENTE_COMERCIAL", "Gerente Comercial"
    
    class PapelContratante(models.TextChoices):
        GESTOR_CONTRATO = "GESTOR_CONTRATO", "Gestor do Contrato"
        FISCAL_ADMINISTRATIVO = "FISCAL_ADMINISTRATIVO", "Fiscal Administrativo"
        FISCAL_TECNICO = "FISCAL_TECNICO", "Fiscal Técnico"
    
    contrato = models.ForeignKey(
        "Contrato",
        on_delete=models.CASCADE,
        related_name="stakeholders",
        verbose_name="Contrato"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoStakeholder.choices,
        verbose_name="Tipo de Stakeholder"
    )
    papel = models.CharField(
        max_length=50,
        verbose_name="Papel/Função",
        help_text="Papel do stakeholder no contrato"
    )
    colaborador = models.ForeignKey(
        "Colaborador",
        on_delete=models.SET_NULL,
        related_name="stakeholders_contrato",
        blank=True,
        null=True,
        verbose_name="Colaborador",
        help_text="Colaborador da contratada (usado quando tipo = Contratada)"
    )
    contato_cliente = models.ForeignKey(
        "ContatoCliente",
        on_delete=models.SET_NULL,
        related_name="stakeholders_contrato",
        blank=True,
        null=True,
        verbose_name="Contato do Cliente",
        help_text="Contato do cliente/contratante (usado quando tipo = Contratante)"
    )
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Stakeholder do Contrato"
        verbose_name_plural = "Stakeholders do Contrato"
        unique_together = ("contrato", "tipo", "papel")
        ordering = ["tipo", "papel"]
    
    def clean(self):
        """Validação: colaborador obrigatório para Contratada, contato_cliente obrigatório para Contratante"""
        if self.tipo == self.TipoStakeholder.CONTRATADA:
            if not self.colaborador:
                raise ValidationError("Colaborador é obrigatório para stakeholders da Contratada.")
            if self.contato_cliente:
                raise ValidationError("Contato do cliente não deve ser preenchido para stakeholders da Contratada.")
        elif self.tipo == self.TipoStakeholder.CONTRATANTE:
            if not self.contato_cliente:
                raise ValidationError("Contato do cliente é obrigatório para stakeholders da Contratante.")
            if self.colaborador:
                raise ValidationError("Colaborador não deve ser preenchido para stakeholders da Contratante.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.tipo == self.TipoStakeholder.CONTRATADA and self.colaborador:
            return f"{self.get_papel_display()} - {self.colaborador.nome_completo}"
        elif self.tipo == self.TipoStakeholder.CONTRATANTE and self.contato_cliente:
            return f"{self.get_papel_display()} - {self.contato_cliente.nome}"
        return f"{self.get_tipo_display()} - {self.papel}"
    
    def get_papel_display(self):
        """Retorna o display do papel baseado no tipo"""
        if self.tipo == self.TipoStakeholder.CONTRATADA:
            for choice in self.PapelContratada.choices:
                if choice[0] == self.papel:
                    return choice[1]
        elif self.tipo == self.TipoStakeholder.CONTRATANTE:
            for choice in self.PapelContratante.choices:
                if choice[0] == self.papel:
                    return choice[1]
        return self.papel
