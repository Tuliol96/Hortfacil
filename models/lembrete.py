from dataclasses import dataclass


@dataclass
class Lembrete:
    id: int | None = None
    mensagem: str = ""
    data_hora: str = ""
    disparado: bool = False
    criado_em: str = ""
