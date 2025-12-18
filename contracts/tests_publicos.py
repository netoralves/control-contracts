"""
Testes para o módulo de Gestão de Contratos Públicos
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from .models_publicos import (
    ProjetoPublico,
    ContratoPublico,
    TermoAditivo,
    RegimeLegal,
    TipoTermoAditivo
)
from .services import ContratoPublicoService


class ContratoPublicoTestCase(TestCase):
    """Testes para Contratos Públicos"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.projeto = ProjetoPublico.objects.create(
            nome="Projeto Teste",
            orcamento_total=Decimal('1000000.00')
        )
        
        self.contrato = ContratoPublico.objects.create(
            projeto=self.projeto,
            numero_contrato="CT-2024-001",
            valor_inicial=Decimal('500000.00'),
            data_inicio=date(2024, 1, 1),
            vigencia_original_meses=24,
            regime_legal=RegimeLegal.LEI_14133,
            objeto="Prestação de serviços de TI"
        )

    def test_calculo_data_fim_atual(self):
        """Testa cálculo automático de data_fim_atual"""
        # Data fim deve ser data_inicio + vigencia_original
        data_esperada = date(2024, 1, 1) + timedelta(days=24*30)  # Aproximado
        data_calculada = self.contrato.data_fim_atual
        self.assertIsNotNone(data_calculada)
        
        # Testar com aditivo de prorrogação
        termo = TermoAditivo.objects.create(
            contrato=self.contrato,
            numero_termo="TA-001",
            tipo=TipoTermoAditivo.PRORROGACAO,
            meses_acrescimo=12,
            data_assinatura=date(2024, 6, 1),
            justificativa="Teste"
        )
        
        # Data fim deve incluir os 12 meses adicionais
        data_fim_com_aditivo = self.contrato.data_fim_atual
        self.assertGreater(data_fim_com_aditivo, data_calculada)

    def test_calculo_valor_atual(self):
        """Testa cálculo automático de valor_atual"""
        # Valor inicial deve ser igual ao valor atual sem aditivos
        self.assertEqual(self.contrato.valor_atual, Decimal('500000.00'))
        
        # Adicionar aditivo de valor
        termo = TermoAditivo.objects.create(
            contrato=self.contrato,
            numero_termo="TA-002",
            tipo=TipoTermoAditivo.VALOR,
            valor_acrescimo=Decimal('100000.00'),
            data_assinatura=date(2024, 6, 1),
            justificativa="Teste"
        )
        
        # Valor atual deve incluir o acréscimo
        self.assertEqual(self.contrato.valor_atual, Decimal('600000.00'))

    def test_validacao_limite_vigencia_lei_14133(self):
        """Testa validação de limite de vigência para Lei 14.133"""
        # Limite é 120 meses
        # Contrato tem 24 meses, podemos adicionar até 96 meses
        is_valid, mensagem = ContratoPublicoService.validar_limite_vigencia(
            self.contrato, meses_adicionais=96
        )
        self.assertTrue(is_valid)
        
        # Tentar adicionar mais que o limite
        is_valid, mensagem = ContratoPublicoService.validar_limite_vigencia(
            self.contrato, meses_adicionais=97
        )
        self.assertFalse(is_valid)
        self.assertIn("ultrapassa o limite legal", mensagem)

    def test_validacao_limite_aditivo_valor(self):
        """Testa validação de limite de 25% para aditivo de valor"""
        # 25% de 500.000 = 125.000
        # Adicionar 100.000 deve ser válido
        is_valid, mensagem = ContratoPublicoService.validar_limite_aditivo_valor(
            self.contrato, Decimal('100000.00')
        )
        self.assertTrue(is_valid)
        
        # Adicionar 150.000 deve ser inválido (ultrapassa 25%)
        is_valid, mensagem = ContratoPublicoService.validar_limite_aditivo_valor(
            self.contrato, Decimal('150000.00')
        )
        self.assertFalse(is_valid)
        self.assertIn("ultrapassa o limite legal", mensagem)

    def test_renovacao_pendente(self):
        """Testa sistema de alertas de renovação pendente"""
        # Criar contrato que vence em 60 dias
        data_vencimento = timezone.now().date() + timedelta(days=60)
        dias_para_vencimento = (data_vencimento - self.contrato.data_inicio).days
        meses_necessarios = dias_para_vencimento // 30
        
        contrato_proximo = ContratoPublico.objects.create(
            projeto=self.projeto,
            numero_contrato="CT-2024-002",
            valor_inicial=Decimal('300000.00'),
            data_inicio=date(2024, 1, 1),
            vigencia_original_meses=meses_necessarios,
            regime_legal=RegimeLegal.LEI_14133,
            objeto="Teste"
        )
        
        # Deve retornar True se está dentro de 90 dias
        if dias_para_vencimento <= 90:
            self.assertTrue(contrato_proximo.renovacao_pendente)

    def test_criar_termo_aditivo_com_validacao(self):
        """Testa criação de termo aditivo com validações automáticas"""
        # Criar prorrogação válida
        termo = ContratoPublicoService.criar_termo_aditivo(
            contrato=self.contrato,
            numero_termo="TA-003",
            tipo=TipoTermoAditivo.PRORROGACAO,
            meses_acrescimo=12,
            justificativa="Prorrogação válida"
        )
        self.assertIsNotNone(termo)
        
        # Tentar criar prorrogação que ultrapassa limite
        with self.assertRaises(ValidationError):
            ContratoPublicoService.criar_termo_aditivo(
                contrato=self.contrato,
                numero_termo="TA-004",
                tipo=TipoTermoAditivo.PRORROGACAO,
                meses_acrescimo=100,  # Ultrapassa limite
                justificativa="Prorrogação inválida"
            )

