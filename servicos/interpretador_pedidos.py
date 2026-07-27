import re
import unicodedata
from dataclasses import dataclass, field
from difflib import get_close_matches

CORTE_SIMILARIDADE = 0.7

# apelidos que não batem por similaridade de texto e precisam de tradução direta
ALIASES_PRODUTO = {
    "usa": "americana",
    "salsa": "salsinha",
    # "crespa" sozinho é sempre alface crespa (produto muito mais comum que
    # salsa crespa) — evita ambiguidade no caso mais frequente.
    "crespa": "alface crespa",
}

UNIDADES_CONHECIDAS = {
    "kg": "kg",
    "kilo": "kg",
    "kilos": "kg",
    "quilo": "kg",
    "quilos": "kg",
    "g": "g",
    "grama": "g",
    "gramas": "g",
    "und": "und",
    "un": "und",
    "unid": "und",
    "unidade": "und",
    "unidades": "und",
}

# "PEDIDO <NOME DO CLIENTE>"
PADRAO_CLIENTE = re.compile(r"^\s*pedido\s+(.+?)\s*$", re.IGNORECASE)

# "Produto : quantidade [unidade]" — ex.: "Alface americana: 4 und"
PADRAO_COM_DOIS_PONTOS = re.compile(
    r"^(?P<nome>.+?)\s*[:\-]\s*(?P<qtd>\d+(?:[.,]\d+)?)\s*"
    r"(?P<unidade>kg|kilos?|quilos?|gramas?|g|unidades?|unid\.?|und|un)?\.?\s*$",
    re.IGNORECASE,
)

# "quantidade produto", sem separador — ex.: "06alface crespa", "0 4 hortelã"
PADRAO_QUANTIDADE_NO_INICIO = re.compile(
    r"^(?P<qtd>(?:\d\s*){1,3})(?P<nome>[A-Za-zÀ-ÿ].*\S)\s*$"
)

# "quantidade decimal [unidade] produto" — ex.: "0,4 pimenta dedo moça", "0.5kg couve"
PADRAO_QUANTIDADE_DECIMAL_NO_INICIO = re.compile(
    r"^(?P<qtd>\d+[.,]\d+)\s*"
    r"(?P<unidade>kg|kilos?|quilos?|gramas?|g|unidades?|unid\.?|und|un)?\s+"
    r"(?P<nome>[A-Za-zÀ-ÿ].*\S)\s*$",
    re.IGNORECASE,
)

# "produto quantidade [unidade]" — ex.: "Alface crespa 18", "Couve 10"
PADRAO_QUANTIDADE_NO_FINAL = re.compile(
    r"^(?P<nome>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9\s\-]*?)\s+(?P<qtd>\d+(?:[.,]\d+)?)\s*"
    r"(?P<unidade>kg|kilos?|quilos?|gramas?|g|unidades?|unid\.?|und|un)?\.?\s*$",
    re.IGNORECASE,
)


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", texto).strip().lower()


def _converter_quantidade(quantidade, unidade):
    if unidade == "g":
        return quantidade / 1000
    return quantidade


def _candidatos_correspondencia(alvo, itens_normalizados):
    """itens_normalizados: lista de tuplas (item_original, nome_normalizado)

    Retorna a lista de itens candidatos para o alvo, em ordem de prioridade:
    - nome exatamente igual: resolve sozinho, sem ambiguidade;
    - nomes que contêm/são contidos no alvo: pode haver mais de um, e nesse
      caso é ambíguo (ex.: "crespa" bate com "Alface Crespa" e "Salsa Crespa");
    - nome parecido por similaridade de texto: só o mais próximo.
    """

    if not alvo:
        return []

    for item, nome_norm in itens_normalizados:
        if nome_norm == alvo:
            return [item]

    candidatos = [
        item for item, nome_norm in itens_normalizados
        if alvo in nome_norm or nome_norm in alvo
    ]
    if candidatos:
        candidatos.sort(key=lambda item: len(item["nome"]))
        return candidatos

    nomes = [nome_norm for _, nome_norm in itens_normalizados]
    proximos = get_close_matches(alvo, nomes, n=1, cutoff=CORTE_SIMILARIDADE)
    if proximos:
        return [
            item for item, nome_norm in itens_normalizados
            if nome_norm == proximos[0]
        ]

    return []


def _melhor_correspondencia(alvo, itens_normalizados):
    """Resolve sempre para um único item (usado para casar cliente, onde
    não faz sentido perguntar ao usuário)."""

    candidatos = _candidatos_correspondencia(alvo, itens_normalizados)
    return candidatos[0] if candidatos else None


@dataclass
class ItemInterpretado:
    produto_id: int
    produto_nome: str
    produto_unidade: str
    quantidade: float
    preco_unitario: float | None
    subtotal: float | None = field(init=False)

    def __post_init__(self):
        if self.preco_unitario is None:
            self.subtotal = None
        else:
            self.subtotal = round(self.quantidade * self.preco_unitario, 2)


@dataclass
class ItemAmbiguo:
    """Linha do pedido que bateu com mais de um produto cadastrado —
    precisa que o usuário escolha qual produto usar."""

    linha_original: str
    quantidade: float
    candidatos: list  # produtos (linhas de listar_produtos()) em ordem de nome mais curto


@dataclass
class ResultadoInterpretacao:
    cliente_id: int | None = None
    cliente_nome_detectado: str | None = None
    itens: list[ItemInterpretado] = field(default_factory=list)
    itens_ambiguos: list[ItemAmbiguo] = field(default_factory=list)
    nao_reconhecidos: list[str] = field(default_factory=list)


def interpretar_pedido(texto, produtos, clientes):
    """
    Interpreta um texto de pedido (colado do WhatsApp) e tenta casar cada
    linha com um cliente/produto cadastrado.

    produtos e clientes: resultados de listar_produtos()/listar_clientes()
    (linhas de sqlite3.Row, precisam ter pelo menos "id", "nome" e,
    no caso dos produtos, "unidade" e "preco").
    """

    resultado = ResultadoInterpretacao()

    produtos_normalizados = [(p, _normalizar(p["nome"])) for p in produtos]
    clientes_normalizados = [(c, _normalizar(c["nome"])) for c in clientes]

    for linha_bruta in texto.splitlines():
        linha = linha_bruta.replace("*", "").strip()

        if not linha:
            continue

        match_cliente = PADRAO_CLIENTE.match(linha)
        if match_cliente:
            nome_cliente = match_cliente.group(1)
            cliente = _melhor_correspondencia(
                _normalizar(nome_cliente), clientes_normalizados
            )
            resultado.cliente_nome_detectado = nome_cliente
            if cliente:
                resultado.cliente_id = cliente["id"]
            continue

        nome_produto_texto = None
        quantidade = None
        unidade = None

        match = PADRAO_COM_DOIS_PONTOS.match(linha)
        if match:
            nome_produto_texto = match.group("nome")
            quantidade = float(match.group("qtd").replace(",", "."))
            unidade_bruta = match.group("unidade")
            if unidade_bruta:
                unidade = UNIDADES_CONHECIDAS.get(unidade_bruta.lower().rstrip("."))
        else:
            match = PADRAO_QUANTIDADE_DECIMAL_NO_INICIO.match(linha)
            if match:
                nome_produto_texto = match.group("nome")
                quantidade = float(match.group("qtd").replace(",", "."))
                unidade_bruta = match.group("unidade")
                if unidade_bruta:
                    unidade = UNIDADES_CONHECIDAS.get(unidade_bruta.lower().rstrip("."))
            else:
                match = PADRAO_QUANTIDADE_NO_INICIO.match(linha)
                if match:
                    qtd_texto = re.sub(r"\s+", "", match.group("qtd"))
                    quantidade = float(qtd_texto)
                    nome_produto_texto = match.group("nome")
                else:
                    match = PADRAO_QUANTIDADE_NO_FINAL.match(linha)
                    if match:
                        nome_produto_texto = match.group("nome")
                        quantidade = float(match.group("qtd").replace(",", "."))
                        unidade_bruta = match.group("unidade")
                        if unidade_bruta:
                            unidade = UNIDADES_CONHECIDAS.get(unidade_bruta.lower().rstrip("."))

        if nome_produto_texto is None:
            continue

        quantidade = _converter_quantidade(quantidade, unidade)

        alvo_produto = _normalizar(nome_produto_texto)
        alvo_produto = ALIASES_PRODUTO.get(alvo_produto, alvo_produto)

        candidatos_produto = _candidatos_correspondencia(alvo_produto, produtos_normalizados)

        if not candidatos_produto:
            resultado.nao_reconhecidos.append(linha)
            continue

        if len(candidatos_produto) > 1:
            resultado.itens_ambiguos.append(
                ItemAmbiguo(
                    linha_original=linha,
                    quantidade=quantidade,
                    candidatos=candidatos_produto,
                )
            )
            continue

        produto = candidatos_produto[0]

        resultado.itens.append(
            ItemInterpretado(
                produto_id=produto["id"],
                produto_nome=produto["nome"],
                produto_unidade=produto["unidade"],
                quantidade=quantidade,
                preco_unitario=produto["preco"],
            )
        )

    return resultado
