"""
Comando para criar um contrato de demonstração com histórico completo
Demonstra todas as funcionalidades do módulo de contratos públicos
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from contracts.models import (
    Cliente,
    Contrato,
    TermoAditivo,
    RegimeLegal,
    TipoTermoAditivo,
)


class Command(BaseCommand):
    help = 'Cria um contrato de demonstração com histórico completo de aditivos'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Criando contrato de demonstração...'))
        
        # 1. Criar ou buscar cliente
        cliente, created = Cliente.objects.get_or_create(
            cnpj_cpf='00.000.000/0001-00',
            defaults={
                'nome_razao_social': 'Ministério da Economia - Demonstração',
                'nome_fantasia': 'ME Demo',
                'tipo_cliente': 'publico',
                'tipo_pessoa': 'juridica',
                'natureza_juridica': 'Órgão Público Federal',
                'endereco': 'Esplanada dos Ministérios, Bloco P',
                'numero': 'S/N',
                'bairro': 'Zona Cívico-Administrativa',
                'cidade': 'Brasília',
                'estado': 'DF',
                'cep': '70048-900',
                'nome_responsavel': 'João da Silva',
                'cargo_responsavel': 'Coordenador de TI',
                'telefone_contato': '(61) 3412-0000',
                'email_contato': 'contato@economia.gov.br',
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Cliente criado: {cliente.nome_razao_social}'))
        else:
            self.stdout.write(f'→ Cliente já existe: {cliente.nome_razao_social}')
        
        # 2. Criar contrato (iniciado há 3 anos)
        data_inicio = date.today() - relativedelta(years=3)
        
        contrato, created = Contrato.objects.get_or_create(
            numero_contrato='CT-DEMO-2021/001',
            defaults={
                'cliente': cliente,
                'regime_legal': RegimeLegal.LEI_14133,
                'processo': 'PROC-2021/00123',
                'pregao_eletronico': 'PE-2021/001',
                'ata_registro_preco': 'ARP-2021/001',
                'termo_referencia': 'TR-TI-2021/001',
                'objeto': 'Contratação de serviços de consultoria em Tecnologia da Informação para suporte técnico, desenvolvimento de sistemas e gestão de projetos de TI, conforme especificações do Termo de Referência.',
                'valor_inicial': Decimal('1000000.00'),  # R$ 1.000.000,00
                'vigencia': 24,  # 24 meses
                'data_assinatura': data_inicio,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Contrato criado: {contrato.numero_contrato}'))
            self.stdout.write(f'  → Valor inicial: R$ {contrato.valor_inicial:,.2f}')
            self.stdout.write(f'  → Vigência original: {contrato.vigencia} meses')
            self.stdout.write(f'  → Data início: {contrato.data_assinatura}')
        else:
            self.stdout.write(f'→ Contrato já existe: {contrato.numero_contrato}')
            # Limpar aditivos existentes para recriar
            contrato.termos_aditivos.all().delete()
            self.stdout.write('  → Aditivos anteriores removidos para recriação')
        
        # 3. Criar histórico de termos aditivos
        
        # Aditivo 1: Prorrogação após 24 meses (1º ano de execução)
        data_aditivo1 = data_inicio + relativedelta(months=22)
        aditivo1 = TermoAditivo.objects.create(
            contrato=contrato,
            numero_termo='TA-001/2023',
            tipo=TipoTermoAditivo.PRORROGACAO,
            meses_acrescimo=12,
            valor_acrescimo=Decimal('0.00'),
            data_assinatura=data_aditivo1,
            justificativa='Prorrogação do contrato por mais 12 meses, conforme Art. 107 da Lei 14.133/2021, considerando a necessidade de continuidade dos serviços de TI e a satisfatória execução contratual.'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Aditivo 1 criado: {aditivo1.numero_termo} - Prorrogação +12 meses'))
        
        # Aditivo 2: Aditivo de Valor (10% do valor inicial) - Expansão de escopo
        data_aditivo2 = data_inicio + relativedelta(months=30)
        valor_acrescimo2 = contrato.valor_inicial * Decimal('0.10')  # 10%
        aditivo2 = TermoAditivo.objects.create(
            contrato=contrato,
            numero_termo='TA-002/2023',
            tipo=TipoTermoAditivo.VALOR,
            meses_acrescimo=0,
            valor_acrescimo=valor_acrescimo2,
            data_assinatura=data_aditivo2,
            justificativa='Aditivo de valor para expansão do escopo contratual, incluindo novos serviços de desenvolvimento de sistemas, conforme Art. 125 da Lei 14.133/2021. Acréscimo de 10% sobre o valor inicial.'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Aditivo 2 criado: {aditivo2.numero_termo} - Valor +R$ {valor_acrescimo2:,.2f} (10%)'))
        
        # Aditivo 3: Segunda Prorrogação
        data_aditivo3 = data_inicio + relativedelta(months=34)
        aditivo3 = TermoAditivo.objects.create(
            contrato=contrato,
            numero_termo='TA-003/2024',
            tipo=TipoTermoAditivo.PRORROGACAO,
            meses_acrescimo=12,
            valor_acrescimo=Decimal('0.00'),
            data_assinatura=data_aditivo3,
            justificativa='Segunda prorrogação do contrato por mais 12 meses, mantendo a continuidade dos serviços essenciais de TI para a Administração.'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Aditivo 3 criado: {aditivo3.numero_termo} - Prorrogação +12 meses'))
        
        # Aditivo 4: Reequilíbrio Econômico-Financeiro (5%)
        data_aditivo4 = data_inicio + relativedelta(months=36)
        valor_atual = contrato.valor_inicial + valor_acrescimo2
        valor_reequilibrio = valor_atual * Decimal('0.05')  # 5%
        aditivo4 = TermoAditivo.objects.create(
            contrato=contrato,
            numero_termo='TA-004/2024',
            tipo=TipoTermoAditivo.REEQUILIBRIO,
            meses_acrescimo=0,
            valor_acrescimo=valor_reequilibrio,
            data_assinatura=data_aditivo4,
            justificativa='Reequilíbrio econômico-financeiro do contrato devido à variação do IPCA acumulado no período, conforme Art. 124, II, "d" da Lei 14.133/2021.'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Aditivo 4 criado: {aditivo4.numero_termo} - Reequilíbrio +R$ {valor_reequilibrio:,.2f} (5%)'))
        
        # Aditivo 5: Aditivo de Valor adicional (próximo do limite de 25%)
        data_aditivo5 = date.today() - relativedelta(months=1)
        # Calcular valor para ficar próximo de 25%
        valor_total_aditivos = valor_acrescimo2 + valor_reequilibrio
        valor_limite_25 = contrato.valor_inicial * Decimal('0.25')
        valor_disponivel = valor_limite_25 - valor_total_aditivos
        valor_acrescimo5 = valor_disponivel * Decimal('0.90')  # 90% do disponível
        
        aditivo5 = TermoAditivo.objects.create(
            contrato=contrato,
            numero_termo='TA-005/2024',
            tipo=TipoTermoAditivo.VALOR,
            meses_acrescimo=0,
            valor_acrescimo=valor_acrescimo5,
            data_assinatura=data_aditivo5,
            justificativa='Aditivo de valor para inclusão de novos módulos de sistema e ampliação da equipe técnica. Valor próximo ao limite legal de 25% do Art. 125 da Lei 14.133/2021.'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Aditivo 5 criado: {aditivo5.numero_termo} - Valor +R$ {valor_acrescimo5:,.2f}'))
        
        # Atualizar contrato
        contrato.atualizar_data_fim()
        contrato.refresh_from_db()
        
        # Resumo final
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(self.style.SUCCESS('RESUMO DO CONTRATO DE DEMONSTRAÇÃO'))
        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(f'Contrato: {contrato.numero_contrato}')
        self.stdout.write(f'Cliente: {contrato.cliente.nome_razao_social}')
        self.stdout.write(f'Regime Legal: {contrato.get_regime_legal_display()}')
        self.stdout.write('')
        self.stdout.write(f'Valor Inicial: R$ {contrato.valor_inicial:,.2f}')
        self.stdout.write(f'Valor Atual: R$ {contrato.valor_atual:,.2f}')
        self.stdout.write(f'Acréscimo Total: R$ {(contrato.valor_atual - contrato.valor_inicial):,.2f} ({((contrato.valor_atual / contrato.valor_inicial - 1) * 100):.1f}%)')
        self.stdout.write('')
        self.stdout.write(f'Vigência Original: {contrato.vigencia} meses')
        self.stdout.write(f'Vigência Total: {contrato.vigencia_total_meses} meses')
        self.stdout.write(f'Data Início: {contrato.data_assinatura}')
        self.stdout.write(f'Data Término Atual: {contrato.data_fim_atual}')
        self.stdout.write(f'Dias para Vencimento: {contrato.dias_para_vencimento}')
        self.stdout.write(f'Renovação Pendente: {"Sim" if contrato.renovacao_pendente else "Não"}')
        self.stdout.write('')
        self.stdout.write(f'Total de Aditivos: {contrato.termos_aditivos.count()}')
        self.stdout.write(f'  - Prorrogações: {contrato.termos_aditivos.filter(tipo=TipoTermoAditivo.PRORROGACAO).count()}')
        self.stdout.write(f'  - Aditivos de Valor: {contrato.termos_aditivos.filter(tipo=TipoTermoAditivo.VALOR).count()}')
        self.stdout.write(f'  - Reequilíbrios: {contrato.termos_aditivos.filter(tipo=TipoTermoAditivo.REEQUILIBRIO).count()}')
        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Contrato de demonstração criado com sucesso!'))
        self.stdout.write(f'Acesse: /contratos-publicos/{contrato.pk}/')

