"""O `flask seed-demo` cria o banco de demonstração e pode rodar de novo sem duplicar nada."""

from app.extensions import db
from app.importacao.rotulos import RESUMO_CHECKLIST
from app.models import (
    Aluno,
    Anotacao,
    Compra,
    Importacao,
    Pauta,
    Papel,
    Programa,
    SituacaoImportacao,
    StatusTarefa,
    Tarefa,
    TipoImportacao,
    TipoPrograma,
    Usuario,
)
from app.seed_demo import EMAILS_DEMO, SENHA_DEMO, USUARIOS_DEMO


def _contar(modelo) -> int:
    return db.session.execute(db.select(db.func.count()).select_from(modelo)).scalar_one()


def _contagens() -> dict:
    modelos = (Usuario, Aluno, Programa, Compra, Tarefa, Pauta, Anotacao, Importacao)
    return {modelo.__name__: _contar(modelo) for modelo in modelos}


def test_seed_demo_cria_os_dados(app):
    resultado = app.test_cli_runner().invoke(args=["seed-demo"])
    assert resultado.exit_code == 0, resultado.output
    assert "Dados de demonstração criados" in resultado.output
    assert SENHA_DEMO in resultado.output

    contagens = _contagens()
    assert contagens["Usuario"] == len(USUARIOS_DEMO)
    assert contagens["Aluno"] >= 24
    assert contagens["Programa"] >= 24
    assert contagens["Compra"] >= 30
    assert contagens["Tarefa"] >= 50
    assert contagens["Pauta"] >= 14
    assert contagens["Importacao"] >= 2

    # Os quatro papéis de demonstração, com a senha documentada.
    for nome, email, papel in USUARIOS_DEMO:
        usuario = db.session.execute(db.select(Usuario).filter_by(email=email)).scalar_one()
        assert usuario.nome == nome and usuario.papel == papel
        assert usuario.verificar_senha(SENHA_DEMO)

    # Programas dos dois tipos, alunos teen e programas VIP.
    tipos = db.session.execute(db.select(Programa.tipo)).scalars().all()
    assert tipos.count(TipoPrograma.NORMAL) >= 6 and tipos.count(TipoPrograma.SO_VISTO) >= 2
    assert db.session.execute(db.select(Programa).filter_by(vip_erp=True)).scalars().first() is not None
    teens = db.session.execute(db.select(Aluno).filter_by(teen=True)).scalars().all()
    assert [a.nome for a in teens] == ["Marina Costa"]

    # Tarefas em todos os status, com atraso justificado e sem justificativa.
    status = set(db.session.execute(db.select(Tarefa.status)).scalars())
    assert status == set(StatusTarefa)
    atrasadas = [t for t in db.session.execute(db.select(Tarefa)).scalars() if t.atrasada()]
    assert any(t.tem_justificativa for t in atrasadas) and any(not t.tem_justificativa for t in atrasadas)
    assert contagens["Anotacao"] >= 1  # observação interna pendente de lançamento como NEG

    # Datas planejadas para a visão de calendário e tarefas concluídas esperando lançamento no ERP.
    planejadas = db.session.execute(db.select(Tarefa).where(Tarefa.data_planejada.is_not(None))).scalars().all()
    assert len(planejadas) >= 10
    para_lancar = [
        t for t in db.session.execute(db.select(Tarefa)).scalars()
        if t.status in (StatusTarefa.CONCLUIDA, StatusTarefa.NAO_SE_APLICA)
        and t.lancada_erp_em is None and t.encerrada_erp_em is None
    ]
    assert len(para_lancar) >= 3

    # Pautas nos estados internos, incluindo as quebras de 72h (na unidade e em outro setor).
    estados = set(db.session.execute(db.select(Pauta.estado_interno)).scalars())
    assert {"acao", "aguardando", "acompanhamento", "finalizada"} <= estados
    quebra = db.session.execute(db.select(Pauta).filter_by(quebra_72h_unidade=True)).scalars().first()
    assert quebra is not None and quebra.estado_interno == "acao"
    assert db.session.execute(db.select(Pauta).filter_by(quebra_72h_outro=True)).scalars().first() is not None
    assert db.session.execute(db.select(Pauta).where(Pauta.ativa.is_(False))).scalars().first() is not None

    # Importações confirmadas no histórico, com resumo nos termos da tela e ocorrências.
    importacoes = db.session.execute(
        db.select(Importacao).filter_by(tipo=TipoImportacao.CHECKLIST, situacao=SituacaoImportacao.CONFIRMADA)
    ).scalars().all()
    assert {i.arquivo_hash for i in importacoes} >= {"demo-import-001", "demo-import-002"}
    for importacao in importacoes:
        assert set(importacao.resumo) <= set(RESUMO_CHECKLIST) | {"detalhes"}
        assert importacao.ocorrencias
        assert importacao.concluida_em is not None and importacao.iniciada_por_id is not None
    # As tarefas de demonstração vêm da importação mais recente: nada "fora do período".
    ultima = max(importacoes, key=lambda i: i.concluida_em)
    demo_sem_importacao = db.session.execute(
        db.select(Tarefa).where(Tarefa.ultima_importacao_id.is_(None), Tarefa.item_checklist_erp.like("DEMO-%"))
    ).scalars().all()
    assert demo_sem_importacao == []
    assert db.session.execute(db.select(Tarefa).where(Tarefa.ultima_importacao_id == ultima.id)).scalars().first()


def test_seed_demo_duas_vezes_nao_duplica_nada(app):
    runner = app.test_cli_runner()
    primeira = runner.invoke(args=["seed-demo"])
    assert primeira.exit_code == 0, primeira.output
    depois_da_primeira = _contagens()

    segunda = runner.invoke(args=["seed-demo"])
    assert segunda.exit_code == 0, segunda.output
    assert "já existem" in segunda.output
    assert _contagens() == depois_da_primeira


def test_seed_demo_nao_sobrescreve_trabalho_da_equipe(app):
    """Senha trocada pela equipe continua valendo depois de rodar o seed de novo."""
    runner = app.test_cli_runner()
    assert runner.invoke(args=["seed-demo"]).exit_code == 0

    ana = db.session.execute(db.select(Usuario).filter_by(email="ana.souza@exemplo.com")).scalar_one()
    ana.definir_senha("Senha Nova 12345")
    db.session.commit()

    assert runner.invoke(args=["seed-demo"]).exit_code == 0
    db.session.refresh(ana)
    assert ana.verificar_senha("Senha Nova 12345")
    assert not ana.verificar_senha(SENHA_DEMO)


def test_emails_demo_cobrem_as_contas_de_exemplo():
    assert EMAILS_DEMO == {"admin@exemplo.com", "ana.souza@exemplo.com",
                           "carlos.lima@exemplo.com", "estagio@exemplo.com"}
