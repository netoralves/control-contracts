# Service Layer - Gestão de Contratos Públicos

## Visão Geral

Este módulo implementa a gestão de contratos públicos conforme as Leis 14.133/2021 e 13.303/2016, com toda a lógica de negócios encapsulada em uma camada de serviços.

## Estrutura

### Models (`models_publicos.py`)

- **ProjetoPublico**: Entidade raiz dos projetos
- **ContratoPublico**: Contratos vinculados a projetos
- **TermoAditivo**: Termos aditivos aos contratos

### Service Layer (`contrato_publico_service.py`)

A classe `ContratoPublicoService` encapsula toda a lógica de negócios:

- Cálculos automáticos (data_fim_atual, valor_atual)
- Validações legais
- Sistema de alertas

## Uso Básico

### Criar um Projeto

```python
from contracts.models_publicos import ProjetoPublico

projeto = ProjetoPublico.objects.create(
    nome="Projeto de Infraestrutura",
    orcamento_total=Decimal('1000000.00')
)
```

### Criar um Contrato

```python
from contracts.models_publicos import ContratoPublico, RegimeLegal
from contracts.services import ContratoPublicoService

contrato = ContratoPublico.objects.create(
    projeto=projeto,
    numero_contrato="CT-2024-001",
    valor_inicial=Decimal('500000.00'),
    data_inicio=date(2024, 1, 1),
    vigencia_original_meses=24,
    regime_legal=RegimeLegal.LEI_14133,
    objeto="Prestação de serviços de TI"
)

# Acessar propriedades computadas
data_fim = contrato.data_fim_atual  # Calculado automaticamente
valor_atual = contrato.valor_atual  # Calculado automaticamente
```

### Criar Termo Aditivo (usando Service)

```python
from contracts.models_publicos import TipoTermoAditivo
from contracts.services import ContratoPublicoService

# Prorrogação (com validação automática de limite legal)
termo = ContratoPublicoService.criar_termo_aditivo(
    contrato=contrato,
    numero_termo="TA-001",
    tipo=TipoTermoAditivo.PRORROGACAO,
    meses_acrescimo=12,
    justificativa="Necessidade de prorrogação para conclusão dos serviços"
)

# Aditivo de Valor (com validação automática de 25%)
termo_valor = ContratoPublicoService.criar_termo_aditivo(
    contrato=contrato,
    numero_termo="TA-002",
    tipo=TipoTermoAditivo.VALOR,
    valor_acrescimo=Decimal('100000.00'),
    justificativa="Acréscimo de escopo"
)
```

### Validações Legais

```python
from contracts.services import ContratoPublicoService

# Validar limite de vigência antes de criar aditivo
is_valid, mensagem = ContratoPublicoService.validar_limite_vigencia(
    contrato, meses_adicionais=12
)
if not is_valid:
    print(f"Erro: {mensagem}")

# Validar limite de aditivo de valor (25%)
is_valid, mensagem = ContratoPublicoService.validar_limite_aditivo_valor(
    contrato, valor_acrescimo=Decimal('150000.00')
)
if not is_valid:
    print(f"Erro: {mensagem}")
```

### Sistema de Alertas

```python
from contracts.services import ContratoPublicoService

# Verificar se renovação está pendente
if contrato.renovacao_pendente:
    print("Atenção: Contrato próximo do vencimento!")

# Listar todos os contratos com renovação pendente
contratos_pendentes = ContratoPublicoService.listar_contratos_com_renovacao_pendente()
for contrato in contratos_pendentes:
    print(f"{contrato.numero_contrato} - Vence em {contrato.data_fim_atual}")
```

### Obter Resumo Completo

```python
from contracts.services import ContratoPublicoService

resumo = ContratoPublicoService.obter_resumo_contrato(contrato)
print(f"Valor atual: R$ {resumo['valor_atual']:,.2f}")
print(f"Data fim: {resumo['data_fim_atual']}")
print(f"Renovação pendente: {resumo['renovacao_pendente']}")
```

## Regras de Negócio Implementadas

### 1. Campos Computados (Nunca Editáveis)

- `data_fim_atual`: Calculada automaticamente
- `valor_atual`: Calculado automaticamente

### 2. Validações Legais

- **Limite de Vigência**: 
  - Lei 14.133/2021: 120 meses (10 anos)
  - Lei 13.303/2016: 60 meses (5 anos)

- **Limite de Aditivo de Valor**: 
  - 25% do valor inicial atualizado (Art. 125 Lei 14.133)

### 3. Sistema de Alertas

- `renovacao_pendente`: True se faltam 90 dias ou menos para vencimento

## Boas Práticas

1. **Sempre use o Service Layer** para criar termos aditivos (não crie diretamente)
2. **Nunca edite diretamente** `data_fim_atual` ou `valor_atual` (são calculados)
3. **Valide antes de criar** usando os métodos de validação do service
4. **Use propriedades do modelo** para acessar valores calculados

