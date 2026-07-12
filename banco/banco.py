import sqlite3
from pathlib import Path


class Banco:

    def __init__(self):

        # Caminho do banco de dados
        pasta = Path(__file__).parent
        self.caminho = pasta / "hortfacil.db"

        # Conexão
        self.conexao = sqlite3.connect(self.caminho)

        # Permite acessar colunas pelo nome
        self.conexao.row_factory = sqlite3.Row

        # Cursor
        self.cursor = self.conexao.cursor()

    def criar_tabelas(self):

        # ==========================
        # TABELA DE PRODUTOS
        # ==========================

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                nome TEXT NOT NULL,

                categoria TEXT NOT NULL,

                unidade TEXT NOT NULL,

                preco REAL NOT NULL,

                favorito INTEGER NOT NULL DEFAULT 0,

                ativo INTEGER NOT NULL DEFAULT 1,

                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,

                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP

            )
        """)

        self.conexao.commit()

    def fechar(self):
        self.conexao.close()