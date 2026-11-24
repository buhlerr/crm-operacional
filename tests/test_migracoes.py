"""As migrações precisam funcionar num banco com dados: é o que acontece no
servidor a cada atualização (instalar/atualizar.ps1 roda flask db upgrade)."""

import sqlite3

from flask_migrate import downgrade, upgrade

from app import create_app
from app.extensions import db


def test_unica_migracao_inicial_cria_todas_as_tabelas(tmp_path, monkeypatch):
    monkeypatch.setenv("CHECKLIST_DADOS", str(tmp_path))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    app = create_app()
    with app.app_context():
        upgrade()
        from sqlalchemy import inspect

        no_banco = set(inspect(db.engine).get_table_names()) - {"alembic_version"}
        do_modelo = {t for t in db.metadata.tables if not t.startswith("sqlite_")}
        assert no_banco == do_modelo
        db.engine.dispose()


def test_migracao_sobe_e_desce_com_dados(tmp_path, monkeypatch):
    monkeypatch.setenv("CHECKLIST_DADOS", str(tmp_path))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    app = create_app()
    arquivo = tmp_path / "checklist.db"
    with app.app_context():
        upgrade()
        # Usuário referenciado por outras tabelas: é isso que faz o SQLite recusar recriar a tabela.
        with db.engine.begin() as conexao:
            conexao.exec_driver_sql(
                "INSERT INTO usuario (nome, email, papel, ativo, criado_em, atualizado_em) "
                "VALUES ('Pessoa', 'p@exemplo.test', 'admin', 1, '2026-09-29', '2026-09-29')"
            )
            conexao.exec_driver_sql(
                "INSERT INTO importacao (tipo, situacao, iniciada_por_id, iniciada_em) VALUES ('base_alunos', 'confirmada', 1, '2026-09-29')"
            )
        downgrade(revision="base")  # desce tudo (uma migração só)...
        upgrade()  # ...e sobe de novo
        upgrade()  # rodar de novo não faz nada
        db.engine.dispose()

    with sqlite3.connect(arquivo) as conexao:
        assert conexao.execute("PRAGMA foreign_key_check").fetchall() == []
        assert not conexao.execute("SELECT name FROM sqlite_master WHERE name LIKE '_alembic_tmp%'").fetchall()
