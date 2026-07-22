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

    def listar_categorias(self):

        self.banco.cursor.execute("""
            SELECT DISTINCT categoria
            FROM produtos
            WHERE categoria IS NOT NULL AND categoria != ''
            ORDER BY categoria
        """)

        return [linha["categoria"] for linha in self.banco.cursor.fetchall()]

    def listar_unidades(self):

        self.banco.cursor.execute("""
            SELECT DISTINCT unidade
            FROM produtos
            WHERE unidade IS NOT NULL AND unidade != ''
            ORDER BY unidade
        """)

        return [linha["unidade"] for linha in self.banco.cursor.fetchall()]

    def desativar(self, id_produto):

        self.banco.cursor.execute("""
            UPDATE produtos
            SET
                ativo = 0,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (id_produto,))

        self.banco.conexao.commit()