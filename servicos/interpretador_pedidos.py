import re
import unicodedata
from dataclasses import dataclass, field
from difflib import get_close_matches

CORTE_SIMILARIDADE = 0.7

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


def _melhor_correspondencia(alvo, itens_normalizados):
    """itens_normalizados: lista de tuplas (item_original, nome_normalizado)"""

    if not alvo:
        return None

    for item, nome_norm in itens_normalizados:
        if nome_norm == alvo:
            return item

    candidatos = [
        item for item, nome_norm in itens_normalizados
        if alvo in nome_norm or nome_norm in alvo
    ]
    if candidatos:
        candidatos.sort(key=lambda item: len(item["nome"]))
        return candidatos[0]

    nomes = [nome_norm for _, nome_norm in itens_normalizados]
    proximos = get_close_matches(alvo, nomes, n=1, cutoff=CORTE_SIMILARIDADE)
    if proximos:
        for item, nome_norm in itens_normalizados:
            if nome_norm == proximos[0]:
                return item

    return None


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
class ResultadoInterpretacao:
    cliente_id: int | None = None
    cliente_nome_detectado: str | None = None
    itens: list[ItemInterpretado] = field(default_factory=list)
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
        linha = linha_bruta.strip()

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

        produto = _melhor_correspondencia(
            _normalizar(nome_produto_texto), produtos_normalizados
        )

        if produto is None:
            resultado.nao_reconhecidos.append(linha)
            continue

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
