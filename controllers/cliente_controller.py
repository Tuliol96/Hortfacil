from models.cliente import Cliente
from repositories.cliente_repository import ClienteRepository


class ClienteController:

    def __init__(self, banco):
        self.repository = ClienteRepository(banco)

    def listar_clientes(self):
        return self.repository.listar()

    def cadastrar_cliente(
        self,
        nome,
        telefone,
        endereco,
        numero,
        bairro,
        cidade
    ):

        cliente = Cliente(
            nome=nome.strip(),
            telefone=telefone.strip(),
            endereco=endereco.strip(),
            numero=numero.strip(),
            bairro=bairro.strip(),
            cidade=cidade.strip()
        )

        self.repository.inserir(cliente)

    def atualizar_cliente(
        self,
        id_cliente,
        nome,
        telefone,
        endereco,
        numero,
        bairro,
        cidade
    ):

        cliente = Cliente(
            id=id_cliente,
            nome=nome.strip(),
            telefone=telefone.strip(),
            endereco=endereco.strip(),
            numero=numero.strip(),
            bairro=bairro.strip(),
            cidade=cidade.strip()
        )

        self.repository.atualizar(cliente)

    def excluir_cliente(self, id_cliente):
        self.repository.desativar(id_cliente)

    def buscar_cliente(self, id_cliente):
        return self.repository.buscar_por_id(id_cliente)
