# Lógica, Arquitetura e Regras de Negócio: Módulo de Pautas TM

Este documento descreve a lógica de negócio, a modelagem de dados, as regras de SLA e a integração das **Pautas de Comunicação Interna** dentro da aplicação **CRM Operacional**.

---

## 1. Visão Geral e Contexto de Negócio

### O que são as Pautas?
As **Pautas** são os protocolos e chamados formais de comunicação interna entre a equipe de ponta — o **Suporte ao Aluno** — e todos os setores operacionais da empresa:

- **Acomodação** (casas de estudantes, albergues, residências, homestays);
- **Vistos e Aplicações** (assessoria consular, documentação);
- **Aéreo e Reembolsos** (emissão de bilhetes, alterações de trecho, cancelamentos, estornos);
- **Matrículas e Operações de Curso** (confirmação com escolas parceiras);
- **Financeiro** (boletos, baixas, pagamentos e fornecedores);
- **Comercial e Diretoria** (exceções contratuais, negociações especiais).

### O Papel do CRM Operacional
Historicamente, o acompanhamento das pautas dependia da inspeção manual página por página no sistema corporativo (TM) ou de planilhas locais manuais (`Auxiliar!A:B`). O CRM centraliza essas pautas em um painel unificado que:
1. **Calcula SLAs dinâmicos** para cada categoria de chamado;
2. **Segmenta a visualização por consultor** da unidade (responsável, criador ou vinculado ao aluno);
3. **Identifica pendências ativas** (de quem é a vez de responder);
4. **Alerta quebras de prazo de 72h+** com distinção clara entre atrasos internos da unidade e atrasos dos outros setores;
5. **Permite anotações e observações internas** sem perigo de perda em futuras sincronizações da base do TM.

---

### Escopo atual de identificação

A configuração operacional cobre a **unidade local** (nome definido em `NOME_UNIDADE`, padrão "Unidade Matriz"). O CRM identifica automaticamente como membro da unidade qualquer nome do TM que corresponda a um usuário ativo do sistema ou a um nome informado em `PAUTAS_MEMBROS_UNIDADE`. Não é necessário cadastrar novamente esses nomes em `ColaboradorSetor`.

Para pessoas de outros setores, o sistema só consegue exibir o setor correto depois que o nome for relacionado ao departamento no cadastro administrativo de pautas. Enquanto não houver esse relacionamento, a pessoa é classificada como **Outro Setor**. A identificação detalhada de setores externos é opcional neste momento.

## 2. O Princípio Operacional do TM: "Salvar = Atualizar"

Uma particularidade essencial do sistema TM é a mecânica de atualização:
> **"Toda ação de comunicação ou alteração de status no TM exige clicar no botão 'Salvar'."**

Isso implica que:
- Quando um consultor da nossa unidade ou um atendente de outro setor responde uma pauta, o sistema corporativo atualiza imediatamente:
  - `Atualizado em` (data e hora da última ação);
  - `Atualizado por` (nome de quem salvou);
  - `Tempo de Inatividade` (é zerado e reinicia a contagem).
- Se o status muda de "Em aberto" para "Aguardando retorno...", isso também conta como um evento de atualização salvo.

### Como o CRM interpreta isso?
O CRM analisa o par (`Atualizado por`, `Responsável`):
- Se `Atualizado por` pertence à **nossa unidade**: a bola foi passada para o outro setor ou para o aluno.
- Se `Atualizado por` pertence a um **setor externo** e o `Responsável` é alguém da **nossa unidade**: a bola voltou para nós respondermos!

---

## 3. Mapeamento de Unidades e Setores

### Substituição da Planilha `Auxiliar!A:B`
No formato de planilha manual, existia uma aba auxiliar mapeando cada colaborador ao seu respectivo setor. No CRM, a identificação usa os nomes que vêm no arquivo do TM:
1. **Nossa unidade:** são os registros da tabela `Usuario` com `ativo = True`; se ainda não houver usuários cadastrados, são usados os nomes de `PAUTAS_MEMBROS_UNIDADE`. Quando o nome de quem abriu, atualizou ou é responsável bate com essa lista, o sistema atribui o nome da unidade (ex.: `Unidade Matriz`).
2. **Setores externos:** podem ser registrados na tabela `ColaboradorSetor`, gerenciável em `/cadastros/pautas`. O cadastro deve usar o nome como aparece no TM e o setor correspondente. Sem esse cadastro, o resultado é **`Outro Setor`**.

### Qual setor abriu e qual setor é responsável?

A importação preserva separadamente os nomes e calcula o setor de cada papel. A origem é o próprio arquivo exportado pelo TM:

| Campo Calculado | O que Representa | Como é Determinado |
| :--- | :--- | :--- |
| **`UN Atualizou`** | Setor de quem realizou o último salvamento no TM | Lê `Atualizado por` e procura primeiro na nossa unidade; depois em `ColaboradorSetor`; se não encontrar, usa `Outro Setor`. |
| **`UN Responsável`** | Setor da pessoa que tem o encargo formal de resolver a pauta | Lê `Responsável` e aplica a mesma identificação. Este é o campo usado para decidir de quem é a ação e onde ocorre a quebra de 72h. |
| **`UN Criou`** | Setor de quem abriu/criou a pauta | Lê `Criada por` e aplica a mesma identificação. Assim é possível saber se a solicitação teve origem na nossa unidade ou em outro setor. |
| **`UN Final`** | Resumo da responsabilidade e da origem | Combina `UN Responsável` e `UN Criou` quando forem diferentes; caso contrário, mostra apenas o setor identificado. |

Os nomes originais continuam disponíveis em `Responsável`, `Criada por` e `Atualizado por`. Portanto, "setor que abriu" não é inferido pelo título da pauta ou pelo nome do aluno: é calculado exclusivamente a partir de `Criada por`. Da mesma forma, o setor responsável vem exclusivamente de `Responsável`.

### Configuração necessária

1. Cadastre em **Cadastros > Usuários** todos os membros atuais da unidade e mantenha-os ativos. O nome deve corresponder ao nome exibido pelo TM; a comparação ignora maiúsculas, minúsculas e acentos.
2. Caso a unidade ainda não tenha usuários cadastrados, informe os nomes em `PAUTAS_MEMBROS_UNIDADE` na configuração do ambiente. Essa é uma alternativa de identificação, não uma lista de setores externos.
3. Faça a importação do CSV ou MHTML do TM. A cada importação, o sistema recalcula `UN Criou`, `UN Responsável` e `UN Atualizou`.
4. Cadastre em `/cadastros/pautas` somente os colaboradores externos que precisarem ser distinguidos por setor.

Uma alteração de usuário, da variável de configuração ou do mapeamento externo passa a valer na próxima importação. Pautas já existentes recebem os novos indicadores sem perder observações, anotações ou atribuições internas.

---

## 4. Regras de Prazos, SLA e Quebra de 72h+ ("Quebrou")

### Catálogo de SLAs por Categoria
O sistema lê a tabela de prazos por categoria (`app/dados/pautas_sla.csv`, só `categoria;horas`; para atualizar sem mexer no código, ponha um `pautas_sla.csv` no mesmo formato na pasta de dados), que define o prazo nominal de resposta em horas para cada assunto (ex.: 24h, 48h, 72h).

### Categorização de Atrasos:
1. **Dentro do Prazo:** tempo de inatividade menor ou igual ao SLA da categoria.
2. **Atrasada (`TAG: Atrasada`):** pauta sem movimentação cujo tempo inativo ultrapassou o SLA nominal.
3. **Quebrou (`72h+`):** pauta que permaneceu inativa por mais de 72 horas além do limite aceitável.

### A Regra de Ouro da Quebra de 72h:
> **"A pauta quebra estritamente para o setor do `UN Responsável`."**

- **💥 Quebra UN (72h+ na unidade):** ocorre quando `UN Responsável` é a nossa unidade e o chamado está há mais de 72 horas parado. Representa **risco operacional direto** para a equipe, exigindo ação imediata do consultor.
- **⚠️ Quebra Outro (72h+ Outro Setor):** ocorre quando `UN Responsável` é um setor externo (ex.: Acomodação ou Vistos) e o chamado passou de 72h sem retorno deles. Representa um chamado travado no parceiro interno, exigindo que o consultor cobre o setor responsável.

---

## 5. Os 4 Estágios do Pipeline (Visão em Etapas)

O CRM oferece duas visualizações: a **Tabela Detalhada** (para conferência e filtros rápidos) e o **Pipeline por Etapas** (organização visual de fluxo de trabalho):

### 1️⃣ Em Aberto
- **Definição:** pautas recém-abertas no TM ou que ainda não tiveram atendimento inicial.
- **Foco:** triagem, conferência de dados e encaminhamento ao setor de destino.

### 2️⃣ Em Análise / Triagem
- **Definição:** pautas com status corporativos ativos como *"Em aberto"*, *"Em andamento"*, *"Pendente"*.
- **Foco:** acompanhamento do trabalho técnico executado pelo setor especialista.

### 3️⃣ Aguardando Retorno (O Estágio Crítico)
Quando o status no TM é *"Aguardando retorno do aluno/fornecedor"*, o CRM desmembra a situação em **3 sub-estados inteligentes**:
- **🚨 Ação Pendente da UN:** o chamado é de nossa responsabilidade (`UN Responsável` = nossa unidade), mas a última atualização veio de fora. Significa que o aluno ou fornecedor respondeu e nós precisamos dar andamento!
- **👤 Aguardando Nosso Aluno:** a responsabilidade é nossa, mas fomos nós que atualizamos/salvamos por último. Estamos esperando o aluno responder às orientações ou enviar documentos.
- **🏢 Aguardando Outro Setor:** o chamado está com setor externo; estamos apenas monitorando para garantir cumprimento do prazo.

### 4️⃣ Concluídas / Arquivadas
- **Definição:** pautas finalizadas, resolvidas ou canceladas no TM (ou marcadas como finalizadas pela equipe aqui).
- **Armazenamento:** mantidas com status inativo no banco de dados para fins de histórico e auditoria.

---

## 6. Persistência de Dados e Estratégia de Upsert Seguro

### O Desafio da Reimportação
Como os dados do TM são exportados periodicamente via CSV (`pautaList-*.csv`) ou MHTML, o sistema **NÃO pode** simplesmente limpar a tabela e inserir de novo, pois isso apagaria anotações internas da equipe.

### A Estrutura dos Modelos SQLAlchemy
1. **`Pauta` (`app/models/pautas.py`):**
   - Chave primária: `id` (o ID numérico oficial do chamado no TM, ex.: `910001`).
   - Campos do TM: atualizados a cada importação (`status_tm`, `atualizado_por_tm`, `atualizado_em_tm`, `tag`, `tempo_inativo_horas`, etc.).
   - Campos internos da unidade: **permanentes e intocáveis pela importação** (`observacao`, `observacao_atualizada_em`, `consultor_id`, `estado_interno`).
   - Flag de arquivamento: `ativa` (booleano) e `encerrada_em` (data).
2. **`PautaAnotacao`:** histórico de notas adicionadas por usuários internos, com registro de autor e data/hora.
3. **`ColaboradorSetor`:** tabela de suporte com o catálogo de pessoas externas e seus respectivos departamentos.

### Algoritmo de Sincronização (`sincronizar_pautas_no_banco`):
```mermaid
flowchart TD
    A[Arquivo CSV / MHTML do TM] --> B[Parser e Extração de Linhas]
    B --> C[Cálculo de SLA e Regras de Unidade]
    C --> D{Pauta já existe no Banco?}
    D -- Sim --> E[Atualiza Dados do TM\nPreserva Observação Interna]
    D -- Não --> F[Cria Nova Pauta no SQLite]
    E --> G[Verifica Pautas Ausentes]
    F --> G
    G --> H[Marca Ausentes como\nativa=False e encerrada_em=agora]
    H --> I[Commit no Banco SQLite]
```

---

## 7. Painel Administrativo de Configuração (`/cadastros/pautas`)

### Por que esta tela existe?
Pessoas entram e saem da empresa, e outras mudam de departamento constantemente. Em vez de exigir que desenvolvedores alterem o código-fonte, o painel administrativo em `/cadastros/pautas` permite:
1. **Adicionar/Editar Setores:** vincular livremente um nome de colaborador ao seu setor.
2. **Sugestões Inteligentes de Colaboradores:** o sistema analisa as pautas recém-importadas e detecta automaticamente colaboradores externos que ainda não possuem setor cadastrado, exibindo um botão de preenchimento automático.
3. **Consistência Imediata:** ao cadastrar o setor de alguém, todas as métricas de `UN Responsável` e quebras de 72h passam a considerar a classificação instantaneamente.

---

## 8. Dados de Demonstração

O comando `flask seed-demo` cria seis pautas fictícias cobrindo os estados internos (`acao`, `aguardando`, `acompanhamento`, `finalizada`), incluindo um caso com quebra de 72h na própria unidade e outro com quebra em setor externo, cada uma com observação e anotação interna. Os IDs de demonstração (910001–910006) nunca colidem com IDs reais do TM.

---

## 9. Resumo das Rotas e Endpoints

| Rota | Método | Função |
| :--- | :--- | :--- |
| `/pautas/` | GET | Painel principal com alternância entre Pipeline (Etapas) e Tabela, filtros por consultor e busca. |
| `/pautas/<id>` | GET | Detalhe da pauta com histórico de estados e anotações. |
| `/pautas/<id>/estado` | POST | Muda o estado interno (drag-and-drop no pipeline ou formulário). |
| `/pautas/<id>/observacao` | POST | Endpoint AJAX para edição rápida de anotações internas inline. |
| `/pautas/enviar` | POST | Recebe novos arquivos `.csv` ou `.mhtml` exportados do TM e executa a sincronização com upsert seguro. |
| `/pautas/exportar-json` | GET | Exporta as pautas filtradas em JSON para relatórios externos ou integrações. |
| `/cadastros/pautas` | GET/POST | Administração do mapeamento de colaboradores e setores (`ColaboradorSetor`). |
