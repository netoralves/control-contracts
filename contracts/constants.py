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
}

FORNECEDORES_LIST = list(FORNECEDORES_MAP.keys())

# Novos tipos de item de contrato e item de fornecedor
TIPOS_ITEM_CONTRATO_CHOICES = [
    ("equipamento_hw", "Equipamento (somente HW)"),
    ("equipamento_sw_embarcado", "Equipamento com SW embarcado"),
    ("licenca_software", "Licença de Software"),
    ("subscricao_software", "Subscrição de Software"),
    ("solucao", "Solução"),
    ("servico", "Serviço"),
    ("treinamento", "Treinamento"),
]

# Tipos que podem ser usados em Ordem de Fornecimento (OF)
TIPOS_OF_ITEM_CONTRATO = [
    "equipamento_hw",
    "equipamento_sw_embarcado",
    "licenca_software",
    "subscricao_software",
    "solucao",
    "treinamento",
]

# Tipos que podem ser usados em Ordem de Serviço (OS)
TIPOS_OS_ITEM_CONTRATO = [
    "servico",
    "treinamento",
]

# Tipos de produto (para NF-e)
TIPOS_PRODUTO_NFE = [
    "equipamento_hw",
    "equipamento_sw_embarcado",
]

# Tipos de serviço (para NFS-e)
TIPOS_SERVICO_NFSE = [
    "licenca_software",
    "subscricao_software",
    "solucao",
    "treinamento",
]

# Tipos de serviço e treinamento (para compatibilidade)
TIPOS_SERVICO_TREINAMENTO_CONST = ["servico", "treinamento"]
# Tipos de produto (para compatibilidade - será atualizado gradualmente)
TIPOS_PRODUTO_CONST = ["equipamento_hw", "equipamento_sw_embarcado", "licenca_software", "subscricao_software", "solucao"]

# Tipos de item de fornecedor
TIPOS_ITEM_FORNECEDOR_CHOICES = [
    ("equipamento_hw", "Equipamento (somente HW)"),
    ("equipamento_sw_embarcado", "Equipamento com SW embarcado"),
    ("licenca_software", "Licença de Software"),
    ("subscricao_software", "Subscrição de Software"),
    ("solucao", "Solução"),
    ("servico", "Serviço"),
    ("treinamento", "Treinamento"),
]

# Tipos de item de fornecedor permitidos para OF com Equipamento com SW embarcado
TIPOS_FORNECEDOR_OF_EQUIPAMENTO_SW = [
    "equipamento_hw",
    "licenca_software",
    "subscricao_software",
]

# Tipos de item de fornecedor permitidos para OF com Solução
TIPOS_FORNECEDOR_OF_SOLUCAO = [
    "licenca_software",
    "subscricao_software",
]

# Tipos de item de fornecedor permitidos para OS com Serviço
TIPOS_FORNECEDOR_OS_SERVICO = [
    "servico",
]

# Tipos de item de fornecedor permitidos para OS com Treinamento
TIPOS_FORNECEDOR_OS_TREINAMENTO = [
    "treinamento",
]

VIGENCIA_PRODUTO_CHOICES_CONT = [
        (12, "12 meses"),
        (24, "24 meses"),
        (36, "36 meses"),
    ]