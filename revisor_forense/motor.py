"""Aplicação das regras sobre os parágrafos."""
from __future__ import annotations

import re
import statistics
import unicodedata
from dataclasses import asdict, dataclass

from .leitura import Paragrafo
from .regras import REGRAS_ESTRUTURA, regras_do_perfil

# Trechos entre aspas são texto alheio (lei, decisão, depoimento) e não são revisados.
ASPAS = re.compile(r'"[^"\n]*"|“[^”]*”|«[^»]*»|‘[^’]*’')
ABREVIATURAS = {
    "art", "arts", "inc", "incs", "al", "par", "fl", "fls", "p", "pp", "n", "nº", "min", "rel", "des", "dr",
    "dra", "exmo", "exma", "sr", "sra", "ss", "cf", "v", "vol", "ed", "doc", "docs", "id", "ev", "proc",
    "sec", "obs", "ex", "etc", "c", "tj", "stj", "stf", "res", "cap", "t",
}
PALAVRA = re.compile(r"[\wÀ-ÿ][\wÀ-ÿ'\-/.,º°ª§]*")


@dataclass
class Achado:
    regra: str
    categoria: str
    rotulo: str
    gravidade: str
    local: str
    trecho: str
    orientacao: str


def dobrar(texto: str) -> str:
    """Minúsculas sem acento, preservando o comprimento (cada caractere vira um)."""
    saida = []
    for c in texto:
        base = unicodedata.normalize("NFD", c)[0].lower()
        saida.append(base if len(base) == 1 else c)
    return "".join(saida)


def mascarar_aspas(texto: str) -> str:
    return ASPAS.sub(lambda m: " " * len(m.group(0)), texto)


def periodos(texto: str) -> list[tuple[int, str]]:
    """Divide o parágrafo em períodos, respeitando abreviaturas jurídicas e números."""
    resultado, inicio = [], 0
    for m in re.finditer(r"[.!?]+(?=\s+[\"“(]?[A-ZÀ-Ý])", texto):
        anterior = re.search(r"([\wÀ-ÿº]+)$", texto[inicio:m.start()])
        if anterior and (anterior.group(1).lower() in ABREVIATURAS or len(anterior.group(1)) == 1):
            continue
        resultado.append((inicio, texto[inicio:m.end()].strip()))
        inicio = m.end()
        while inicio < len(texto) and texto[inicio].isspace():
            inicio += 1
    resto = texto[inicio:].strip()
    if resto:
        resultado.append((inicio, resto))
    return resultado


def contar_palavras(texto: str) -> int:
    return len(PALAVRA.findall(texto))


def _recorte(texto: str, inicio: int, fim: int, folga: int = 50) -> str:
    a, b = max(0, inicio - folga), min(len(texto), fim + folga)
    return ("..." if a else "") + texto[a:b].strip() + ("..." if b < len(texto) else "")


def revisar(paragrafos: list[Paragrafo], perfil: str = "padrao", min_palavras: int = 15,
            desativadas: set[str] | None = None) -> dict:
    desativadas = {d.upper() for d in (desativadas or set())}
    regras = [(r, re.compile(r.padrao, re.I)) for r in regras_do_perfil(perfil) if r.id not in desativadas]
    achados: list[Achado] = []
    tamanhos: list[int] = []

    for par in paragrafos:
        if par.protegido:
            continue
        busca = dobrar(mascarar_aspas(par.texto))
        for regra, rx in regras:
            for m in rx.finditer(busca):
                gravidade = "bloqueio" if perfil == "estrito" and regra.estrito_bloqueia else regra.gravidade
                achados.append(Achado(regra.id, regra.categoria, regra.rotulo, gravidade, par.local,
                                      _recorte(par.texto, m.start(), m.end()), regra.orientacao))
        if par.titulo:
            continue

        lista = periodos(par.texto)
        # O período curto só interessa dentro de parágrafo de argumentação; numeração de item,
        # vocativo, fecho ("Pede deferimento.") e rótulos ("Procuração.") ficam fora.
        argumentativo = len(lista) >= 2 and contar_palavras(par.texto) >= 40
        for inicio, periodo in lista:
            n = contar_palavras(periodo)
            tamanhos.append(n)
            if "E02" not in desativadas and re.match(r"ao\s+[a-z]+(?:ar|er|ir|por)\b", dobrar(periodo)):
                cat, rot, grav, ori = REGRAS_ESTRUTURA["E02"]
                if perfil == "estrito":
                    grav = "bloqueio"
                achados.append(Achado("E02", cat, rot, grav, par.local, _recorte(periodo, 0, 0, 90), ori))
            if "E01" not in desativadas and argumentativo and 4 <= n < min_palavras:
                cat, rot, grav, ori = REGRAS_ESTRUTURA["E01"]
                achados.append(Achado("E01", cat, rot, grav, par.local, periodo,
                                      f"{ori} ({n} palavras; mínimo de referência {min_palavras}.)"))

    metricas = {
        "periodos": len(tamanhos),
        "media_palavras": round(statistics.mean(tamanhos), 1) if tamanhos else 0,
        "desvio_padrao": round(statistics.pstdev(tamanhos), 1) if len(tamanhos) > 1 else 0,
        "referencia": "média entre 18 e 32 palavras e desvio de 8 ou mais indicam ritmo variado",
    }
    return {
        "perfil": perfil,
        "bloqueios": sum(1 for a in achados if a.gravidade == "bloqueio"),
        "alertas": sum(1 for a in achados if a.gravidade == "alerta"),
        "metricas": metricas,
        "achados": [asdict(a) for a in achados],
    }
