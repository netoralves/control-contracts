# utils.py
from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.http import HttpResponseForbidden


def group_required(*group_names):
    """
    Decorador para restringir acesso a usuários de grupos específicos.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if (
                request.user.is_authenticated
                and request.user.groups.filter(name__in=group_names).exists()
            ):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden(
                "🚫 Você não tem permissão para acessar esta página."
            )

        return _wrapped_view

    return decorator


def map_tipo_item_contrato_para_fornecedor(tipo_contrato):
    mapa = {
        "hardware": "produto",
        "software": "produto",
        "solucao": "produto",
        "servico": "servico",
        "treinamento": "treinamento",
    }
    return mapa.get(tipo_contrato.lower())
