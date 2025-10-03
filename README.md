# Croma – Autenticação e Autorização (Django)

## 1) Requisitos
- Python 3.11+
- Git

> Por padrão, os passos abaixo usam **SQLite** (não exige instalação de banco).

## 2) Passo a passo (Quickstart – SQLite)

## Clonar o repositório**
```bash
git clone <https://github.com/BrunoDonato/Croma/tree/main>
cd croma

## Criar e ativar ambiente virtual
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate


## Instalar Dependências
pip install -r requirements.txt

## Aplicar migrações e criar dados de demonstração (grupos e usuários)
python manage.py migrate --settings=core.settings_demo
python manage.py seed_demo --settings=core.settings_demo

## Subir o servidor
python manage.py runserver --settings=core.settings_demo

## Acessar
App: http://127.0.0.1:8000/contas/login/

## Usuarios de teste
Admin → usuário: admin / senha: 123456
Usuário comum → usuário: teste / senha: 123456


## Fluxo implementado 

Login/Logout com sessão (senhas com hash).

Regeneração do ID de sessão após login.

Proteção de páginas com @login_required.

Perfis por grupos: user (padrão) e admin (acesso à /contas/admin-area/).

Redirecionamentos com alerta:

Sessão ausente/expirada →  (alerta amarelo).

Acesso negado (sem permissão) → (alerta vermelho).

Mensagens claras: erros de formulário, login inválido, registro concluído.

Bloqueio após N tentativas de login (controle por sessão).

Segurança extra em produção (DEBUG=False): cookies Secure/HttpOnly, HTTPS/HSTS.


## Estrutura principal do projeto

core/
  settings.py            # Config principal
  settings_demo.py       # Quickstart com SQLite
contas/
  apps.py                # AppConfig (carrega signals)
  signals.py             # Cria grupos 'admin' e 'user' após migrate
  forms.py               # Registro e Login
  views.py               # registrar, dashboard, admin_area, etc.
  decorators.py          # @admin_required
  management/
    commands/
      seed_demo.py       # Cria grupos e usuários de teste (admin/teste)
templates/
  base.html
  403.html
  contas/
    dashboard.html
    admin_area.html
  registration/
    login.html
    registrar.html
static/
  css/auth.css
requirements.txt


## Testes manuais

Login inválido → mensagem em vermelho.

Registro válido → mensagem de sucesso e redirecionamento para login.

Sessão expirada → aguardar o tempo configurado, recarregar página → voltar ao login com alerta amarelo.

Acesso negado (usuário comum em /contas/admin-area/) → alerta vermelho.

Logout → encerra sessão e volta ao login.

Perfis:

Usuário novo cai no grupo user automaticamente.

Promover a admin (via /admin ou shell) dá acesso à área admin.

Bloqueio por tentativas → após falhas repetidas, login bloqueado por alguns minutos.

## Equivalência com os entregáveis

O exercicio o pede: código-fonte em PHP, um .sql com CREATE TABLE e 1 usuário de teste já com senha hasheada.

No presente projeto (implementado em **Django**), os equivalentes são:

- **Código-fonte completo**: disponível neste repositório no GitHub.
- **Estrutura do banco (.sql)**: em Django, a estrutura de tabelas é controlada pelas **migrations**, que já estão versionadas e podem ser aplicadas via:
  ```bash
  python manage.py migrate
