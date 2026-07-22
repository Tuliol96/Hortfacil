from dataclasses import dataclass


@dataclass
class Configuracao:
    nome_empresa: str = ""
    cnpj: str = ""
    endereco: str = ""
    telefone: str = ""
