from django import forms
from .models import (
    Cliente,
    Contrato,
    ItemContrato,
    ItemFornecedor,
    OrdemFornecimento,
    OrdemServico,
)
from dateutil.relativedelta import relativedelta
from .utils import map_tipo_item_contrato_para_fornecedor
from .constants import FORNECEDORES_MAP
from django.utils import timezone
from django.forms import DateInput


# Cliente Form
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = "__all__"


# 🔗 Lista padrão de fornecedores
FORNECEDORES_CHOICES = [(key, label) for key, label in FORNECEDORES_MAP.items()]


# Contrato Form
class ContratoForm(forms.ModelForm):
    fornecedores = forms.MultipleChoiceField(
        choices=FORNECEDORES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Fornecedores",
    )

    class Meta:
        model = Contrato
        fields = "__all__"
        widgets = {
            "data_assinatura": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
                }
            ),
            "data_fim": forms.DateInput(
                attrs={
                    "type": "date",
                    "readonly": "readonly",
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #  Buscar fornecedores cadastrados no ItemFornecedor
        fornecedores_db = ItemFornecedor.objects.values_list(
            "fornecedor", flat=True
        ).distinct()

        # 🔗 Unificar lista padrão + fornecedores do banco (normalizando para UPPER)
        fornecedores_unicos = set(FORNECEDORES_MAP.keys())
        fornecedores_db_upper = {f.strip().upper() for f in fornecedores_db}
        fornecedores_unicos.update(fornecedores_db_upper)

        # Ordena pelo nome amigável (label)
        fornecedores_ordenados = sorted(
            [(f, FORNECEDORES_MAP.get(f, f.title())) for f in fornecedores_unicos],
            key=lambda x: x[1],
        )

        # Aplica no campo
        self.fields["fornecedores"].choices = fornecedores_ordenados

        # Carregar fornecedores existentes no contrato, quando em edição
        if self.instance and self.instance.pk:
            self.initial["fornecedores"] = [
                f.upper() for f in self.instance.fornecedores
            ]

        # Aplicar CSS em todos os campos (exceto DateInput e Checkbox)
        for field_name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                }
            )

            # Corrige preenchimento dos campos date no modo edição
            if isinstance(field.widget, DateInput):
                field.widget.format = "%Y-%m-%d"
                if self.instance and getattr(self.instance, field_name):
                    field.initial = getattr(self.instance, field_name)

    def clean(self):
        cleaned_data = super().clean()

        # Normaliza fornecedores para UPPER (banco salvo sempre em caixa alta)
        fornecedores = cleaned_data.get("fornecedores")
        if fornecedores:
            cleaned_data["fornecedores"] = [f.strip().upper() for f in fornecedores]

        # Calcula data_fim automaticamente
        data_assinatura = cleaned_data.get("data_assinatura")
        vigencia = cleaned_data.get("vigencia")

        if data_assinatura and vigencia:
            cleaned_data["data_fim"] = data_assinatura + relativedelta(months=vigencia)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.fornecedores = self.cleaned_data.get("fornecedores", [])
        if commit:
            instance.save()
        return instance


# ItemContrato Form
class ItemContratoForm(forms.ModelForm):
    class Meta:
        model = ItemContrato
        fields = "__all__"
        widgets = {
            "contrato": forms.Select(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                }
            ),
            "descricao": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
                }
            ),
            "data_ativacao": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg "
                    "focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 "
                    "dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                }
            )

        # CSS global para todos os campos
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.DateInput) and not isinstance(
                field.widget, forms.Textarea
            ):
                field.widget.attrs.update(
                    {
                        "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                    }
                )

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")

        if tipo in ["Hardware", "Software", "Solução"]:
            if not cleaned_data.get("vigencia_produto"):
                self.add_error(
                    "vigencia_produto",
                    "Este campo é obrigatório para Hardware, Software ou Solução.",
                )
        else:
            cleaned_data["vigencia_produto"] = None

        return cleaned_data


# ItemFornecedor Form
class ItemFornecedorForm(forms.ModelForm):
    class Meta:
        model = ItemFornecedor
        fields = "__all__"
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fornecedor = cleaned_data.get("fornecedor")
        outro_fornecedor = cleaned_data.get("outro_fornecedor")
        valor_unitario = cleaned_data.get("valor_unitario")

        if fornecedor == "Outro Fornecedor" and not outro_fornecedor:
            self.add_error("outro_fornecedor", "Informe o nome do outro fornecedor.")

        if valor_unitario is not None and valor_unitario < 0:
            self.add_error("valor_unitario", "O valor unitário deve ser positivo.")
    


# Ordem Fornecimento Form
from django import forms
from .models import OrdemFornecimento, Contrato, ItemContrato, ItemFornecedor


class OrdemFornecimentoForm(forms.ModelForm):
    class Meta:
        model = OrdemFornecimento
        fields = "__all__"
        widgets = {
            "numero_of": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500"
                }
            ),
            "numero_of_cliente": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500"
                }
            ),
            "cliente": forms.Select(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500"
                }
            ),
            "contrato": forms.Select(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500"
                }
            ),
            "item_contrato": forms.Select(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500"
                }
            ),
            "item_fornecedor": forms.Select(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500"
                }
            ),
            "unidade": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "quantidade": forms.NumberInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500"
                }
            ),
            "vigencia_produto": forms.NumberInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "valor_unitario": forms.NumberInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500",
                    "readonly": "readonly",
                }
            ),
            "valor_total": forms.NumberInput(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500",
                    "readonly": "readonly",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500"
                }
            ),
            "data_ativacao": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "data_faturamento": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500",
                }
            ),
            "observacoes": forms.Textarea(
                attrs={
                    "rows": "2",
                    "class": "w-full rounded-lg border border-gray-300 dark:border-gray-600 "
                    "bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white "
                    "focus:ring-blue-500 focus:border-blue-500",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Clientes com contrato ativo
        self.fields["cliente"].queryset = Cliente.objects.filter(
            contratos__situacao="Ativo"
        ).distinct()

        # Status padrão na criação
        if not self.instance.pk:
            self.fields["status"].choices = [("aberta", "Aberta")]
            self.initial["status"] = "aberta"
        else:
            status_atual = self.instance.status

            # if self.instance.status not in ['finalizada', 'faturada']:
            #     self.fields['data_ativacao'].widget = forms.HiddenInput()

            # if self.instance.status != 'faturada':
            #     self.fields['data_faturamento'].widget = forms.HiddenInput()

            # Define as opções válidas conforme o status atual
            if status_atual == "aberta":
                self.fields["status"].choices = [
                    ("aberta", "Aberta"),
                    ("execucao", "Em Execução"),
                ]
            elif status_atual == "execucao":
                self.fields["status"].choices = [
                    ("execucao", "Em Execução"),
                    ("finalizada", "Finalizada"),
                ]
            elif status_atual == "finalizada":
                self.fields["status"].choices = [
                    ("finalizada", "Finalizada"),
                    ("faturada", "Faturada"),
                ]
            elif status_atual == "faturada":
                self.fields["status"].choices = [("faturada", "Faturada")]

        # Valor Unitário como somente leitura
        self.fields["valor_unitario"].widget.attrs["readonly"] = True
        self.fields["valor_total"].widget.attrs["readonly"] = True

    def clean(self):
        cleaned_data = super().clean()

        status = cleaned_data.get("status")
        item_contrato = cleaned_data.get("item_contrato")
        quantidade = cleaned_data.get("quantidade")

        # Preenche automaticamente valor unitário
        if item_contrato:
            cleaned_data["valor_unitario"] = item_contrato.valor_unitario
        else:
            cleaned_data["valor_unitario"] = 0
        if quantidade and cleaned_data["valor_unitario"]:
            cleaned_data["valor_total"] = quantidade * cleaned_data["valor_unitario"]
        else:
            cleaned_data["valor_total"] = 0

        # Data de ativação (permanece desde Finalizada)
        if status in ["finalizada", "faturada"]:
            if not cleaned_data.get("data_ativacao"):
                cleaned_data["data_ativacao"] = timezone.now().date()

        # Data de faturamento obrigatória se Faturada
        if status == "faturada":
            if not cleaned_data.get("data_faturamento"):
                cleaned_data["data_faturamento"] = timezone.now().date()

        return cleaned_data


# Ordem Serviço Form
class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = "__all__"
        widgets = {
            "data_inicio": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "data_termino": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "hora_termino": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "data_emissao_trd": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "data_faturamento": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "observacoes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aplica classes CSS aos campos
        for field in self.fields.values():
            field.widget.attrs.update(
                {
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg "
                    "focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 "
                    "dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                }
            )

        # Filtrar clientes com contrato ativo
        self.fields["cliente"].queryset = Cliente.objects.filter(
            contratos__situacao="Ativo"
        ).distinct()

        # Configuração das opções de status
        if not self.instance.pk:
            self.fields["status"].choices = [("aberta", "Aberta")]
            self.initial["status"] = "aberta"
        else:
            status_atual = self.instance.status
            if status_atual == "aberta":
                self.fields["status"].choices = [
                    ("aberta", "Aberta"),
                    ("execucao", "Em Execução"),
                ]
            elif status_atual == "execucao":
                self.fields["status"].choices = [
                    ("execucao", "Em Execução"),
                    ("finalizada", "Finalizada"),
                ]
            elif status_atual == "finalizada":
                self.fields["status"].choices = [
                    ("finalizada", "Finalizada"),
                    ("faturada", "Faturada"),
                ]
            elif status_atual == "faturada":
                self.fields["status"].choices = [("faturada", "Faturada")]

        # Preenche valores iniciais de campos de data para garantir visibilidade
        if self.instance.data_emissao_trd:
            self.fields["data_emissao_trd"].initial = (
                self.instance.data_emissao_trd.strftime("%Y-%m-%d")
            )
        if self.instance.data_faturamento:
            self.fields["data_faturamento"].initial = (
                self.instance.data_faturamento.strftime("%Y-%m-%d")
            )

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        item_contrato = cleaned_data.get("item_contrato")
        quantidade = cleaned_data.get("quantidade")

        # Validação de saldo do item
        if item_contrato:
            saldo = item_contrato.saldo_quantidade
            if quantidade and quantidade > saldo:
                self.add_error(
                    "quantidade",
                    f"Quantidade não pode exceder o saldo do item ({saldo})",
                )

        # Preenchimento automático de campos de data conforme o status
        if status == "finalizada" and not cleaned_data.get("data_emissao_trd"):
            cleaned_data["data_emissao_trd"] = timezone.now().date()

        if status == "faturada" and not cleaned_data.get("data_faturamento"):
            cleaned_data["data_faturamento"] = timezone.now().date()

        return cleaned_data
