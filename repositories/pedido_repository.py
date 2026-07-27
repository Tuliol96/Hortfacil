from models.pedido import ItemPedido, Pedido


class PedidoRepository:

    def __init__(self, banco):
        self.banco = banco

    def inserir(self, pedido: Pedido, itens: list[ItemPedido]):

        self.banco.cursor.execute("""
            INSERT INTO pedidos (cliente_id, total)
            VALUES (?, ?)
        """, (pedido.cliente_id, pedido.total))

        pedido_id = self.banco.cursor.lastrowid

        for item in itens:
            self.banco.cursor.execute("""
                INSERT INTO pedido_itens
                (pedido_id, produto_id, quantidade, preco_unitario, subtotal, sp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                pedido_id,
                item.produto_id,
                item.quantidade,
                item.preco_unitario,
                item.subtotal,
                int(item.sp),
            ))

        self.banco.conexao.commit()

        return pedido_id

    def listar(self):

        self.banco.cursor.execute("""
            SELECT
                pedidos.id,
                pedidos.total,
                pedidos.emitido,
                pedidos.data_emissao,
                pedidos.criado_em,
                clientes.nome AS cliente_nome
            FROM pedidos
            JOIN clientes ON clientes.id = pedidos.cliente_id
            ORDER BY pedidos.criado_em DESC
        """)

        return self.banco.cursor.fetchall()

    def listar_itens(self, pedido_id):

        self.banco.cursor.execute("""
            SELECT
                pedido_itens.produto_id,
                pedido_itens.quantidade,
                pedido_itens.preco_unitario,
                pedido_itens.subtotal,
                pedido_itens.sp,
                produtos.nome AS produto_nome,
                produtos.unidade AS produto_unidade
            FROM pedido_itens
            JOIN produtos ON produtos.id = pedido_itens.produto_id
            WHERE pedido_itens.pedido_id = ?
        """, (pedido_id,))

        return self.banco.cursor.fetchall()

    def atualizar_itens(self, pedido_id, itens: list[ItemPedido], total):
        """Substitui todos os itens do pedido pela lista informada e atualiza o total."""

        self.banco.cursor.execute(
            "DELETE FROM pedido_itens WHERE pedido_id = ?", (pedido_id,)
        )

        for item in itens:
            self.banco.cursor.execute("""
                INSERT INTO pedido_itens
                (pedido_id, produto_id, quantidade, preco_unitario, subtotal, sp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                pedido_id,
                item.produto_id,
                item.quantidade,
                item.preco_unitario,
                item.subtotal,
                int(item.sp),
            ))

        self.banco.cursor.execute("""
            UPDATE pedidos
            SET total = ?, atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (total, pedido_id))

        self.banco.conexao.commit()

    def buscar_por_id(self, pedido_id):

        self.banco.cursor.execute("""
            SELECT
                pedidos.id,
                pedidos.cliente_id,
                pedidos.total,
                pedidos.emitido,
                pedidos.data_emissao,
                pedidos.criado_em,
                clientes.nome AS cliente_nome
            FROM pedidos
            JOIN clientes ON clientes.id = pedidos.cliente_id
            WHERE pedidos.id = ?
        """, (pedido_id,))

        return self.banco.cursor.fetchone()

    def listar_por_cliente(self, cliente_id):

        self.banco.cursor.execute("""
            SELECT
                pedidos.id,
                pedidos.total,
                pedidos.emitido,
                pedidos.data_emissao,
                pedidos.criado_em,
                clientes.nome AS cliente_nome
            FROM pedidos
            JOIN clientes ON clientes.id = pedidos.cliente_id
            WHERE pedidos.cliente_id = ?
            ORDER BY pedidos.criado_em DESC
        """, (cliente_id,))

        return self.banco.cursor.fetchall()

    def listar_por_cliente_periodo(self, cliente_id, data_inicio, data_fim):

        self.banco.cursor.execute("""
            SELECT
                pedidos.id,
                pedidos.total,
                pedidos.emitido,
                pedidos.data_emissao,
                clientes.nome AS cliente_nome
            FROM pedidos
            JOIN clientes ON clientes.id = pedidos.cliente_id
            WHERE pedidos.cliente_id = ?
              AND pedidos.emitido = 1
              AND DATE(pedidos.data_emissao) BETWEEN DATE(?) AND DATE(?)
            ORDER BY pedidos.data_emissao
        """, (cliente_id, data_inicio, data_fim))

        return self.banco.cursor.fetchall()

    def resumo_produtos_por_cliente_periodo(self, cliente_id, data_inicio, data_fim):

        self.banco.cursor.execute("""
            SELECT
                produtos.nome AS produto_nome,
                produtos.unidade AS produto_unidade,
                SUM(pedido_itens.quantidade) AS quantidade_total,
                SUM(pedido_itens.subtotal) AS valor_total
            FROM pedido_itens
            JOIN pedidos ON pedidos.id = pedido_itens.pedido_id
            JOIN produtos ON produtos.id = pedido_itens.produto_id
            WHERE pedidos.cliente_id = ?
              AND pedidos.emitido = 1
              AND DATE(pedidos.data_emissao) BETWEEN DATE(?) AND DATE(?)
            GROUP BY pedido_itens.produto_id
            ORDER BY produtos.nome
        """, (cliente_id, data_inicio, data_fim))

        return self.banco.cursor.fetchall()

    def emitir(self, pedido_id, data_emissao):

        self.banco.cursor.execute("""
            UPDATE pedidos
            SET
                emitido = 1,
                data_emissao = ?,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (data_emissao, pedido_id))

        self.banco.conexao.commit()

    def excluir(self, pedido_id):

        self.banco.cursor.execute(
            "DELETE FROM pedido_itens WHERE pedido_id = ?", (pedido_id,)
        )
        self.banco.cursor.execute(
            "DELETE FROM pedidos WHERE id = ?", (pedido_id,)
        )

        self.banco.conexao.commit()
