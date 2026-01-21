from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.forms import AdminPasswordChangeForm
from .models import (
    Cliente,
    Contrato,
    ItemContrato,
    ItemFornecedor,
    OrdemFornecimento,
    OrdemServico,
    FeedbackSprintOS,
    ContatoCliente,
    Projeto,
    StakeholderContrato,
)
from dateutil.relativedelta import relativedelta
from .utils import map_tipo_item_contrato_para_fornecedor
from .constants import FORNECEDORES_MAP, TIPOS_OF_ITEM_CONTRATO
from django.utils import timezone
from django.forms import DateInput


# Widget para upload múltiplo de arquivos
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs['multiple'] = True

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        value = files.get(name)
        if isinstance(value, list):
            return value
        if value:
            return [value]
        return []


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput)
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not self.required and not data:
            return []
        if isinstance(data, list):
            result = []
            for item in data:
                result.append(super().clean(item, initial))
            return result
        return [super().clean(data, initial)]


# Contato Cliente Form
class ContatoClienteForm(forms.ModelForm):
    class Meta:
        model = ContatoCliente
        fields = ["nome", "email", "telefone", "funcao", "principal", "ativo"]
        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
                    "placeholder": "Nome do contato"
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
                    "placeholder": "email@exemplo.com"
                }
            ),
            "telefone": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
                    "placeholder": "(00) 00000-0000"
                }
            ),
            "funcao": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
                    "placeholder": "Cargo/Função"
                }
            ),
            "principal": forms.CheckboxInput(
                attrs={
                    "class": "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                }
            ),
            "ativo": forms.CheckboxInput(
                attrs={
                    "class": "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tornar campos obrigatórios apenas se algum campo estiver preenchido
        # Isso será validado no clean()
        self.fields["nome"].required = False
        self.fields["email"].required = False
        self.fields["telefone"].required = False
        self.fields["funcao"].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        nome = cleaned_data.get("nome")
        email = cleaned_data.get("email")
        telefone = cleaned_data.get("telefone")
        funcao = cleaned_data.get("funcao")
        
        # Se algum campo estiver preenchido, todos devem estar preenchidos
        campos_preenchidos = [nome, email, telefone, funcao]
        tem_preenchido = any(campos_preenchidos)
        
        if tem_preenchido:
            if not nome:
                self.add_error("nome", "Este campo é obrigatório quando outros campos estão preenchidos.")
            if not email:
                self.add_error("email", "Este campo é obrigatório quando outros campos estão preenchidos.")
            if not telefone:
                self.add_error("telefone", "Este campo é obrigatório quando outros campos estão preenchidos.")
            if not funcao:
                self.add_error("funcao", "Este campo é obrigatório quando outros campos estão preenchidos.")
        
        return cleaned_data


# Formset para Contatos
ContatoClienteFormSet = inlineformset_factory(
    Cliente,
    ContatoCliente,
    form=ContatoClienteForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


# Cliente Form
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        # Excluir campos antigos de contato, pois agora usamos ContatoCliente
        exclude = ["nome_responsavel", "cargo_responsavel", "telefone_contato", "email_contato"]
        widgets = {
            "nome_razao_social": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                }
            ),
            "nome_fantasia": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                }
            ),
            "cnpj_cpf": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                }
            ),
            "endereco": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                }
            ),
            "ativo": forms.CheckboxInput(
                attrs={
                    "class": "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicar CSS padrão em todos os campos
        for field_name, field in self.fields.items():
            if field_name not in ["ativo"] and not isinstance(field.widget, forms.CheckboxInput):
                if "class" not in field.widget.attrs:
                    field.widget.attrs.update(
                        {
                            "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                        }
                    )


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
        exclude = ["situacao", "valor_inicial"]  # Excluir situacao e valor_inicial pois são calculados automaticamente
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
        exclude = ["numero_of"]  # Excluir numero_of pois será gerado automaticamente
        widgets = {
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
        
        # Inicializar contrato e item_contrato com querysets vazios (serão preenchidos via JavaScript)
        # Mas se houver dados POST ou instância existente, preencher os querysets
        if self.data and 'cliente' in self.data:
            # Se há dados POST, usar o cliente do POST para filtrar contratos
            cliente_id = self.data.get('cliente')
            if cliente_id:
                self.fields["contrato"].queryset = Contrato.objects.filter(
                    cliente_id=cliente_id
                )
            if 'contrato' in self.data:
                contrato_id = self.data.get('contrato')
                if contrato_id:
                    self.fields["item_contrato"].queryset = ItemContrato.objects.filter(
                        contrato_id=contrato_id,
                        tipo__in=TIPOS_OF_ITEM_CONTRATO
                    )
        elif self.instance.pk:
            # Se estiver editando, permitir o contrato e item_contrato atuais
            if self.instance.contrato:
                self.fields["contrato"].queryset = Contrato.objects.filter(
                    cliente=self.instance.cliente
                )
            if self.instance.item_contrato:
                self.fields["item_contrato"].queryset = ItemContrato.objects.filter(
                    contrato=self.instance.contrato,
                    tipo__in=TIPOS_OF_ITEM_CONTRATO
                )
        else:
            # Nova OF - querysets vazios
            self.fields["contrato"].queryset = Contrato.objects.none()
            self.fields["item_contrato"].queryset = ItemContrato.objects.none()

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

        # Filtrar contratos baseado no cliente selecionado
        from .constants import TIPOS_OS_ITEM_CONTRATO
        
        # Se há dados POST (formulário sendo re-renderizado após erro)
        if self.data and 'cliente' in self.data:
            cliente_id = self.data.get('cliente')
            if cliente_id:
                self.fields["contrato"].queryset = Contrato.objects.filter(
                    cliente_id=cliente_id
                )
            else:
                self.fields["contrato"].queryset = Contrato.objects.none()
            
            # Filtrar itens do contrato baseado no contrato selecionado
            if 'contrato' in self.data:
                contrato_id = self.data.get('contrato')
                if contrato_id:
                    self.fields["item_contrato"].queryset = ItemContrato.objects.filter(
                        contrato_id=contrato_id,
                        tipo__in=TIPOS_OS_ITEM_CONTRATO
                    )
                else:
                    self.fields["item_contrato"].queryset = ItemContrato.objects.filter(
                        tipo__in=TIPOS_OS_ITEM_CONTRATO
                    )
            else:
                self.fields["item_contrato"].queryset = ItemContrato.objects.filter(
                    tipo__in=TIPOS_OS_ITEM_CONTRATO
                )
        # Se estiver editando uma instância existente
        elif self.instance.pk:
            if self.instance.cliente:
                self.fields["contrato"].queryset = Contrato.objects.filter(
                    cliente=self.instance.cliente
                )
            else:
                self.fields["contrato"].queryset = Contrato.objects.none()
            
            if self.instance.contrato:
                self.fields["item_contrato"].queryset = ItemContrato.objects.filter(
                    contrato=self.instance.contrato,
                    tipo__in=TIPOS_OS_ITEM_CONTRATO
                )
            else:
                self.fields["item_contrato"].queryset = ItemContrato.objects.filter(
                    tipo__in=TIPOS_OS_ITEM_CONTRATO
                )
        # Se há valores iniciais (ex: quando vem de um projeto)
        elif self.initial:
            if 'cliente' in self.initial:
                cliente_id = self.initial.get('cliente')
                if cliente_id:
                    self.fields["contrato"].queryset = Contrato.objects.filter(
                        cliente_id=cliente_id
                    )
                else:
                    self.fields["contrato"].queryset = Contrato.objects.none()
            
            if 'contrato' in self.initial:
                contrato_id = self.initial.get('contrato')
                if contrato_id:
                    self.fields["item_contrato"].queryset = ItemContrato.objects.filter(
                        contrato_id=contrato_id,
                        tipo__in=TIPOS_OS_ITEM_CONTRATO
                    )
                else:
                    self.fields["item_contrato"].queryset = ItemContrato.objects.filter(
                        tipo__in=TIPOS_OS_ITEM_CONTRATO
                    )
            else:
                # Se não há contrato inicial, ainda filtrar por tipo
                self.fields["item_contrato"].queryset = ItemContrato.objects.filter(
                    tipo__in=TIPOS_OS_ITEM_CONTRATO
                )
        else:
            # Nova OS - querysets vazios ou apenas filtrados por tipo
            self.fields["contrato"].queryset = Contrato.objects.none()
            self.fields["item_contrato"].queryset = ItemContrato.objects.filter(
                tipo__in=TIPOS_OS_ITEM_CONTRATO
            )

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
            saldo = item_contrato.saldo_quantidade_atual or 0
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


class CriarTicketContatoForm(forms.ModelForm):
    """Formulário para criar ticket de contato manualmente"""
    
    class Meta:
        model = FeedbackSprintOS
        fields = [
            'cliente',
            'contrato',
            'projeto',
            'sprint',
            'ordem_servico',
            'motivador_contato',
            'gerente_sucessos',
        ]
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
            'contrato': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
            'projeto': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
            'sprint': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
            'ordem_servico': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
            'motivador_contato': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
            'gerente_sucessos': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from contracts.models import Colaborador, Contrato, Projeto, Sprint, OrdemServico, Cliente
        from django.db.models import Q
        
        self.fields['gerente_sucessos'].queryset = Colaborador.objects.filter(
            Q(cargo__icontains='sucesso') | Q(cargo__icontains='customer')
        ).order_by('nome_completo')
        
        # Limitar opções de motivador_contato para tickets manuais
        # Apenas "Contato Proativo" e "Contato Reativo"
        # A opção "Obter Feedback do Serviço Prestado (Automático)" só é usada em tickets automáticos
        self.fields['motivador_contato'].choices = [
            ('voluntario_cs', 'Contato Proativo'),
            ('solicitacao_comercial', 'Contato Reativo'),
        ]
        
        # Se houver initial com cliente, carregar contratos desse cliente
        if self.initial and 'cliente' in self.initial:
            cliente = self.initial['cliente']
            if isinstance(cliente, Cliente):
                self.fields['contrato'].queryset = Contrato.objects.filter(cliente=cliente)
                self.fields['cliente'].initial = cliente
        
        # Se houver dados POST (formulário sendo re-renderizado após erro), 
        # carregar os querysets com os valores selecionados
        if self.data:
            # Contrato: se houver cliente selecionado, carregar contratos desse cliente
            cliente_id = self.data.get('cliente')
            if cliente_id:
                self.fields['contrato'].queryset = Contrato.objects.filter(cliente_id=cliente_id)
            else:
                self.fields['contrato'].queryset = Contrato.objects.none()
            
            # Projeto: se houver contrato selecionado, carregar projetos desse contrato
            contrato_id = self.data.get('contrato')
            if contrato_id:
                self.fields['projeto'].queryset = Projeto.objects.filter(contrato_id=contrato_id)
            else:
                self.fields['projeto'].queryset = Projeto.objects.none()
            
            # Sprint: se houver projeto selecionado, carregar sprints desse projeto
            projeto_id = self.data.get('projeto')
            if projeto_id:
                self.fields['sprint'].queryset = Sprint.objects.filter(projeto_id=projeto_id)
            else:
                self.fields['sprint'].queryset = Sprint.objects.none()
            
            # Ordem de Serviço: se houver contrato selecionado, carregar OS desse contrato
            if contrato_id:
                os_queryset = OrdemServico.objects.filter(contrato_id=contrato_id)
                # Se também houver projeto, filtrar por projeto
                if projeto_id:
                    os_queryset = os_queryset.filter(sprint__projeto_id=projeto_id)
                self.fields['ordem_servico'].queryset = os_queryset
            else:
                self.fields['ordem_servico'].queryset = OrdemServico.objects.none()
        else:
            # Inicializar campos dependentes vazios para serem preenchidos dinamicamente via JavaScript
            # Os métodos clean_* irão validar os valores dinamicamente adicionados
            # Contrato: inicialmente vazio, será preenchido quando cliente for selecionado
            self.fields['contrato'].queryset = Contrato.objects.none()
            
            # Projeto: inicialmente vazio, será preenchido quando contrato for selecionado
            self.fields['projeto'].queryset = Projeto.objects.none()
            
            # Sprint: inicialmente vazia, será preenchida quando projeto for selecionado
            self.fields['sprint'].queryset = Sprint.objects.none()
            
            # Ordem de Serviço: inicialmente vazia, será preenchida quando contrato/projeto for selecionado
            self.fields['ordem_servico'].queryset = OrdemServico.objects.none()
        
        # Tornar campos opcionais
        self.fields['sprint'].required = False
        self.fields['ordem_servico'].required = False
        self.fields['projeto'].required = False
    
    def clean_contrato(self):
        """Validação customizada para aceitar contratos adicionados dinamicamente"""
        contrato = self.cleaned_data.get('contrato')
        if contrato:
            # Se já for um objeto Contrato, retornar diretamente
            if isinstance(contrato, Contrato):
                return contrato
            # Se for um ID, buscar o objeto
            try:
                contrato = Contrato.objects.get(pk=contrato)
                return contrato
            except (Contrato.DoesNotExist, ValueError, TypeError):
                raise forms.ValidationError("Contrato inválido.")
        if self.fields['contrato'].required and not contrato:
            raise forms.ValidationError("Este campo é obrigatório.")
        return contrato
    
    def clean_projeto(self):
        """Validação customizada para aceitar projetos adicionados dinamicamente"""
        projeto = self.cleaned_data.get('projeto')
        if projeto:
            # Se já for um objeto Projeto, retornar diretamente
            if isinstance(projeto, Projeto):
                return projeto
            # Se for um ID, buscar o objeto
            try:
                projeto = Projeto.objects.get(pk=projeto)
                return projeto
            except (Projeto.DoesNotExist, ValueError, TypeError):
                raise forms.ValidationError("Projeto inválido.")
        return projeto
    
    def clean_sprint(self):
        """Validação customizada para aceitar sprints adicionadas dinamicamente"""
        sprint = self.cleaned_data.get('sprint')
        if sprint:
            # Se já for um objeto Sprint, retornar diretamente
            if isinstance(sprint, Sprint):
                return sprint
            # Se for um ID, buscar o objeto
            try:
                sprint = Sprint.objects.get(pk=sprint)
                return sprint
            except (Sprint.DoesNotExist, ValueError, TypeError):
                raise forms.ValidationError("Sprint inválida.")
        return sprint
    
    def clean_ordem_servico(self):
        """Validação customizada para aceitar OS adicionadas dinamicamente"""
        os = self.cleaned_data.get('ordem_servico')
        if os:
            # Se já for um objeto OrdemServico, retornar diretamente
            if isinstance(os, OrdemServico):
                return os
            # Se for um ID, buscar o objeto
            try:
                os = OrdemServico.objects.get(pk=os)
                return os
            except (OrdemServico.DoesNotExist, ValueError, TypeError):
                raise forms.ValidationError("Ordem de Serviço inválida.")
        return os


# ==================== FORMULÁRIOS ADICIONAIS ====================

from .models import (
    Colaborador,
    SLA,
    CentroCusto,
    Projeto,
    Backlog,
    Sprint,
    Tarefa,
    LancamentoHora,
    AnaliseContrato,
    DocumentoContrato,
    PlanoTrabalho,
    SLAImportante,
    QuadroPenalizacao,
    MatrizRACI,
    ClausulaCritica,
    TermoAditivo,
)


class ColaboradorForm(forms.ModelForm):
    grupos = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Grupos",
        help_text="Selecione os grupos aos quais este colaborador pertence"
    )
    
    criar_usuario = forms.BooleanField(
        required=False,
        initial=True,
        label="Criar usuário automaticamente",
        help_text="Se marcado, um usuário será criado automaticamente com base no email do colaborador",
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
            }
        )
    )
    
    username = forms.CharField(
        required=False,
        label="Nome de usuário",
        help_text="Deixe em branco para usar o email como nome de usuário",
        widget=forms.TextInput(
            attrs={
                "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
            }
        )
    )
    
    password = forms.CharField(
        required=False,
        label="Senha",
        help_text="Deixe em branco para gerar uma senha aleatória (será enviada por email)",
        widget=forms.PasswordInput(
            attrs={
                "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
            }
        )
    )
    
    class Meta:
        model = Colaborador
        fields = ["nome_completo", "email", "telefone", "cargo", "ativo", "user"]
        widgets = {
            "nome_completo": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                }
            ),
            "telefone": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                }
            ),
            "cargo": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                }
            ),
            "ativo": forms.CheckboxInput(
                attrs={
                    "class": "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                }
            ),
            "user": forms.Select(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar usuários que não têm colaborador associado ou que são o próprio colaborador sendo editado
        from django.contrib.auth.models import User
        usuarios_disponiveis = User.objects.filter(
            colaborador__isnull=True
        ) | User.objects.filter(
            colaborador=self.instance if self.instance.pk else None
        )
        self.fields['user'].queryset = usuarios_disponiveis
        
        # Se estiver editando e já tem usuário, não mostrar opção de criar
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['grupos'].initial = self.instance.user.groups.all()
            self.fields['criar_usuario'].initial = False
            self.fields['criar_usuario'].widget.attrs['disabled'] = True
            self.fields['username'].widget.attrs['readonly'] = True
            self.fields['password'].widget.attrs['readonly'] = True
            self.fields['user'].widget.attrs['readonly'] = True
        else:
            # Se for novo colaborador, campo user não é obrigatório
            self.fields['user'].required = False
            self.fields['user'].help_text = "Selecione um usuário existente ou deixe em branco para criar um novo"
    
    def clean(self):
        cleaned_data = super().clean()
        criar_usuario = cleaned_data.get('criar_usuario', False)
        email = cleaned_data.get('email')
        username = cleaned_data.get('username')
        user = cleaned_data.get('user')
        
        # Se não está editando e não tem usuário selecionado
        if not self.instance.pk and not user:
            if criar_usuario and email:
                # Verificar se já existe usuário com este email
                from django.contrib.auth.models import User
                usuario_existente = User.objects.filter(email=email).first()
                
                if usuario_existente:
                    # Se o usuário já existe mas não tem colaborador, vincular automaticamente
                    if not hasattr(usuario_existente, 'colaborador') or usuario_existente.colaborador is None:
                        # Vincular ao usuário existente automaticamente
                        cleaned_data['user'] = usuario_existente
                        cleaned_data['criar_usuario'] = False
                        # Não mostrar erro, apenas vincular
                    else:
                        # Usuário já tem colaborador associado
                        raise forms.ValidationError({
                            'email': f'Já existe um colaborador associado a este email. Usuário: {usuario_existente.username}'
                        })
                
                # Se username não foi fornecido, usar email
                if not username:
                    cleaned_data['username'] = email
            elif not criar_usuario:
                # Se não vai criar usuário, deve selecionar um existente
                if not user:
                    # Verificar se existe usuário com o email fornecido
                    if email:
                        from django.contrib.auth.models import User
                        usuario_existente = User.objects.filter(email=email).first()
                        if usuario_existente and (not hasattr(usuario_existente, 'colaborador') or usuario_existente.colaborador is None):
                            # Vincular automaticamente
                            cleaned_data['user'] = usuario_existente
                        else:
                            raise forms.ValidationError({
                                'user': 'Selecione um usuário existente ou marque a opção "Criar usuário automaticamente".'
                            })
                    else:
                        raise forms.ValidationError({
                            'user': 'Selecione um usuário existente ou marque a opção "Criar usuário automaticamente".'
                        })
        
        return cleaned_data
    
    def save(self, commit=True):
        from django.contrib.auth.models import User
        import secrets
        import string
        
        colaborador = super().save(commit=False)
        criar_usuario = self.cleaned_data.get('criar_usuario', False)
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        grupos = self.cleaned_data.get('grupos', [])
        user = self.cleaned_data.get('user')
        
        # Se já tem usuário selecionado (vinculando a existente), usar ele
        # Verificar se o relacionamento user existe usando getattr para evitar exceção
        has_user = getattr(colaborador, 'user', None) is not None
        if user and not has_user:
            colaborador.user = user
            # Atualizar email do colaborador se necessário
            if email and not colaborador.email:
                colaborador.email = email
        
        # Criar usuário se necessário
        elif not has_user and criar_usuario and email:
            if not username:
                username = email
            
            # Verificar se usuário já existe
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': colaborador.nome_completo.split()[0] if colaborador.nome_completo else '',
                    'last_name': ' '.join(colaborador.nome_completo.split()[1:]) if len(colaborador.nome_completo.split()) > 1 else '',
                }
            )
            
            # Se foi criado, definir senha
            if created:
                if password:
                    user.set_password(password)
                else:
                    # Gerar senha aleatória
                    alphabet = string.ascii_letters + string.digits
                    password = ''.join(secrets.choice(alphabet) for i in range(12))
                    user.set_password(password)
                user.save()
            
            colaborador.user = user
        
        if commit:
            colaborador.save()
            # Verificar se o relacionamento user existe antes de acessar
            if hasattr(colaborador, 'user') and colaborador.user:
                colaborador.user.groups.set(grupos)
        
        return colaborador


class GrupoForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all().select_related('content_type'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Permissões",
        help_text="Selecione as permissões para este grupo"
    )
    
    class Meta:
        model = Group
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['permissions'].initial = self.instance.permissions.all()
        
        # Organizar permissões por app e modelo
        permissions = Permission.objects.all().select_related('content_type').order_by('content_type__app_label', 'content_type__model', 'codename')
        self.fields['permissions'].queryset = permissions
    
    def save(self, commit=True):
        grupo = super().save(commit=commit)
        if commit:
            grupo.permissions.set(self.cleaned_data['permissions'])
        return grupo


class ColaboradorPasswordChangeForm(forms.Form):
    """Formulário para alteração de senha do colaborador (similar ao AdminPasswordChangeForm)"""
    password1 = forms.CharField(
        label="Nova senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white",
                "autocomplete": "new-password"
            }
        ),
        help_text="A senha deve conter pelo menos 8 caracteres."
    )
    password2 = forms.CharField(
        label="Confirmação da nova senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white",
                "autocomplete": "new-password"
            }
        ),
        help_text="Digite a mesma senha novamente para verificação."
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("As duas senhas não coincidem.")
        return password2
    
    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1 and len(password1) < 8:
            raise forms.ValidationError("A senha deve conter pelo menos 8 caracteres.")
        return password1
    
    def save(self, commit=True):
        """Altera a senha do usuário"""
        password = self.cleaned_data["password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


class SLAForm(forms.ModelForm):
    class Meta:
        model = SLA
        fields = "__all__"
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'meta': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'tipo': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'valor_penalidade': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500', 'step': '0.01'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500 pr-10'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500 pr-10'}),
            'descricao': forms.Textarea(attrs={'rows': 4, 'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'observacoes': forms.Textarea(attrs={'rows': 4, 'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600'}),
        }


class CentroCustoForm(forms.ModelForm):
    class Meta:
        model = CentroCusto
        fields = "__all__"


class ProjetoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        fields = ["nome", "descricao", "gerente_projeto", "status", "item_contrato"]
        exclude = ["contrato", "backlog_origem", "data_inicio", "data_fim_prevista", "criado_em", "atualizado_em"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar item_contrato apenas para Serviço ou Treinamento
        from .constants import TIPOS_OS_ITEM_CONTRATO
        if 'item_contrato' in self.fields:
            self.fields['item_contrato'].queryset = ItemContrato.objects.filter(
                tipo__in=TIPOS_OS_ITEM_CONTRATO
            )
            # Se estiver editando e tiver contrato, filtrar por contrato
            if self.instance and self.instance.pk and self.instance.contrato:
                self.fields['item_contrato'].queryset = self.fields['item_contrato'].queryset.filter(
                    contrato=self.instance.contrato
                )


class BacklogForm(forms.ModelForm):
    class Meta:
        model = Backlog
        fields = "__all__"


class SprintForm(forms.ModelForm):
    class Meta:
        model = Sprint
        fields = "__all__"


class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = "__all__"
    
    def __init__(self, *args, **kwargs):
        # Extrair projeto_id se fornecido (não é um argumento padrão do ModelForm)
        projeto_id = kwargs.pop('projeto_id', None)
        super().__init__(*args, **kwargs)
        
        # Se projeto_id foi fornecido, filtrar sprints por projeto
        if projeto_id:
            from .models import Projeto, Sprint
            try:
                projeto = Projeto.objects.get(pk=projeto_id)
                if 'sprint' in self.fields:
                    self.fields['sprint'].queryset = Sprint.objects.filter(projeto=projeto)
                if 'projeto' in self.fields:
                    self.fields['projeto'].initial = projeto
            except Projeto.DoesNotExist:
                pass


class StakeholderContratoForm(forms.ModelForm):
    PAPEIS_CONTRATADA = [
        ("PREPOSTO", "Preposto"),
        ("PREPOSTO_SUBSTITUTO", "Preposto Substituto"),
        ("CS", "CS (Customer Success)"),
        ("GERENTE_CONTRATO", "Gerente do Contrato"),
        ("GERENTE_PROJETO", "Gerente do Projeto"),
        ("GERENTE_SUBSTITUTO", "Gerente Substituto"),
        ("GERENTE_COMERCIAL", "Gerente Comercial"),
    ]
    
    PAPEIS_CONTRATANTE = [
        ("GESTOR_CONTRATO", "Gestor do Contrato"),
        ("FISCAL_ADMINISTRATIVO", "Fiscal Administrativo"),
        ("FISCAL_TECNICO", "Fiscal Técnico"),
    ]
    
    class Meta:
        model = StakeholderContrato
        fields = ["tipo", "papel", "colaborador", "contato_cliente", "nome", "email", "telefone", "observacoes", "ativo"]
        widgets = {
            'tipo': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'papel': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'colaborador': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'contato_cliente': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'nome': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'email': forms.EmailInput(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'telefone': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.contrato = kwargs.pop('contrato', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar colaboradores ativos
        from .models import Colaborador
        self.fields['colaborador'].queryset = Colaborador.objects.filter(ativo=True).order_by("nome_completo")
        
        # Filtrar contatos do cliente do contrato
        if self.contrato and self.contrato.cliente:
            self.fields['contato_cliente'].queryset = ContatoCliente.objects.filter(
                cliente=self.contrato.cliente
            ).order_by("nome")
        else:
            self.fields['contato_cliente'].queryset = ContatoCliente.objects.none()
        
        # Ajustar opções de papel baseado no tipo
        if self.instance and self.instance.pk:
            tipo_atual = self.instance.tipo
        elif self.data and 'tipo' in self.data:
            tipo_atual = self.data.get('tipo')
        else:
            tipo_atual = self.initial.get('tipo', None)
        
        if tipo_atual == StakeholderContrato.TipoStakeholder.CONTRATADA:
            self.fields['papel'].widget = forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'})
            self.fields['papel'].choices = [('', '---------')] + self.PAPEIS_CONTRATADA
            self.fields['colaborador'].required = True
            self.fields['contato_cliente'].required = False
            self.fields['contato_cliente'].widget = forms.HiddenInput()
            self.fields['nome'].required = False
            self.fields['nome'].widget = forms.HiddenInput()
            self.fields['email'].required = False
            self.fields['email'].widget = forms.HiddenInput()
            self.fields['telefone'].required = False
            self.fields['telefone'].widget = forms.HiddenInput()
        elif tipo_atual == StakeholderContrato.TipoStakeholder.CONTRATANTE:
            self.fields['papel'].widget = forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'})
            self.fields['papel'].choices = [('', '---------')] + self.PAPEIS_CONTRATANTE
            self.fields['contato_cliente'].required = True
            self.fields['colaborador'].required = False
            self.fields['colaborador'].widget = forms.HiddenInput()
            self.fields['nome'].required = False
            self.fields['nome'].widget = forms.HiddenInput()
            self.fields['email'].required = False
            self.fields['email'].widget = forms.HiddenInput()
            self.fields['telefone'].required = False
            self.fields['telefone'].widget = forms.HiddenInput()
        elif tipo_atual == StakeholderContrato.TipoStakeholder.EQUIPE_TECNICA:
            # Para Equipe Técnica, papel é texto livre
            self.fields['papel'].widget = forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'})
            self.fields['papel'].required = True
            self.fields['nome'].required = True
            self.fields['email'].required = True
            self.fields['telefone'].required = False
            self.fields['colaborador'].required = False
            self.fields['colaborador'].widget = forms.HiddenInput()
            self.fields['contato_cliente'].required = False
            self.fields['contato_cliente'].widget = forms.HiddenInput()
        else:
            # Estado inicial - todos os campos visíveis mas não obrigatórios
            self.fields['papel'].widget = forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'})
            self.fields['papel'].choices = [('', '---------')] + self.PAPEIS_CONTRATADA + self.PAPEIS_CONTRATANTE
            self.fields['colaborador'].required = False
            self.fields['contato_cliente'].required = False
            self.fields['nome'].required = False
            self.fields['email'].required = False
            self.fields['telefone'].required = False
        
        # JavaScript será usado para atualizar dinamicamente
        self.fields['tipo'].widget.attrs.update({
            'onchange': 'updateStakeholderFields(this.value);'
        })
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        colaborador = cleaned_data.get('colaborador')
        contato_cliente = cleaned_data.get('contato_cliente')
        nome = cleaned_data.get('nome')
        email = cleaned_data.get('email')
        
        if tipo == StakeholderContrato.TipoStakeholder.CONTRATADA:
            if not colaborador:
                raise forms.ValidationError("Colaborador é obrigatório para stakeholders da Contratada.")
        elif tipo == StakeholderContrato.TipoStakeholder.CONTRATANTE:
            if not contato_cliente:
                raise forms.ValidationError("Contato do cliente é obrigatório para stakeholders da Contratante.")
        elif tipo == StakeholderContrato.TipoStakeholder.EQUIPE_TECNICA:
            if not nome:
                raise forms.ValidationError("Nome é obrigatório para membros da Equipe Técnica.")
            if not email:
                raise forms.ValidationError("E-mail é obrigatório para membros da Equipe Técnica.")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.contrato:
            instance.contrato = self.contrato
        if commit:
            instance.save()
        return instance




class LancamentoHoraForm(forms.ModelForm):
    class Meta:
        model = LancamentoHora
        fields = "__all__"
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'hora_fim': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'}),
        }


class ContratoPublicoForm(forms.ModelForm):
    fornecedores = forms.MultipleChoiceField(
        choices=FORNECEDORES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Fornecedores",
    )
    outro_fornecedor_nome = forms.CharField(
        required=False,
        label="Outros Fornecedores",
        help_text="Digite fornecedores adicionais separados por vírgula (ex: Fornecedor A, Fornecedor B)",
        widget=forms.TextInput(
            attrs={
                "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
                "placeholder": "Ex: Fornecedor A, Fornecedor B, Fornecedor C"
            }
        )
    )

    class Meta:
        model = Contrato
        fields = "__all__"
        exclude = ["situacao", "valor_inicial"]  # Excluir situacao e valor_inicial pois são calculados automaticamente
        widgets = {
            "data_assinatura": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Buscar fornecedores cadastrados no ItemFornecedor
        fornecedores_db = ItemFornecedor.objects.values_list(
            "fornecedor", flat=True
        ).distinct()

        # Unificar lista padrão + fornecedores do banco (normalizando para UPPER)
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
            fornecedores_existentes = [f.upper() for f in self.instance.fornecedores]
            
            # Separar fornecedores que estão nas choices dos que são customizados
            fornecedores_customizados = []
            fornecedores_em_choices = []
            choices_dict = dict(fornecedores_ordenados)
            
            for f in fornecedores_existentes:
                if f in choices_dict:
                    fornecedores_em_choices.append(f)
                else:
                    fornecedores_customizados.append(f)
            
            # Preencher checkboxes apenas com fornecedores que estão nas choices
            self.initial["fornecedores"] = fornecedores_em_choices
            
            # Preencher campo de texto com fornecedores customizados
            if fornecedores_customizados:
                self.initial["outro_fornecedor_nome"] = ", ".join(fornecedores_customizados)

        # Aplicar CSS em todos os campos (exceto DateInput e Checkbox)
        for field_name, field in self.fields.items():
            if field_name not in ["fornecedores", "outro_fornecedor_nome"] and not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update(
                    {
                        "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                    }
                )

            # Corrige preenchimento dos campos date no modo edição
            if isinstance(field.widget, forms.DateInput):
                field.widget.format = "%Y-%m-%d"
                if self.instance and getattr(self.instance, field_name, None):
                    field.initial = getattr(self.instance, field_name)
        
        # Configurar widgets específicos para campos de origem
        if 'origem_contrato' in self.fields:
            self.fields['origem_contrato'].widget.attrs.update({
                "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
            })
        
        if 'origem_contrato_detalhe' in self.fields:
            self.fields['origem_contrato_detalhe'].widget.attrs.update({
                "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
                "placeholder": "Ex: Nº do edital, dispositivo legal, etc."
            })
        
        # Configurar widgets para novos campos
        novos_campos = {
            'modalidade_licitacao': {
                'placeholder': 'Ex: Pregão Eletrônico, Tomada de Preços, Concorrência'
            },
            'numero_edital': {
                'placeholder': 'Ex: 001/2025'
            },
            'orgao_gerenciador_arp': {
                'placeholder': 'Ex: Ministério da Economia'
            },
            'numero_rfp_rfq': {
                'placeholder': 'Ex: RFP-2025-001'
            }
        }
        
        for campo, attrs in novos_campos.items():
            if campo in self.fields:
                self.fields[campo].widget.attrs.update({
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
                    **attrs
                })

    def clean(self):
        cleaned_data = super().clean()
        
        # Normalizar fornecedores dos checkboxes para UPPER
        fornecedores = cleaned_data.get("fornecedores", [])
        fornecedores_normalizados = [f.strip().upper() for f in fornecedores] if fornecedores else []
        
        # Processar fornecedores customizados do campo de texto
        outro_fornecedor_nome = cleaned_data.get("outro_fornecedor_nome", "")
        if outro_fornecedor_nome:
            # Separar por vírgula e normalizar
            fornecedores_customizados = [
                f.strip().upper() 
                for f in outro_fornecedor_nome.split(",") 
                if f.strip()
            ]
            # Adicionar aos fornecedores (evitando duplicatas)
            for f in fornecedores_customizados:
                if f and f not in fornecedores_normalizados:
                    fornecedores_normalizados.append(f)
        
        cleaned_data["fornecedores"] = fornecedores_normalizados

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.fornecedores = self.cleaned_data.get("fornecedores", [])
        if commit:
            instance.save()
        return instance


class TermoAditivoForm(forms.ModelForm):
    class Meta:
        model = TermoAditivo
        fields = "__all__"


class AnaliseContratoForm(forms.Form):
    """Formulário para upload múltiplo de documentos para análise por IA"""
    
    nome_analise = forms.CharField(
        max_length=255,
        required=True,
        label="Nome da Análise",
        help_text="Ex: Análise Contrato 009/2025 - CNPQ",
        error_messages={
            'required': 'O nome da análise é obrigatório.',
            'max_length': 'O nome da análise não pode ter mais de 255 caracteres.',
        },
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Nome da análise'
        })
    )
    
    numero_contrato_busca = forms.CharField(
        max_length=100,
        required=False,
        label="Número do Contrato (opcional)",
        help_text="Deixe em branco para criar novo contrato. Preencha para vincular a um contrato existente.",
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Ex: 009/2025'
        })
    )
    
    arquivos = forms.FileField(
        required=False,
        label="Arquivos",
        help_text="Selecione um ou mais arquivos (PDF ou Word). Máximo 50MB por arquivo.",
        widget=MultipleFileInput(attrs={
            'class': 'block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 dark:file:bg-blue-900 dark:file:text-blue-300',
            'accept': '.pdf,.doc,.docx',
        })
    )
    
    def clean_nome_analise(self):
        """Validação customizada para o nome da análise"""
        nome_analise = self.cleaned_data.get('nome_analise')
        if not nome_analise or not nome_analise.strip():
            raise forms.ValidationError('O nome da análise é obrigatório.')
        return nome_analise.strip()


class JSONFormattedField(forms.CharField):
    """Campo customizado para exibir JSON formatado"""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', forms.Textarea(attrs={'rows': 15, 'spellcheck': 'false'}))
        super().__init__(*args, **kwargs)
    
    def prepare_value(self, value):
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                import json
                value = json.loads(value)
            except (ValueError, TypeError):
                pass
        if isinstance(value, (dict, list)):
            import json
            return json.dumps(value, indent=4, ensure_ascii=False, sort_keys=False)
        return value


class PlanoTrabalhoForm(forms.ModelForm):
    """Formulário para edição do Plano de Trabalho"""
    
    class Meta:
        model = PlanoTrabalho
        fields = [
            'resumo_contrato',
            'data_inicio_prevista',
            'data_fim_prevista',
            'template_status_report',
            'frequencia_status_report',
        ]
        widgets = {
            'resumo_contrato': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500',
                'rows': 6
            }),
            'data_inicio_prevista': forms.DateInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
            'data_fim_prevista': forms.DateInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
            'template_status_report': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500',
                'rows': 8
            }),
            'frequencia_status_report': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ex: semanal, quinzenal, mensal, diária'
            }),
        }


class FeedbackSprintOSForm(forms.ModelForm):
    """Formulário para registro de ticket de contato e feedback do cliente"""
    
    class Meta:
        model = FeedbackSprintOS
        fields = [
            'motivador_contato',
            'status',
            'pergunta_nps',
            'pergunta_satisfacao_qualidade',
            'pergunta_satisfacao_prazos',
            'pergunta_satisfacao_comunicacao',
            'elogios_criticas',
            'data_contato',
            'data_resposta',
            'observacoes',
            'gerente_sucessos',
        ]
        widgets = {
            'motivador_contato': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
            'pergunta_nps': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
            'pergunta_satisfacao_qualidade': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
            'pergunta_satisfacao_prazos': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
            'pergunta_satisfacao_comunicacao': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
            'elogios_criticas': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Compartilhe elogios, críticas ou sugestões de melhoria'
            }),
            'data_contato': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
            'data_resposta': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Observações internas do gerente de Customer Success'
            }),
            'gerente_sucessos': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar gerentes de sucesso (colaboradores com cargo relacionado)
        from django.db.models import Q
        self.fields['gerente_sucessos'].queryset = Colaborador.objects.filter(
            Q(cargo__icontains='sucesso') | Q(cargo__icontains='customer')
        ).order_by('nome_completo')
        
        # Se for edição e já tiver gerente, incluir ele mesmo
        if self.instance and self.instance.pk and self.instance.gerente_sucessos:
            gerente_atual = self.instance.gerente_sucessos
            if gerente_atual not in self.fields['gerente_sucessos'].queryset:
                self.fields['gerente_sucessos'].queryset = Colaborador.objects.filter(
                    Q(cargo__icontains='sucesso') | Q(cargo__icontains='customer') | Q(id=gerente_atual.id)
                ).order_by('nome_completo')
