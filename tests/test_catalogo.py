from app.catalogo_inicial import ETAPAS, buscar_etapa_por_texto, carregar_catalogo, nome_da_etapa
from app.models import CategoriaServico, EtapaModelo, ServicoCatalogo, Trilha

# Textos de procedimento que aparecem nas exportações de checklist e precisam de etapa no catálogo.
PROCEDIMENTOS_CSV = [
    "SA - GERAL - Realização de Onboarding com novos alunos (pacotes)",
    "SA - GERAL - Ter a cópia do passaporte do aluno",
    "SA - GERAL - Cadastrar flight details",
    "SA - GERAL - Ter confirmação de realização do teste de nivelamento (requisito para embarque)",
    "SA - GERAL - Agendar consultoria de integração do Summer Schools",
    "SA - GERAL - Realizar contato de relacionamento pré - embarque",
    "SA - GERAL - Realizar contato de relacionamento pré-embarque",
    "SA - GERAL - Realizar contato de relacionamento pós embarque (pré NPS)",
    "SA - VISTOS - Realizar a aplicação do CAQ (visto de estudo - Canadá - Quebec)",
    "SA - VISTOS - Ter a primeira versão da carta de intenções e do formulário de visto preenchido",
    "SA - VISTOS - Entrega da 1a documentação para aplicação do visto",
    "SA - VISTOS - Documentação OK ? Envio para embaixada/consulado",
    "SA - VISTOS - Documentação OK - Envio para a embaixada/consulado",
    "SA - VIP - Primeiro contato de relacionamento com aluno",
    "SA - ON - Contact student who didn`t login after enrolment",
]


def test_carrega_trilhas_e_etapas(db):
    carregar_catalogo()
    assert [t.codigo for t in db.session.execute(db.select(Trilha).order_by(Trilha.ordem)).scalars()] == [
        "GERAL", "VISTOS", "VIP", "ON",
    ]
    assert db.session.query(EtapaModelo).count() == sum(len(v) for v in ETAPAS.values()) == 14


def nomes_da_trilha(db, codigo):
    trilha = db.session.execute(db.select(Trilha).filter_by(codigo=codigo)).scalar_one()
    return [e.nome for e in sorted(trilha.etapas, key=lambda e: e.ordem)]


def test_geral_termina_no_contato_pre_embarque(db):
    carregar_catalogo()
    geral = nomes_da_trilha(db, "GERAL")
    assert "pré - embarque" in geral[-2]  # antes do contato pós-embarque
    assert "pós embarque" in geral[-1]


def test_apelido_aponta_para_a_mesma_etapa(db):
    carregar_catalogo()
    com_espaco = buscar_etapa_por_texto("SA - GERAL - Realizar contato de relacionamento pré - embarque")
    sem_espaco = buscar_etapa_por_texto("SA - GERAL - Realizar contato de relacionamento pré-embarque")
    assert com_espaco.id == sem_espaco.id
    interrogacao = buscar_etapa_por_texto("SA - VISTOS - Documentação OK ? Envio para embaixada/consulado")
    com_traco = buscar_etapa_por_texto("SA - VISTOS - Documentação OK - Envio para a embaixada/consulado")
    assert interrogacao.id == com_traco.id


def test_trilha_on_e_primeiro_contato(db):
    carregar_catalogo()
    assert db.session.execute(db.select(Trilha).filter_by(codigo="ON")).scalar_one().nome == "Primeiro contato"


def test_carga_da_nome_a_trilha_provisoria_mas_respeita_nome_editado(db):
    carregar_catalogo()
    trilhas = {t.codigo: t for t in db.session.execute(db.select(Trilha)).scalars()}
    trilhas["ON"].nome = "ON"  # banco antigo, nome provisório
    trilhas["VIP"].nome = "Relacionamento"  # editado pela interface
    db.session.commit()
    carregar_catalogo()
    assert trilhas["ON"].nome == "Primeiro contato"
    assert trilhas["VIP"].nome == "Relacionamento"


def test_segunda_carga_nao_duplica(db):
    carregar_catalogo()
    assert carregar_catalogo() == {"trilhas": 0, "etapas": 0, "apelidos": 0, "servicos": 0}
    assert db.session.query(EtapaModelo).count() == 14


def test_segunda_carga_nao_sobrescreve_edicao(db):
    carregar_catalogo()
    etapa = buscar_etapa_por_texto("SA - GERAL - Cadastrar flight details")
    etapa.regra_prazo = "Editado pela equipe"
    db.session.commit()
    carregar_catalogo()
    assert buscar_etapa_por_texto("SA - GERAL - Cadastrar flight details").regra_prazo == "Editado pela equipe"


def test_todo_procedimento_do_csv_tem_etapa(db):
    carregar_catalogo()

    for texto in PROCEDIMENTOS_CSV:
        etapa = buscar_etapa_por_texto(texto)
        assert etapa is not None, texto
        esperada = texto.split(" - ")[1]
        assert etapa.trilha.codigo == esperada, texto


def test_servicos_classificados(db):
    carregar_catalogo()
    categorias = {s.nome: s.categoria for s in db.session.execute(db.select(ServicoCatalogo)).scalars()}
    assert categorias["Summer Schools"] == CategoriaServico.CURSO
    assert categorias["Grupo Premium"] == CategoriaServico.CURSO
    assert categorias["Visto - Canadá - eTA"] == CategoriaServico.VISTO
    assert categorias["Transfer (chegada e saída)"] == CategoriaServico.AVULSO
    assert categorias["Valores Extras"] == CategoriaServico.IGNORADO
    assert CategoriaServico.NAO_CLASSIFICADO not in categorias.values()


def test_carga_classifica_servico_pendente_mas_respeita_decisao_da_equipe(db):
    carregar_catalogo()
    servicos = {s.nome: s for s in db.session.execute(db.select(ServicoCatalogo)).scalars()}
    servicos["Curso Budget"].categoria = CategoriaServico.NAO_CLASSIFICADO  # banco antigo, ainda sem decisão
    servicos["Seguro Viagem"].categoria = CategoriaServico.IGNORADO  # decisão tomada pela interface
    db.session.commit()
    carregar_catalogo()
    assert servicos["Curso Budget"].categoria == CategoriaServico.CURSO
    assert servicos["Seguro Viagem"].categoria == CategoriaServico.IGNORADO


def test_nome_da_etapa():
    assert nome_da_etapa("SA - VISTOS - Realizar a aplicação do CAQ (visto de estudo - Canadá - Quebec)") == (
        "Realizar a aplicação do CAQ (visto de estudo - Canadá - Quebec)"
    )
