# Guia de Versionamento - Control Contracts

## ✅ Configuração Concluída

O repositório foi configurado corretamente para versionamento seguro.

### 📋 O que foi feito:

1. **`.gitignore` atualizado** - Agora inclui:
   - Ambientes virtuais (venv/, .venv/)
   - Arquivos Python compilados (*.pyc, __pycache__/)
   - Arquivos de ambiente (.env)
   - Arquivos estáticos gerados (staticfiles/)
   - Arquivos de mídia (/media)
   - Arquivos temporários e de backup
   - Configurações de IDEs
   - Node modules

2. **Arquivos removidos do rastreamento**:
   - `.venv/` (ambiente virtual)
   - `staticfiles/` (arquivos estáticos compilados)
   - `.env` (variáveis de ambiente)
   - `__pycache__/` (arquivos Python compilados)

## 🚀 Próximos Passos para Fazer Commit

### 1. Verificar o status atual:
```bash
git status
```

### 2. Adicionar os arquivos importantes:
```bash
# Adicionar todas as mudanças (exceto os ignorados)
git add .

# OU adicionar arquivos específicos:
git add .gitignore
git add contracts/
git add controlcontratos/
git add manage.py
git add requirements.txt
git add package.json
git add README.md
```

### 3. Verificar o que será commitado:
```bash
git status
```

### 4. Fazer o commit:
```bash
git commit -m "feat: Restauração do código ao estado de 17/12/2025 23:59

- Corrigida dependência da migração 0036_add_plano_trabalho
- Atualizado .gitignore para excluir arquivos desnecessários
- Removidos arquivos do ambiente virtual e estáticos do rastreamento
- Código restaurado ao estado estável de ontem"
```

### 5. Enviar para o repositório remoto:
```bash
git push origin main
```

## 📝 Boas Práticas

### ✅ O que DEVE ser versionado:
- Código fonte Python (.py)
- Templates HTML
- Arquivos de configuração (settings.py, urls.py)
- Migrações do Django
- requirements.txt
- package.json
- README.md
- Scripts de setup

### ❌ O que NÃO deve ser versionado:
- `.env` (variáveis de ambiente sensíveis)
- `venv/` ou `.venv/` (ambiente virtual)
- `__pycache__/` (arquivos compilados)
- `staticfiles/` (arquivos estáticos compilados)
- `media/` (uploads de usuários)
- `node_modules/` (dependências Node.js)
- Arquivos temporários e backups

## 🔒 Segurança

**IMPORTANTE**: Nunca commite arquivos `.env` que contenham:
- SECRET_KEY do Django
- Credenciais de banco de dados
- Chaves de API
- Senhas

Crie um arquivo `.env.example` com variáveis de exemplo (sem valores reais) para documentar as variáveis necessárias.

## 📦 Estrutura Recomendada

```
control-contracts/
├── .gitignore          ✅ Versionado
├── .env                ❌ NÃO versionado
├── .env.example        ✅ Versionado (template)
├── requirements.txt    ✅ Versionado
├── manage.py           ✅ Versionado
├── contracts/          ✅ Versionado
├── controlcontratos/   ✅ Versionado
├── venv/               ❌ NÃO versionado
├── staticfiles/        ❌ NÃO versionado
└── media/              ❌ NÃO versionado
```

## 🆘 Comandos Úteis

### Ver o que será commitado:
```bash
git status
git diff --cached
```

### Desfazer mudanças não commitadas:
```bash
git restore <arquivo>
git restore .
```

### Ver histórico:
```bash
git log --oneline
git log --graph --oneline --all
```

### Criar uma branch para desenvolvimento:
```bash
git checkout -b feature/nova-funcionalidade
```

## 📚 Recursos Adicionais

- [Documentação do Git](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)

