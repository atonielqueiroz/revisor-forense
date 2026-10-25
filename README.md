# Revisor forense

Ferramenta de linha de comando que lê uma peça jurídica (Word, Markdown ou texto) e aponta as marcas
mais comuns de texto gerado por inteligência artificial e de fórmula de praxe: anúncios vazios
("cumpre destacar"), adjetivos que afirmam sem demonstrar ("prova robusta"), metáforas decorativas
("moldura fática"), latim ornamental ("in casu"), travessões e períodos curtos de efeito.

Cada apontamento traz o trecho, o local (linha ou parágrafo do Word) e a orientação de como corrigir.
A ferramenta **não reescreve o texto**: quem decide e corrige é o advogado.

## Para que serve

Para fazer uma checagem objetiva antes da revisão humana, seja de minuta escrita com auxílio de IA ou
de peça antiga que acumulou vícios de redação. Ela é útil para o escritório que quer um padrão de prosa
sóbrio, técnico e direto, em que o fato e a norma sustentam o argumento e o adjetivo não substitui
a prova.

## Instalação

É preciso ter Python 3.9 ou superior. O revisor não depende de nenhuma outra biblioteca.

```bash
pip install git+https://github.com/SEU-USUARIO/revisor-forense
```

## Uso

```bash
revisor-forense "Apelação.docx"
```

```bash
revisor-forense minuta.md --perfil estrito --json relatorio.json
```

Exemplo de saída:

```
BLOQUEIO Q01 | parágrafo 14 | Qualificador que afirma sem demonstrar
         trecho: ...a prova é robusta quanto à autoria...
         como corrigir: Retire o adjetivo e mostre o dado documental que sustenta a afirmação.
-- 3 bloqueio(s), 5 alerta(s); 42 períodos, média de 24.3 palavras, desvio 9.1
```

Opções:

| Opção | O que faz |
|---|---|
| `--perfil padrao` | Vícios reconhecidos de escrita automatizada e de praxe (é o padrão). |
| `--perfil estrito` | Acrescenta vetos de estilo mais rigorosos e transforma em bloqueio alguns alertas. |
| `--desativar Q05,V07` | Desliga regras pelo código. |
| `--min-palavras 15` | Tamanho mínimo de referência para o período dentro de parágrafo argumentativo. |
| `--json arquivo.json` | Grava o relatório completo. |
| `--listar-regras` | Mostra todas as regras com código, gravidade e perfil. |

O programa termina com código 1 quando há bloqueio. Assim, ele pode servir de trava automática em
fluxos de produção de peças.

## O que é apontado

| Código | Categoria | Exemplos | Como corrigir |
|---|---|---|---|
| F01 a F10 | Fórmulas e metadiscurso | "vale ressaltar", "cumpre destacar", "nesse contexto", "à luz de", "no que tange", "em suma", "divisor de águas" | Comece pela premissa factual ou pela consequência jurídica. |
| Q01 a Q05 | Qualificadores | "robusto", "cristalino", "evidente", "resta manifesto", "depoimento firme", "relato contundente" | Mostre o dado e a página; quem qualifica a prova é o julgador. |
| V01 a V07 | Vocabulário de IA | "articular", "autônomo", "distinto", "moldura", "nuances", "panorama", "mergulhar", "Carta Magna", "in casu" | Use o verbo técnico e o nome do instituto. |
| P01 | Pontuação | travessão longo (—) | Vírgula, parênteses, ponto e vírgula ou subordinada. |
| E01, E02 | Estrutura | período curto de efeito dentro do parágrafo; abertura em série com "Ao + infinitivo" | Funda os períodos que integram o mesmo raciocínio. |
| S01 a S08 | Perfil estrito | "próprio", "sem que", "sem + infinitivo", "deixou de + infinitivo", "alcança", "se apoia" | Constatação objetiva no passado: "a decisão não especificou". |

### O que não é apontado

- **Texto citado.** Trechos entre aspas, citações em bloco do Word (estilo de citação ou recuo esquerdo
  de 2 cm ou mais) e linhas iniciadas por `>` no Markdown. A lei, a decisão e o depoimento são
  transcritos como estão.
- **Termos técnicos** que coincidem com palavras vetadas: "fato notório", "acórdão paradigma",
  "trajetória do projétil", "decisão manifestamente contrária à prova dos autos", "habeas corpus",
  "bis in idem".
- **Vocativos e fechos**, como "Egrégia Câmara Criminal" e "Termos em que pede deferimento".

## Limites

Zero apontamentos **não significa** texto aprovado. O revisor examina a forma, e não verifica fatos,
fidelidade às fontes, citações, prazos, cabimento nem estratégia. Toda peça continua a depender da
leitura e da responsabilidade técnica do advogado que a assina.

As regras procuram palavras e construções, e não sentido. Por isso alguns alertas exigem juízo humano;
quando um termo for legítimo no seu contexto, desative a regra com `--desativar`.

## Como contribuir

As regras ficam em [`revisor_forense/regras.py`](revisor_forense/regras.py), cada uma com código,
categoria, padrão, gravidade e orientação. Os padrões são aplicados sobre o texto em minúsculas e sem
acentos ("Cenário" vira "cenario"). Para propor uma regra nova:

1. acrescente a regra com um exemplo real (anonimizado) do vício;
2. acrescente em `tests/test_revisor.py` um caso que deve ser apontado e um caso legítimo que não deve;
3. rode `python -m unittest discover -s tests`.

## Licença

MIT. Veja [LICENSE](LICENSE).
