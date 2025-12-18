"""
Service Layer para Gestão de Contratos
Encapsula lógica de negócios e validações legais
Conforme Leis 14.133/2021 e 13.303/2016
"""
from typing import Tuple, List, Optional
from django.core.exceptions import ValidationError
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from datetime import date

from ..models import (
    Contrato,
    TermoAditivo,
    RegimeLegal,
    TipoTermoAditivo
)


class ContratoService:
    """
    Service Layer para operações com contratos
    Encapsula toda a lógica de negócios e validações legais
    """

    # Limites legais conforme as leis brasileiras
    LIMITE_VIGENCIA_LEI_14133 = 120  # meses (10 anos)
    LIMITE_VIGENCIA_LEI_13303 = 60   # meses (5 anos)
    LIMITE_VIGENCIA_PRIVADO = 240    # meses (20 anos) - sem limite legal
    LIMITE_ADITIVO_VALOR_PERCENTUAL = 25  # 25% do valor inicial (Art. 125 Lei 14.133)
    DIAS_ALERTA_RENOVACAO = 90  # dias antes do vencimento

    # ==================== COMPUTED FIELDS ====================

    @staticmethod
    def calcular_data_fim_atual(contrato: Contrato) -> date:
        """
        Calcula a data de fim atual do contrato
        data_assinatura + vigencia_original + soma(meses_acrescimo dos aditivos)
        
        Args:
            contrato: Instância do Contrato
            
        Returns:
            date: Data de fim atual calculada
        """
        if not contrato.data_assinatura:
            raise ValidationError("Contrato deve ter data de assinatura definida.")
        
        meses_totais = contrato.vigencia or 0
        if contrato.pk:
            meses_totais += sum(
                aditivo.meses_acrescimo or 0
                for aditivo in contrato.termos_aditivos.filter(
                    tipo=TipoTermoAditivo.PRORROGACAO
                )
            )
        
        return contrato.data_assinatura + relativedelta(months=meses_totais)

    @staticmethod
    def calcular_valor_atual(contrato: Contrato) -> Decimal:
        """
        Calcula o valor atual do contrato
        valor_inicial + soma(valor_acrescimo dos aditivos)
        
        Args:
            contrato: Instância do Contrato
            
        Returns:
            Decimal: Valor atual calculado
        """
        valor = contrato.valor_inicial or Decimal('0.00')
        if contrato.pk:
            valor += sum(
                aditivo.valor_acrescimo or Decimal('0.00')
                for aditivo in contrato.termos_aditivos.filter(
                    tipo__in=[TipoTermoAditivo.VALOR, TipoTermoAditivo.REEQUILIBRIO]
                )
            )
        return valor

    # ==================== VALIDAÇÕES LEGAIS ====================

    @staticmethod
    def get_limite_vigencia(regime_legal: str) -> int:
        """Retorna o limite de vigência em meses conforme o regime legal"""
        if regime_legal == RegimeLegal.LEI_14133:
            return ContratoService.LIMITE_VIGENCIA_LEI_14133
        elif regime_legal == RegimeLegal.LEI_13303:
            return ContratoService.LIMITE_VIGENCIA_LEI_13303
        else:
            return ContratoService.LIMITE_VIGENCIA_PRIVADO

    @staticmethod
    def validar_limite_vigencia(contrato: Contrato, meses_adicionais: int = 0) -> Tuple[bool, str]:
        """
        Valida se a renovação/prorrogação ultrapassa o limite legal
        
        Args:
            contrato: Instância do Contrato
            meses_adicionais: Meses adicionais que serão adicionados (para validação prévia)
            
        Returns:
            tuple: (is_valid, mensagem_erro)
        """
        limite_meses = ContratoService.get_limite_vigencia(contrato.regime_legal)
        
        # Determinar nome do regime para mensagem
        regime_nome = dict(RegimeLegal.choices).get(contrato.regime_legal, "Contrato Privado")
        
        # Calcular vigência total atual
        vigencia_atual = contrato.vigencia or 0
        if contrato.pk:
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
    def validar_limite_aditivo_valor(contrato: Contrato, valor_acrescimo: Decimal) -> Tuple[bool, str]:
        """
        Valida se o aditivo de valor ultrapassa 25% do valor inicial atualizado
        Conforme Art. 125 da Lei 14.133/2021
        
        Nota: Esta validação só se aplica a contratos sob a Lei 14.133/2021
        
        Args:
            contrato: Instância do Contrato
            valor_acrescimo: Valor que será adicionado
            
        Returns:
            tuple: (is_valid, mensagem_erro)
        """
        # Esta validação só se aplica a contratos sob a Lei 14.133
        if contrato.regime_legal != RegimeLegal.LEI_14133:
            return (True, "")
        
        # Calcular valor atual antes do novo aditivo
        valor_atual = ContratoService.calcular_valor_atual(contrato)
        
        # Calcular 25% do valor atual
        limite_percentual = valor_atual * Decimal(ContratoService.LIMITE_ADITIVO_VALOR_PERCENTUAL) / 100
        
        # Verificar se o acréscimo ultrapassa o limite
        if valor_acrescimo > limite_percentual:
            return (
                False,
                f"Valor de acréscimo (R$ {valor_acrescimo:,.2f}) ultrapassa o limite legal "
                f"de 25% do valor atual (R$ {limite_percentual:,.2f}). "
                f"Valor atual do contrato: R$ {valor_atual:,.2f}. "
                f"Conforme Art. 125 da Lei 14.133/2021."
            )
        
        return (True, "")

    # ==================== REGRAS DE ORIGEM / ARP ====================

    @staticmethod
    def is_contrato_publico(contrato: Contrato) -> bool:
        """Retorna True se o contrato estiver sob Lei 14.133 ou 13.303"""
        return contrato.regime_legal in (RegimeLegal.LEI_14133, RegimeLegal.LEI_13303)

    @staticmethod
    def origem_aceitavel_para_regime(contrato: Contrato) -> Tuple[bool, str]:
        """
        Valida se a origem escolhida é compatível com o regime legal do contrato.
        Não bloqueia o salvamento (apenas alerta), para flexibilidade.
        """
        from ..models import Contrato as ContratoModel

        origem = contrato.origem_contrato

        # Regime privado: aceita qualquer origem, mas sugere RFP/privado por padrão
        if contrato.regime_legal == RegimeLegal.PRIVADO:
            return True, ""

        # Lei 14.133: apenas origens públicas compatíveis
        if contrato.regime_legal == RegimeLegal.LEI_14133:
            publicas_validas = {
                ContratoModel.OrigemContrato.LIC_14133_PROPRIA,
                ContratoModel.OrigemContrato.ARP_GERENCIADOR,
                ContratoModel.OrigemContrato.ARP_PARTICIPANTE,
                ContratoModel.OrigemContrato.ARP_ADESAO_CARONA,
                ContratoModel.OrigemContrato.DISPENSA_14133,
                ContratoModel.OrigemContrato.INEXIGIBILIDADE_14133,
                ContratoModel.OrigemContrato.OUTRO,
            }
            if origem not in publicas_validas:
                return (
                    False,
                    "A origem escolhida não é típica de contratos sob a Lei 14.133. "
                    "Verifique se o campo 'Origem do Contrato' está coerente (licitação própria, ARP, dispensa, inexigibilidade, etc.)."
                )

        # Lei 13.303: apenas origens de estatais
        if contrato.regime_legal == RegimeLegal.LEI_13303:
            estatais_validas = {
                ContratoModel.OrigemContrato.LIC_13303_PROPRIA,
                ContratoModel.OrigemContrato.CONTR_ESTATAL_DIRETA,
                ContratoModel.OrigemContrato.OUTRO,
            }
            if origem not in estatais_validas:
                return (
                    False,
                    "A origem escolhida não é típica de contratos sob a Lei 13.303. "
                    "Use licitação própria (Lei 13.303) ou contratação direta conforme aplicável."
                )

        return True, ""

    # ==================== ALERTAS ====================

    @staticmethod
    def verificar_renovacao_pendente(contrato: Contrato) -> bool:
        """
        Verifica se há renovação pendente
        Retorna True se (data_fim_atual - hoje) <= 90 dias
        
        Args:
            contrato: Instância do Contrato
            
        Returns:
            bool: True se renovação está pendente
        """
        try:
            data_fim = ContratoService.calcular_data_fim_atual(contrato)
        except ValidationError:
            return False
        
        if not data_fim:
            return False
        
        hoje = timezone.now().date()
        dias_restantes = (data_fim - hoje).days
        
        return 0 < dias_restantes <= ContratoService.DIAS_ALERTA_RENOVACAO

    @staticmethod
    def listar_contratos_com_renovacao_pendente() -> List[Contrato]:
        """
        Lista todos os contratos com renovação pendente
        
        Returns:
            list: Lista de contratos com renovação pendente
        """
        contratos = Contrato.objects.filter(situacao="Ativo")
        contratos_pendentes = []
        
        for contrato in contratos:
            if ContratoService.verificar_renovacao_pendente(contrato):
                contratos_pendentes.append(contrato)
        
        return contratos_pendentes

    # ==================== OPERAÇÕES ====================

    @staticmethod
    def criar_termo_aditivo(
        contrato: Contrato,
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
            is_valid, mensagem = ContratoService.validar_limite_vigencia(
                contrato, meses_adicionais=meses_acrescimo
            )
            if not is_valid:
                raise ValidationError(mensagem)
        
        elif tipo in [TipoTermoAditivo.VALOR, TipoTermoAditivo.REEQUILIBRIO]:
            if valor_acrescimo <= 0:
                raise ValidationError("Aditivos de valor ou reequilíbrio devem ter valor de acréscimo maior que zero.")
            
            # Validar limite de 25%
            is_valid, mensagem = ContratoService.validar_limite_aditivo_valor(
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
    def obter_resumo_contrato(contrato: Contrato) -> dict:
        """
        Retorna um resumo completo do contrato com todos os dados calculados
        
        Args:
            contrato: Instância do Contrato
            
        Returns:
            dict: Dicionário com resumo do contrato
        """
        try:
            data_fim_atual = ContratoService.calcular_data_fim_atual(contrato)
        except ValidationError:
            data_fim_atual = None
        
        return {
            "contrato": contrato,
            "valor_inicial": contrato.valor_inicial,
            "valor_atual": ContratoService.calcular_valor_atual(contrato),
            "data_inicio": contrato.data_assinatura,
            "data_fim_atual": data_fim_atual,
            "vigencia_original": contrato.vigencia,
            "vigencia_total": contrato.vigencia_total_meses,
            "regime_legal": contrato.get_regime_legal_display(),
            "renovacao_pendente": ContratoService.verificar_renovacao_pendente(contrato),
            "dias_para_vencimento": contrato.dias_para_vencimento,
            "total_aditivos": contrato.termos_aditivos.count() if contrato.pk else 0,
            "aditivos_prorrogacao": contrato.termos_aditivos.filter(
                tipo=TipoTermoAditivo.PRORROGACAO
            ).count() if contrato.pk else 0,
            "aditivos_valor": contrato.termos_aditivos.filter(
                tipo__in=[TipoTermoAditivo.VALOR, TipoTermoAditivo.REEQUILIBRIO]
            ).count() if contrato.pk else 0,
        }

    @staticmethod
    def validar_termo_aditivo(
        contrato: Contrato,
        tipo: str,
        meses_acrescimo: int = 0,
        valor_acrescimo: Decimal = Decimal('0.00')
    ) -> Tuple[bool, str]:
        """
        Valida um termo aditivo antes de criar (para uso em formulários)
        
        Returns:
            tuple: (is_valid, mensagem_erro)
        """
        if tipo == TipoTermoAditivo.PRORROGACAO:
            if meses_acrescimo <= 0:
                return (False, "Termos de prorrogação devem ter meses de acréscimo maior que zero.")
            return ContratoService.validar_limite_vigencia(contrato, meses_acrescimo)
        
        elif tipo in [TipoTermoAditivo.VALOR, TipoTermoAditivo.REEQUILIBRIO]:
            if valor_acrescimo <= 0:
                return (False, "Aditivos de valor ou reequilíbrio devem ter valor de acréscimo maior que zero.")
            return ContratoService.validar_limite_aditivo_valor(contrato, valor_acrescimo)
        
        return (True, "")

