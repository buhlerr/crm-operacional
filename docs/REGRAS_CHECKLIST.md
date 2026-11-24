# Sistema de Checklist Pós-Venda — Regras de Negócio

Este documento descreve as entidades, os fluxos e as regras de negócio do módulo de checklist pós-venda do CRM Operacional. É a referência para entender o que a importação faz, o que ela nunca toca e como o atraso é calculado.

## Objetivo

Sistema interno para acompanhar o checklist pós-venda de cada aluno: os procedimentos que a equipe precisa cumprir entre a venda e o embarque. Substitui o acompanhamento manual (listas genéricas e planilhas por consultor) por filas de trabalho organizadas, com histórico e justificativas.

A equipe inclui pessoas não técnicas. A interface é simples, em português, sem jargão. Nenhuma operação do dia a dia exige terminal.

## Stack

- Python 3.12+ / Flask 3 (Application Factory) com blueprints em `app/web/`.
- SQLAlchemy 2.x sobre SQLite (WAL + busy_timeout), pronto para Postgres (enums como texto + CHECK, IDs em texto normalizado).
- Migrações versionadas com Flask-Migrate/Alembic em modo batch.
- Leitura de planilhas com `python-calamine` (parser Rust) e fallback `openpyxl`.
- Produção em Linux/Docker com gunicorn (waitress no Windows).

## Entidades

**Aluno**: `aluno_id_erp` (vem do sistema ERP), nome, marca de público teen. Representa a pessoa.

**Programa**: `programa_id_erp` (do ERP; vazio nos programas criados pelo checklist), `aluno_id`, consultor, mês de embarque, visto normalizado, país, cidade, escola, acomodação, grupo, situação (ativo/cancelado/incorporado). Representa cada programa comprado. Um mesmo aluno pode ter mais de um programa, e o checklist é feito por programa, não por pessoa.

**Compra**: `compra_id_erp` (do ERP), `programa_id`, origem (planilha ou checklist). Cada programa é formado por várias compras. É por elas que o item do checklist se liga ao programa.

**Trilha**: GERAL, VISTOS, VIP, ON ("Primeiro contato"). Agrupa as etapas por tipo de trabalho. O serviço contratado gera os procedimentos no ERP; aqui a trilha serve para organizar as filas.

**Etapa (catálogo)**: lista ordenada de procedimentos de cada trilha, com as orientações operacionais (prazo de referência, o que é, importância, quando cabe NEG, link de gravação). A carga inicial está em `app/catalogo_inicial.py` (`flask catalogo carregar`, idempotente). O catálogo NÃO gera tarefas: quem cria é a importação. Cada etapa tem apelidos (textos que apontam para ela). Procedimento novo que aparecer no CSV entra sozinho no catálogo, marcado para revisão.

**Tarefa**: é um item do checklist do ERP (uma linha do CSV, chave `#` guardada em `item_checklist_erp`). Pertence a um programa e a uma compra. Quem cria as tarefas é o CSV, não o catálogo.

O responsável é da tarefa, não do aluno. Por padrão ele segue o consultor do programa; se alguém trocar à mão (`responsavel_manual_id`), a troca fica e a importação não desfaz.

Status: A fazer, Em andamento, Aguardando aluno, Concluída, Não se aplica.

**Serviço**: classificação editável dos serviços do ERP (`ServicoCatalogo`). Curso é um programa e precisa estar na base; Visto pode vir sozinho (programa "só de visto"); Avulso (transfer, seguro) vai junto de um programa; Ignorado não gera tarefa nem aviso.

## Duas datas

- **Data do procedimento** (`prazo_erp`): fixa, vem do CSV. É por ela que se conta o atraso e que a NEG vira justificativa.
- **Data planejada** (`data_planejada`): quando o consultor vai fazer. Vazia = igual à do procedimento. Ordena as filas, alimenta o filtro "Data de/até" e posiciona a tarefa no calendário, onde dá para arrastar para outro dia. Nunca muda o atraso. Planejada depois da data do procedimento gera aviso ("provavelmente vai precisar de NEG").

`Tarefa.data_prevista` = planejada ou procedimento.

## Fonte de dados: o relatório de checklist (CSV)

O checklist é a importação principal: alimenta alunos, programas, tarefas e a base do painel RSA ao mesmo tempo.

Regras gerais:
- A correspondência é **sempre por ID** (`aluno_id_erp`, `programa_id_erp`, `compra_id_erp`, `item_checklist_erp`), nunca por nome.
- O aluno vem do ID Aluno; o programa é um por aluno, com todas as compras dele. Só compras de visto: "só de visto"; chegou compra de curso, vira normal.
- Cadastro do programa: a cada importação, com o valor que mais aparece nas linhas do aluno (consultor, embarque, visto, país, cidade, escola, grupo). Serviços se acumulam. Campo vazio não apaga o gravado.
- Status: "Finalizado" ou Data da Finalização preenchida = tarefa concluída (se não existia, entra já concluída, fora das filas). Status com "cancel" = encerrada como cancelada. O resto está em aberto.
- VIP: procedimento `SA - VIP - ...` ou tag `VIP` (`Programa.vip_erp`).
- A importação nunca sobrescreve o trabalho feito aqui: status, responsável alterado manualmente, datas planejadas e anotações.
- Rodar a mesma importação duas vezes não duplica nada (idempotência). O arquivo é reconhecido pelo hash.
- Antes de gravar, mostra uma **prévia** com o resumo para confirmação; confirmar recalcula e confere que os números não mudaram.

Ciclo de vida do item:
- Item novo no CSV: cria a tarefa.
- Item que some do CSV: foi finalizado ou cancelado no ERP. A tarefa vira Concluída, com `encerrada_erp_em` e motivo (cancelado se a compra ou o programa saiu; senão finalizado).
- Enquanto o CSV for exportado por período, o sumiço só vale para itens com prazo dentro do período da importação. Exportação sem filtro de período (`--completo`) encerra tudo o que ficou para trás.
- Item que reaparece: a tarefa é reaberta.
- Tarefas fora do período não são encerradas sozinhas: na página da importação mais recente, o administrador marca e encerra à mão. Só vêm pré-marcadas as de prazo antes do início do período; as de prazo depois do fim vêm desmarcadas, com aviso.

Compras do CSV que não estão em nenhum programa:
- Visto ou avulso, e o aluno tem programa: a compra é juntada a esse programa (`origem = checklist`).
- Visto, e o aluno não tem programa: aluno só de visto (não é erro). Cria um "programa só de visto", sem `programa_id_erp`, com o consultor do CSV.
- Aluno com 2 ou mais programas: aviso para escolher à mão.
- Serviço não classificado: a compra entra com aviso, e os itens dela ficam de fora até alguém classificar.

Erros e avisos nunca são descartados em silêncio: ficam registrados em `OcorrenciaImportacao`, com gravidade, linha e mensagem, e aparecem na prévia e no detalhe da importação.

## NEG e anotações

- **NEG** é a observação registrada no sistema ERP, pelo botão do procedimento. Costuma ser a justificativa de um atraso. Guardada em `Tarefa.obs_erp`, mostrada como "Observação do sistema ERP", separada das anotações internas. A reimportação atualiza esse campo, mas nunca toca nas anotações daqui.
- **Anotação** (`Anotacao`) é interna deste sistema: lembretes e contexto do caso, com autor e data. Aparece embaixo da NEG nas filas; o "+ observação" permite anotar sem sair da fila.
- Justificativa de atraso é **só** a NEG. Anotação não conta.
- `app/texto.py:separar_neg()` quebra a NEG (várias observações coladas, cada uma terminando em "(Nome, dd-mm-aaaa, HHhMM)") para mostrar uma por linha.
- Tela "Para lançar no ERP" (`/para-lancar`, com contador na barra lateral): o que foi feito aqui e ainda precisa ser baixado lá.
  - Procedimentos concluídos ou "não se aplica" aqui, ainda abertos no CSV: a pessoa lança no ERP e clica em "Lancei no ERP" (`Tarefa.lancada_erp_em`).
  - Anotações deste sistema: "Lancei como NEG" ou "Não precisa" (`Anotacao.lancada_erp_em` / `nao_precisa_lancar`).
  - Confirmação: quando o item some do CSV, sai da lista. Se uma importação posterior ainda traz o item, ele vai para "Marcadas como lançadas, mas ainda abertas no ERP".
  - Reabrir a tarefa desfaz o "lancei".

## Visões obrigatórias

- Por consultor
- Fila por status (a fila de trabalho da equipe)
- "Minha fila": tarefas em que o usuário logado é o responsável

Visualizações de fila (`app/templates/filas/`): Lista, Kanban (colunas por status; arrastar muda o status via POST com `X-Requested-With: fetch`), Quadro por aluno (um cartão por programa, o mais urgente primeiro) e Calendário (semanas de segunda a domingo; arrastar muda a data planejada). A escolha fica em `usuario.visao_fila`; links com `fixar=0` abrem outra visão sem trocar a preferida.

"Organizar por" (`consultas.Organizar`): na lista, agrupa por data prevista, procedimento, tipo de visto, embarque, responsável ou status; no quadro, ordena os alunos. A escolha fica em `usuario.organizar_lista` / `organizar_quadro`.

## Andamento até o embarque

Na página do programa aparece a % de procedimentos finalizados. Clicar abre a lista simples, com ✓ finalizado, ● em aberto e ○ ainda não criado. A regra está em `app/andamento.py`.

O ERP cria os procedimentos aos poucos, e o sistema só vê o que estava em aberto nas importações. Por isso a conta é uma estimativa, com o catálogo como roteiro:
- Procedimento sem tarefa conta como finalizado se vem antes do primeiro em aberto da trilha; se vem depois, conta como pendente ("ainda não criado pelo ERP"). Quem já embarcou tem finalizado tudo o que não está em aberto.
- Procedimentos que só valem para parte dos alunos ficam em `SO_PARA_ALGUNS` (ex.: CAQ só para visto Canadá-Quebec; teste de nivelamento, só quando o ERP cria a tarefa).

## Público teen

A equipe de Teens é separada do Suporte, mas usa as mesmas estruturas no ERP. Os alunos teen NÃO são excluídos: ficam marcados (`Aluno.teen`, `teen_motivo`) e as filas têm o filtro "Público" (Todos / Suporte / Teen).

É teen o aluno inteiro que tiver, em qualquer programa ou compra: um serviço marcado como teen (padrão: Summer Schools, Winter Schools, Viagem Cultural, Vancouver Experience), a tag `summer` ou um consultor da equipe teen. Serviços e consultores teen são editáveis em Administração → Público teen; a marca é recalculada em `app/publico_teen.py:recalcular()` a cada importação e a cada alteração na tela.

## Painel Executivo e RSA

- **Painel Executivo** (`app/painel_executivo.py`): o painel HTML de arquivo único (enviado pelo administrador, guardado em `instance/painel_executivo/`) ganha um grupo extra com as tarefas abertas deste sistema. Tudo o que o sistema insere fica entre marcadores, então gerar de novo não duplica nada e é possível voltar ao original. O grupo leva só dados agregados: nenhum nome ou ID de aluno.
- **RSA** (`app/rsa.py`): dashboard HTML de arquivo único, servido num iframe com sandbox de origem opaca (sem `allow-same-origin`: o arquivo enviado nunca acessa cookies, DOM ou rotas do CRM). Os dados vêm do relatório de checklist do ano; o HTML guardado funciona como layout.

## Estrutura do código

- `app/models/`: modelo do banco. IDs do ERP em texto, enums como texto + CHECK, nomes de constraints fixos: pronto para Postgres.
- `migrations/`: Alembic. Depois de mudar um modelo: `flask db migrate -m "..."` e revisar o arquivo gerado. O `env.py` desliga as chaves estrangeiras do SQLite durante a migração e confere as referências no fim. `tests/test_migracoes.py` roda todas as migrações num banco com dados: não apagar.
- `app/importacao/`: fluxo prévia → confirmação com coletor de erros e avisos; leitores de CSV e Excel; `valores.py` (IDs, datas, números); `consultores.py` (nome → usuário, com apelidos editáveis pela interface).
- `app/cli.py`: comandos de instalação e teste (`flask importar checklist ARQUIVO [--de/--ate | --completo]`, `flask usuarios adicionar/listar/apelido`, `flask seed-demo`, `flask backup`, `flask diagnostico`). O dia a dia é pelas telas.
- `app/consultas.py`: regras das filas (na fila, responsável, prazo, atrasada com/sem justificativa) e o resumo por consultor.
- `app/acoes_tarefa.py`: o que a equipe faz na tarefa (status, responsável, prazo, anotação, lançamento no ERP), sempre com histórico em `HistoricoTarefa`.
- `app/web/` + `app/templates/` + `app/static/estilo.css`: telas (Flask blueprints), sem framework de JavaScript. Todo POST exige o token CSRF. Importar arquivos e mexer nos cadastros: só papel admin. Filas, tarefas e busca: todos.
- Em templates, não usar `pagina` como variável no `base.html`/includes: é o número da página da paginação.
- `app/seed_demo.py`: dados de demonstração fictícios para o `flask seed-demo` (idempotente).
- `tests/`: pytest. Só dados fictícios.

## Como rodar (desenvolvimento)

```bash
python3 -m pip install -r requirements.txt
flask --app wsgi db upgrade
flask --app wsgi catalogo carregar
flask --app wsgi seed-demo          # opcional: banco de demonstração
flask --app wsgi run                # http://localhost:5000
```

Ou `docker compose up --build` para o ambiente completo (migração automática, gunicorn na 8080).

- Datas gravadas em UTC; para mostrar, usar `hora_local()` de `app/models/base.py`.
- `servidor.py`: servidor de produção (waitress), com reinício automático e log em `<dados>/logs`. Recusa subir com a SECRET_KEY padrão ou login provisório sem SENHA_PROVISORIA.
- Configuração: padrões em `create_app`, depois `<dados>/config.py`, depois o dicionário de teste. A pasta de dados é `CHECKLIST_DADOS`; sem ela, `instance/`.
- O acesso externo deve passar por proxy reverso com HTTPS (Nginx, Caddy, Traefik); `ATRAS_DE_PROXY=1` liga o ProxyFix, os cookies seguros e o HSTS.

## Regras inegociáveis (resumo)

1. Correspondência sempre por ID, nunca por nome.
2. A importação nunca sobrescreve o trabalho da equipe (status, responsável manual, data planejada, anotações).
3. Prévia obrigatória e idempotência em toda importação.
4. NEG (do ERP) separada das anotações internas; só a NEG é justificativa formal.
5. O atraso é sempre pela data do procedimento (`prazo_erp`), nunca pela planejada.
6. Interface em português claro, sem jargão técnico.
7. Nunca versionar dados reais de alunos ou colaboradores; testes usam exclusivamente dados fictícios.
