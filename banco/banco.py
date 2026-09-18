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

                preco REAL,

                favorito INTEGER NOT NULL DEFAULT 0,

                ativo INTEGER NOT NULL DEFAULT 1,

                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,

                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP

            )
        """)

        self._migrar_preco_opcional()

        # ==========================
        # TABELA DE CLIENTES
        # ==========================

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                nome TEXT NOT NULL,

                telefone TEXT NOT NULL,

                endereco TEXT NOT NULL,

                numero TEXT NOT NULL,

                bairro TEXT NOT NULL,

                cidade TEXT NOT NULL,

                ativo INTEGER NOT NULL DEFAULT 1,

                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,

                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP

            )
        """)

        # ==========================
        # TABELA DE PEDIDOS
        # ==========================

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                cliente_id INTEGER NOT NULL,

                total REAL NOT NULL DEFAULT 0,

                emitido INTEGER NOT NULL DEFAULT 0,

                data_emissao TEXT,

                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,

                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (cliente_id) REFERENCES clientes (id)

            )
        """)

        self._migrar_emissao_pedidos()

        # ==========================
        # TABELA DE ITENS DO PEDIDO
        # ==========================

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pedido_itens (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                pedido_id INTEGER NOT NULL,

                produto_id INTEGER NOT NULL,

                quantidade REAL NOT NULL,

                preco_unitario REAL NOT NULL,

                subtotal REAL NOT NULL,

                sp INTEGER NOT NULL DEFAULT 0,

                hidro INTEGER NOT NULL DEFAULT 0,

                nao_cobrar INTEGER NOT NULL DEFAULT 0,

                FOREIGN KEY (pedido_id) REFERENCES pedidos (id),

                FOREIGN KEY (produto_id) REFERENCES produtos (id)

            )
        """)

        self._migrar_sp_pedido_itens()
        self._migrar_hidro_pedido_itens()
        self._migrar_nao_cobrar_pedido_itens()

        # ==========================
        # TABELA DE LEMBRETES
        # ==========================

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lembretes (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                mensagem TEXT NOT NULL,

                data_hora TEXT NOT NULL,

                disparado INTEGER NOT NULL DEFAULT 0,

                criado_em TEXT DEFAULT CURRENT_TIMESTAMP

            )
        """)

        # ==========================
        # CONFIGURAÇÕES DA EMPRESA (linha única)
        # ==========================

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (

                id INTEGER PRIMARY KEY CHECK (id = 1),

                nome_empresa TEXT NOT NULL DEFAULT '',

                cnpj TEXT NOT NULL DEFAULT '',

                endereco TEXT NOT NULL DEFAULT '',

                telefone TEXT NOT NULL DEFAULT '',

                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP

            )
        """)

        self.cursor.execute("INSERT OR IGNORE INTO configuracoes (id) VALUES (1)")

        self.conexao.commit()

    def _migrar_preco_opcional(self):
        """
        Bancos criados antes desta versão têm produtos.preco como NOT NULL.
        Recria a tabela permitindo preço nulo (produto com preço variável),
        preservando todos os dados já cadastrados.
        """

        self.cursor.execute("PRAGMA table_info(produtos)")
        colunas = self.cursor.fetchall()
        coluna_preco = next((c for c in colunas if c["name"] == "preco"), None)

        if coluna_preco is None or not coluna_preco["notnull"]:
            return

        self.cursor.execute("""
            CREATE TABLE produtos_novo (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                nome TEXT NOT NULL,

                categoria TEXT NOT NULL,

                unidade TEXT NOT NULL,

                preco REAL,

                favorito INTEGER NOT NULL DEFAULT 0,

                ativo INTEGER NOT NULL DEFAULT 1,

                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,

                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP

            )
        """)

        self.cursor.execute("""
            INSERT INTO produtos_novo
            SELECT id, nome, categoria, unidade, preco, favorito, ativo, criado_em, atualizado_em
            FROM produtos
        """)

        self.cursor.execute("DROP TABLE produtos")
        self.cursor.execute("ALTER TABLE produtos_novo RENAME TO produtos")

        self.conexao.commit()

    def _migrar_emissao_pedidos(self):
        """
        Bancos criados antes desta versão não têm as colunas de emissão.
        Adiciona 'emitido'/'data_emissao' e, só na primeira vez (quando as
        colunas acabaram de ser criadas), marca os pedidos já existentes
        como emitidos, usando a data de criação como data de emissão —
        eles foram feitos antes do fluxo de rascunho existir.
        """

        self.cursor.execute("PRAGMA table_info(pedidos)")
        colunas = {c["name"] for c in self.cursor.fetchall()}

        coluna_nova_adicionada = False

        if "emitido" not in colunas:
            self.cursor.execute(
                "ALTER TABLE pedidos ADD COLUMN emitido INTEGER NOT NULL DEFAULT 0"
            )
            coluna_nova_adicionada = True

        if "data_emissao" not in colunas:
            self.cursor.execute("ALTER TABLE pedidos ADD COLUMN data_emissao TEXT")
            coluna_nova_adicionada = True

        if coluna_nova_adicionada:
            self.cursor.execute("""
                UPDATE pedidos
                SET emitido = 1, data_emissao = criado_em
                WHERE data_emissao IS NULL
            """)

        self.conexao.commit()

    def _migrar_sp_pedido_itens(self):
        """
        Bancos criados antes desta versão não têm a coluna 'sp' (produto
        de origem paulista) em pedido_itens. Adiciona a coluna, com os
        itens já existentes marcados como não-SP.
        """

        self.cursor.execute("PRAGMA table_info(pedido_itens)")
        colunas = {c["name"] for c in self.cursor.fetchall()}

        if "sp" not in colunas:
            self.cursor.execute(
                "ALTER TABLE pedido_itens ADD COLUMN sp INTEGER NOT NULL DEFAULT 0"
            )
            self.conexao.commit()

    def _migrar_hidro_pedido_itens(self):
        """
        Bancos criados antes desta versão não têm a coluna 'hidro' (produto
        de cultivo hidropônico) em pedido_itens. Adiciona a coluna, com os
        itens já existentes marcados como não-hidropônicos.
        """

        self.cursor.execute("PRAGMA table_info(pedido_itens)")
        colunas = {c["name"] for c in self.cursor.fetchall()}

        if "hidro" not in colunas:
            self.cursor.execute(
                "ALTER TABLE pedido_itens ADD COLUMN hidro INTEGER NOT NULL DEFAULT 0"
            )
            self.conexao.commit()

    def _migrar_nao_cobrar_pedido_itens(self):
        """
        Bancos criados antes desta versão não têm a coluna 'nao_cobrar' em
        pedido_itens. Adiciona a coluna, com os itens já existentes
        marcados como cobrados normalmente.
        """

        self.cursor.execute("PRAGMA table_info(pedido_itens)")
        colunas = {c["name"] for c in self.cursor.fetchall()}

        if "nao_cobrar" not in colunas:
            self.cursor.execute(
                "ALTER TABLE pedido_itens ADD COLUMN nao_cobrar INTEGER NOT NULL DEFAULT 0"
            )
            self.conexao.commit()

    def fechar(self):
        self.conexao.close()