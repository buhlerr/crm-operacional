import pytest
from app import create_app
from app.extensions import db
from app.models import Papel, Usuario
from app.seed_demo import SENHA_DEMO


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "CSRF_DESLIGADO": True})
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_usuario_definir_e_verificar_senha(app):
    u = Usuario(nome="Consultor Teste", email="consultor@exemplo.test", papel=Papel.CONSULTOR)
    u.definir_senha("SenhaSegura123")
    db.session.add(u)
    db.session.commit()

    assert u.senha_hash is not None
    assert u.verificar_senha("SenhaSegura123") is True
    assert u.verificar_senha("SenhaErrada") is False
    assert u.verificar_senha("") is False


def test_login_com_email_e_senha(app, client):
    u = Usuario(nome="Admin Teste", email="admin@exemplo.test", papel=Papel.ADMIN)
    u.definir_senha("Admin@12345")
    db.session.add(u)
    db.session.commit()

    # Login com senha errada
    res = client.post("/entrar", data={"email": "admin@exemplo.test", "senha": "errada"})
    assert res.status_code == 200
    assert b"E-mail ou senha incorretos." in res.data

    # Login com senha certa
    res = client.post("/entrar", data={"email": "admin@exemplo.test", "senha": "Admin@12345"})
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/minha-fila")


def test_trocar_senha_usuario(app, client):
    u = Usuario(nome="Usuario Teste", email="user@exemplo.test", papel=Papel.CONSULTOR)
    u.definir_senha("SenhaAntiga1")
    db.session.add(u)
    db.session.commit()

    with client.session_transaction() as sess:
        sess["usuario_id"] = u.id

    # Troca com senha atual errada
    res = client.post("/trocar-senha", data={
        "senha_atual": "errada",
        "nova_senha": "NovaSenhaForte2",
        "confirmacao": "NovaSenhaForte2"
    })
    assert b"A senha atual informada est" in res.data

    # Troca com sucesso
    res = client.post("/trocar-senha", data={
        "senha_atual": "SenhaAntiga1",
        "nova_senha": "NovaSenhaForte2",
        "confirmacao": "NovaSenhaForte2"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Sua senha foi alterada com sucesso." in res.data

    db.session.refresh(u)
    assert u.verificar_senha("NovaSenhaForte2") is True
    assert u.verificar_senha("SenhaAntiga1") is False


def test_admin_cria_e_edita_usuario_com_senha(app, client):
    admin = Usuario(nome="Admin", email="admin@exemplo.test", papel=Papel.ADMIN)
    admin.definir_senha("AdminPass1")
    db.session.add(admin)
    db.session.commit()

    with client.session_transaction() as sess:
        sess["usuario_id"] = admin.id

    # Cria novo usuário com senha
    res = client.post("/cadastros/usuarios", data={
        "nome": "Novo Consultor",
        "email": "novo@exemplo.test",
        "papel": "consultor",
        "senha": "ConsultorPass1"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Novo Consultor cadastrado(a) com sucesso." in res.data

    novo = db.session.execute(db.select(Usuario).filter_by(email="novo@exemplo.test")).scalar_one()
    assert novo.verificar_senha("ConsultorPass1") is True

    # Redefine a senha do consultor
    res = client.post(f"/cadastros/usuarios/{novo.id}", data={
        "nome": "Novo Consultor Alterado",
        "email": "novo@exemplo.test",
        "papel": "consultor",
        "ativo": "1",
        "nova_senha": "ResetPass999"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert "Usuário atualizado com sucesso.".encode("utf-8") in res.data

    db.session.refresh(novo)
    assert novo.verificar_senha("ResetPass999") is True


# ---------------------------------------------------------------- modo demonstração

@pytest.fixture
def app_semeado(app, db):
    """Banco com os dados de demonstração, sem ligar o modo demo."""
    from app.catalogo_inicial import carregar_catalogo
    from app.seed_demo import popular_demo

    carregar_catalogo()
    popular_demo()
    return app


@pytest.fixture
def app_demo(app_semeado):
    app_semeado.config.update(MODO_DEMO=True)
    return app_semeado


def _usuario(email):
    return db.session.execute(db.select(Usuario).filter_by(email=email)).scalar_one()


def test_modo_demo_mostra_acesso_rapido_e_loga_conta_exemplo(app_demo):
    cliente = app_demo.test_client()
    pagina = cliente.get("/entrar").get_data(as_text=True)
    assert "Modo Demo" in pagina
    assert "Acesso rápido à demonstração" in pagina
    assert "Entrar como Consultora Demo" in pagina
    assert "Entrar como Administrador Demo" in pagina

    # O botão envia o mesmo POST do formulário de entrada (nada de rotas novas).
    entrada = cliente.post("/entrar", data={"email": "ana.souza@exemplo.com", "senha": SENHA_DEMO})
    assert entrada.status_code == 302
    assert entrada.headers["Location"].endswith("/minha-fila")

    entrada_admin = cliente.post("/entrar", data={"email": "admin@exemplo.com", "senha": SENHA_DEMO})
    assert entrada_admin.status_code == 302


def test_modo_demo_bloqueia_troca_de_senha_da_conta_exemplo(app_demo):
    cliente = app_demo.test_client()
    ana = _usuario("ana.souza@exemplo.com")
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = ana.id

    resposta = cliente.post("/trocar-senha", data={
        "senha_atual": SENHA_DEMO,
        "nova_senha": "OutraSenha456",
        "confirmacao": "OutraSenha456"
    })
    assert resposta.status_code == 403
    assert "as senhas das contas de exemplo ficam bloqueadas" in resposta.get_data(as_text=True)

    db.session.refresh(ana)
    assert ana.verificar_senha(SENHA_DEMO) is True
    assert ana.verificar_senha("OutraSenha456") is False


def test_modo_demo_protege_cadastro_da_conta_exemplo(app_demo):
    cliente = app_demo.test_client()
    admin = _usuario("admin@exemplo.com")
    ana = _usuario("ana.souza@exemplo.com")
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = admin.id

    def enviar(**campos):
        dados = {"nome": ana.nome, "email": ana.email, "papel": ana.papel.value, "ativo": "1"}
        dados.update(campos)
        return cliente.post(f"/cadastros/usuarios/{ana.id}", data=dados, follow_redirects=True)

    # Redefinir senha, trocar e-mail, trocar papel e desativar: tudo bloqueado.
    resposta = enviar(nova_senha="SenhaInvadida1")
    assert "as contas de exemplo ficam protegidas" in resposta.get_data(as_text=True)
    resposta = enviar(email="outra.conta@exemplo.test")
    assert "as contas de exemplo ficam protegidas" in resposta.get_data(as_text=True)
    resposta = enviar(papel="admin")
    assert "as contas de exemplo ficam protegidas" in resposta.get_data(as_text=True)
    resposta = enviar(ativo=None)
    assert "as contas de exemplo ficam protegidas" in resposta.get_data(as_text=True)

    db.session.refresh(ana)
    assert ana.email == "ana.souza@exemplo.com" and ana.papel == Papel.CONSULTOR and ana.ativo
    assert ana.verificar_senha(SENHA_DEMO) is True

    # O nome continua editável: não é via de acesso, é só rótulo da conta.
    resposta = enviar(nome="Ana Souza da Silva")
    assert "Usuário atualizado com sucesso." in resposta.get_data(as_text=True)
    db.session.refresh(ana)
    assert ana.nome == "Ana Souza da Silva"
    assert ana.verificar_senha(SENHA_DEMO) is True


def test_sem_modo_demo_o_comportamento_continua_o_mesmo(app_semeado):
    cliente = app_semeado.test_client()
    pagina = cliente.get("/entrar").get_data(as_text=True)
    assert "Acesso rápido à demonstração" not in pagina
    assert "Modo Demo" not in pagina

    # Sem MODO_DEMO, a conta de exemplo troca de senha normalmente.
    ana = _usuario("ana.souza@exemplo.com")
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = ana.id
    resposta = cliente.post("/trocar-senha", data={
        "senha_atual": SENHA_DEMO,
        "nova_senha": "SenhaDaEquipe7",
        "confirmacao": "SenhaDaEquipe7"
    }, follow_redirects=True)
    assert "Sua senha foi alterada com sucesso.".encode("utf-8") in resposta.data

    db.session.refresh(ana)
    assert ana.verificar_senha("SenhaDaEquipe7") is True
    assert ana.verificar_senha(SENHA_DEMO) is False
