import io
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from revisor_forense import ler, ler_texto, revisar  # noqa: E402
from revisor_forense.cli import main  # noqa: E402
from revisor_forense.motor import dobrar, periodos  # noqa: E402


def ids(texto, perfil="padrao", **kw):
    return [a["regra"] for a in revisar(ler_texto(texto), perfil, **kw)["achados"]]


class Dobra(unittest.TestCase):
    def test_preserva_comprimento(self):
        texto = "Ação, CORAÇÃO e Cenário — à luz"
        self.assertEqual(len(dobrar(texto)), len(texto))
        self.assertEqual(dobrar("Cenário"), "cenario")


class Regras(unittest.TestCase):
    def test_formulas_qualificadores_e_vocabulario(self):
        texto = ("A prova é robusta, e cumpre destacar que, nesse contexto, a defesa precisa articular teses "
                 "autônomas e distintas na moldura fática, à luz da Carta Magna, conforme o depoimento firme.")
        achados = ids(texto, min_palavras=0)
        for esperado in ("Q01", "F03", "F07", "V01", "V02", "V03", "V04", "F08", "V06", "Q03"):
            self.assertIn(esperado, achados)

    def test_travessao_e_anuncio_de_conclusao(self):
        achados = ids("A nulidade é manifesta — e o prejuízo resta evidente nos autos do processo em exame.")
        self.assertIn("P01", achados)
        self.assertEqual(achados.count("Q02"), 2)

    def test_termos_tecnicos_nao_sao_apontados(self):
        texto = ("O laudo descreveu a trajetória do projétil, o recurso indicou o acórdão paradigma, "
                 "o fato notório dispensa prova e a defesa impetrou habeas corpus contra o bis in idem.")
        self.assertEqual([i for i in ids(texto) if i not in ("E01",)], [])

    def test_citacoes_nao_sao_revisadas(self):
        texto = ('A testemunha declarou que "a prova é robusta e cristalina" na audiência de instrução.\n\n'
                 "> O depoimento firme — robusto e evidente — articula teses autônomas.\n")
        self.assertEqual(ids(texto), [])

    def test_perfil_estrito_acrescenta_vetos(self):
        texto = ("A decisão manteve a prisão sem indicar fato novo e deixou de examinar a conduta própria "
                 "do acusado, sem que o juízo alcançasse a contemporaneidade exigida pelo art. 312 do CPP.")
        self.assertEqual([i for i in ids(texto) if i.startswith("S")], [])
        estrito = ids(texto, "estrito")
        for esperado in ("S01", "S02", "S05", "S06"):
            self.assertIn(esperado, estrito)

    def test_sem_seguido_de_substantivo_nao_e_infinitivo(self):
        texto = "A audiência ocorreu sem qualquer registro, sem prejuízo do exame e sem parecer do Ministério Público."
        self.assertNotIn("S06", ids(texto, "estrito"))

    def test_alerta_no_padrao_vira_bloqueio_no_estrito(self):
        texto = "A defesa passou a articular a nulidade — conforme os autos do processo criminal em exame."
        grav = lambda perfil: {a["regra"]: a["gravidade"] for a in revisar(ler_texto(texto), perfil)["achados"]}
        self.assertEqual((grav("padrao")["V01"], grav("padrao")["P01"]), ("alerta", "alerta"))
        self.assertEqual((grav("estrito")["V01"], grav("estrito")["P01"]), ("bloqueio", "bloqueio"))

    def test_termos_de_lei_e_vocativo_nao_sao_apontados(self):
        texto = "EGRÉGIA CÂMARA CRIMINAL, a decisão dos jurados é manifestamente contrária à prova dos autos."
        self.assertNotIn("Q01", ids(texto))
        self.assertNotIn("Q04", ids(texto))

    def test_desativar_regra(self):
        self.assertNotIn("V04", ids("A moldura fática foi descrita no relatório final da autoridade policial.",
                                    desativadas={"v04"}))


class Estrutura(unittest.TestCase):
    def test_periodo_curto_so_em_paragrafo_com_varios_periodos(self):
        curto = ("A prova é insuficiente. O art. 155 do CPP veda condenação fundada exclusivamente em elementos "
                 "colhidos no inquérito policial, e a sentença indicou como fundamento da autoria apenas o "
                 "reconhecimento fotográfico feito na delegacia, que não foi repetido em juízo.")
        self.assertIn("E01", ids(curto))
        self.assertNotIn("E01", ids("Termos em que pede deferimento."))

    def test_abreviaturas_nao_quebram_periodo(self):
        texto = "Conforme o art. 5º, inc. LVII, da Constituição e as fls. 12, o Min. Relator acolheu o pedido."
        self.assertEqual(len(periodos(texto)), 1)

    def test_abertura_com_ao_infinitivo(self):
        self.assertIn("E02", ids("Ao examinar a decisão, o tribunal reconheceu a nulidade da busca domiciliar realizada."))
        self.assertNotIn("E02", ids("Ao contrário do que consta na sentença, a busca ocorreu sem mandado judicial."))

    def test_metricas(self):
        rel = revisar(ler_texto("Um período com seis palavras aqui. Outro período com cinco palavras."))
        self.assertEqual(rel["metricas"]["periodos"], 2)


def _docx(caminho, paragrafos):
    w = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    corpo = ""
    for texto, recuo in paragrafos:
        ppr = f'<w:pPr><w:ind w:left="{recuo}"/></w:pPr>' if recuo else ""
        corpo += f"<w:p>{ppr}<w:r><w:t>{texto}</w:t></w:r></w:p>"
    with zipfile.ZipFile(caminho, "w") as z:
        z.writestr("word/document.xml", f"<w:document {w}><w:body>{corpo}</w:body></w:document>")


class Word(unittest.TestCase):
    def test_docx_le_paragrafos_e_protege_citacao_recuada(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "peca.docx"
            _docx(arq, [("A prova é robusta conforme os autos do processo criminal em exame.", 0),
                        ("O depoimento firme e robusto da vítima.", 2268)])
            pars = ler(arq)
            self.assertEqual([p.protegido for p in pars], [False, True])
            achados = revisar(pars)["achados"]
            self.assertEqual([a["local"] for a in achados], ["parágrafo 1"])


class Linha(unittest.TestCase):
    def test_codigo_de_saida_e_json(self):
        with tempfile.TemporaryDirectory() as d:
            ruim, bom, saida = Path(d) / "ruim.md", Path(d) / "bom.md", Path(d) / "r.json"
            ruim.write_text("Vale ressaltar que a prova é robusta.\n", encoding="utf-8")
            bom.write_text("A sentença fundamentou a condenação apenas no reconhecimento feito na delegacia.\n",
                           encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(ruim), "--json", str(saida)]), 1)
                self.assertEqual(main([str(bom)]), 0)
                self.assertEqual(main(["--listar-regras"]), 0)
            self.assertEqual(json.loads(saida.read_text(encoding="utf-8"))[str(ruim)]["bloqueios"], 2)


if __name__ == "__main__":
    unittest.main()
