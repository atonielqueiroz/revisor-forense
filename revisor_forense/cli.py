"""Linha de comando: revisor-forense peca.docx [outra.md ...]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .leitura import ler
from .motor import revisar
from .regras import REGRAS, REGRAS_ESTRUTURA


def _listar() -> None:
    for r in REGRAS:
        print(f"{r.id}  [{r.gravidade:8}] [{r.perfil:7}] {r.rotulo}")
    for rid, (_, rotulo, grav, _) in REGRAS_ESTRUTURA.items():
        print(f"{rid}  [{grav:8}] [padrao ] {rotulo}")


def _imprimir(caminho: str, rel: dict) -> None:
    m = rel["metricas"]
    print(f"\n== {caminho}  (perfil {rel['perfil']})")
    for a in rel["achados"]:
        marca = "BLOQUEIO" if a["gravidade"] == "bloqueio" else "alerta  "
        print(f"{marca} {a['regra']} | {a['local']} | {a['rotulo']}")
        print(f"         trecho: {a['trecho']}")
        print(f"         como corrigir: {a['orientacao']}")
    print(f"-- {rel['bloqueios']} bloqueio(s), {rel['alertas']} alerta(s); "
          f"{m['periodos']} períodos, média de {m['media_palavras']} palavras, desvio {m['desvio_padrao']} "
          f"({m['referencia']}).")


def main(argv: list[str] | None = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(
        prog="revisor-forense",
        description="Aponta marcas de escrita automatizada e fórmulas de praxe em peças jurídicas "
                    "(.docx, .md, .txt). Não substitui a revisão do advogado.")
    ap.add_argument("arquivos", nargs="*", help="arquivos a revisar")
    ap.add_argument("--perfil", choices=["padrao", "estrito"], default="padrao")
    ap.add_argument("--min-palavras", type=int, default=15,
                    help="período abaixo disso, dentro de parágrafo com mais de um período, gera alerta (padrão 15)")
    ap.add_argument("--desativar", default="", help="IDs de regra separados por vírgula, por exemplo Q05,V07")
    ap.add_argument("--json", metavar="SAIDA", help="grava o relatório completo em JSON")
    ap.add_argument("--listar-regras", action="store_true")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)

    if args.listar_regras:
        _listar()
        return 0
    if not args.arquivos:
        ap.print_usage()
        return 2

    desativadas = {x.strip() for x in args.desativar.split(",") if x.strip()}
    relatorios, bloqueou = {}, False
    for arquivo in args.arquivos:
        try:
            rel = revisar(ler(arquivo), args.perfil, args.min_palavras, desativadas)
        except (OSError, ValueError, KeyError) as erro:
            print(f"erro ao ler {arquivo}: {erro}", file=sys.stderr)
            return 2
        relatorios[arquivo] = rel
        bloqueou = bloqueou or rel["bloqueios"] > 0
        _imprimir(arquivo, rel)
    if args.json:
        Path(args.json).write_text(json.dumps(relatorios, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nZero apontamentos não significa texto aprovado: a revisão jurídica e factual é do advogado.")
    return 1 if bloqueou else 0


if __name__ == "__main__":
    sys.exit(main())
