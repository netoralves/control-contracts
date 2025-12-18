from django import template

register = template.Library()


@register.filter
def is_in_group(user, group_name):
    """Verifica se o usuário está em um grupo específico"""
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()


@register.simple_tag
def user_has_group(user, group_name):
    """Tag para verificar se o usuário está em um grupo específico"""
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()

