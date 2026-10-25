"""Catálogo de regras do revisor.

Os padrões são aplicados sobre o texto "dobrado": minúsculo e sem acentos ("Cenário" vira
"cenario"), com o mesmo comprimento do original, de modo que a posição de cada achado
continua a apontar para o trecho verdadeiro. Por isso os padrões abaixo não usam acento.

Gravidade:
- "bloqueio": o texto não deve sair com a ocorrência (código de saída 1);
- "alerta": pede exame humano, porque o termo pode ter uso técnico legítimo.

Perfil:
- "padrao": vícios reconhecidos de escrita automatizada e de fórmula de praxe;
- "estrito": acrescenta vetos de estilo mais rigorosos, úteis para quem quer prosa seca e
  constatações no passado ("a decisão não especificou" em vez de "sem especificar").
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Regra:
    id: str
    categoria: str
    rotulo: str
    padrao: str
    gravidade: str
    orientacao: str
    perfil: str = "padrao"
    estrito_bloqueia: bool = False  # alerta no perfil padrão, bloqueio no estrito


# Infinitivo para os vetos de "sem" e "deixou de": terminação -ar, -er, -ir, a família de "pôr"
# (propor, expor, impor) e a ênclise ("intima-lo", "ouvi-la"), com próclise opcional.
_CLITICO = r"(?:(?:se|lhe|lhes|me|nos|te)\s+)?"
_INFINITIVO = r"(?:[a-z]+(?:ar|er|ir|por)(?:-(?:se|lhes?|me|nos))?\b|[a-z]+(?:a|e|i|o)-l[oa]s?\b)"
# Palavras que terminam como infinitivo e não são verbo depois de "sem".
_SEM_NAO_VERBO = (
    "qualquer", "quaisquer", "lugar", "mulher", "par", "carater", "parecer", "poder", "dever", "prazer",
    "olhar", "mar", "bar", "lar", "altar", "acucar", "colher", "talher", "celular", "revolver", "titular",
    "familiar", "auxiliar", "preliminar", "militar", "particular", "similar", "singular", "regular",
    "exemplar", "popular", "mister", "lider", "cadaver", "reporter", "vapor", "torpor", "estupor",
    "prejuizo",
)

REGRAS: list[Regra] = [
    # Fórmulas anunciadoras e metadiscurso
    Regra("F01", "formula", "Fórmula anunciadora vazia",
          r"\be\s+importante\s+(?:ressaltar|destacar|observar|frisar|salientar|registrar)\b",
          "bloqueio", "Retire o anúncio e apresente o fato, a norma e a consequência."),
    Regra("F02", "formula", "Vale ressaltar / vale destacar",
          r"\bvale\s+(?:destacar|ressaltar|notar|observar|lembrar|registrar|frisar)\b",
          "bloqueio", "Retire o anúncio e comece pela premissa."),
    Regra("F03", "formula", "Cumpre destacar / cumpre observar",
          r"\bcumpre\s+(?:destacar|observar|ressaltar|registrar|consignar|salientar|frisar)\b",
          "bloqueio", "Retire o anúncio e comece pela premissa."),
    Regra("F04", "formula", "É imperioso destacar",
          r"\b(?:e\s+)?imperioso\s+(?:sublinhar|destacar|ressaltar|observar|reconhecer)\b",
          "bloqueio", "Diga o que se reconhece e por quê, sem a solenidade."),
    Regra("F05", "formula", "Não se pode olvidar",
          r"\bnao\s+se\s+pode\s+(?:olvidar|esquecer|perder\s+de\s+vista)\b",
          "bloqueio", "Afirme diretamente o dado que não pode ser esquecido."),
    Regra("F06", "formula", "Metadiscurso de síntese",
          r"\b(?:em\s+suma|em\s+sintese|em\s+ultima\s+analise|nesse\s+diapasao|neste\s+diapasao)\b",
          "bloqueio", "A conclusão aparece pelo encadeamento das premissas, sem rótulo."),
    Regra("F07", "formula", "Conector espacial de IA",
          r"\b(?:neste|nesse)\s+(?:plano|quadro|contexto|cenario)\b|\bsob\s+(?:este|esse|tal)\s+prisma\b"
          r"|\bdiante\s+d(?:esse|este)\s+(?:cenario|quadro|contexto)\b|\bem\s+um\s+cenario\s+(?:em\s+)?(?:que|onde)\b",
          "bloqueio", "Elimine a transição e abra pela premissa factual ou pela consequência jurídica."),
    Regra("F08", "formula", "Fórmula de praxe",
          r"\b(?:a\s+luz\s+d[aeo]s?|no\s+que\s+tange\s+a[os]?|no\s+que\s+concerne\s+a[os]?|de\s+suma\s+importancia"
          r"|faz-se\s+mister|mister\s+se\s+faz|passa-se\s+a\s+expor|vejamos)\b",
          "bloqueio", "Troque por construção direta (\"o art. 386 do CPP exige\", \"quanto à prisão\")."),
    Regra("F09", "formula", "Clichê de efeito",
          r"\b(?:papel\s+crucial|divisor\s+de\s+aguas|tecido\s+social|lanca\s+luz\s+sobre|cheque\s+em\s+branco"
          r"|salta\s+aos\s+olhos|alta\s+voltagem|virada\s+(?:analitica|hermeneutica|interpretativa)"
          r"|advocacia\s+combativa|o\s+fim\s+nao\s+justifica\s+os\s+meios)\b",
          "bloqueio", "Substitua a imagem pelo dado concreto que ela pretendia sugerir."),
    Regra("F10", "formula", "Delimitação negativa artificial",
          r"\bnao\s+se\s+(?:pede|pretende|questiona|busca|trata)\b"
          r"|\ba\s+defesa\s+nao\s+(?:afirma|pede|requer|pretende|sustenta)\b",
          "alerta", "Afirme a tese diretamente, sem dizer o que ela não é.", estrito_bloqueia=True),

    # Qualificadores que afirmam sem demonstrar
    Regra("Q01", "qualificador", "Qualificador que afirma sem demonstrar",
          r"\b(?:robust[oa]s?|robustez|cristalin[oa]s?|evidentes?|evidentemente|claramente|patentemente"
          r"|manifestamente(?!\s+contrari[oa]s?\s+a\s+prova)|induvidos[oa]s?|insofismave(?:l|is)|incontestave(?:l|is)|indiscutive(?:l|is))\b"
          r"|(?<!fato\s)(?<!fatos\s)\bnotori[oa]s?\b|\bnotoriamente\b",
          "bloqueio", "Retire o adjetivo e mostre o dado documental que sustenta a afirmação. "
                      "\"Fato notório\" (sentido técnico) não é apontado."),
    Regra("Q02", "qualificador", "Anúncio de conclusão",
          r"\b(?:e|resta|restou|fica|ficou|mostra-se|revela-se)\s+(?:evidente|manifest[oa]|patente|cristalin[oa]"
          r"|inequivoc[oa]|flagrante|incontroverso)\b",
          "bloqueio", "Exponha a lesão ou o dado concreto; quem conclui é o leitor."),
    Regra("Q03", "qualificador", "Qualificador persuasivo de prova ou testemunha",
          r"\b(?:depoimentos?|relatos?|testemunhos?|laudos?|provas?|versao|versoes)\s+(?:firmes?|seguros?|segura"
          r"|contundentes?|categoric[oa]s?|taxativ[oa]s?|irrefutave(?:l|is)|fragil|frageis|harmonic[oa]s?|coesos?|coesa)\b",
          "bloqueio", "Use verbo neutro (declarou, afirmou, consignou) e mostre a contradição ou a coerência nos autos."),
    Regra("Q04", "qualificador", "Louvor a tribunal, voto ou relator",
          r"\b(?:voto\s+(?:paradigmatico|historico|irretocavel|primoroso|brilhante|lapidar)"
          r"|relatoria\s+(?:precisa|brilhante|segura|firme|primorosa|lapidar)"
          r"|vitoria\s+(?:maiuscula|historica|expressiva|retumbante))\b",
          "alerta", "O elogio não acrescenta fundamento; cite o ponto decidido e a razão."),
    Regra("Q05", "qualificador", "\"Patente\" como qualificador",
          r"\bpatentes?\b",
          "alerta", "Se for adjetivo (\"ilegalidade patente\"), retire e demonstre; patente militar ou industrial fica."),

    # Vocabulário de escrita automatizada
    Regra("V01", "vocabulario", "Verbo \"articular\" e derivados",
          r"\b(?:des)?articul[a-z]*\b",
          "alerta", "Diga a ação concreta: sustentar, fundamentar, formular, encadear, impugnar.", estrito_bloqueia=True),
    Regra("V02", "vocabulario", "\"Autônomo\" como muleta classificatória",
          r"\bautonom[oa]s?\b",
          "alerta", "Use \"independente\", \"específico\" ou demonstre o conteúdo sem a classificação.", estrito_bloqueia=True),
    Regra("V03", "vocabulario", "\"Distinto\" como muleta",
          r"\bdistint[oa]s?\b",
          "alerta", "Use \"separado\", \"dessemelhante\", \"outro\" ou reestruture a oração.", estrito_bloqueia=True),
    Regra("V04", "vocabulario", "Metáfora decorativa ou jargão abstrato",
          r"\b(?:nuances?|molduras?|camadas?|lentes?|tramas?|mosaicos?|panoramas?|ecossistemas?|jornadas?"
          r"|trajetorias?(?!\s+d[oa]s?\s+(?:projet(?:il|eis)|disparos?|balas?|tiros?))"
          r"|(?<!acordao\s)(?<!acordaos\s)(?<!decisao\s)paradigmas?|espectros?|sinergias?|holistic[oa]s?"
          r"|operar\s+como|naveg(?:ar|a|am|ou)|abracar|ressoa(?:r|m)?|mergulh(?:ar|a|am|ou)"
          r"|perme(?:ar|ia|iam|ou)|tecer|sublinh(?:ar|a|am|ou)|trazer\s+a\s+baila)\b",
          "bloqueio", "Descreva o ato, o procedimento ou a consequência. \"Acórdão paradigma\" e "
                      "\"trajetória do projétil\" não são apontados."),
    Regra("V05", "vocabulario", "\"Plano\" em sentido espacial ou estruturante",
          r"\b(?:(?:neste|nesse|naquele|em\s+(?:outro|um|dois|tres|[0-9]+))\s+planos?"
          r"|no\s+plano\s+(?:juridico|fatico|probatorio|processual|analitico|argumentativo|constitucional)"
          r"|planos?\s+(?:processual|constitucional|fatico|juridico|probatorio|analitico|argumentativo))\b",
          "bloqueio", "Nomeie o instituto, a competência ou a fase processual."),
    Regra("V06", "vocabulario", "Latim ornamental e floreio solene",
          r"\b(?:carta\s+magna|lei\s+maior|pretorio\s+excelso|sodalicio|mandamus|in\s+casu|in\s+specie"
          r"|data\s+maxima\s+venia|permissa\s+venia)\b",
          "bloqueio", "Use \"Constituição\", \"STF\", \"neste caso\". O latim técnico do instituto "
                      "(habeas corpus, bis in idem) não é apontado."),
    Regra("V07", "vocabulario", "\"Recair\" como muleta abstrata",
          r"\b(?:recai[a-z]*|recaem)\b",
          "alerta", "Diga quem fez o quê: \"a denúncia imputou\", \"a suspeita dirigiu-se a\".", estrito_bloqueia=True),

    # Pontuação
    Regra("P01", "pontuacao", "Travessão longo fora de citação",
          r"—",
          "alerta", "Use vírgula, parênteses, ponto e vírgula ou oração subordinada.", estrito_bloqueia=True),

    # Vetos do perfil estrito
    Regra("S01", "estilo", "\"Próprio\" e derivados", r"\bpropri[oa]s?\b|\bpropriamente\b",
          "bloqueio", "Individualize (\"conduta do acusado\", \"ato dele\") ou corte.", "estrito"),
    Regra("S02", "estilo", "\"Sem que\" para fato negativo", r"\bsem\s+que\b",
          "bloqueio", "\"embora a decisão não...\", \"e nenhuma das revisões...\", \"mas não...\".", "estrito"),
    Regra("S03", "estilo", "\"Alcança\" como verbo de efeito",
          r"\balcanc(?:a|am|ou|aram|ava|avam|aria|ariam|ar|ando)\b",
          "bloqueio", "Diga o efeito: \"não se aplica\", \"não se ajusta\", \"não afasta\".", "estrito"),
    Regra("S04", "estilo", "\"Se apoia\" e derivados",
          r"\bse\s+apoi(?:a|am|ou|ava|avam|aram|e|em|ar|asse)\b|\bapoi(?:a|am|ou|ava|aram)-se\b",
          "bloqueio", "\"fundamenta\", \"tem por base\", \"invocou\".", "estrito"),
    Regra("S05", "estilo", "\"Deixou de\" + infinitivo",
          r"\bdeix(?:a|am|ar|ara|aram|aria|ariam|asse|assem|ava|avam|ado|ando|e|em|ou)\s+de\s+" + _CLITICO + _INFINITIVO,
          "bloqueio", "Passado direto: \"não fixou\", \"não recebeu\"; para cessação, \"cessou\".", "estrito"),
    Regra("S06", "estilo", "\"Sem\" + infinitivo para fato negativo",
          r"\bsem\s+(?!(?:" + "|".join(_SEM_NAO_VERBO) + r")\b)" + _CLITICO + _INFINITIVO,
          "bloqueio", "Afirme a negativa como constatação: \"a decisão não especificou\".", "estrito"),
    Regra("S07", "estilo", "Verbo \"confrontar\" em prosa autoral", r"\bconfront(?!os?\b)[a-z]+\b",
          "alerta", "\"comparar\", \"cotejar\" ou diga o resultado da comparação.", "estrito"),
    Regra("S08", "estilo", "Fórmula genérica dirigida à defesa", r"\b(?:a\s+defesa\s+(?:pode|deve)|cabe\s+a\s+defesa)\b",
          "alerta", "Diga o que a defesa fez ou requer neste caso.", "estrito"),
]

# Regras de estrutura, calculadas sobre os períodos (não são expressões regulares).
REGRAS_ESTRUTURA = {
    "E01": ("estrutura", "Período curto dentro de parágrafo (tópico frasal ou fecho de efeito)", "alerta",
            "Funda o período com o anterior ou o seguinte por subordinação, coordenação ou ponto e vírgula, "
            "se ambos integram o mesmo raciocínio. Não alongue por enchimento."),
    "E02": ("estrutura", "Abertura de período com \"Ao\" + infinitivo", "alerta",
            "Comece pelo sujeito e pelo ato documentado (\"A decisão reconheceu...\")."),
}


def regras_do_perfil(perfil: str) -> list[Regra]:
    if perfil == "estrito":
        return list(REGRAS)
    return [r for r in REGRAS if r.perfil == "padrao"]
