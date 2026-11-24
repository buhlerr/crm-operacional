"""Dados de demonstração para o `flask seed-demo`.

Cria um banco pronto para explorar as telas sem nenhum dado real: usuários com
senha conhecida, alunos claramente fictícios, programas, tarefas em todos os
status, pautas internas e importações confirmadas no histórico. Tudo é sintético
(IDs com prefixo DEMO-, e-mails @exemplo.com, nomes comuns de exemplo).

A criação é idempotente: cada registro é procurado pela sua chave externa antes
de ser criado, então rodar o comando de novo não duplica nada nem sobrescreve
o que já existe (nem senhas trocadas, nem anotações da equipe).
"""

from datetime import date, timedelta
from decimal import Decimal

from flask import current_app

from app.extensions import db
from app.models import (
    Aluno,
    Anotacao,
    Compra,
    Gravidade,
    Importacao,
    MotivoEncerramento,
    OcorrenciaImportacao,
    OrigemCompra,
    Papel,
    Pauta,
    PautaAnotacao,
    Programa,
    SituacaoImportacao,
    SituacaoPrograma,
    StatusTarefa,
    Tarefa,
    TipoImportacao,
    TipoOcorrencia,
    TipoPrograma,
    Usuario,
)
from app.models.base import agora
from app.models.pautas import nome_unidade

SENHA_DEMO = "Demo@123456"

# (nome, e-mail, papel)
USUARIOS_DEMO = (
    ("Administrador Demo", "admin@exemplo.com", Papel.ADMIN),
    ("Ana Souza", "ana.souza@exemplo.com", Papel.CONSULTOR),
    ("Carlos Lima", "carlos.lima@exemplo.com", Papel.CONSULTOR),
    ("Júlia Prado", "estagio@exemplo.com", Papel.ESTAGIARIO),
)

# E-mails das contas de exemplo criadas por este seed. No modo demonstração
# (MODO_DEMO=1) elas ficam protegidas: a senha, o e-mail, o papel e o ativo
# não podem ser alterados pela interface, para o acesso público nunca se perder.
EMAILS_DEMO = frozenset(email for _nome, email, _papel in USUARIOS_DEMO)


def conta_demo_protegida(usuario: Usuario) -> bool:
    """True quando o modo demonstração está ligado e o usuário é uma conta de exemplo."""
    return bool(current_app.config.get("MODO_DEMO") and (usuario.email or "").lower() in EMAILS_DEMO)


# (id no ERP, nome)
ALUNOS_DEMO = (
    ("DEMO-A001", "Lucas Ferreira"),
    ("DEMO-A002", "Marina Costa"),
    ("DEMO-A003", "Pedro Henrique Alves"),
    ("DEMO-A004", "Sofia Nakamura"),
    ("DEMO-A005", "Rafael Duarte"),
    ("DEMO-A006", "Beatriz Camargo"),
    ("DEMO-A007", "Gustavo Peixoto"),
    ("DEMO-A008", "Helena Vieira"),
)

# Turma extra (DEMO-A009..DEMO-A024): volume e variedade para as filas, o calendário
# e os relatórios. Cada linha cria um aluno, um programa e suas compras; as tarefas
# vêm na tabela TAREFAS_EXTRA abaixo. Nomes, escolas e cidades são fictícios.
# (aluno, nome, programa_id, tipo, visto, país, cidade, escola, acomodação,
#  pontuação, serviços do ERP, dias até o embarque, vip, consultor, compras)
_TURMA_EXTRA = (
    ("DEMO-A009", "Bruno Martins", "DEMO-P009", TipoPrograma.NORMAL, "Visto - Canadá - eTA", "Canadá",
     "Vancouver", "Vancouver Language Institute", "Homestay", Decimal("78"), "Curso Premium, Seguro Viagem",
     55, False, "ana", (("DEMO-C011", "Curso Premium", OrigemCompra.PLANILHA),
                        ("DEMO-C012", "Seguro Viagem", OrigemCompra.CHECKLIST))),
    ("DEMO-A010", "Camila Rocha", "DEMO-P010", TipoPrograma.NORMAL, "Visto - Irlanda - Estudante", "Irlanda",
     "Dublin", "Dublin Language Workshop", "Apartamento compartilhado", Decimal("45"), "Curso Smart, Transfer (chegada e saída)",
     75, False, "carlos", (("DEMO-C013", "Curso Smart", OrigemCompra.PLANILHA),
                           ("DEMO-C014", "Transfer (chegada e saída)", OrigemCompra.CHECKLIST))),
    ("DEMO-A011", "Diego Fontana", None, TipoPrograma.SO_VISTO, "Visto - Estados Unidos", "Estados Unidos",
     None, None, None, None, "Visto - Estados Unidos", 100, False, "carlos",
     (("DEMO-C015", "Visto - Estados Unidos", OrigemCompra.CHECKLIST),)),
    ("DEMO-A012", "Elisa Cardoso", "DEMO-P012", TipoPrograma.NORMAL, None, "Malta",
     "St. Julian's", "St. Julian's Institute of English", "Residência estudantil", Decimal("25"), "Curso Budget",
     25, False, "ana", (("DEMO-C016", "Curso Budget", OrigemCompra.PLANILHA),)),
    ("DEMO-A013", "Felipe Aguiar", None, TipoPrograma.SO_VISTO, "Visto - Canadá - eTA", "Canadá",
     None, None, None, None, "Visto - Canadá - eTA", 120, False, "ana",
     (("DEMO-C017", "Visto - Canadá - eTA", OrigemCompra.CHECKLIST),)),
    ("DEMO-A014", "Gabriela Menezes", "DEMO-P014", TipoPrograma.NORMAL, "Visto - Nova Zelândia - Estudante", "Nova Zelândia",
     "Wellington", "Wellington English Academy", "Homestay", Decimal("62"), "Curso + Trabalho",
     120, False, "carlos", (("DEMO-C018", "Curso + Trabalho", OrigemCompra.PLANILHA),)),
    ("DEMO-A015", "Henrique Salles", "DEMO-P015", TipoPrograma.NORMAL, "Visto - Austrália - Estudante", "Austrália",
     "Brisbane", "Brisbane Institute of English", "Apartamento compartilhado", Decimal("50"), "Curso Smart, Seguro Viagem",
     180, False, "ana", (("DEMO-C019", "Curso Smart", OrigemCompra.PLANILHA),
                         ("DEMO-C020", "Seguro Viagem", OrigemCompra.CHECKLIST))),
    ("DEMO-A016", "Isabela Freitas", None, TipoPrograma.SO_VISTO, "Visto - Estados Unidos", "Estados Unidos",
     None, None, None, None, "Visto - Estados Unidos", 90, False, "ana",
     (("DEMO-C021", "Visto - Estados Unidos", OrigemCompra.CHECKLIST),)),
    ("DEMO-A017", "João Batista Ribeiro", "DEMO-P017", TipoPrograma.NORMAL, "Visto - Irlanda - Estudante", "Irlanda",
     "Dublin", "Dublin Riverside College", "Apartamento compartilhado", Decimal("90"), "Curso Premium, Seguro Viagem",
     200, True, "ana", (("DEMO-C022", "Curso Premium", OrigemCompra.PLANILHA),
                        ("DEMO-C023", "Seguro Viagem", OrigemCompra.CHECKLIST))),
    ("DEMO-A018", "Karina Almeida", "DEMO-P018", TipoPrograma.NORMAL, "Visto - Canadá - Estudante", "Canadá",
     "Ottawa", "Ottawa River College", "Homestay", Decimal("35"), "Curso Smart, Seguro Viagem",
     85, False, "carlos", (("DEMO-C024", "Curso Smart", OrigemCompra.PLANILHA),
                           ("DEMO-C025", "Seguro Viagem", OrigemCompra.CHECKLIST))),
    ("DEMO-A019", "Leonardo Pires", "DEMO-P019", TipoPrograma.NORMAL, None, "Malta",
     "St. Paul's Bay", "Bayview English School", "Residência estudantil", Decimal("20"), "Curso Budget",
     40, False, "ana", (("DEMO-C026", "Curso Budget", OrigemCompra.PLANILHA),)),
    ("DEMO-A020", "Larissa Nunes", None, TipoPrograma.SO_VISTO, "Visto - Canadá - eTA", "Canadá",
     None, None, None, None, "Visto - Canadá - eTA", 110, False, "carlos",
     (("DEMO-C027", "Visto - Canadá - eTA", OrigemCompra.CHECKLIST),)),
    ("DEMO-A021", "Matheus Teixeira", "DEMO-P021", TipoPrograma.NORMAL, "Visto - Nova Zelândia - Estudante", "Nova Zelândia",
     "Auckland", "Auckland City Learning Centre", "Homestay", Decimal("48"), "Grupo Premium",
     95, False, "ana", (("DEMO-C028", "Grupo Premium", OrigemCompra.PLANILHA),)),
    ("DEMO-A022", "Natalia Prado", "DEMO-P022", TipoPrograma.NORMAL, "Visto - Irlanda - Estudante", "Irlanda",
     "Cork", "Cork Language Studio", "Homestay", Decimal("58"), "Curso Smart, Transfer (chegada e saída)",
     33, False, "carlos", (("DEMO-C029", "Curso Smart", OrigemCompra.PLANILHA),
                           ("DEMO-C030", "Transfer (chegada e saída)", OrigemCompra.CHECKLIST))),
    ("DEMO-A023", "Rafaela Simões", "DEMO-P023", TipoPrograma.NORMAL, "Visto - Estados Unidos", "Estados Unidos",
     "Boston", "Boston Language House", "Homestay", Decimal("70"), "Curso + Trabalho, Seguro Viagem",
     140, False, "ana", (("DEMO-C031", "Curso + Trabalho", OrigemCompra.PLANILHA),
                         ("DEMO-C032", "Seguro Viagem", OrigemCompra.CHECKLIST))),
    ("DEMO-A024", "Thiago Barbosa", None, TipoPrograma.SO_VISTO, "Visto - Estados Unidos", "Estados Unidos",
     None, None, None, None, "Visto - Estados Unidos", 60, False, "carlos",
     (("DEMO-C033", "Visto - Estados Unidos", OrigemCompra.CHECKLIST),)),
)

# Tarefas da turma extra (DEMO-T019..DEMO-T054), de hoje-14 a hoje+35 dias.
# Cada linha é um dicionário: item, aluno, serviço da compra, procedimento (texto do
# catálogo), prazo em dias a partir de hoje e, quando vale, status (padrão A fazer),
# planejada (dias), neg=(autor, dias, hora, texto), concluida (dias atrás),
# lancada (dias atrás), encerrada=(dias atrás, motivo) e anotacao=(texto, do consultor do programa).
_TAREFAS_EXTRA = (
    # Bruno Martins: onboarding em dia, passaporte atrasado com NEG e anotação interna.
    dict(item="DEMO-T019", aluno="DEMO-A009", servico="Curso Premium", prazo=12, planejada=10,
         etapa="SA - GERAL - Realização de Onboarding com novos alunos (pacotes)"),
    dict(item="DEMO-T020", aluno="DEMO-A009", servico="Curso Premium", prazo=-6,
         status=StatusTarefa.AGUARDANDO_ALUNO,
         etapa="SA - GERAL - Ter a cópia do passaporte do aluno",
         neg=("Ana Souza", -5, "10h20", "Passaporte digitalizado com a foto cortada; pedimos outra cópia"),
         anotacao="Aluno prometeu reenviar hoje; conferir amanhã de manhã."),
    dict(item="DEMO-T021", aluno="DEMO-A009", servico="Curso Premium", prazo=25,
         etapa="SA - GERAL - Cadastrar flight details"),
    # Camila Rocha: onboarding planejado e teste de nivelamento adiante.
    dict(item="DEMO-T022", aluno="DEMO-A010", servico="Curso Smart", prazo=9, planejada=7,
         etapa="SA - GERAL - Realização de Onboarding com novos alunos (pacotes)"),
    dict(item="DEMO-T023", aluno="DEMO-A010", servico="Curso Smart", prazo=30, planejada=27,
         etapa="SA - GERAL - Ter confirmação de realização do teste de nivelamento (requisito para embarque)"),
    # Diego Fontana: visto atrasado em andamento com NEG e envio à embaixada adiante.
    dict(item="DEMO-T024", aluno="DEMO-A011", servico="Visto - Estados Unidos", prazo=-3,
         status=StatusTarefa.EM_ANDAMENTO, planejada=1,
         etapa="SA - VISTOS - Ter a primeira versão da carta de intenções e do formulário de visto preenchido",
         neg=("Carlos Lima", -2, "16h05", "Falta o comprovante de residência assinado para fechar o formulário")),
    dict(item="DEMO-T025", aluno="DEMO-A011", servico="Visto - Estados Unidos", prazo=30,
         etapa="SA - VISTOS - Documentação OK ? Envio para embaixada/consulado"),
    # Elisa Cardoso: onboarding concluído ontem, ainda para lançar no ERP.
    dict(item="DEMO-T026", aluno="DEMO-A012", servico="Curso Budget", prazo=-2,
         status=StatusTarefa.CONCLUIDA, concluida=1,
         etapa="SA - GERAL - Realização de Onboarding com novos alunos (pacotes)"),
    dict(item="DEMO-T027", aluno="DEMO-A012", servico="Curso Budget", prazo=18, planejada=15,
         etapa="SA - GERAL - Ter confirmação de realização do teste de nivelamento (requisito para embarque)"),
    # Felipe Aguiar: documentação do visto parada no aluno.
    dict(item="DEMO-T028", aluno="DEMO-A013", servico="Visto - Canadá - eTA", prazo=-10,
         status=StatusTarefa.AGUARDANDO_ALUNO,
         etapa="SA - VISTOS - Entrega da 1a documentação para aplicação do visto",
         neg=("Ana Souza", -8, "09h40", "Formulário devolvido sem assinatura do responsável; reenviado para o aluno")),
    dict(item="DEMO-T029", aluno="DEMO-A013", servico="Visto - Canadá - eTA", prazo=14,
         etapa="SA - VISTOS - Ter uma cópia do visto/negativa"),
    # Gabriela Menezes: a tarefa atrasada mais antiga, sem justificativa.
    dict(item="DEMO-T030", aluno="DEMO-A014", servico="Curso + Trabalho", prazo=8,
         etapa="SA - GERAL - Realização de Onboarding com novos alunos (pacotes)"),
    dict(item="DEMO-T031", aluno="DEMO-A014", servico="Curso + Trabalho", prazo=-14,
         etapa="SA - GERAL - Ter a cópia do passaporte do aluno"),
    dict(item="DEMO-T032", aluno="DEMO-A014", servico="Curso + Trabalho", prazo=35,
         etapa="SA - GERAL - Cadastrar flight details"),
    # Henrique Salles: embarque longe; aluno sem login na área do aluno.
    dict(item="DEMO-T033", aluno="DEMO-A015", servico="Curso Smart", prazo=20, planejada=17,
         etapa="SA - GERAL - Realização de Onboarding com novos alunos (pacotes)"),
    dict(item="DEMO-T034", aluno="DEMO-A015", servico="Curso Smart", prazo=3,
         etapa="SA - ON - Contact student who didn`t login after enrolment"),
    # Isabela Freitas: visto em andamento e cópia pendente já vencida.
    dict(item="DEMO-T035", aluno="DEMO-A016", servico="Visto - Estados Unidos", prazo=5,
         status=StatusTarefa.EM_ANDAMENTO, planejada=2,
         etapa="SA - VISTOS - Ter a primeira versão da carta de intenções e do formulário de visto preenchido"),
    dict(item="DEMO-T036", aluno="DEMO-A016", servico="Visto - Estados Unidos", prazo=-1,
         etapa="SA - VISTOS - Ter uma cópia do visto/negativa"),
    # João Batista Ribeiro: programa VIP com contato parado no aluno.
    dict(item="DEMO-T037", aluno="DEMO-A017", servico="Curso Premium", prazo=-2,
         status=StatusTarefa.AGUARDANDO_ALUNO,
         etapa="SA - VIP - Primeiro contato de relacionamento com aluno",
         neg=("Ana Souza", -1, "15h30", "Aluno em viagem de trabalho; pediu contato por videochamada no retorno")),
    dict(item="DEMO-T038", aluno="DEMO-A017", servico="Curso Premium", prazo=10, planejada=6,
         etapa="SA - GERAL - Realização de Onboarding com novos alunos (pacotes)"),
    # Karina Almeida: onboarding concluído e já lançado no ERP.
    dict(item="DEMO-T039", aluno="DEMO-A018", servico="Curso Smart", prazo=-5,
         status=StatusTarefa.CONCLUIDA, concluida=4, lancada=3,
         etapa="SA - GERAL - Realização de Onboarding com novos alunos (pacotes)"),
    dict(item="DEMO-T040", aluno="DEMO-A018", servico="Curso Smart", prazo=30, planejada=28,
         etapa="SA - GERAL - Ter confirmação de realização do teste de nivelamento (requisito para embarque)"),
    dict(item="DEMO-T041", aluno="DEMO-A018", servico="Curso Smart", prazo=-12,
         status=StatusTarefa.EM_ANDAMENTO,
         etapa="SA - GERAL - Ter a cópia do passaporte do aluno",
         neg=("Carlos Lima", -10, "11h50", "Cópia enviada pelo aplicativo veio sem a página do visto anterior; pedimos o arquivo completo")),
    # Leonardo Pires: flight details em andamento com data planejada.
    dict(item="DEMO-T042", aluno="DEMO-A019", servico="Curso Budget", prazo=6,
         etapa="SA - GERAL - Realização de Onboarding com novos alunos (pacotes)"),
    dict(item="DEMO-T043", aluno="DEMO-A019", servico="Curso Budget", prazo=18,
         status=StatusTarefa.EM_ANDAMENTO, planejada=14,
         etapa="SA - GERAL - Cadastrar flight details"),
    # Larissa Nunes: documentação do visto atrasada com NEG.
    dict(item="DEMO-T044", aluno="DEMO-A020", servico="Visto - Canadá - eTA", prazo=-8,
         status=StatusTarefa.AGUARDANDO_ALUNO,
         etapa="SA - VISTOS - Entrega da 1a documentação para aplicação do visto",
         neg=("Carlos Lima", -7, "14h25", "Tradução do comprovante financeiro em andamento; o resto da documentação está pronto")),
    dict(item="DEMO-T045", aluno="DEMO-A020", servico="Visto - Canadá - eTA", prazo=21,
         etapa="SA - VISTOS - Ter uma cópia do visto/negativa"),
    # Matheus Teixeira: onboarding para esta semana e flight details no limite do período.
    dict(item="DEMO-T046", aluno="DEMO-A021", servico="Grupo Premium", prazo=2, planejada=1,
         etapa="SA - GERAL - Realização de Onboarding com novos alunos (pacotes)"),
    dict(item="DEMO-T047", aluno="DEMO-A021", servico="Grupo Premium", prazo=35,
         etapa="SA - GERAL - Cadastrar flight details"),
    # Natalia Prado: contato pré-embarque concluído (para lançar) e teste com anotação.
    dict(item="DEMO-T048", aluno="DEMO-A022", servico="Curso Smart", prazo=1,
         etapa="SA - GERAL - Realização de Onboarding com novos alunos (pacotes)"),
    dict(item="DEMO-T049", aluno="DEMO-A022", servico="Curso Smart", prazo=23,
         status=StatusTarefa.CONCLUIDA, concluida=1,
         etapa="SA - GERAL - Realizar contato de relacionamento pré - embarque"),
    dict(item="DEMO-T050", aluno="DEMO-A022", servico="Curso Smart", prazo=12,
         status=StatusTarefa.EM_ANDAMENTO, planejada=9,
         etapa="SA - GERAL - Ter confirmação de realização do teste de nivelamento (requisito para embarque)",
         anotacao="Escola liberou o teste online; acompanhar até sexta."),
    # Rafaela Simões: passaporte encerrado pelo ERP e visto a encaminhar.
    dict(item="DEMO-T051", aluno="DEMO-A023", servico="Curso + Trabalho", prazo=-4,
         status=StatusTarefa.CONCLUIDA, concluida=3, encerrada=(2, MotivoEncerramento.FINALIZADO),
         etapa="SA - GERAL - Ter a cópia do passaporte do aluno"),
    dict(item="DEMO-T052", aluno="DEMO-A023", servico="Curso + Trabalho", prazo=28,
         etapa="SA - VISTOS - Documentação OK ? Envio para embaixada/consulado"),
    dict(item="DEMO-T053", aluno="DEMO-A023", servico="Curso + Trabalho", prazo=4,
         etapa="SA - ON - Contact student who didn`t login after enrolment"),
    # Thiago Barbosa: procedimento que não se aplica (já tem visto válido), para lançar.
    dict(item="DEMO-T054", aluno="DEMO-A024", servico="Visto - Estados Unidos", prazo=-14,
         status=StatusTarefa.NAO_SE_APLICA, concluida=2,
         etapa="SA - VISTOS - Documentação OK ? Envio para embaixada/consulado"),
)


def _dia(hoje: date, dias: int) -> date:
    return hoje + timedelta(days=dias)


def _neg(hoje: date, autor: str, dias: int, hora: str, texto: str) -> str:
    """NEG no formato que vem do ERP: texto + (autor, data, hora)."""
    return f"{texto} ({autor}, {_dia(hoje, dias).strftime('%d-%m-%Y')}, {hora})"


def _criar_usuarios(contagem: dict) -> dict[str, Usuario]:
    """Cria (ou reaproveita) os usuários de demonstração. Senha só é definida na criação."""
    usuarios: dict[str, Usuario] = {}
    for nome, email, papel in USUARIOS_DEMO:
        usuario = db.session.execute(db.select(Usuario).filter_by(email=email)).scalar_one_or_none()
        if usuario is None:
            usuario = Usuario(nome=nome, email=email, papel=papel, ativo=True)
            usuario.definir_senha(SENHA_DEMO)
            db.session.add(usuario)
            db.session.flush()
            contagem["usuarios"] += 1
        usuarios[email] = usuario
    return usuarios


def _etapa(texto: str):
    from app.catalogo_inicial import buscar_etapa_por_texto

    etapa = buscar_etapa_por_texto(texto)
    if etapa is None:
        raise ValueError(
            f'Etapa "{texto}" não encontrada no catálogo. Rode "flask catalogo carregar" antes do seed-demo.'
        )
    return etapa


def _tarefa(contagem: dict, **campos) -> Tarefa:
    """Cria a tarefa se o item (#) ainda não existir e devolve a instância."""
    existente = db.session.execute(
        db.select(Tarefa).filter_by(item_checklist_erp=campos["item_checklist_erp"])
    ).scalar_one_or_none()
    if existente:
        return existente
    nova = Tarefa(**campos)
    db.session.add(nova)
    db.session.flush()
    contagem["tarefas"] += 1
    return nova


def _compra(contagem: dict, programa_: Programa, compra_id: str, servico: str, origem: OrigemCompra) -> Compra:
    existente = db.session.execute(db.select(Compra).filter_by(compra_id_erp=compra_id)).scalar_one_or_none()
    if existente:
        return existente
    nova = Compra(compra_id_erp=compra_id, programa_id=programa_.id, servico=servico, origem=origem)
    db.session.add(nova)
    db.session.flush()
    contagem["compras"] += 1
    return nova


def popular_demo() -> dict:
    """Popula o banco com os dados de demonstração. Não cria nada que já exista.

    Deve rodar dentro do contexto da aplicação, depois de `carregar_catalogo()`.
    """
    hoje = date.today()
    contagem = {"usuarios": 0, "alunos": 0, "programas": 0, "compras": 0, "tarefas": 0,
                "anotacoes": 0, "pautas": 0, "anotacoes_pautas": 0, "importacoes": 0}

    usuarios = _criar_usuarios(contagem)
    ana, carlos = usuarios["ana.souza@exemplo.com"], usuarios["carlos.lima@exemplo.com"]
    importacao_atual = _criar_importacoes(contagem, usuarios["admin@exemplo.com"], hoje)

    alunos: dict[str, Aluno] = {}
    for aluno_id, nome in ALUNOS_DEMO:
        aluno = db.session.execute(db.select(Aluno).filter_by(aluno_id_erp=aluno_id)).scalar_one_or_none()
        if aluno is None:
            aluno = Aluno(aluno_id_erp=aluno_id, nome=nome)
            db.session.add(aluno)
            db.session.flush()
            contagem["alunos"] += 1
        alunos[aluno_id] = aluno

    def programa(aluno_id: str, **campos) -> Programa:
        """Programa normal é procurado pelo programa_id_erp; o "só de visto", pelo aluno
        (só pode haver um ativo por aluno)."""
        p = campos.pop("programa_id_erp", None)
        consulta = db.select(Programa).filter_by(aluno_id=alunos[aluno_id].id)
        if p:
            consulta = consulta.filter_by(programa_id_erp=p)
        else:
            consulta = consulta.filter_by(tipo=TipoPrograma.SO_VISTO, situacao=SituacaoPrograma.ATIVO)
        existente = db.session.execute(consulta).scalars().first()
        if existente:
            return existente
        novo = Programa(aluno_id=alunos[aluno_id].id, programa_id_erp=p, **campos)
        db.session.add(novo)
        db.session.flush()
        contagem["programas"] += 1
        return novo

    # ---- Lucas Ferreira: programa normal, uma tarefa atrasada sem justificativa ----
    p1 = programa("DEMO-A001", programa_id_erp="DEMO-P001", tipo=TipoPrograma.NORMAL,
                  consultor_id=ana.id, consultor_texto=ana.nome,
                  mes_embarque=_dia(hoje, 150).replace(day=1), data_embarque=_dia(hoje, 150),
                  visto_normalizado="Visto - Canadá - Estudante", pais="Canadá", cidade="Toronto",
                  escola="Toronto Language School", acomodacao="Homestay", pontuacao=Decimal("55"),
                  servicos_erp="Curso Premium, Seguro Viagem")
    c_curso1 = _compra(contagem, p1, "DEMO-C001", "Curso Premium", OrigemCompra.PLANILHA)
    _compra(contagem, p1, "DEMO-C002", "Seguro Viagem", OrigemCompra.PLANILHA)
    _tarefa(contagem, item_checklist_erp="DEMO-T001", programa_id=p1.id, compra_id=c_curso1.id,
            etapa_id=_etapa("SA - GERAL - Realização de Onboarding com novos alunos (pacotes)").id,
            prazo_erp=_dia(hoje, 10), status=StatusTarefa.A_FAZER, status_erp="Aguardando")
    _tarefa(contagem, item_checklist_erp="DEMO-T002", programa_id=p1.id, compra_id=c_curso1.id,
            etapa_id=_etapa("SA - GERAL - Ter a cópia do passaporte do aluno").id,
            prazo_erp=_dia(hoje, -3), status=StatusTarefa.A_FAZER, status_erp="Aguardando")

    # ---- Marina Costa: público teen (compra de Summer Schools), tarefa atrasada com NEG e
    #      uma concluída aqui que ainda precisa ser lançada no ERP ----
    p2 = programa("DEMO-A002", programa_id_erp="DEMO-P002", tipo=TipoPrograma.NORMAL,
                  consultor_id=carlos.id, consultor_texto=carlos.nome,
                  mes_embarque=_dia(hoje, 60).replace(day=1), data_embarque=_dia(hoje, 60),
                  visto_normalizado="Visto - Canadá - eTA", pais="Canadá", cidade="Vancouver",
                  escola="Vancouver Summer Academy", acomodacao="Residência estudantil", pontuacao=Decimal("40"),
                  servicos_erp="Summer Schools, Transfer (chegada e saída)")
    c_curso2 = _compra(contagem, p2, "DEMO-C003", "Summer Schools", OrigemCompra.CHECKLIST)
    _compra(contagem, p2, "DEMO-C004", "Transfer (chegada e saída)", OrigemCompra.CHECKLIST)
    _tarefa(contagem, item_checklist_erp="DEMO-T003", programa_id=p2.id, compra_id=c_curso2.id,
            etapa_id=_etapa("SA - GERAL - Realização de Onboarding com novos alunos (pacotes)").id,
            prazo_erp=_dia(hoje, 30), status=StatusTarefa.CONCLUIDA, status_erp="Aguardando",
            concluida_em=agora() - timedelta(days=5))
    t004 = _tarefa(contagem, item_checklist_erp="DEMO-T004", programa_id=p2.id, compra_id=c_curso2.id,
                   etapa_id=_etapa("SA - GERAL - Ter a cópia do passaporte do aluno").id,
                   prazo_erp=_dia(hoje, -8), status=StatusTarefa.AGUARDANDO_ALUNO, status_erp="Aguardando",
                   obs_erp=("Aluno renovou o passaporte e ainda não reenviou a cópia (Carlos Lima, "
                            + _dia(hoje, -6).strftime("%d-%m-%Y") + ", 14h10)"),
                   obs_erp_atualizada_em=agora() - timedelta(days=6))
    if not t004.anotacoes:
        db.session.add(Anotacao(tarefa_id=t004.id, autor_id=carlos.id,
                                texto="Prometeu enviar o passaporte até sexta; se não vier, pego no telefone."))
        contagem["anotacoes"] += 1
    _tarefa(contagem, item_checklist_erp="DEMO-T005", programa_id=p2.id, compra_id=c_curso2.id,
            etapa_id=_etapa("SA - GERAL - Agendar consultoria de integração do Summer Schools").id,
            prazo_erp=_dia(hoje, 15), status=StatusTarefa.A_FAZER, status_erp="Aguardando")

    # ---- Pedro Henrique Alves: programa VIP (procedimento SA - VIP), contato atrasado ----
    p3 = programa("DEMO-A003", programa_id_erp="DEMO-P003", tipo=TipoPrograma.NORMAL,
                  consultor_id=ana.id, consultor_texto=ana.nome, vip_erp=True,
                  mes_embarque=_dia(hoje, 200).replace(day=1), data_embarque=_dia(hoje, 200),
                  visto_normalizado="Visto - Irlanda - Estudante", pais="Irlanda", cidade="Dublin",
                  escola="Dublin City College", acomodacao="Apartamento compartilhado", pontuacao=Decimal("92"),
                  servicos_erp="Curso Premium")
    c_curso3 = _compra(contagem, p3, "DEMO-C005", "Curso Premium", OrigemCompra.PLANILHA)
    _tarefa(contagem, item_checklist_erp="DEMO-T006", programa_id=p3.id, compra_id=c_curso3.id,
            etapa_id=_etapa("SA - VIP - Primeiro contato de relacionamento com aluno").id,
            prazo_erp=_dia(hoje, -1), status=StatusTarefa.A_FAZER, status_erp="Aguardando")
    _tarefa(contagem, item_checklist_erp="DEMO-T007", programa_id=p3.id, compra_id=c_curso3.id,
            etapa_id=_etapa("SA - GERAL - Realização de Onboarding com novos alunos (pacotes)").id,
            prazo_erp=_dia(hoje, 7), status=StatusTarefa.A_FAZER, status_erp="Aguardando")

    # ---- Sofia Nakamura: programa só de visto, atrasada com NEG de duas partes ----
    p4 = programa("DEMO-A004", tipo=TipoPrograma.SO_VISTO, consultor_id=ana.id, consultor_texto=ana.nome,
                  consultor_do_checklist=True, mes_embarque=_dia(hoje, 120).replace(day=1),
                  data_embarque=_dia(hoje, 120), visto_normalizado="Visto - Canadá - eTA",
                  pais="Canadá", servicos_erp="Visto - Canadá - eTA")
    c_visto1 = _compra(contagem, p4, "DEMO-C006", "Visto - Canadá - eTA", OrigemCompra.CHECKLIST)
    _tarefa(contagem, item_checklist_erp="DEMO-T008", programa_id=p4.id, compra_id=c_visto1.id,
            etapa_id=_etapa("SA - VISTOS - Entrega da 1a documentação para aplicação do visto").id,
            prazo_erp=_dia(hoje, -12), status=StatusTarefa.AGUARDANDO_ALUNO, status_erp="Aguardando",
            obs_erp=("Aguardando o formulário assinado pelo aluno (Ana Souza, "
                     + _dia(hoje, -10).strftime("%d-%m-%Y") + ", 09h05)"
                     "Tradução do comprovante financeiro em andamento (Ana Souza, "
                     + _dia(hoje, -9).strftime("%d-%m-%Y") + ", 16h40)"),
            obs_erp_atualizada_em=agora() - timedelta(days=9))
    _tarefa(contagem, item_checklist_erp="DEMO-T009", programa_id=p4.id, compra_id=c_visto1.id,
            etapa_id=_etapa("SA - VISTOS - Ter uma cópia do visto/negativa").id,
            prazo_erp=_dia(hoje, -2), status=StatusTarefa.A_FAZER, status_erp="Aguardando")

    # ---- Rafael Duarte: programa só de visto, tarefa em andamento planejada ----
    p5 = programa("DEMO-A005", tipo=TipoPrograma.SO_VISTO, consultor_id=carlos.id, consultor_texto=carlos.nome,
                  consultor_do_checklist=True, mes_embarque=_dia(hoje, 100).replace(day=1),
                  data_embarque=_dia(hoje, 100), visto_normalizado="Visto - Estados Unidos",
                  pais="Estados Unidos", servicos_erp="Visto - Estados Unidos")
    c_visto2 = _compra(contagem, p5, "DEMO-C007", "Visto - Estados Unidos", OrigemCompra.CHECKLIST)
    _tarefa(contagem, item_checklist_erp="DEMO-T010", programa_id=p5.id, compra_id=c_visto2.id,
            etapa_id=_etapa("SA - VISTOS - Ter a primeira versão da carta de intenções e do formulário de visto preenchido").id,
            prazo_erp=_dia(hoje, 5), data_planejada=_dia(hoje, 2),
            status=StatusTarefa.EM_ANDAMENTO, status_erp="Aguardando")
    _tarefa(contagem, item_checklist_erp="DEMO-T011", programa_id=p5.id, compra_id=c_visto2.id,
            etapa_id=_etapa("SA - VISTOS - Documentação OK ? Envio para embaixada/consulado").id,
            prazo_erp=_dia(hoje, 40), status=StatusTarefa.A_FAZER, status_erp="Aguardando")

    # ---- Beatriz Camargo: "não se aplica" para lançar e tarefa encerrada pelo ERP ----
    p6 = programa("DEMO-A006", programa_id_erp="DEMO-P006", tipo=TipoPrograma.NORMAL,
                  consultor_id=carlos.id, consultor_texto=carlos.nome,
                  mes_embarque=_dia(hoje, 90).replace(day=1), data_embarque=_dia(hoje, 90),
                  visto_normalizado="Visto - Canadá - Estudante", pais="Canadá", cidade="Montreal",
                  escola="Montreal International College", acomodacao="Homestay", pontuacao=Decimal("70"),
                  servicos_erp="Curso Smart")
    c_curso4 = _compra(contagem, p6, "DEMO-C008", "Curso Smart", OrigemCompra.PLANILHA)
    _tarefa(contagem, item_checklist_erp="DEMO-T012", programa_id=p6.id, compra_id=c_curso4.id,
            etapa_id=_etapa("SA - GERAL - Ter confirmação de realização do teste de nivelamento (requisito para embarque)").id,
            prazo_erp=_dia(hoje, 20), status=StatusTarefa.NAO_SE_APLICA, status_erp="Aguardando",
            concluida_em=agora() - timedelta(days=1))
    _tarefa(contagem, item_checklist_erp="DEMO-T013", programa_id=p6.id, compra_id=c_curso4.id,
            etapa_id=_etapa("SA - GERAL - Realizar contato de relacionamento pré - embarque").id,
            prazo_erp=_dia(hoje, 12), data_planejada=_dia(hoje, 9),
            status=StatusTarefa.A_FAZER, status_erp="Aguardando")
    _tarefa(contagem, item_checklist_erp="DEMO-T014", programa_id=p6.id, compra_id=c_curso4.id,
            etapa_id=_etapa("SA - GERAL - Cadastrar flight details").id,
            prazo_erp=_dia(hoje, -20), status=StatusTarefa.CONCLUIDA, status_erp="Finalizado",
            concluida_em=agora() - timedelta(days=20),
            encerrada_erp_em=agora() - timedelta(days=19), motivo_encerramento=MotivoEncerramento.FINALIZADO)

    # ---- Gustavo Peixoto: embarque próximo, planejada para antes do prazo ----
    p7 = programa("DEMO-A007", programa_id_erp="DEMO-P007", tipo=TipoPrograma.NORMAL,
                  consultor_id=ana.id, consultor_texto=ana.nome,
                  mes_embarque=_dia(hoje, 14).replace(day=1), data_embarque=_dia(hoje, 14),
                  visto_normalizado="Visto - Nova Zelândia - Estudante", pais="Nova Zelândia", cidade="Auckland",
                  escola="Auckland Institute of Studies", acomodacao="Homestay", pontuacao=Decimal("60"),
                  servicos_erp="Curso + Trabalho")
    c_curso5 = _compra(contagem, p7, "DEMO-C009", "Curso + Trabalho", OrigemCompra.PLANILHA)
    _tarefa(contagem, item_checklist_erp="DEMO-T015", programa_id=p7.id, compra_id=c_curso5.id,
            etapa_id=_etapa("SA - GERAL - Cadastrar flight details").id,
            prazo_erp=_dia(hoje, 3), data_planejada=_dia(hoje, 1),
            status=StatusTarefa.A_FAZER, status_erp="Aguardando")
    _tarefa(contagem, item_checklist_erp="DEMO-T016", programa_id=p7.id, compra_id=c_curso5.id,
            etapa_id=_etapa("SA - GERAL - Realizar contato de relacionamento pré - embarque").id,
            prazo_erp=_dia(hoje, 4), status=StatusTarefa.EM_ANDAMENTO, status_erp="Aguardando")

    # ---- Helena Vieira: sem visto informado, concluída e já lançada no ERP ----
    p8 = programa("DEMO-A008", programa_id_erp="DEMO-P008", tipo=TipoPrograma.NORMAL,
                  consultor_id=carlos.id, consultor_texto=carlos.nome,
                  mes_embarque=_dia(hoje, 45).replace(day=1), data_embarque=_dia(hoje, 45),
                  pais="Malta", cidade="Sliema", escola="Sliema Language Centre",
                  acomodacao="Apartamento compartilhado", pontuacao=Decimal("30"), servicos_erp="Curso Budget")
    c_curso6 = _compra(contagem, p8, "DEMO-C010", "Curso Budget", OrigemCompra.PLANILHA)
    _tarefa(contagem, item_checklist_erp="DEMO-T017", programa_id=p8.id, compra_id=c_curso6.id,
            etapa_id=_etapa("SA - GERAL - Realização de Onboarding com novos alunos (pacotes)").id,
            prazo_erp=_dia(hoje, 30), status=StatusTarefa.CONCLUIDA, status_erp="Aguardando",
            concluida_em=agora() - timedelta(days=3),
            lancada_erp_em=agora() - timedelta(days=2), lancada_erp_por_id=carlos.id)
    _tarefa(contagem, item_checklist_erp="DEMO-T018", programa_id=p8.id, compra_id=c_curso6.id,
            etapa_id=_etapa("SA - GERAL - Ter a cópia do passaporte do aluno").id,
            prazo_erp=_dia(hoje, -5), data_planejada=_dia(hoje, 1),
            status=StatusTarefa.EM_ANDAMENTO, status_erp="Aguardando",
            obs_erp=("Documento ilegível, pedimos outra digitalização (Carlos Lima, "
                     + _dia(hoje, -4).strftime("%d-%m-%Y") + ", 11h25)"),
            obs_erp_atualizada_em=agora() - timedelta(days=4))

    # ---- Turma extra (DEMO-A009..DEMO-A024): volume para as filas, o calendário e os
    #      relatórios, com todas as combinações de status, atraso e lançamento no ERP ----
    consultores = {"ana": ana, "carlos": carlos}
    programas_extra: dict[str, Programa] = {}
    compras_extra: dict[str, dict[str, Compra]] = {}
    for (aluno_id, nome, programa_id, tipo, visto, pais, cidade, escola, acomodacao,
         pontuacao, servicos_erp, embarque, vip, chave, compras_da_linha) in _TURMA_EXTRA:
        aluno = db.session.execute(db.select(Aluno).filter_by(aluno_id_erp=aluno_id)).scalar_one_or_none()
        if aluno is None:
            aluno = Aluno(aluno_id_erp=aluno_id, nome=nome)
            db.session.add(aluno)
            db.session.flush()
            contagem["alunos"] += 1
        alunos[aluno_id] = aluno
        consultor = consultores[chave]
        p = programa(aluno_id, programa_id_erp=programa_id, tipo=tipo,
                     consultor_id=consultor.id, consultor_texto=consultor.nome,
                     consultor_do_checklist=(tipo == TipoPrograma.SO_VISTO), vip_erp=vip,
                     mes_embarque=_dia(hoje, embarque).replace(day=1), data_embarque=_dia(hoje, embarque),
                     visto_normalizado=visto, pais=pais, cidade=cidade, escola=escola,
                     acomodacao=acomodacao, pontuacao=pontuacao, servicos_erp=servicos_erp)
        programas_extra[aluno_id] = p
        compras_extra[aluno_id] = {}
        for compra_id, servico, origem in compras_da_linha:
            compras_extra[aluno_id][servico] = _compra(contagem, p, compra_id, servico, origem)

    for spec in _TAREFAS_EXTRA:
        if db.session.execute(db.select(Tarefa).filter_by(item_checklist_erp=spec["item"])).scalar_one_or_none():
            continue  # idempotente pela chave externa (#)
        programa_extra = programas_extra[spec["aluno"]]
        compra = compras_extra[spec["aluno"]].get(spec["servico"])
        campos: dict = dict(
            item_checklist_erp=spec["item"], programa_id=programa_extra.id,
            compra_id=compra.id if compra else None,
            etapa_id=_etapa(spec["etapa"]).id,
            prazo_erp=_dia(hoje, spec["prazo"]),
            status=spec.get("status", StatusTarefa.A_FAZER),
            status_erp="Finalizado" if spec.get("encerrada") else "Aguardando",
        )
        if spec.get("planejada") is not None:
            campos["data_planejada"] = _dia(hoje, spec["planejada"])
        if spec.get("neg"):
            autor, dias, hora, texto = spec["neg"]
            campos["obs_erp"] = _neg(hoje, autor, dias, hora, texto)
            campos["obs_erp_atualizada_em"] = agora() - timedelta(days=abs(dias))
        if spec.get("concluida") is not None:
            campos["concluida_em"] = agora() - timedelta(days=spec["concluida"])
        if spec.get("lancada") is not None:
            campos["lancada_erp_em"] = agora() - timedelta(days=spec["lancada"])
            campos["lancada_erp_por_id"] = programa_extra.consultor_id
        if spec.get("encerrada"):
            dias_encerrada, motivo = spec["encerrada"]
            campos["encerrada_erp_em"] = agora() - timedelta(days=dias_encerrada)
            campos["motivo_encerramento"] = motivo
        nova = Tarefa(**campos)
        db.session.add(nova)
        db.session.flush()
        contagem["tarefas"] += 1
        if spec.get("anotacao") and not nova.anotacoes:
            db.session.add(Anotacao(tarefa_id=nova.id, autor_id=programa_extra.consultor_id,
                                    texto=spec["anotacao"]))
            contagem["anotacoes"] += 1

    _criar_pautas(contagem, ana, carlos)
    _vincular_tarefas_importacao(importacao_atual)

    # Público teen é recalculado pelas regras oficiais (compra de Summer Schools marca a Marina).
    from app.publico_teen import recalcular

    recalcular()
    db.session.commit()
    return contagem


def _criar_importacoes(contagem: dict, admin: Usuario, hoje: date) -> Importacao:
    """Histórico fictício de importações confirmadas, para as telas /importacoes.

    Cada registro é idempotente pelo arquivo_hash. Devolve a importação mais
    recente, que as tarefas de demonstração apontam como a sua origem.
    """
    especificacoes = (
        dict(
            hash="demo-import-001", nome="checklist-demo-semana-34.csv",
            periodo=(_dia(hoje, -21), _dia(hoje, -7)),
            lida_em=agora() - timedelta(days=7, hours=3),
            duracao=timedelta(minutes=8),
            resumo={
                "linhas_importadas": 389, "linhas_sem_dados_ignoradas": 2,
                "tarefas_novas": 58, "tarefas_concluidas_novas": 7, "tarefas_atualizadas": 66,
                "tarefas_sem_mudanca": 251, "tarefas_reabertas": 1, "tarefas_finalizadas": 9,
                "tarefas_canceladas": 1, "itens_cancelados": 0, "tarefas_fora_do_periodo": 11,
                "compras_juntadas": 5, "alunos_criados": 9, "programas_criados": 9,
                "programas_so_visto_criados": 2, "programas_viraram_normais": 1,
                "programas_atualizados": 7, "itens_ignorados": 6, "itens_sem_programa": 0,
                "etapas_criadas": 1, "rsa_procedimentos": 322, "rsa_em_aberto": 121,
                "rsa_alunos_teen": 8, "erros": 0, "avisos": 1,
                "detalhes": {
                    "campos_atualizados": {"prazo": 12, "NEG": 6, "status no ERP": 9},
                    "etapas_criadas": ["SA - GERAL - Agendar consultoria de integração do Summer Schools"],
                },
            },
            ocorrencias=(
                (Gravidade.AVISO, TipoOcorrencia.PROCEDIMENTO_NOVO, 214, "DEMO-T005",
                 'Procedimento novo incluído no catálogo: "SA - GERAL - Agendar consultoria '
                 'de integração do Summer Schools". Complete as orientações na tela do catálogo.'),
            ),
        ),
        dict(
            hash="demo-import-002", nome="checklist-demo-semana-35.csv",
            periodo=(_dia(hoje, -14), hoje),
            lida_em=agora() - timedelta(hours=5),
            duracao=timedelta(minutes=11),
            resumo={
                "linhas_importadas": 402, "linhas_sem_dados_ignoradas": 1,
                "tarefas_novas": 44, "tarefas_concluidas_novas": 5, "tarefas_atualizadas": 81,
                "tarefas_sem_mudanca": 265, "tarefas_reabertas": 0, "tarefas_finalizadas": 7,
                "tarefas_canceladas": 0, "itens_cancelados": 0, "tarefas_fora_do_periodo": 0,
                "compras_juntadas": 3, "alunos_criados": 6, "programas_criados": 6,
                "programas_so_visto_criados": 1, "programas_viraram_normais": 0,
                "programas_atualizados": 12, "itens_ignorados": 4, "itens_sem_programa": 0,
                "etapas_criadas": 0, "rsa_procedimentos": 336, "rsa_em_aberto": 128,
                "rsa_alunos_teen": 9, "erros": 0, "avisos": 1,
                "detalhes": {
                    "campos_atualizados": {"prazo": 15, "NEG": 8, "status no ERP": 11, "programa": 2, "procedimento": 1},
                    "programas_atualizados": [
                        {"programa_id": "DEMO-P018", "aluno": "Karina Almeida", "campos": "escola, acomodação"},
                        {"programa_id": "DEMO-P022", "aluno": "Natalia Prado", "campos": "data_embarque"},
                    ],
                },
            },
            ocorrencias=(
                (Gravidade.AVISO, TipoOcorrencia.CONSULTOR_NAO_ENCONTRADO, 38, "Equipe de Vendas",
                 'Consultor "Equipe de Vendas": não bate com nenhum usuário (2 programa(s)). '
                 "Cadastre o usuário ou uma exceção de nome; até lá, esses programas ficam sem consultor."),
            ),
        ),
    )

    mais_recente: Importacao | None = None
    for esp in especificacoes:
        importacao = db.session.execute(
            db.select(Importacao).filter_by(arquivo_hash=esp["hash"])
        ).scalar_one_or_none()
        if importacao is None:
            importacao = Importacao(
                tipo=TipoImportacao.CHECKLIST, situacao=SituacaoImportacao.CONFIRMADA,
                arquivo_nome=esp["nome"], arquivo_hash=esp["hash"],
                periodo_inicio=esp["periodo"][0], periodo_fim=esp["periodo"][1],
                iniciada_por_id=admin.id, iniciada_em=esp["lida_em"],
                concluida_em=esp["lida_em"] + esp["duracao"],
                resumo=esp["resumo"], dados_lidos=None,
            )
            db.session.add(importacao)
            db.session.flush()
            for gravidade, tipo, linha, chave, mensagem in esp["ocorrencias"]:
                db.session.add(OcorrenciaImportacao(
                    importacao_id=importacao.id, gravidade=gravidade, tipo=tipo,
                    linha=linha, chave=chave, mensagem=mensagem,
                ))
            contagem["importacoes"] += 1
        mais_recente = importacao  # a última especificação é a mais recente
    assert mais_recente is not None
    return mais_recente


def _vincular_tarefas_importacao(importacao: Importacao) -> None:
    """Aponta as tarefas de demonstração para a importação fictícia mais recente.

    Sem isso, a tela da importação listaria todas as tarefas como "fora do
    período"; com o vínculo, o histórico aparece como no dia a dia de verdade.
    Só mexe em tarefas criadas por este seed (item com prefixo DEMO-) que
    ainda não vieram de nenhuma importação.
    """
    tarefas = db.session.execute(
        db.select(Tarefa).where(Tarefa.ultima_importacao_id.is_(None), Tarefa.item_checklist_erp.like("DEMO-%"))
    ).scalars().all()
    for tarefa in tarefas:
        tarefa.ultima_importacao_id = importacao.id


def _criar_pautas(contagem: dict, ana: Usuario, carlos: Usuario) -> None:
    """Pautas de comunicação interna fictícias, nos estados internos principais."""
    unidade = nome_unidade()

    def pauta(pid: int, **campos) -> Pauta:
        existente = db.session.get(Pauta, pid)
        if existente:
            return existente
        nova = Pauta(id=pid, **campos)
        db.session.add(nova)
        db.session.flush()
        contagem["pautas"] += 1
        return nova

    def anotacao(p: Pauta, autor: Usuario, texto: str) -> None:
        if p.anotacoes:
            return
        db.session.add(PautaAnotacao(pauta_id=p.id, autor_id=autor.id, texto=texto))
        contagem["anotacoes_pautas"] += 1

    # Ação necessária, com quebra de 72h na própria unidade.
    p1 = pauta(910001, categoria="ATD - Dúvida de embarque", categoria_limpa="ATD - Dúvida de embarque",
               pauta_titulo="910001 - AC-DEMO - Lucas Ferreira - Toronto Language School (Toronto) - dúvida sobre conexão do voo",
               aluno="Lucas Ferreira", status_tm="Em aberto", responsavel_tm=ana.nome,
               criado_em_tm=agora() - timedelta(days=5), criado_por_tm=ana.nome,
               atualizado_em_tm=agora() - timedelta(days=4), atualizado_por_tm="Renata Kimura",
               tag="Atrasada 72h +", tempo_inativo_texto="80:00:00", tempo_inativo_horas=80, prazo_sla_horas=48,
               un_atualizou="Setor de Aéreo", un_responsavel=unidade, un_criou=unidade, un_final=unidade,
               atualizada_un=False, quebra_72h_unidade=True, estado_interno="acao",
               estado_interno_por_id=ana.id, consultor_id=ana.id,
               observacao="Setor de Aéreo conferindo a conexão; se não voltar hoje, ligo para o aluno acalmar.")
    anotacao(p1, ana, "Renata prometeu responder até o fim do dia; cobrar de novo amanhã se não voltar.")

    # Ação pendente da unidade, ainda dentro do prazo.
    p2 = pauta(910002, categoria="ESC - Matrícula e documentação escolar",
               categoria_limpa="ESC - Matrícula e documentação escolar",
               pauta_titulo="910002 - AC-DEMO - Marina Costa - Vancouver Summer Academy (Vancouver) - confirmação de matrícula",
               aluno="Marina Costa", status_tm="Em aberto", responsavel_tm=carlos.nome,
               criado_em_tm=agora() - timedelta(days=2), criado_por_tm=carlos.nome,
               atualizado_em_tm=agora() - timedelta(days=1), atualizado_por_tm="Otávio Mendes",
               tempo_inativo_texto="26:00:00", tempo_inativo_horas=26, prazo_sla_horas=72,
               un_atualizou="Setor de Escolas", un_responsavel=unidade, un_criou=unidade, un_final=unidade,
               atualizada_un=False, estado_interno="acao", estado_interno_por_id=carlos.id, consultor_id=carlos.id,
               observacao="Escola pediu o comprovante de pagamento de novo; anexar na resposta.")
    anotacao(p2, carlos, "Otávio vai reenviar o formulário da escola; responder assim que chegar.")

    # Aguardando retorno do aluno (a bola está com ele).
    p3 = pauta(910003, categoria="VISTOS - Documentação inicial", categoria_limpa="VISTOS - Documentação inicial",
               pauta_titulo="910003 - AC-DEMO - Sofia Nakamura - visto eTA - formulário assinado",
               aluno="Sofia Nakamura", status_tm="Aguardando retorno do aluno/fornecedor", responsavel_tm=ana.nome,
               criado_em_tm=agora() - timedelta(days=9), criado_por_tm=ana.nome,
               atualizado_em_tm=agora() - timedelta(days=3), atualizado_por_tm=ana.nome,
               tempo_inativo_texto="20:00:00", tempo_inativo_horas=20, prazo_sla_horas=72,
               un_atualizou=unidade, un_responsavel=unidade, un_criou=unidade, un_final=unidade,
               atualizada_un=True, estado_interno="aguardando", estado_interno_por_id=ana.id, consultor_id=ana.id,
               observacao="Respondemos com a lista de documentos; aguardando o aluno.")
    anotacao(p3, ana, "Aluno viajou; retomar o contato na semana que vem.")

    # Acompanhando outro setor, que lá quebrou o prazo de 72h.
    p4 = pauta(910004, categoria="FIN - Conferência de pagamento", categoria_limpa="FIN - Conferência de pagamento",
               pauta_titulo="910004 - AC-DEMO - Helena Vieira - Sliema Language Centre (Sliema) - boleto em aberto",
               aluno="Helena Vieira", status_tm="Em aberto", responsavel_tm="Patrícia Lopes",
               criado_em_tm=agora() - timedelta(days=6), criado_por_tm=carlos.nome,
               atualizado_em_tm=agora() - timedelta(days=5), atualizado_por_tm="Patrícia Lopes",
               tag="Atrasada 72h +", tempo_inativo_texto="96:00:00", tempo_inativo_horas=96, prazo_sla_horas=48,
               un_atualizou="Setor Financeiro", un_responsavel="Setor Financeiro", un_criou=unidade,
               un_final="Setor Financeiro - " + unidade, atualizada_un=False, quebra_72h_outro=True,
               estado_interno="acompanhamento", estado_interno_por_id=carlos.id, consultor_id=carlos.id,
               observacao="Cobrança semanal ao financeiro até a baixa aparecer no extrato.")
    anotacao(p4, carlos, "Patrícia disse que a baixa foi feita; conferir na próxima importação.")

    # Acompanhando outro setor, dentro do prazo.
    p5 = pauta(910005, categoria="ALO - Solicitação de acomodação", categoria_limpa="ALO - Solicitação de acomodação",
               pauta_titulo="910005 - AC-DEMO - Gustavo Peixoto - Auckland Institute of Studies (Auckland) - homestay com quintal",
               aluno="Gustavo Peixoto", status_tm="Em aberto", responsavel_tm="Renata Kimura",
               criado_em_tm=agora() - timedelta(days=1), criado_por_tm=ana.nome,
               atualizado_em_tm=agora() - timedelta(hours=12), atualizado_por_tm="Renata Kimura",
               tempo_inativo_texto="12:00:00", tempo_inativo_horas=12, prazo_sla_horas=48,
               un_atualizou="Setor de Acomodação", un_responsavel="Setor de Acomodação", un_criou=unidade,
               un_final="Setor de Acomodação - " + unidade, atualizada_un=False,
               estado_interno="acompanhamento", estado_interno_por_id=ana.id, consultor_id=ana.id)
    anotacao(p5, ana, "Família com quintal confirmada; aguardando o contrato assinado.")

    # Finalizada (histórico).
    p6 = pauta(910006, categoria="AER - Alteração de passagem", categoria_limpa="AER - Alteração de passagem",
               pauta_titulo="910006 - AC-DEMO - Beatriz Camargo - remarcação de voo aprovada",
               aluno="Beatriz Camargo", status_tm="Finalizando", responsavel_tm=carlos.nome,
               criado_em_tm=agora() - timedelta(days=8), criado_por_tm=carlos.nome,
               atualizado_em_tm=agora() - timedelta(hours=2), atualizado_por_tm=carlos.nome,
               tempo_inativo_texto="02:00:00", tempo_inativo_horas=2, prazo_sla_horas=48,
               un_atualizou=unidade, un_responsavel=unidade, un_criou=unidade, un_final=unidade,
               atualizada_un=True, ativa=False, encerrada_em=agora() - timedelta(hours=2),
               estado_interno="finalizada", estado_interno_por_id=carlos.id, consultor_id=carlos.id,
               observacao="Remarcação confirmada com a companhia aérea e repassada ao aluno.")
    anotacao(p6, carlos, "Caso encerrado; arquivar após a conferência do novo bilhete.")

    # Ação necessária com quebra de 72h na própria unidade: material de boas-vindas parado no marketing.
    p7 = pauta(910007, categoria="MKT - Criação de material", categoria_limpa="MKT - Criação de material",
               pauta_titulo="910007 - AC-DEMO - Bruno Martins - material de boas-vindas do curso de Vancouver",
               aluno="Bruno Martins", status_tm="Em aberto", responsavel_tm=ana.nome,
               criado_em_tm=agora() - timedelta(days=4), criado_por_tm=carlos.nome,
               atualizado_em_tm=agora() - timedelta(days=3), atualizado_por_tm="Marcelo Tavares",
               tag="Atrasada 72h +", tempo_inativo_texto="90:00:00", tempo_inativo_horas=90, prazo_sla_horas=72,
               un_atualizou="Setor de Marketing", un_responsavel=unidade, un_criou=unidade, un_final=unidade,
               atualizada_un=False, quebra_72h_unidade=True, estado_interno="acao",
               estado_interno_por_id=ana.id, consultor_id=ana.id,
               observacao="Arte aprovada; falta só o texto final do setor de Marketing.")
    anotacao(p7, ana, "Marcelo prometeu o texto hoje; se atrasar, subo a arte sem ele.")

    # Ação pendente da unidade, dentro do prazo: primeiro contato do aluno.
    p8 = pauta(910008, categoria="ATD - Primeiro contato do aluno", categoria_limpa="ATD - Primeiro contato do aluno",
               pauta_titulo="910008 - AC-DEMO - Camila Rocha - primeiro contato do pré-embarque",
               aluno="Camila Rocha", status_tm="Em aberto", responsavel_tm=carlos.nome,
               criado_em_tm=agora() - timedelta(hours=5), criado_por_tm=ana.nome,
               atualizado_em_tm=agora() - timedelta(hours=5), atualizado_por_tm=ana.nome,
               tempo_inativo_texto="05:00:00", tempo_inativo_horas=5, prazo_sla_horas=24,
               un_atualizou="Comercial", un_responsavel=unidade, un_criou=unidade, un_final=unidade,
               atualizada_un=False, estado_interno="acao", estado_interno_por_id=carlos.id,
               consultor_id=carlos.id, observacao="Primeira ligação marcada para hoje à tarde.")

    # Aguardando retorno do aluno: tradução do visto.
    p9 = pauta(910009, categoria="VISTOS - Pendência de tradução", categoria_limpa="VISTOS - Pendência de tradução",
               pauta_titulo="910009 - AC-DEMO - Diego Fontana - tradução do comprovante financeiro",
               aluno="Diego Fontana", status_tm="Aguardando retorno do aluno/fornecedor", responsavel_tm=carlos.nome,
               criado_em_tm=agora() - timedelta(days=3), criado_por_tm=carlos.nome,
               atualizado_em_tm=agora() - timedelta(days=1), atualizado_por_tm=carlos.nome,
               tempo_inativo_texto="30:00:00", tempo_inativo_horas=30, prazo_sla_horas=48,
               un_atualizou=unidade, un_responsavel=unidade, un_criou=unidade, un_final=unidade,
               atualizada_un=True, estado_interno="aguardando", estado_interno_por_id=carlos.id,
               consultor_id=carlos.id, observacao="Tradutora avisou que entrega sexta; o aluno já sabe.")
    anotacao(p9, carlos, "Se a tradução não chegar sexta, buscar outra tradutora.")

    # Aguardando retorno do aluno: documentação pendente.
    p10 = pauta(910010, categoria="DOC - Documentação pendente do aluno",
                categoria_limpa="DOC - Documentação pendente do aluno",
                pauta_titulo="910010 - AC-DEMO - Isabela Freitas - histórico escolar digitalizado",
                aluno="Isabela Freitas", status_tm="Aguardando retorno do aluno/fornecedor", responsavel_tm=ana.nome,
                criado_em_tm=agora() - timedelta(days=2), criado_por_tm=ana.nome,
                atualizado_em_tm=agora() - timedelta(hours=20), atualizado_por_tm=ana.nome,
                tempo_inativo_texto="20:00:00", tempo_inativo_horas=20, prazo_sla_horas=72,
                un_atualizou=unidade, un_responsavel=unidade, un_criou=unidade, un_final=unidade,
                atualizada_un=True, estado_interno="aguardando", estado_interno_por_id=ana.id,
                consultor_id=ana.id, observacao="Falta o histórico escolar digitalizado; o resto já foi conferido.")

    # Acompanhando outro setor, que lá quebrou o prazo de 72h: reembolso.
    p11 = pauta(910011, categoria="FIN - Reembolso solicitado", categoria_limpa="FIN - Reembolso solicitado",
                pauta_titulo="910011 - AC-DEMO - Leonardo Pires - reembolso do seguro cancelado",
                aluno="Leonardo Pires", status_tm="Em aberto", responsavel_tm="Juliana Reis",
                criado_em_tm=agora() - timedelta(days=7), criado_por_tm=carlos.nome,
                atualizado_em_tm=agora() - timedelta(days=5), atualizado_por_tm="Juliana Reis",
                tag="Atrasada 72h +", tempo_inativo_texto="110:00:00", tempo_inativo_horas=110, prazo_sla_horas=72,
                un_atualizou="Setor Financeiro", un_responsavel="Setor Financeiro", un_criou=unidade,
                un_final="Setor Financeiro - " + unidade, atualizada_un=False, quebra_72h_outro=True,
                estado_interno="acompanhamento", estado_interno_por_id=carlos.id, consultor_id=carlos.id,
                observacao="Reembolso aprovado no financeiro; falta o crédito cair na fatura do aluno.")
    anotacao(p11, carlos, "Juliana confirmou o crédito para esta semana; fechar a pauta quando o aluno avisar.")

    # Acompanhando outro setor, dentro do prazo: dúvida de bagagem.
    p12 = pauta(910012, categoria="AER - Dúvida de bagagem", categoria_limpa="AER - Dúvida de bagagem",
                pauta_titulo="910012 - AC-DEMO - Matheus Teixeira - regras de bagagem da companhia aérea",
                aluno="Matheus Teixeira", status_tm="Em aberto", responsavel_tm="Marcelo Tavares",
                criado_em_tm=agora() - timedelta(hours=10), criado_por_tm=ana.nome,
                atualizado_em_tm=agora() - timedelta(hours=2), atualizado_por_tm="Marcelo Tavares",
                tempo_inativo_texto="02:00:00", tempo_inativo_horas=2, prazo_sla_horas=24,
                un_atualizou="Setor de Passagens", un_responsavel="Setor de Passagens", un_criou=unidade,
                un_final="Setor de Passagens - " + unidade, atualizada_un=False,
                estado_interno="acompanhamento", estado_interno_por_id=ana.id, consultor_id=ana.id,
                observacao="Setor de Passagens explicou as regras da companhia; aluno pediu o resumo por e-mail.")

    # Finalizada (histórico): seguro viagem emitido.
    p13 = pauta(910013, categoria="SEG - Emissão de seguro viagem", categoria_limpa="SEG - Emissão de seguro viagem",
                pauta_titulo="910013 - AC-DEMO - Natalia Prado - apólice do seguro viagem emitida",
                aluno="Natalia Prado", status_tm="Finalizando", responsavel_tm=carlos.nome,
                criado_em_tm=agora() - timedelta(days=2), criado_por_tm=carlos.nome,
                atualizado_em_tm=agora() - timedelta(hours=3), atualizado_por_tm=carlos.nome,
                tempo_inativo_texto="03:00:00", tempo_inativo_horas=3, prazo_sla_horas=24,
                un_atualizou=unidade, un_responsavel=unidade, un_criou=unidade, un_final=unidade,
                atualizada_un=True, ativa=False, encerrada_em=agora() - timedelta(hours=3),
                estado_interno="finalizada", estado_interno_por_id=carlos.id, consultor_id=carlos.id,
                observacao="Apólice emitida e enviada; a aluna confirmou o recebimento.")
    anotacao(p13, carlos, "Caso encerrado.")

    # Finalizada (histórico): transfer reservado.
    p14 = pauta(910014, categoria="TRA - Solicitação de transfer", categoria_limpa="TRA - Solicitação de transfer",
                pauta_titulo="910014 - AC-DEMO - Rafaela Simões - transfer de chegada em Boston",
                aluno="Rafaela Simões", status_tm="Finalizando", responsavel_tm=ana.nome,
                criado_em_tm=agora() - timedelta(days=1), criado_por_tm=ana.nome,
                atualizado_em_tm=agora() - timedelta(hours=8), atualizado_por_tm=ana.nome,
                tempo_inativo_texto="08:00:00", tempo_inativo_horas=8, prazo_sla_horas=48,
                un_atualizou=unidade, un_responsavel=unidade, un_criou=unidade, un_final=unidade,
                atualizada_un=True, ativa=False, encerrada_em=agora() - timedelta(hours=8),
                estado_interno="finalizada", estado_interno_por_id=ana.id, consultor_id=ana.id,
                observacao="Transfer de chegada reservado; motorista confirmado com a aluna.")
