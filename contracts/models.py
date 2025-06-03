from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, datetime, time, date
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, F, FloatField, ExpressionWrapper, Value, DecimalField
from django.db.models.functions import Coalesce

from .constants import FORNECEDORES_MAP


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
    nome_responsavel = models.CharField(max_length=100)
    cargo_responsavel = models.CharField(max_length=100)
    telefone_contato = models.CharField(max_length=20)
    email_contato = models.EmailField()
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.nome_fantasia or self.nome_razao_social


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

    TIPO_ITEM = [
        ("produto", "Produto"),
        ("servico", "Serviço"),
        ("treinamento", "Treinamento"),
    ]
    fornecedor = models.CharField(
        max_length=100,
        choices=FORNECEDORES_CHOICES,
        default="iB Services",
        verbose_name="Fornecedor",
    )
    outro_fornecedor = models.CharField(max_length=100, blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_ITEM)
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


class Contrato(models.Model):
    VIGENCIA_CHOICES = [(12, "12 meses"), (24, "24 meses"), (36, "36 meses")]

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

    vigencia = models.IntegerField("Vigência (meses)", choices=VIGENCIA_CHOICES)
    data_assinatura = models.DateField("Data de Assinatura")
    data_fim = models.DateField("Data de Fim", blank=True, null=True)

    fornecedores = models.JSONField("Fornecedores", default=list, blank=True)

    situacao = models.CharField(
        "Situação",
        max_length=20,
        choices=[("Ativo", "Ativo"), ("Inativo", "Inativo")],
        default="Ativo",
    )
    valor_global = models.DecimalField(
        max_digits=14, decimal_places=2, editable=False, default=0
    )

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"

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

    def save(self, *args, **kwargs):
        # ✅ Normaliza fornecedores (UPPER)
        if self.fornecedores:
            self.fornecedores = [f.strip().upper() for f in self.fornecedores]

        # 🗓️ Calcula a data de fim
        if self.data_assinatura and self.vigencia:
            self.data_fim = self.data_assinatura + relativedelta(months=self.vigencia)

        # 🔄 Atualiza situação
        if self.data_fim:
            self.situacao = (
                "Ativo" if self.data_fim >= timezone.now().date() else "Inativo"
            )

        # 🚩 Primeiro save (precisa da PK)
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # 🔄 Atualiza valor_global após garantir PK
        if is_new:
            self.valor_global = self.calcular_valor_global
            super().save(update_fields=["valor_global"])

    def __str__(self):
        return f"Contrato {self.numero_contrato} - {self.cliente}"


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
    VIGENCIA_PRODUTO_CHOICES_CONT
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
        max_length=20, 
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

    def __str__(self):
        # Tentativa de obter o número do contrato de forma segura
        numero_contrato_str = self.contrato.numero_contrato if self.contrato else "N/A"
        return f"Item {self.numero_item} - {self.descricao[:30]}... ({numero_contrato_str})"

    def get_valor_total_faturado_os(self):
        from .models import OrdemServico # Movido para dentro para evitar importação circular se necessário
        if not hasattr(self, 'ordens_servico'): # related_name para OrdemServico->ItemContrato
            return DecimalField().to_python(0)
            
        total_faturado = self.ordens_servico.filter(status="faturada").aggregate(
            total=Coalesce(Sum(F('valor_unitario') * F('quantidade')), Value(0), output_field=DecimalField())
        )['total']
        return total_faturado

    def get_valor_total_faturado_of(self):
        from .models import OrdemFornecimento # Movido para dentro para evitar importação circular se necessário
        if not hasattr(self, 'ordens_fornecimento'): # related_name para OrdemFornecimento->ItemContrato
            return DecimalField().to_python(0)

        total_faturado = self.ordens_fornecimento.filter(status="faturada").aggregate(
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
            if not hasattr(self, 'ordens_fornecimento'):
                 return self.vigencia_produto # Ou None, dependendo da lógica desejada

            ativacoes = self.ordens_fornecimento.filter(
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
        max_length=20, unique=True, verbose_name="Número da OF"
    )
    numero_of_cliente = models.CharField(
        max_length=100, verbose_name="Número da OF do Cliente", blank=True, null=True
    )
    cliente = models.ForeignKey("Cliente", on_delete=models.PROTECT)
    contrato = models.ForeignKey("Contrato", on_delete=models.PROTECT)
    item_contrato = models.ForeignKey(
        "ItemContrato",
        limit_choices_to={"tipo__in": ["hardware", "software", "solucao"]},
        on_delete=models.PROTECT,
    )
    item_fornecedor = models.ForeignKey(
        "ItemFornecedor", limit_choices_to={"tipo": "produto"}, on_delete=models.PROTECT
    )

    unidade = models.CharField(max_length=20, verbose_name="Unidade", default="Licença")
    quantidade = models.PositiveIntegerField()
    vigencia_produto = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Vigência do Produto (meses)"
    )
    valor_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    valor_total = models.DecimalField(max_digits=14, decimal_places=2)

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
        if self.item_contrato.tipo not in ["hardware", "software", "solucao"]:
            raise ValidationError(
                "Item do contrato deve ser do tipo Hardware, Software ou Solução."
            )

        if self.item_fornecedor.tipo != "produto":
            raise ValidationError("O item do fornecedor deve ser do tipo Produto.")

        if self.item_fornecedor.fornecedor not in [
            f.upper() for f in self.contrato.fornecedores
        ]:
            raise ValidationError(
                f"O fornecedor '{self.item_fornecedor.fornecedor}' não está vinculado a este contrato."
            )

        total_consumido = sum(
            of.quantidade
            for of in OrdemFornecimento.objects.filter(
                item_contrato=self.item_contrato
            ).exclude(pk=self.pk)
        )

        saldo_disponivel = self.item_contrato.quantidade - total_consumido

        if self.quantidade > saldo_disponivel:
            raise ValidationError(
                f"A quantidade ({self.quantidade}) excede o saldo disponível ({saldo_disponivel})."
            )

    def save(self, *args, **kwargs):
        # Atualização automática de campos derivados
        self.unidade = self.item_contrato.unidade
        self.vigencia_produto = self.item_contrato.vigencia_produto
        self.valor_unitario = self.item_contrato.valor_unitario
        self.valor_total = self.valor_unitario * self.quantidade

        # Preenchimento das datas baseado no status
        if self.status == self.STATUS_FINALIZADA and not self.data_ativacao:
            self.data_ativacao = timezone.now().date()

        if self.status == self.STATUS_FATURADA and not self.data_faturamento:
            self.data_faturamento = timezone.now().date()

        super().save(*args, **kwargs)

    @property
    def vigencia_restante(self):
        if self.item_contrato.vigencia_produto and self.data_ativacao:
            delta = timezone.now().date() - self.data_ativacao
            meses_decorridos = delta.days // 30
            return max(self.item_contrato.vigencia_produto - meses_decorridos, 0)
        return None


class OrdemServico(models.Model):
    STATUS_CHOICES = [
        ("aberta", "Aberta"),
        ("execucao", "Em execução"),
        ("finalizada", "Finalizada"),
        ("faturada", "Faturada"),
    ]

    numero_os = models.CharField(max_length=20, unique=True)
    numero_os_cliente = models.CharField(max_length=50, blank=True, null=True)

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE)
    item_contrato = models.ForeignKey(ItemContrato, on_delete=models.CASCADE)
    item_fornecedor = models.ForeignKey(ItemFornecedor, on_delete=models.CASCADE)

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

    class Meta:
        unique_together = ("numero_os", "contrato")

    def __str__(self):
        return f"{self.numero_os} - {self.cliente.nome_fantasia}"

    def save(self, *args, **kwargs):
        is_update = self.pk is not None
        old_instance = None

        if is_update:
            old_instance = OrdemServico.objects.get(pk=self.pk)

        # Definir unidade e valor unitário
        self.unidade = self.item_contrato.unidade
        self.valor_unitario = self.item_contrato.valor_unitario
        self.valor_total = self.quantidade * self.valor_unitario

        # Definir Tipo OS automaticamente
        self.tipo_os = self.item_contrato.tipo

        # Calcular Horas Totais se for do tipo Serviço
        if self.tipo_os == "Serviço":
            self.horas_totais = (self.horas_consultor or 0) + (self.horas_gerente or 0)
        else:
            self.horas_totais = 0

        # Calcular Data e Hora de Término
        if self.data_inicio and self.hora_inicio and self.horas_totais > 0:
            self.data_termino, self.hora_termino = self.calcula_termino()

        # Gerar data_emissao_trd se status for Finalizada
        if self.status == "Finalizada" and not self.data_emissao_trd:
            self.data_emissao_trd = timezone.now().date()

        # Gerar data_faturamento se status for Faturada
        if self.status == "Faturada" and not self.data_faturamento:
            self.data_faturamento = timezone.now().date()

        super().save(*args, **kwargs)

        if self.status == "faturada":
            if not is_update or (old_instance and old_instance.status != "faturada"):
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
