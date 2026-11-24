from app.extensions import db
from app.models import ApelidoEtapa, CategoriaServico, EtapaModelo, ServicoCatalogo, Trilha
from app.texto import normalizar_texto

TRILHAS = [
    ("GERAL", "Geral"),
    ("VISTOS", "Vistos"),
    ("VIP", "VIP"),
    ("ON", "Primeiro contato"),
]


def _etapa(texto, regra_prazo=None, o_que_e=None, importancia=None, neg=None, link=None, apelidos=()):
    return {
        "texto_erp": texto,
        "regra_prazo": regra_prazo,
        "o_que_e": o_que_e,
        "importancia": importancia,
        "quando_cabe_neg": neg,
        "link_gravacao": link,
        "apelidos": list(apelidos),
    }


# Em cada trilha, a ordem da lista é a ordem de exibição (aproximadamente a do processo).
ETAPAS = {
    "GERAL": [
        _etapa(
            "SA - GERAL - Realização de Onboarding com novos alunos (pacotes)",
            regra_prazo="Até 7 dias após a confirmação da matrícula.",
            o_que_e="Apresentar o sistema, a equipe e os próximos passos ao aluno recém-matriculado.",
            importancia="Alinhar expectativas e evitar dúvidas repetidas nos contatos seguintes.",
            neg="Sem NEG.",
        ),
        _etapa(
            "SA - GERAL - Ter a cópia do passaporte do aluno",
            regra_prazo="Assim que o programa for confirmado.",
            o_que_e="Ter a cópia das páginas de identificação do passaporte.",
            importancia="Emissão dos documentos corretos.\nVerificar validade.",
            neg="Aguardando retorno do aluno.\nMais de 90 dias do embarque.",
        ),
        _etapa(
            "SA - GERAL - Cadastrar flight details",
            regra_prazo="30 a 60 dias antes do embarque.",
            o_que_e="Cadastrar a passagem aérea completa do aluno.",
            importancia="Conferir se está de acordo com as datas de acomodação e as cidades corretas.\n"
            "Confirmar que o aluno vai embarcar.",
            neg="Aguardando retorno do visto.\nMais de 30 dias do embarque.",
        ),
        _etapa(
            "SA - GERAL - Ter confirmação de realização do teste de nivelamento (requisito para embarque)",
            regra_prazo="Antes do embarque.",
            o_que_e="Confirmar que o aluno fez o teste de nivelamento exigido pela escola.",
            importancia="Chegar na escola sem pendências.",
            neg="Sem NEG.",
        ),
        _etapa(
            "SA - GERAL - Agendar consultoria de integração do Summer Schools",
            regra_prazo="Depois da confirmação da compra do programa de curta duração.",
            o_que_e="Agendar a consultoria de integração do programa teen de curta duração com a base de destino.",
            importancia="Programa de curta duração tem prazo apertado: a integração precisa sair cedo.",
            neg="Sem NEG.",
        ),
        _etapa(
            "SA - GERAL - Realizar contato de relacionamento pré - embarque",
            regra_prazo="10 dias antes do embarque.",
            o_que_e="Verificar se o aluno está preparado para a viagem.",
            importancia="Reforçar a lista de documentos.\nEsclarecer as últimas dúvidas do aluno.",
            neg="Sem NEG.",
            apelidos=["SA - GERAL - Realizar contato de relacionamento pré-embarque"],
        ),
        _etapa(
            "SA - GERAL - Realizar contato de relacionamento pós embarque (pré NPS)",
            regra_prazo="3 dias depois do embarque.",
            o_que_e="Garantir que foi tudo certo na chegada do aluno.",
            importancia="Contato ativo com o aluno.\nResolver se teve algum problema.",
            neg="Sem NEG.",
        ),
    ],
    "VISTOS": [
        _etapa(
            "SA - VISTOS - Realizar a aplicação do CAQ (visto de estudo - Canadá - Quebec)",
            regra_prazo="165 dias antes do embarque.",
            o_que_e="Realizar a aplicação do certificado provincial de estudo.",
            importancia="Realizar dentro do prazo para garantir que o aluno consiga embarcar.",
            neg="Falta documento da escola.\nAguardando retorno do aluno.",
        ),
        _etapa(
            "SA - VISTOS - Ter a primeira versão da carta de intenções e do formulário de visto preenchido",
            regra_prazo="148 dias antes do embarque.",
            o_que_e="Conferir carta de intenções e formulários.",
            importancia="Fazer com antecedência e garantir que terá tudo certo para a aplicação.\n"
            "Informações necessárias e corretas para a aplicação.",
            neg="Sem NEG.",
        ),
        _etapa(
            "SA - VISTOS - Entrega da 1a documentação para aplicação do visto",
            regra_prazo="120 dias antes do embarque.",
            o_que_e="Garantir que os documentos sejam enviados dentro do prazo.\n"
            "Lembrete dos documentos pendentes.",
            importancia="Ter, dentro do prazo de aplicação, os documentos certos.",
            neg="Documentos ainda com tradução.\nAguardando retorno do aluno.",
        ),
        _etapa(
            "SA - VISTOS - Documentação OK ? Envio para embaixada/consulado",
            regra_prazo="30 a 120 dias antes do embarque, conforme o destino.",
            o_que_e="Finalizar o procedimento de visto.",
            importancia="Aplicar com atenção e no prazo para o aluno embarcar a tempo.",
            neg="Documentos com tradução pendente.\nSe tiver ok do aluno de que pode atrasar.",
            apelidos=["SA - VISTOS - Documentação OK - Envio para a embaixada/consulado"],
        ),
        _etapa(
            "SA - VISTOS - Ter uma cópia do visto/negativa",
            regra_prazo="15 dias antes do embarque.",
            o_que_e="Anexar a cópia do visto.",
            importancia="Métricas internas.\nAcompanhamento de cada aluno.",
            neg="Se o visto não saiu.",
        ),
    ],
    "VIP": [
        _etapa(
            "SA - VIP - Primeiro contato de relacionamento com aluno",
            regra_prazo="Assim que o aluno for identificado como VIP.",
            o_que_e="Primeiro contato de relacionamento com o aluno VIP.",
            importancia="Aluno prioritário: atendimento próximo desde o começo do programa.",
            neg="Sem NEG.",
        ),
    ],
    "ON": [
        _etapa(
            "SA - ON - Contact student who didn`t login after enrolment",
            regra_prazo="7 dias da matrícula.",
            o_que_e="Informar ao aluno sobre a área do aluno.",
            importancia="Deixar o aluno ciente da área do aluno, da necessidade e da importância dela.",
            neg="Não tem NEG.",
        ),
    ],
}

# Página de ajuda sobre NEG.
ORIENTACOES_NEG = {
    "geral": [
        "Alinhamento sobre as possíveis NEGs.",
        "Fazer anotações no bloco de notas ajuda a lembrar do caso depois; usar o campo da NEG apenas para a NEG.",
        "Mesmo que não seja mais um indicador, precisamos ter atenção, pois faz parte da experiência do aluno.",
    ],
    "dicas": [
        "Puxar cada um dos procedimentos separados.",
        "Alguns procedimentos, principalmente os ligados ao visto, puxar com bastante antecedência e ir cobrando os documentos.",
        "Passaporte e flight details (se visto aprovado): já cobrar com 90, 100, 120 dias antes do procedimento.",
    ],
    "nao_e_neg": [
        "Em qualquer procedimento: sem retorno do aluno e tentativas de contato.",
    ],
    "excecoes": [
        "Exceções de matrícula.",
        "Alteração de data: precisa ter pauta ou confirmação por escrito do aluno de que vai alterar.",
        "Deadline (cuidar sempre, pois pode gerar cancelamento).",
        "Se já sabe que não vai ter NEG, não coloca nada.",
    ],
}

SERVICOS = {
    CategoriaServico.CURSO: [
        "Curso Premium", "Curso Budget", "Curso Smart", "Curso + Trabalho", "Grupo Premium",
        "Summer Schools", "Winter Schools", "Viagem Cultural", "Vancouver Experience",
    ],
    CategoriaServico.VISTO: [
        "Visto - Estados Unidos", "Visto - Canadá", "Visto - Canadá - eTA", "SEVIS",
    ],
    CategoriaServico.AVULSO: ["Transfer (chegada e saída)", "Seguro Viagem"],
    CategoriaServico.IGNORADO: ["Valores Extras", "Reserva técnica"],
}


def nome_da_etapa(texto_erp: str) -> str:
    """'SA - VISTOS - Agendar consulta' -> 'Agendar consulta'."""
    partes = texto_erp.split(" - ", 2)
    return partes[2].strip() if len(partes) == 3 else texto_erp.strip()


def buscar_etapa_por_texto(texto: str) -> EtapaModelo | None:
    apelido = db.session.execute(
        db.select(ApelidoEtapa).filter_by(texto_normalizado=normalizar_texto(texto))
    ).scalar_one_or_none()
    return apelido.etapa if apelido else None


def carregar_catalogo() -> dict:
    """Cria o que ainda não existe. Não altera registros existentes, exceto
    serviços ainda "não classificados" e trilhas com nome provisório (igual ao código)."""
    contagem = {"trilhas": 0, "etapas": 0, "apelidos": 0, "servicos": 0}

    trilhas = {t.codigo: t for t in db.session.execute(db.select(Trilha)).scalars()}
    for ordem, (codigo, nome) in enumerate(TRILHAS, start=1):
        if codigo not in trilhas:
            trilhas[codigo] = Trilha(codigo=codigo, nome=nome, ordem=ordem)
            db.session.add(trilhas[codigo])
            contagem["trilhas"] += 1
        elif trilhas[codigo].nome == codigo and nome != codigo:
            # Nome igual ao código = provisório, ninguém deu nome ainda.
            trilhas[codigo].nome = nome
            contagem["trilhas"] += 1
    db.session.flush()

    for codigo, etapas in ETAPAS.items():
        for ordem, dados in enumerate(etapas, start=1):
            textos = [dados["texto_erp"], *dados["apelidos"]]
            etapa = next((e for e in map(buscar_etapa_por_texto, textos) if e), None)
            if etapa is None:
                campos = {k: v for k, v in dados.items() if k != "apelidos"}
                etapa = EtapaModelo(
                    trilha=trilhas[codigo], nome=nome_da_etapa(dados["texto_erp"]), ordem=ordem, **campos
                )
                db.session.add(etapa)
                contagem["etapas"] += 1
            for texto in textos:
                if buscar_etapa_por_texto(texto) is None:
                    db.session.add(ApelidoEtapa(etapa=etapa, texto=texto, texto_normalizado=normalizar_texto(texto)))
                    db.session.flush()
                    contagem["apelidos"] += 1

    existentes = {s.nome_normalizado: s for s in db.session.execute(db.select(ServicoCatalogo)).scalars()}
    for categoria, nomes in SERVICOS.items():
        for nome in nomes:
            servico = existentes.get(normalizar_texto(nome))
            if servico is None:
                db.session.add(ServicoCatalogo(nome=nome, nome_normalizado=normalizar_texto(nome), categoria=categoria))
                contagem["servicos"] += 1
            elif servico.categoria == CategoriaServico.NAO_CLASSIFICADO and categoria != servico.categoria:
                # "Não classificado" quer dizer que ninguém decidiu ainda: pode receber a classificação nova.
                servico.categoria = categoria
                contagem["servicos"] += 1
    db.session.flush()

    # Público teen: na primeira vez (nenhum serviço marcado ainda), marca os programas teen.
    # Depois disso, quem decide é a tela Cadastros → Público teen.
    from app import publico_teen

    ja_configurado = db.session.execute(db.select(ServicoCatalogo.id).filter_by(teen=True).limit(1)).first()
    if ja_configurado is None:
        nomes_teen = {normalizar_texto(n) for n in publico_teen.SERVICOS_TEEN_PADRAO}
        for servico in db.session.execute(db.select(ServicoCatalogo)).scalars():
            if servico.nome_normalizado in nomes_teen:
                servico.teen = True
                contagem["servicos"] += 1
        publico_teen.recalcular()

    db.session.commit()
    return contagem
