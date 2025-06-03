# contracts/constants.py

FORNECEDORES_MAP = {
    "IB SERVICES": "iB Services",
    "MVC SECURITY": "MVC Security",
    "RED HAT": "Red Hat",
    "CYBERARK": "CyberArk",
    "TREND MICRO": "Trend Micro",
    "FORTINET": "Fortinet",
    "RIDGE SECURITY": "Ridge Security",
    "THALES": "Thales",
    "VIEWTINET": "Viewtinet",
    "OUTRO FORNECEDOR": "Outro Fornecedor",
}

FORNECEDORES_LIST = list(FORNECEDORES_MAP.keys())

TIPOS_ITEM_CONTRATO_CHOICES = [
    ("hardware", "Hardware"),
    ("software", "Software"),
    ("solucao", "Solução"),
    ("servico", "Serviço"),
    ("treinamento", "Treinamento"),
]

TIPOS_SERVICO_TREINAMENTO_CONST = ["servico", "treinamento"] # Renomeando para indicar que é uma constante
TIPOS_PRODUTO_CONST = ["hardware", "software", "solucao"]   # Renomeando para indicar que é uma constante

VIGENCIA_PRODUTO_CHOICES_CONT = [
        (12, "12 meses"),
        (24, "24 meses"),
        (36, "36 meses"),
    ]