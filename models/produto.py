from dataclasses import dataclass


@dataclass
class Produto:
    id: int | None = None
    nome: str = ""
    categoria: str = ""
    unidade: str = ""
    preco: float | None = None
    favorito: bool = False
    ativo: bool = True
    criado_em: str = ""
    atualizado_em: str = ""