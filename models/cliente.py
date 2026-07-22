from dataclasses import dataclass


@dataclass
class Cliente:
    id: int | None = None
    nome: str = ""
    telefone: str = ""
    endereco: str = ""
    numero: str = ""
    bairro: str = ""
    cidade: str = ""
    ativo: bool = True
    criado_em: str = ""
    atualizado_em: str = ""
