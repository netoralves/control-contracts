"""
Service Layer para Gestão de Contratos Públicos
Encapsula lógica de negócios e validações legais
Conforme Leis 14.133/2021 e 13.303/2016
"""
from typing import Tuple
from django.core.exceptions import ValidationError
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from datetime import date

from ..models_publicos import (
    ContratoPublico,
    TermoAditivo,
    RegimeLegal,
    TipoTermoAditivo
)


class ContratoPublicoService:
    """
    Service Layer para operações com contratos públicos
    Encapsula toda a lógica de negócios e validações legais
    """

    # Limites legais conforme as leis
    LIMITE_VIGENCIA_LEI_14133 = 120  # meses (10 anos)
    LIMITE_VIGENCIA_LEI_13303 = 60  # meses (5 anos) - padrão
    LIMITE_ADITIVO_VALOR_PERCENTUAL = 25  # 25% do valor inicial atualizado (Art. 125 Lei 14.133)
    DIAS_ALERTA_RENOVACAO = 90  # dias antes do vencimento

    @staticmethod
    def calcular_data_fim_atual(contrato: ContratoPublico) -> date:
        """
        Calcula a data de fim atual do contrato
        data_inicio + vigencia_original + soma(meses_acrescimo dos aditivos)
        
        Args:
            contrato: Instância do ContratoPublico
            
        Returns:
            date: Data de fim atual calculada
        """
        if not contrato.data_inicio:
            raise ValidationError("Contrato deve ter data de início definida.")
        
        meses_totais = contrato.vigencia_original_meses
        # Somar meses de acréscimo de todos os aditivos de prorrogação
        meses_totais += sum(
            aditivo.meses_acrescimo or 0
            for aditivo in contrato.termos_aditivos.filter(
                tipo=TipoTermoAditivo.PRORROGACAO
            )
        )
        
        return contrato.data_inicio + relativedelta(months=meses_totais)

    @staticmethod
    def calcular_valor_atual(contrato: ContratoPublico) -> Decimal:
        """
        Calcula o valor atual do contrato
        valor_inicial + soma(valor_acrescimo dos aditivos)
        
        Args:
            contrato: Instância do ContratoPublico
            
        Returns:
            Decimal: Valor atual calculado
        """
        valor = contrato.valor_inicial or Decimal('0.00')
        # Somar acréscimos de valor de todos os aditivos de valor e reequilíbrio
        valor += sum(
            aditivo.valor_acrescimo or Decimal('0.00')
            for aditivo in contrato.termos_aditivos.filter(
                tipo__in=[TipoTermoAditivo.VALOR, TipoTermoAditivo.REEQUILIBRIO]
            )
        )
        return valor

    @staticmethod
    def validar_limite_vigencia(contrato: ContratoPublico, meses_adicionais: int = 0) -> tuple[bool, str]:
        """
        Valida se a renovação/prorrogação ultrapassa o limite legal
        
        Args:
            contrato: Instância do ContratoPublico
            meses_adicionais: Meses adicionais que serão adicionados (para validação prévia)
            
        Returns:
            tuple: (is_valid, mensagem_erro)
        """
        # Determinar limite conforme regime legal
        if contrato.regime_legal == RegimeLegal.LEI_14133:
            limite_meses = ContratoPublicoService.LIMITE_VIGENCIA_LEI_14133
            regime_nome = "Lei 14.133/2021"
        else:  # LEI_13303
            limite_meses = ContratoPublicoService.LIMITE_VIGENCIA_LEI_13303
            regime_nome = "Lei 13.303/2016"
        
        # Calcular vigência total atual
        vigencia_atual = contrato.vigencia_original_meses
        vigencia_atual += sum(
            aditivo.meses_acrescimo or 0
            for aditivo in contrato.termos_aditivos.filter(
                tipo=TipoTermoAditivo.PRORROGACAO
            )
        )
        
        # Adicionar meses que serão adicionados
        vigencia_total = vigencia_atual + meses_adicionais
        
        if vigencia_total > limite_meses:
            return (
                False,
                f"Vigência total ({vigencia_total} meses) ultrapassa o limite legal "
                f"de {limite_meses} meses conforme {regime_nome}."
            )
        
        return (True, "")

    @staticmethod
    def validar_limite_aditivo_valor(contrato: ContratoPublico, valor_acrescimo: Decimal) -> Tuple[bool, str]:
        """
        Valida se o aditivo de valor ultrapassa 25% do valor inicial atualizado
        Conforme Art. 125 da Lei 14.133/2021
        
        Args:
            contrato: Instância do ContratoPublico
            valor_acrescimo: Valor que será adicionado
            
        Returns:
            tuple: (is_valid, mensagem_erro)
        """
        # Calcular valor atual antes do novo aditivo
        valor_atual = ContratoPublicoService.calcular_valor_atual(contrato)
        
        # Calcular 25% do valor atual
        limite_percentual = valor_atual * Decimal(ContratoPublicoService.LIMITE_ADITIVO_VALOR_PERCENTUAL) / 100
        
        # Verificar se o acréscimo ultrapassa o limite
        if valor_acrescimo > limite_percentual:
            return (
                False,
                f"Valor de acréscimo (R$ {valor_acrescimo:,.2f}) ultrapassa o limite legal "
                f"de 25% do valor atual (R$ {limite_percentual:,.2f}). "
                f"Valor atual do contrato: R$ {valor_atual:,.2f}."
            )
        
        return (True, "")

    @staticmethod
    def verificar_renovacao_pendente(contrato: ContratoPublico) -> bool:
        """
        Verifica se há renovação pendente
        Retorna True se (data_fim_atual - hoje) <= 90 dias
        
        Args:
            contrato: Instância do ContratoPublico
            
        Returns:
            bool: True se renovação está pendente
        """
        data_fim = ContratoPublicoService.calcular_data_fim_atual(contrato)
        if not data_fim:
            return False
        
        hoje = timezone.now().date()
        dias_restantes = (data_fim - hoje).days
        
        return 0 < dias_restantes <= ContratoPublicoService.DIAS_ALERTA_RENOVACAO

    @staticmethod
    def criar_termo_aditivo(
        contrato: ContratoPublico,
        numero_termo: str,
        tipo: str,
        meses_acrescimo: int = 0,
        valor_acrescimo: Decimal = Decimal('0.00'),
        data_assinatura: date = None,
        justificativa: str = ""
    ) -> TermoAditivo:
        """
        Cria um termo aditivo com validações legais
        
        Args:
            contrato: Contrato ao qual o termo será vinculado
            numero_termo: Número do termo aditivo
            tipo: Tipo do termo aditivo
            meses_acrescimo: Meses de acréscimo (para prorrogação)
            valor_acrescimo: Valor de acréscimo (para aditivos de valor)
            data_assinatura: Data de assinatura
            justificativa: Justificativa do termo aditivo
            
        Returns:
            TermoAditivo: Termo aditivo criado
            
        Raises:
            ValidationError: Se as validações legais falharem
        """
        # Validações específicas por tipo
        if tipo == TipoTermoAditivo.PRORROGACAO:
            if meses_acrescimo <= 0:
                raise ValidationError("Termos de prorrogação devem ter meses de acréscimo maior que zero.")
            
            # Validar limite de vigência
            is_valid, mensagem = ContratoPublicoService.validar_limite_vigencia(
                contrato, meses_adicionais=meses_acrescimo
            )
            if not is_valid:
                raise ValidationError(mensagem)
        
        elif tipo in [TipoTermoAditivo.VALOR, TipoTermoAditivo.REEQUILIBRIO]:
            if valor_acrescimo <= 0:
                raise ValidationError("Aditivos de valor ou reequilíbrio devem ter valor de acréscimo maior que zero.")
            
            # Validar limite de 25% (apenas para Lei 14.133)
            if contrato.regime_legal == RegimeLegal.LEI_14133:
                is_valid, mensagem = ContratoPublicoService.validar_limite_aditivo_valor(
                    contrato, valor_acrescimo
                )
                if not is_valid:
                    raise ValidationError(mensagem)
        
        # Criar termo aditivo
        termo = TermoAditivo.objects.create(
            contrato=contrato,
            numero_termo=numero_termo,
            tipo=tipo,
            meses_acrescimo=meses_acrescimo,
            valor_acrescimo=valor_acrescimo,
            data_assinatura=data_assinatura or timezone.now().date(),
            justificativa=justificativa
        )
        
        return termo

    @staticmethod
    def listar_contratos_com_renovacao_pendente() -> list[ContratoPublico]:
        """
        Lista todos os contratos com renovação pendente
        
        Returns:
            list: Lista de contratos com renovação pendente
        """
        contratos = ContratoPublico.objects.all()
        contratos_pendentes = []
        
        for contrato in contratos:
            if ContratoPublicoService.verificar_renovacao_pendente(contrato):
                contratos_pendentes.append(contrato)
        
        return contratos_pendentes

    @staticmethod
    def obter_resumo_contrato(contrato: ContratoPublico) -> dict:
        """
        Retorna um resumo completo do contrato com todos os dados calculados
        
        Args:
            contrato: Instância do ContratoPublico
            
        Returns:
            dict: Dicionário com resumo do contrato
        """
        return {
            "contrato": contrato,
            "valor_inicial": contrato.valor_inicial,
            "valor_atual": ContratoPublicoService.calcular_valor_atual(contrato),
            "data_inicio": contrato.data_inicio,
            "data_fim_atual": ContratoPublicoService.calcular_data_fim_atual(contrato),
            "vigencia_original": contrato.vigencia_original_meses,
            "vigencia_total": (
                contrato.vigencia_original_meses +
                sum(
                    aditivo.meses_acrescimo or 0
                    for aditivo in contrato.termos_aditivos.filter(
                        tipo=TipoTermoAditivo.PRORROGACAO
                    )
                )
            ),
            "regime_legal": contrato.get_regime_legal_display(),
            "renovacao_pendente": ContratoPublicoService.verificar_renovacao_pendente(contrato),
            "total_aditivos": contrato.termos_aditivos.count(),
            "aditivos_prorrogacao": contrato.termos_aditivos.filter(
                tipo=TipoTermoAditivo.PRORROGACAO
            ).count(),
            "aditivos_valor": contrato.termos_aditivos.filter(
                tipo__in=[TipoTermoAditivo.VALOR, TipoTermoAditivo.REEQUILIBRIO]
            ).count(),
        }

