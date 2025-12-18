"""
Serviço para exportação de planos de trabalho por fornecedor
Baseado nos modelos em /Users/fneto/Downloads/Modelos
"""
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
import json


class PlanoTrabalhoExportService:
    """Serviço para exportação de planos de trabalho com templates por fornecedor"""
    
    # Mapeamento de fornecedores para templates
    FORNECEDORES_TEMPLATES = {
        'CYBERARK': 'cyberark',
        'FORTINET': 'fortinet',
        'RED HAT': 'redhat',
        'REDHAT': 'redhat',
        'TREND': 'trend',
        'TREND MICRO': 'trend',
        'AGNOSTICO': 'agnostico',
    }
    
    @staticmethod
    def identificar_fornecedor(plano) -> Optional[str]:
        """
        Identifica o fornecedor do plano de trabalho
        
        Args:
            plano: Instância de PlanoTrabalho
            
        Returns:
            Nome do template a ser usado ou None para template genérico
        """
        if not plano.fornecedor:
            # Tentar identificar pelo contrato
            if plano.projeto and plano.projeto.contrato:
                fornecedores = plano.projeto.contrato.fornecedores
                if fornecedores:
                    if isinstance(fornecedores, list) and fornecedores:
                        fornecedor_nome = fornecedores[0].upper()
                    elif isinstance(fornecedores, str):
                        fornecedor_nome = fornecedores.upper()
                    else:
                        return None
                    
                    # Verificar no mapeamento
                    for key, template in PlanoTrabalhoExportService.FORNECEDORES_TEMPLATES.items():
                        if key in fornecedor_nome:
                            return template
        
        if plano.fornecedor:
            fornecedor_nome = plano.fornecedor.upper()
            for key, template in PlanoTrabalhoExportService.FORNECEDORES_TEMPLATES.items():
                if key in fornecedor_nome:
                    return template
        
        return None
    
    @staticmethod
    def exportar_pdf(plano, buffer: BytesIO, template: Optional[str] = None) -> None:
        """
        Exporta o plano de trabalho em PDF
        
        Args:
            plano: Instância de PlanoTrabalho
            buffer: BytesIO para escrever o PDF
            template: Nome do template a usar (None = genérico)
        """
        if not plano.projeto:
            raise ValueError("O plano de trabalho deve estar vinculado a um projeto")
        
        contrato = plano.projeto.contrato
        projeto = plano.projeto
        
        # Se não especificado, identificar automaticamente
        if template is None:
            template = PlanoTrabalhoExportService.identificar_fornecedor(plano)
        
        # Criar documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        
        # Cores Alltech
        cor_laranja_hex = '#FF6B35'
        cor_azul_escuro_hex = '#1e3a5f'
        cor_cinza_hex = '#9ca3af'
        
        cor_laranja = colors.HexColor(cor_laranja_hex)
        cor_azul_escuro = colors.HexColor(cor_azul_escuro_hex)
        cor_cinza = colors.HexColor(cor_cinza_hex)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=cor_azul_escuro,
            spaceAfter=12,
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=cor_azul_escuro,
            spaceAfter=10,
        )
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            alignment=TA_LEFT,
        )
        header_cell_style = ParagraphStyle(
            'HeaderCellStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
            textColor=colors.white,
        )
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        normal_style.leading = 14
        
        # Conteúdo do PDF
        story = []
        
        # Cabeçalho
        header_data = [
            [Paragraph(f'<font color="{cor_laranja_hex}"><b>ALL</b></font><font color="{cor_azul_escuro_hex}"><b>TECH</b></font><br/><font size="9" color="{cor_cinza_hex}">Soluções em Tecnologia</font>', 
                      ParagraphStyle('Header', parent=styles['Normal'], 
                                   fontSize=28, alignment=TA_CENTER, spaceAfter=5))],
            [Paragraph('<b>PLANO DE TRABALHO</b>', 
                      ParagraphStyle('HeaderTitle', parent=styles['Normal'],
                                   fontSize=18, textColor=colors.white,
                                   alignment=TA_CENTER, backColor=cor_azul_escuro,
                                   spaceBefore=10, spaceAfter=10))],
            [Paragraph(f'<b>Projeto:</b> {projeto.nome}<br/>'
                      f'<b>Contrato:</b> {contrato.numero_contrato}<br/>'
                      f'<b>Cliente:</b> {contrato.cliente.nome_razao_social}',
                      ParagraphStyle('HeaderInfo', parent=styles['Normal'],
                                   fontSize=10, textColor=colors.white,
                                   alignment=TA_CENTER, spaceAfter=5))],
        ]
        header_table = Table(header_data, colWidths=[16*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 1), (0, 1), cor_azul_escuro),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Informações do Projeto/Contrato
        info_data = [
            [
                Paragraph('<b>Projeto</b>', header_cell_style),
                Paragraph(str(projeto.nome), cell_style),
                Paragraph('<b>Data de Início</b>', header_cell_style),
                Paragraph(plano.data_inicio_prevista.strftime('%d/%m/%Y'), cell_style)
            ],
            [
                Paragraph('<b>Número do Contrato</b>', header_cell_style),
                Paragraph(str(contrato.numero_contrato), cell_style),
                Paragraph('<b>Data de Término</b>', header_cell_style),
                Paragraph(plano.data_fim_prevista.strftime('%d/%m/%Y'), cell_style)
            ],
            [
                Paragraph('<b>Cliente</b>', header_cell_style),
                Paragraph(contrato.cliente.nome_razao_social, cell_style),
                Paragraph('<b>Status</b>', header_cell_style),
                Paragraph(plano.get_status_display(), cell_style)
            ],
            [
                Paragraph('<b>CNPJ/CPF</b>', header_cell_style),
                Paragraph(str(contrato.cliente.cnpj_cpf or ''), cell_style),
                Paragraph('<b>Fornecedor</b>', header_cell_style),
                Paragraph(str(plano.fornecedor or 'Não definido'), cell_style)
            ],
        ]
        info_table = Table(info_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), cor_azul_escuro),
            ('BACKGROUND', (2, 0), (2, 0), cor_azul_escuro),
            ('BACKGROUND', (0, 1), (0, 1), cor_azul_escuro),
            ('BACKGROUND', (2, 1), (2, 1), cor_azul_escuro),
            ('BACKGROUND', (0, 2), (0, 2), cor_azul_escuro),
            ('BACKGROUND', (2, 2), (2, 2), cor_azul_escuro),
            ('BACKGROUND', (0, 3), (0, 3), cor_azul_escuro),
            ('BACKGROUND', (2, 3), (2, 3), cor_azul_escuro),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(Paragraph('<b>Informações do Projeto</b>', heading_style))
        story.append(info_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Resumo do Contrato
        story.append(Paragraph('<b>Resumo do Contrato</b>', title_style))
        story.append(Paragraph(plano.resumo_contrato.replace('\n', '<br/>'), normal_style))
        story.append(Spacer(1, 0.3*cm))
        
        # Processo de Execução (seções específicas por fornecedor podem ser adicionadas aqui)
        if plano.processo_execucao:
            story.append(PageBreak())
            story.append(Paragraph('<b>Processo de Execução</b>', title_style))
            
            for etapa in plano.processo_execucao:
                etapa_nome = etapa.get('nome') or etapa.get('etapa') or 'Etapa'
                fase = etapa.get('fase', '')
                story.append(Paragraph(f'<b>{etapa_nome}</b> - {fase}', heading_style))
                story.append(Paragraph(f'<b>Descrição:</b> {etapa.get("descricao", "-")}', normal_style))
                story.append(Paragraph(f'<b>Duração:</b> {etapa.get("duracao_estimada_dias", etapa.get("duracao_dias", "-"))} dias', normal_style))
                
                if etapa.get('entregaveis'):
                    story.append(Paragraph('<b>Entregáveis:</b>', normal_style))
                    for entregavel in etapa.get('entregaveis', []):
                        story.append(Paragraph(f'• {entregavel}', normal_style))
                
                story.append(Spacer(1, 0.3*cm))
        
        # Construir PDF
        doc.build(story)
        
        return story

