import os
import sys
import django

# Configuração do ambiente Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "controlcontratos.settings")
django.setup()

from contracts.models import Contrato, ItemFornecedor


def validar_fornecedores_e_tipos():
    erros = []
    contratos = Contrato.objects.all()

    for contrato in contratos:
        fornecedores = contrato.fornecedores

        itens_invalidos = ItemFornecedor.objects.exclude(fornecedor__in=fornecedores)
        if itens_invalidos.exists():
            erros.append(
                {
                    "contrato": contrato.numero_contrato,
                    "cliente": contrato.cliente.nome_fantasia,
                    "itens_invalidos": [str(item) for item in itens_invalidos],
                }
            )

    if erros:
        print("Itens de fornecedores não vinculados ao contrato encontrados:")
        for erro in erros:
            print(f"Contrato: {erro['contrato']} ({erro['cliente']})")
            for item in erro["itens_invalidos"]:
                print(f"  - {item}")
    else:
        print("Nenhum erro encontrado. Todos os fornecedores estão corretos.")


if __name__ == "__main__":
    validar_fornecedores_e_tipos()
