"""
Signals para atualização automática de horas planejadas e realizadas nas OSs
e criação automática de tickets de contato quando Sprint/OS é faturada
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Tarefa, LancamentoHora, OrdemServico, Sprint, FeedbackSprintOS


@receiver([post_save, post_delete], sender=Tarefa)
def atualizar_horas_os_tarefa(sender, instance, **kwargs):
    """Atualiza horas planejadas e realizadas da OS quando uma tarefa é salva ou deletada"""
    # A ordem de serviço agora está vinculada ao projeto, não diretamente à tarefa
    if instance.projeto and hasattr(instance.projeto, 'ordem_servico') and instance.projeto.ordem_servico:
        instance.projeto.ordem_servico.calcular_horas_tarefas()


@receiver([post_save, post_delete], sender=LancamentoHora)
def atualizar_horas_os_lancamento(sender, instance, **kwargs):
    """Atualiza horas realizadas da OS quando um lançamento de hora é salvo ou deletado"""
    # A ordem de serviço agora está vinculada ao projeto, não diretamente à tarefa
    if instance.tarefa and instance.tarefa.projeto and hasattr(instance.tarefa.projeto, 'ordem_servico') and instance.tarefa.projeto.ordem_servico:
        instance.tarefa.projeto.ordem_servico.calcular_horas_tarefas()


@receiver(post_save, sender=Sprint)
def criar_ticket_contato_sprint_faturada(sender, instance, created, **kwargs):
    """Cria ticket de contato automaticamente quando uma Sprint é faturada"""
    if not created and instance.status == 'faturada':
        # Verificar se já existe um ticket para esta sprint
        if not FeedbackSprintOS.objects.filter(sprint=instance, motivador_contato='feedback_servico').exists():
            FeedbackSprintOS.objects.create(
                sprint=instance,
                cliente=instance.projeto.contrato.cliente,
                contrato=instance.projeto.contrato,
                projeto=instance.projeto,
                motivador_contato='feedback_servico',
                status='pendente',
            )


@receiver(post_save, sender=OrdemServico)
def criar_ticket_contato_os_faturada(sender, instance, created, **kwargs):
    """Cria ticket de contato automaticamente quando uma OS é faturada"""
    if not created and instance.status == 'faturada':
        # Verificar se já existe um ticket para esta OS
        if not FeedbackSprintOS.objects.filter(ordem_servico=instance, motivador_contato='feedback_servico').exists():
            FeedbackSprintOS.objects.create(
                ordem_servico=instance,
                cliente=instance.cliente,
                contrato=instance.contrato,
                projeto=instance.projeto if hasattr(instance, 'projeto') and instance.projeto else None,
                motivador_contato='feedback_servico',
                status='pendente',
            )

