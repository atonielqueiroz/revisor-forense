"""Leitura de .md, .txt e .docx em parágrafos, sem dependências externas."""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
# Recuo esquerdo a partir do qual o parágrafo do Word é tratado como citação em bloco (2 cm).
RECUO_CITACAO_TWIPS = 1134


@dataclass
class Paragrafo:
    texto: str
    local: str          # "linha 12" (texto) ou "parágrafo 12" (Word)
    protegido: bool     # citação em bloco ou código: não é prosa do autor
    titulo: bool = False


def ler(caminho: str | Path) -> list[Paragrafo]:
    caminho = Path(caminho)
    if caminho.suffix.lower() == ".docx":
        return ler_docx(caminho)
    return ler_texto(caminho.read_text(encoding="utf-8-sig"))


def ler_texto(texto: str) -> list[Paragrafo]:
    """Parágrafos separados por linha em branco; `>` marca citação em bloco e ``` marca código."""
    paragrafos: list[Paragrafo] = []
    bloco: list[str] = []
    inicio = 0
    em_codigo = False

    def fechar():
        if bloco:
            linhas = [l for l in bloco if l.strip()]
            citacao = all(l.lstrip().startswith(">") for l in linhas)
            corpo = " ".join(l.strip() for l in linhas)
            titulo = len(linhas) == 1 and corpo.startswith("#")
            paragrafos.append(Paragrafo(corpo, f"linha {inicio}", citacao, titulo))
            bloco.clear()

    for n, linha in enumerate(texto.splitlines(), 1):
        if linha.strip().startswith("```"):
            fechar()
            em_codigo = not em_codigo
            continue
        if em_codigo:
            continue
        if not linha.strip():
            fechar()
            continue
        if not bloco:
            inicio = n
        bloco.append(linha)
    fechar()
    return paragrafos


def _estilos_citacao_e_titulo(z: zipfile.ZipFile) -> tuple[set[str], set[str]]:
    citacao, titulo = set(), set()
    if "word/styles.xml" not in z.namelist():
        return citacao, titulo
    raiz = ET.fromstring(z.read("word/styles.xml"))
    for estilo in raiz.iter(f"{W}style"):
        sid = estilo.get(f"{W}styleId", "")
        nome_el = estilo.find(f"{W}name")
        nome = (nome_el.get(f"{W}val", "") if nome_el is not None else "") + " " + sid
        nome = nome.lower()
        if re.search(r"cita|quote|recuo", nome):
            citacao.add(sid)
        if re.search(r"heading|t[ií]tulo|title", nome):
            titulo.add(sid)
    return citacao, titulo


def ler_docx(caminho: Path) -> list[Paragrafo]:
    with zipfile.ZipFile(caminho) as z:
        estilos_cit, estilos_tit = _estilos_citacao_e_titulo(z)
        raiz = ET.fromstring(z.read("word/document.xml"))
    corpo = raiz.find(f"{W}body")
    paragrafos: list[Paragrafo] = []
    for n, p in enumerate(corpo.iter(f"{W}p"), 1):
        partes = []
        for el in p.iter():
            if el.tag == f"{W}t" and el.text:
                partes.append(el.text)
            elif el.tag in (f"{W}tab", f"{W}br"):
                partes.append(" ")
        texto = "".join(partes).strip()
        if not texto:
            continue
        estilo, recuo = "", 0
        ppr = p.find(f"{W}pPr")
        if ppr is not None:
            ps = ppr.find(f"{W}pStyle")
            if ps is not None:
                estilo = ps.get(f"{W}val", "")
            ind = ppr.find(f"{W}ind")
            if ind is not None:
                valor = ind.get(f"{W}left") or ind.get(f"{W}start") or "0"
                recuo = int(valor) if valor.lstrip("-").isdigit() else 0
        protegido = estilo in estilos_cit or recuo >= RECUO_CITACAO_TWIPS
        paragrafos.append(Paragrafo(texto, f"parágrafo {n}", protegido, estilo in estilos_tit))
    return paragrafos
