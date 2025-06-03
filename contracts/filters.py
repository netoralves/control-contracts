import django_filters
from .models import Cliente, Contrato, OrdemServico


class ClienteFilter(django_filters.FilterSet):
    class Meta:
        model = Cliente
        fields = ["nome_razao_social", "cnpj_cpf", "cidade", "estado"]


class ContratoFilter(django_filters.FilterSet):
    class Meta:
        model = Contrato
        fields = ["cliente", "vigencia"]


class OrdemServicoFilter(django_filters.FilterSet):
    class Meta:
        model = OrdemServico
        fields = ["cliente", "status", "contrato"]
