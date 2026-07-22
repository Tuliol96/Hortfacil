from models.produto import Produto
from repositories.produto_repository import ProdutoRepository


class ProdutoController:

    def __init__(self, banco):
        self.repository = ProdutoRepository(banco)

    def listar_produtos(self):
        return self.repository.listar()

    def listar_categorias(self):
        return self.repository.listar_categorias()

    def listar_unidades(self):
        return self.repository.listar_unidades()

    def cadastrar_produto(
        self,
        nome,
        categoria,
        unidade,
        preco,
        favorito=False
    ):

        produto = Produto(
            nome=nome.strip(),
            categoria=categoria,
            unidade=unidade,
            preco=float(preco) if preco not in (None, "") else None,
            favorito=favorito
        )

        self.repository.inserir(produto)

    def atualizar_produto(
        self,
        id_produto,
        nome,
        categoria,
        unidade,
        preco,
        favorito=False
    ):

        produto = Produto(
            id=id_produto,
            nome=nome.strip(),
            categoria=categoria,
            unidade=unidade,
            preco=float(preco) if preco not in (None, "") else None,
            favorito=favorito
        )

        self.repository.atualizar(produto)

    def excluir_produto(self, id_produto):
        self.repository.desativar(id_produto)

    def buscar_produto(self, id_produto):
        return self.repository.buscar_por_id(id_produto)
