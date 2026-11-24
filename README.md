# CRM Operacional

Sistema web de gestão do checklist pós-venda para equipes de atendimento ao aluno: filas de trabalho por consultor, importação idempotente do relatório de checklist do sistema ERP, painel executivo, módulo de pautas de comunicação interna e autenticação local com padrões de segurança de produção.

Projeto Flask completo — aplicação, migrações, importações, testes e container — pronto para rodar com um comando e explorar com dados de demonstração.

---

## Destaques de engenharia

- **Flask 3 com Application Factory** (`create_app`) e blueprints por módulo (`app/web/`), sem dependência de estado global.
- **SQLAlchemy 2.x** com `Mapped`/`mapped_column`, enums guardados como texto + `CHECK` (iguais em SQLite e Postgres) e chaves estrangeiras com `PRAGMA foreign_keys=ON`.
- **Migrações versionadas com Flask-Migrate/Alembic** em modo batch (`render_as_batch=True`), idempotentes e testadas contra upgrade/downgrade em banco populado (`tests/test_migracoes.py`).
- **Leitura de planilhas em milissegundos com `python-calamine`** (parser Rust), com fallback `openpyxl` — sem automação COM de Excel.
- **Importações idempotentes com prévia obrigatória**: nada é gravado sem conferência humana, reimportar o mesmo arquivo não duplica registros e o trabalho manual da equipe (status, responsável, datas planejadas, anotações) nunca é sobrescrito.
- **Segurança de produção**: senhas com PBKDF2-SHA256 (Werkzeug), rate-limiting contra força bruta no login, CSRF em todo POST, cabeçalhos `X-Frame-Options`/`nosniff`/HSTS atrás de proxy e `SECRET_KEY` recusada se for valor de exemplo.
- **HTML de terceiros isolado**: os painéis enviados rodam em iframe com sandbox de origem opaca (`app/rsa.py`), sem acesso a cookies ou rotas do CRM.
- **SQLite em modo WAL** com `busy_timeout` para acesso concorrente, backups atômicos pela API de backup do SQLite (`flask backup`).
- **Deploy multiplataforma**: `gunicorn` (Linux/Docker) e `waitress` (Windows), com Docker Compose e imagem Python Slim.

---

## Funcionalidades

- **Filas de trabalho** — Minha fila, Fila da equipe e Por consultor, com visualizações em Lista, Kanban (arrastar muda o status), Quadro por aluno e Calendário (arrastar replaneja a data).
- **Organização avançada** — agrupamento por data, procedimento, tipo de visto, embarque, responsável ou status; filtros de atraso, público e período; preferência salva por usuário.
- **Checklist do ERP** — importação do relatório CSV com prévia, encerramento de itens que saíram do arquivo, tela "Para lançar no ERP" para o que foi feito aqui e ainda falta baixar lá.
- **NEG e anotações separadas** — a observação oficial do ERP (`obs_erp`) é distinta das anotações internas da equipe, que a importação nunca toca.
- **Painel Executivo e RSA** — dashboards HTML de arquivo único embutidos com segurança e alimentados pela base importada.
- **Pautas de comunicação interna** — pipeline Kanban com estados internos, SLA por categoria e alertas de quebra de 72h, preservando observações entre sincronizações.
- **Administração** — usuários e papéis, catálogo de trilhas/etapas, classificação de serviços, público teen, importações e diagnóstico.

---

## Como rodar

### Docker (recomendado)

```bash
docker compose up --build
```

O container sobe em `http://localhost:8080`, roda as migrações automaticamente e persiste o banco no volume `crm_dados`.

### Local (Linux)

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/flask --app wsgi db upgrade
.venv/bin/flask --app wsgi run
```

No Windows, use `iniciar.cmd` (sobe com `waitress` na porta 5000).

### Dados de demonstração

Com o sistema rodando (ou no próprio container), popule o banco com dados fictícios:

```bash
.venv/bin/flask --app wsgi seed-demo        # local
docker exec -it crm-operacional flask seed-demo   # Docker
```

O comando é idempotente — pode rodar quantas vezes quiser sem duplicar nada — e cria alunos, programas, tarefas em todos os status e pautas de exemplo, com estes usuários:

| E-mail | Papel | Senha |
| :--- | :--- | :--- |
| `admin@exemplo.com` | Administrador | `Demo@123456` |
| `ana.souza@exemplo.com` | Consultor | `Demo@123456` |
| `carlos.lima@exemplo.com` | Consultor | `Demo@123456` |
| `estagio@exemplo.com` | Estagiário | `Demo@123456` |

Para um banco limpo de verdade, use `flask criar-admin` e cadastre a equipe em Administração → Usuários.

---

## Hospedagem de demonstração 24/7 (Proxmox / Docker)

Para manter uma instância pública de portfólio rodando 24/7 (ex.: uma VM LXC no Proxmox),
suba a pilha com o override de demonstração:

```bash
docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d --build
```

O override liga `MODO_DEMO=1` e `AUTO_SEED_DEMO=1`:

- **`MODO_DEMO`** mostra o selo "Modo Demo" no topo e na tela de entrada, adiciona botões de
  acesso rápido (Consultora Demo e Administrador Demo, senha `Demo@123456`) e **bloqueia
  alterações nas contas de exemplo** (senha, e-mail, papel e ativo) em `/trocar-senha` e
  Administração → Usuários — ninguém fecha a demonstração para os demais visitantes.
- **`AUTO_SEED_DEMO`** popula o banco com os dados fictícios (`flask seed-demo`) a cada subida
  do container, depois das migrações e do catálogo.

Atrás de um proxy reverso com HTTPS (Nginx, Caddy, Traefik, Cloudflare), ative o ProxyFix,
os cookies seguros e o HSTS exportando `ATRAS_DE_PROXY=1` antes de subir:

```bash
ATRAS_DE_PROXY=1 docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d --build
```

### Reset diário da demonstração

Um cron na máquina host devolve o banco ao estado inicial todo dia (madrugada, horário local):

```cron
0 4 * * *  cd /opt/crm-operacional && ./scripts/reset_demo.sh >> /var/log/crm-demo-reset.log 2>&1
```

O `scripts/reset_demo.sh` apaga `/dados/checklist.db*` dentro do container em execução,
recria o banco (`flask db upgrade && flask catalogo carregar && flask seed-demo`) e reinicia
o serviço — tudo idempotente: rodar quantas vezes quiser não duplica nada.

---

## Testes

```bash
.venv/bin/pytest            # suíte completa
.venv/bin/pytest tests/test_web.py -q   # um módulo
```

A suíte cobre autenticação e segurança, importações (checklist e pautas), filtros e visualizações, migrações com dados, modelos e regras de negócio. Todos os dados de teste são fictícios (`tests/amostras/`).

---

## Configuração

Copie `config.py.exemplo` para `<pasta de dados>/config.py` ou defina variáveis de ambiente. A pasta de dados é `CHECKLIST_DADOS` (no Docker, `/dados`); sem ela, `instance/`.

| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `SECRET_KEY` | *(gerada e persistida em `<dados>/secret_key`)* | Chave das sessões. Valores de exemplo são recusados na subida. |
| `CHECKLIST_DADOS` | `instance` | Pasta do banco, chave, backups e uploads. |
| `SERVIDOR_HOST` / `SERVIDOR_PORTA` | `127.0.0.1` / `8080` | Endereço do servidor WSGI. |
| `SERVIDOR_THREADS` | `8` | Threads de atendimento. |
| `ATRAS_DE_PROXY` | `0` | Com `1`, ativa `ProxyFix`, cookies seguros e HSTS. |
| `LOGIN_PROVISORIO` / `SENHA_PROVISORIA` | `0` / — | Transição: quem ainda não tem senha individual entra com a senha da equipe e define a sua (nunca vale para admin). |
| `MODO_DEMO` | `0` | Com `1`, liga o modo demonstração pública: selo "Modo Demo", acesso rápido na tela de entrada e contas de exemplo protegidas. |
| `AUTO_SEED_DEMO` | `0` | Com `1`, roda `flask seed-demo` na subida do container (banco de demonstração sozinho). |
| `NOME_SISTEMA` / `NOME_UNIDADE` | `CRM Operacional` / `Unidade Matriz` | Identidade whitelabel mostrada nas telas. |
| `DOMINIO_EMAIL_EXEMPLO` | `exemplo.com` | Domínio dos e-mails de exemplo nos formulários. |

---

## Comandos de manutenção

```bash
flask db upgrade                 # aplica migrações pendentes
flask catalogo carregar          # cria trilhas, etapas e serviços padrão (idempotente)
flask seed-demo                  # dados de demonstração fictícios (idempotente)
flask criar-admin                # cria/promove um administrador
flask usuarios listar            # usuários cadastrados
flask backup --manter 30         # backup atômico do banco
flask diagnostico               # confere banco, pasta de dados, segurança e leitor de planilhas
flask importar checklist CSV.csv --sim   # importa o relatório de checklist (com prévia)
```

---

## Estrutura

- `app/` — aplicação: modelos (`models/`), blueprints (`web/`), importações (`importacao/`), CLI (`cli.py`) e templates/estáticos.
- `migrations/` — Alembic versionado (batch mode).
- `tests/` — suíte pytest (somente dados fictícios).
- `ESTRUTURA.md` — mapa detalhado do código.
- `REGRAS_PAUTAS.md` e `docs/REGRAS_CHECKLIST.md` — regras de negócio detalhadas.

O sistema é whitelabel: nome do sistema, unidade e escopo vêm da configuração, sem marca fixa em código.
