from models.produto import Produto


class ProdutoRepository:

    def __init__(self, banco):
        self.banco = banco

    def inserir(self, produto: Produto):

        sql = """
        INSERT INTO produtos
        (
            nome,
            categoria,
            unidade,
            preco,
            favorito,
            ativo
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """

        self.banco.cursor.execute(
            sql,
            (
                produto.nome,
                produto.categoria,
                produto.unidade,
                produto.preco,
                int(produto.favorito),
                int(produto.ativo),
            ),
        )

        self.banco.conexao.commit()

    def listar(self):

        self.banco.cursor.execute("""
            SELECT *
            FROM produtos
            WHERE ativo = 1
            ORDER BY nome
        """)

        return self.banco.cursor.fetchall()

    def buscar_por_id(self, id_produto):

        self.banco.cursor.execute("""
            SELECT *
            FROM produtos
            WHERE id = ?
        """, (id_produto,))

        return self.banco.cursor.fetchone()

    def atualizar(self, produto: Produto):

        self.banco.cursor.execute("""
            UPDATE produtos
            SET
                nome = ?,
                categoria = ?,
                unidade = ?,
                preco = ?,
                favorito = ?,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            produto.nome,
            produto.categoria,
            produto.unidade,
            produto.preco,
            int(produto.favorito),
            produto.id
        ))

        self.banco.conexao.commit()

    def desativar(self, id_produto):

        self.banco.cursor.execute("""
            UPDATE produtos
            SET
                ativo = 0,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (id_produto,))

        self.banco.conexao.commit()