from dataclasses import dataclass


@dataclass
class Pedido:
    id: int | None = None
    cliente_id: int | None = None
    total: float = 0.0
    emitido: bool = False
    data_emissao: str | None = None
    criado_em: str = ""
    atualizado_em: str = ""


@dataclass
class ItemPedido:
    id: int | None = None
    pedido_id: int | None = None
    produto_id: int | None = None
    quantidade: float = 0.0
    preco_unitario: float = 0.0
    subtotal: float = 0.0
