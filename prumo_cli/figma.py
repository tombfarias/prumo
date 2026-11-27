"""Integração com o Figma pela API REST: inventário de telas (TL-xxx) e imagens em docs/05-interface.md."""

import json
import os
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

from . import i18n
from .util import ErroPrumo, gravar, ler, marcador_lacuna, progresso, tem_lacuna

API = "https://api.figma.com/v1"
INICIO, FIM = "<!-- prumo:figma:inicio -->", "<!-- prumo:figma:fim -->"
TIPOS_TELA = {"FRAME", "COMPONENT", "COMPONENT_SET"}
CABECALHO = "| ID | Tela | Página do Figma | Link | Casos de uso | Imagem |\n|---|---|---|---|---|---|"


def chave_do_arquivo(url_ou_chave):
    texto = (url_ou_chave or "").strip()
    m = re.search(r"figma\.com/(?:file|design|proto|board|make)/([A-Za-z0-9]+)(?:/[^/?#]*)?(?:/branch/([A-Za-z0-9]+))?", texto)
    if m:
        return m.group(2) or m.group(1)
    if re.fullmatch(r"[A-Za-z0-9]{10,}", texto):
        return texto
    raise ErroPrumo(f"Não reconheci a URL/chave do Figma: {url_ou_chave}")


def _get(caminho, token, abrir=urllib.request.urlopen):
    req = urllib.request.Request(API + caminho, headers={"X-Figma-Token": token, "User-Agent": "prumo"})
    try:
        with abrir(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        mensagens = {
            403: "acesso negado: confira o FIGMA_TOKEN e se ele tem permissão de leitura do arquivo (escopo file_content:read)",
            404: "arquivo não encontrado: confira a URL e se a sua conta tem acesso a ele",
            429: "limite de requisições do Figma atingido: aguarde alguns minutos",
        }
        raise ErroPrumo(f"Figma respondeu {e.code}: {mensagens.get(e.code, e.reason)}") from e
    except urllib.error.URLError as e:
        raise ErroPrumo(f"Sem conexão com a API do Figma: {e.reason}") from e


def listar_telas(chave, token, abrir=urllib.request.urlopen):
    dados = _get(f"/files/{chave}?depth=3", token, abrir)
    telas = []
    for pagina in (dados.get("document") or {}).get("children", []):
        if pagina.get("type") != "CANVAS":
            continue
        for no in pagina.get("children", []):
            if no.get("visible") is False:
                continue
            if no.get("type") in TIPOS_TELA:
                telas.append({"id": no["id"], "nome": no.get("name", ""), "pagina": pagina.get("name", "")})
            elif no.get("type") == "SECTION":
                for filho in no.get("children", []):
                    if filho.get("type") in TIPOS_TELA and filho.get("visible") is not False:
                        telas.append({"id": filho["id"], "nome": f"{no.get('name', '')} / {filho.get('name', '')}",
                                      "pagina": pagina.get("name", "")})
    return dados.get("name", ""), telas


def link_do_no(chave, node_id):
    return f"https://www.figma.com/design/{chave}/?node-id={node_id.replace(':', '-')}"


def _linhas_existentes(texto):
    """TL -> célula 'Casos de uso' já preenchida (é preservada nas sincronizações)."""
    return {tl: dados["ucs"] for tl, dados in _telas_do_inventario(texto).items()}


def _telas_do_inventario(texto):
    """TL -> {'nome', 'ucs'} das linhas já escritas no inventário (manuais ou de sincronizações anteriores)."""
    if INICIO not in texto or FIM not in texto:
        return {}
    trecho = texto.split(INICIO, 1)[1].split(FIM, 1)[0]
    saida = {}
    for linha in trecho.splitlines():
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(celulas) >= 5 and re.fullmatch(r"TL-\d+", celulas[0]) and not tem_lacuna(celulas[1]):
            saida[celulas[0]] = {"nome": celulas[1], "ucs": celulas[4]}
    return saida


def _normalizar_nome(nome):
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", nome) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", sem_acento.lower()).strip()


def sincronizar_telas(projeto, url=None, token=None, imagens=False, escala=1, abrir=urllib.request.urlopen):
    figma = projeto.config.setdefault("figma", {"ativo": True, "arquivo": "", "telas": {}})
    url = url or figma.get("arquivo")
    if not url:
        raise ErroPrumo("Informe a URL do arquivo do Figma (prumo figma telas <url>) ou defina figma.arquivo em projeto.prumo.json.")
    token = token or os.environ.get("FIGMA_TOKEN")
    if not token:
        raise ErroPrumo("Defina a variável de ambiente FIGMA_TOKEN com um token pessoal do Figma "
                        "(Figma → Settings → Security → Personal access tokens, escopo de leitura de arquivos).\n"
                        "PowerShell: $env:FIGMA_TOKEN = 'seu-token'")
    chave = chave_do_arquivo(url)
    progresso(f"Lendo o arquivo do Figma {chave}...")
    nome_arquivo, telas = listar_telas(chave, token, abrir)

    doc = projeto.docs / "05-interface.md"
    if not doc.exists():
        from .projeto import adicionar_documento
        adicionar_documento(projeto, "05-interface")
    texto = ler(doc)
    existentes = _telas_do_inventario(texto)
    ucs = {tl: dados["ucs"] for tl, dados in existentes.items()}

    mapa = figma.setdefault("telas", {})  # node_id -> TL-xxx (IDs estáveis entre sincronizações)
    # Telas escritas à mão (ex.: pela etapa de interface) mantêm o ID: um frame com o mesmo nome assume a TL existente,
    # e os frames novos recebem números que ainda não foram usados.
    manuais = {tl: d for tl, d in existentes.items() if tl not in mapa.values()}
    por_nome = {_normalizar_nome(d["nome"]): tl for tl, d in manuais.items()}
    usados = [int(v.split("-")[1]) for v in mapa.values()] + [int(tl.split("-")[1]) for tl in existentes]
    proximo = max(usados, default=0) + 1
    for tela in telas:
        if tela["id"] in mapa:
            continue
        tl = por_nome.pop(_normalizar_nome(tela["nome"]), None)
        if tl is None:
            tl = f"TL-{proximo:03d}"
            proximo += 1
        mapa[tela["id"]] = tl

    arquivos_imagem = {}
    if imagens and telas:
        arquivos_imagem = baixar_imagens(projeto, chave, token, telas, mapa, escala, abrir)

    linhas = [CABECALHO]
    vistos = set()
    for tela in telas:
        tl = mapa[tela["id"]]
        vistos.add(tl)
        img = f"[png](telas/{arquivos_imagem[tl]})" if tl in arquivos_imagem else (
            f"[png](telas/{tl}.png)" if (projeto.docs / "telas" / f"{tl}.png").exists() else "—")
        nome = tela["nome"].replace("|", "/")
        linhas.append(f"| {tl} | {nome} | {tela['pagina'].replace('|', '/')} | [abrir]({link_do_no(chave, tela['id'])}) | "
                      f"{ucs.get(tl, marcador_lacuna(projeto.idioma) + ': UC-xxx]')} | {img} |")
    for node_id, tl in sorted(mapa.items(), key=lambda kv: kv[1]):
        if tl not in vistos:
            vistos.add(tl)
            linhas.append(f"| {tl} | (não encontrada no Figma) | — | — | {ucs.get(tl, '—')} | — |")
    for tl in sorted(t for t in manuais if t not in vistos):
        linhas.append(f"| {tl} | {manuais[tl]['nome']} | (sem frame no Figma) | — | {manuais[tl]['ucs']} | — |")
    tabela = i18n.traduzir("\n".join(linhas), projeto.idioma)  # cabeçalho e rótulos no idioma do projeto

    if INICIO in texto and FIM in texto:
        antes, resto = texto.split(INICIO, 1)
        depois = resto.split(FIM, 1)[1]
        texto = f"{antes}{INICIO}\n{tabela}\n{FIM}{depois}"
    else:
        titulo = i18n.traduzir("## Inventário de telas (Figma)", projeto.idioma)
        texto = texto.rstrip() + f"\n\n{titulo}\n\n{INICIO}\n{tabela}\n{FIM}\n"
    texto = texto.replace("| Arquivo do Figma | [PREENCHER: URL] |", f"| Arquivo do Figma | [{nome_arquivo or chave}]({url}) |")
    texto = texto.replace("| Figma file | [FILL: URL] |", f"| Figma file | [{nome_arquivo or chave}]({url}) |")
    gravar(doc, texto)
    figma["arquivo"] = url
    figma["ativo"] = True
    projeto.salvar()
    return {"arquivo": nome_arquivo, "telas": len(telas), "novas": len([t for t in telas if t["id"]]),
            "documento": projeto.rel(doc), "imagens": len(arquivos_imagem)}


def baixar_imagens(projeto, chave, token, telas, mapa, escala, abrir=urllib.request.urlopen):
    pasta = projeto.docs / "telas"
    pasta.mkdir(parents=True, exist_ok=True)
    salvos = {}
    ids = [t["id"] for t in telas]
    for i in range(0, len(ids), 40):
        lote = ids[i:i + 40]
        consulta = urllib.parse.urlencode({"ids": ",".join(lote), "format": "png", "scale": escala})
        resposta = _get(f"/images/{chave}?{consulta}", token, abrir)
        for node_id, url in (resposta.get("images") or {}).items():
            if not url:
                continue
            tl = mapa[node_id]
            progresso(f"  baixando {tl}.png")
            try:
                with abrir(urllib.request.Request(url, headers={"User-Agent": "prumo"}), timeout=120) as r:
                    (pasta / f"{tl}.png").write_bytes(r.read())
                salvos[tl] = f"{tl}.png"
            except Exception as e:  # imagem é opcional
                progresso(f"  falhou ({e}); seguindo")
    return salvos
