#  Croma – Sistema de Controle, Registro, Ordens de Serviço, Manutenção (Django)

## 1) Requisitos
- Python **3.11+**
- Git
- Navegador moderno (Chrome, Edge, Firefox)

> 💡 Por padrão, o projeto utiliza **SQLite** (não exige instalação de banco).  
> Também há suporte fácil para **PostgreSQL** — basta ajustar o `settings.py`.

---

## 2) Passo a passo (Quickstart – SQLite)

### Clonar o repositório
```bash
git clone https://github.com/BrunoDonato/Croma.git
cd Croma
```
--- 

### Criar e ativar ambiente virtual
> python -m venv .venv
### Windows
> .\.venv\Scripts\activate
### macOS/Linux
> source .venv/bin/activate


### Instalar Dependências
> pip install -r requirements.txt

### Aplicar migrações e criar dados de demonstração
> python manage.py migrate --settings=core.settings_demo
> python manage.py seed_demo --settings=core.settings_demo 

###  Executar o servidor
> python manage.py runserver --settings=core.settings_demo

### Acessar o sistema
> http://127.0.0.1:8000/contas/login/

---

## 3) Principais Funcionalidades
### Autenticação e Perfis
>   Login/logout seguro com hash de senhas.  
    Regeneração de sessão após login.  
    Grupos: Admin e Usuário Comum.  
    Controle de acesso via decorators e permissões.  
    Sessão expirada → redireciona automaticamente para o login.  
    Bloqueio temporário após múltiplas tentativas inválidas.

### Ordens de Serviço (OS)
>    Abertura de OS pelos usuários comuns.  
    Visualização e gestão completa de OS pelos administradores.  
    Campos principais: loja, solicitante, prioridade, status, data de abertura/fechamento, técnico responsável.  
    Filtros inteligentes no Django Admin (status, loja, técnico responsável, prioridade, datas).  
    Ações rápidas de status: Em análise, Em execução, Finalizada, Cancelada.  
    Anexos de arquivos e registro de andamentos (comentários).  
    Usuários comuns veem apenas suas OS e comentários públicos.  
    Admins podem registrar andamentos internos e viagens vinculadas à OS.

### Módulo de Viagens
>   Cadastro de viagens associadas a Ordens de Serviço.  
    Campos: origem, destino, responsável, veículo, data de partida e retorno.  
    Regras de validação (origem ≠ destino, retorno ≥ partida).  
    Apenas admins podem criar e editar viagens.  

### Módulo de Estoque
>   Controle central e local de peças.
    Marcação de loja central única.
    Controle de entrada, saída e transferência entre estoques.
    Visualização por loja e relatórios de saldo.

### Interface e Usabilidade
>   Painel lateral dinâmico com base no tipo de usuário.
    Dashboard limpo e responsivo.
    Estilo profissional com paleta azul escuro e lilás
    Mensagens de sucesso e erro contextuais.
    Alertas de permissão e sessão.

---

## 4) Estrutura principal do projeto (Até o momento)
```bash
core/
  settings.py
  settings_demo.py
contas/
  signals.py
  views.py
  forms.py
  decorators.py
ordens/
  models.py
  views.py
  admin.py
  forms.py
viagens/
  models.py
  forms.py
  views.py
estoque/
  models.py
  admin.py
templates/
  base.html
  partials/sidebar.html
  ordens/os_listar.html
  ordens/os_detalhe.html
  viagens/viagem_nova.html
static/
  css/auth.css

```

---

## 5) Testes Manuais Recomendados

| **Cenário de Teste** | **Ação do Usuário** | **Resultado Esperado** |
|-----------------------|---------------------|-------------------------|
| **Login inválido** | Inserir credenciais incorretas | Exibir mensagem em vermelho informando erro de autenticação |
| **Login válido (Admin)** | Entrar com usuário admin | Redirecionar para o dashboard com acesso total |
| **Login válido (Usuário comum)** | Entrar com usuário comum | Redirecionar para a tela de criação de nova OS |
| **Sessão expirada** | Esperar tempo limite de sessão e atualizar página | Redirecionar para o login com alerta amarelo |
| **Logout** | Clicar em "Sair" | Encerrar sessão e voltar à tela de login |
| **Tentativas múltiplas de login falho** | Inserir senha incorreta diversas vezes | Exibir aviso de bloqueio temporário por segurança |
| **Registro de novo usuário** | Preencher formulário de registro corretamente | Criar usuário no grupo `user` e redirecionar para login |
| **Acesso negado (usuário comum)** | Tentar acessar `/contas/dashboard/` diretamente | Exibir alerta vermelho "Acesso negado" |
| **Abrir Nova OS (usuário comum)** | Preencher descrição e prioridade | Criar OS associada automaticamente ao usuário logado |
| **Visualizar Minhas OS** | Acessar “Minhas OS” no menu lateral | Listar apenas as OS criadas pelo usuário logado |
| **Visualizar OS (admin)** | Acessar “Ordens de Serviço” | Listar todas as OS registradas no sistema |
| **Filtrar OS por status** | Selecionar “Finalizada” no filtro lateral | Mostrar apenas OS finalizadas |
| **Filtrar OS por técnico responsável** | Selecionar um admin específico no filtro | Mostrar apenas as OS atribuídas àquele responsável |
| **Editar OS (admin)** | Alterar prioridade ou técnico responsável | Atualizar os campos e registrar histórico automático de andamento |
| **Alterar status da OS** | Clicar em “Iniciar Execução” ou “Finalizar OS” | Mudar status e registrar andamento interno |
| **Cancelar OS (admin)** | Inserir motivo e confirmar | Status muda para “Cancelada” e motivo é salvo |
| **Usuário comum tenta cancelar OS** | Acessar tela de OS | Botões de ação (iniciar, finalizar, cancelar) **não aparecem** |
| **Registrar andamento (admin)** | Adicionar texto com visibilidade “Interna” | Apenas admins veem esse andamento |
| **Registrar andamento (usuário comum)** | Adicionar comentário | Comentário é salvo como “Público” e visível a todos |
| **Anexar arquivo (admin ou usuário)** | Enviar imagem ou PDF | Arquivo aparece na lista de anexos abaixo do formulário |
| **Visualizar anexos** | Acessar OS com anexos | Mostrar lista de arquivos com nome, autor e data |
| **Registrar viagem (admin)** | Clicar em “+ Registrar viagem desta OS” | Redireciona para formulário de nova viagem com OS pré-selecionada |
| **Validação de viagem** | Selecionar mesma loja em origem e destino | Exibir erro “Origem e destino devem ser diferentes” |
| **Salvar viagem válida** | Informar datas coerentes e salvar | Viagem é criada e vinculada à OS corretamente |
| **Usuário comum tenta acessar /viagens/** | Acessar manualmente a URL | Exibir mensagem de “Acesso negado (403)” |
| **Admin acessa relatório de viagens** | Entrar em “Relatórios” | Exibir resumo das viagens registradas |
| **Controle de estoque** | Registrar entrada e saída de produtos | Atualizar saldos nas lojas e no estoque central |
| **Coerência de estoque** | Retirar peças do central e enviar para loja | Quantidade central diminui e local aumenta proporcionalmente |
| **Responsividade da interface** | Acessar o sistema em diferentes resoluções | Layout ajusta-se corretamente sem sobreposição de elementos |
| **Mensagens do sistema** | Executar ações válidas e inválidas | Exibir mensagens contextuais de sucesso, erro ou alerta |
| **Segurança de cookies** | Rodar com `DEBUG=False` | Cookies `HttpOnly` e `Secure` são ativados automaticamente |
| **Permissões de grupos** | Promover usuário para “admin” | Ele ganha acesso imediato ao dashboard e filtros do admin |

---

## 6) Créditos
>   Desenvolvido por: Bruno Amaral Carvalho Donato  
    Curso: Ciência da Computação – UNIPAC Barbacena  
    Tecnologias: Django, HTML, CSS, SQLite/PostgreSQL
