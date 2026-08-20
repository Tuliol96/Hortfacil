from models.pedido import ItemPedido, Pedido
from repositories.pedido_repository import PedidoRepository


class PedidoController:

    def __init__(self, banco):
        self.repository = PedidoRepository(banco)

    def listar_pedidos(self):
        return self.repository.listar()

    def listar_itens(self, pedido_id):
        return self.repository.listar_itens(pedido_id)

    def buscar_pedido(self, pedido_id):
        return self.repository.buscar_por_id(pedido_id)

    def listar_pedidos_por_cliente(self, cliente_id):
        return self.repository.listar_por_cliente(cliente_id)

    def excluir_pedido(self, pedido_id):
        self.repository.excluir(pedido_id)

    def emitir_pedido(self, pedido_id, data_emissao):
        self.repository.emitir(pedido_id, data_emissao)

    def listar_pedidos_por_cliente_periodo(self, cliente_id, data_inicio, data_fim):
        return self.repository.listar_por_cliente_periodo(cliente_id, data_inicio, data_fim)

    def resumo_produtos_por_cliente_periodo(self, cliente_id, data_inicio, data_fim):
        return self.repository.resumo_produtos_por_cliente_periodo(cliente_id, data_inicio, data_fim)

    def criar_pedido(self, cliente_id, itens):
        """itens: lista de tuplas (produto_id, quantidade, preco_unitario, sp, hidro)"""

        itens_pedido = [
            ItemPedido(
                produto_id=produto_id,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                subtotal=round(quantidade * preco_unitario, 2),
                sp=sp,
                hidro=hidro,
            )
            for produto_id, quantidade, preco_unitario, sp, hidro in itens
        ]

        total = round(sum(item.subtotal for item in itens_pedido), 2)

        pedido = Pedido(cliente_id=cliente_id, total=total)

        return self.repository.inserir(pedido, itens_pedido)

    def atualizar_pedido(self, pedido_id, itens):
        """itens: lista de tuplas (produto_id, quantidade, preco_unitario, sp, hidro)"""

        itens_pedido = [
            ItemPedido(
                produto_id=produto_id,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                subtotal=round(quantidade * preco_unitario, 2),
                sp=sp,
                hidro=hidro,
            )
            for produto_id, quantidade, preco_unitario, sp, hidro in itens
        ]

        total = round(sum(item.subtotal for item in itens_pedido), 2)

        self.repository.atualizar_itens(pedido_id, itens_pedido, total)
