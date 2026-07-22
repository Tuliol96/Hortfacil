from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.cliente_controller import ClienteController
from controllers.pedido_controller import PedidoController
from telas.ui.dialogo_detalhes_pedido import DetalhesPedidoDialog
from util.formatacao import formatar_data_hora

COLUNAS = ["ID", "Nome", "Telefone", "Endereço", "Número", "Bairro", "Cidade"]
COLUNAS_PEDIDOS = ["ID", "Total", "Status", "Data Emissão"]


class PaginaClientes(QWidget):

    def __init__(self, banco):
        super().__init__()

        self.banco = banco
        self.controller = ClienteController(banco)
        self.pedido_controller = PedidoController(banco)
        self.id_selecionado = None

        self.montar_interface()
        self.carregar_clientes()

    def montar_interface(self):

        layout = QVBoxLayout(self)

        titulo = QLabel("Cadastro de Clientes")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size:24px; font-weight:bold;")
        layout.addWidget(titulo)

        # ==========================
        # Formulário
        # ==========================

        formulario = QFormLayout()

        self.campo_nome = QLineEdit()
        self.campo_telefone = QLineEdit()
        self.campo_endereco = QLineEdit()
        self.campo_numero = QLineEdit()
        self.campo_bairro = QLineEdit()
        self.campo_cidade = QLineEdit()

        formulario.addRow("Nome:", self.campo_nome)
        formulario.addRow("Telefone:", self.campo_telefone)
        formulario.addRow("Endereço:", self.campo_endereco)
        formulario.addRow("Número:", self.campo_numero)
        formulario.addRow("Bairro:", self.campo_bairro)
        formulario.addRow("Cidade:", self.campo_cidade)

        layout.addLayout(formulario)

        # ==========================
        # Botões
        # ==========================

        botoes = QHBoxLayout()

        self.botao_salvar = QPushButton("Cadastrar")
        self.botao_excluir = QPushButton("Excluir")
        self.botao_excluir.setProperty("perigo", True)
        self.botao_limpar = QPushButton("Limpar")
        self.botao_limpar.setProperty("limpar", True)

        self.botao_salvar.clicked.connect(self.salvar_cliente)
        self.botao_excluir.clicked.connect(self.excluir_cliente)
        self.botao_limpar.clicked.connect(self.limpar_formulario)

        botoes.addWidget(self.botao_salvar)
        botoes.addWidget(self.botao_excluir)
        botoes.addWidget(self.botao_limpar)

        layout.addLayout(botoes)

        # ==========================
        # Tabela de clientes
        # ==========================

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(len(COLUNAS))
        self.tabela.setHorizontalHeaderLabels(COLUNAS)
        self.tabela.setColumnHidden(0, True)
        self.tabela.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.itemSelectionChanged.connect(self.selecionar_cliente)

        layout.addWidget(self.tabela)

        # ==========================
        # Histórico de pedidos do cliente selecionado
        # ==========================

        self.label_pedidos_cliente = QLabel("Pedidos do cliente:")
        layout.addWidget(self.label_pedidos_cliente)

        self.tabela_pedidos_cliente = QTableWidget()
        self.tabela_pedidos_cliente.setColumnCount(len(COLUNAS_PEDIDOS))
        self.tabela_pedidos_cliente.setHorizontalHeaderLabels(COLUNAS_PEDIDOS)
        self.tabela_pedidos_cliente.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela_pedidos_cliente.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela_pedidos_cliente.itemDoubleClicked.connect(self.abrir_detalhes_pedido)
        layout.addWidget(self.tabela_pedidos_cliente)

    def carregar_clientes(self):

        clientes = self.controller.listar_clientes()

        self.tabela.setRowCount(len(clientes))

        for linha, cliente in enumerate(clientes):
            self.tabela.setItem(linha, 0, QTableWidgetItem(str(cliente["id"])))
            self.tabela.setItem(linha, 1, QTableWidgetItem(cliente["nome"]))
            self.tabela.setItem(linha, 2, QTableWidgetItem(cliente["telefone"]))
            self.tabela.setItem(linha, 3, QTableWidgetItem(cliente["endereco"]))
            self.tabela.setItem(linha, 4, QTableWidgetItem(cliente["numero"]))
            self.tabela.setItem(linha, 5, QTableWidgetItem(cliente["bairro"]))
            self.tabela.setItem(linha, 6, QTableWidgetItem(cliente["cidade"]))

    def selecionar_cliente(self):

        linhas = self.tabela.selectionModel().selectedRows()

        if not linhas:
            self.carregar_pedidos_cliente(None)
            return

        linha = linhas[0].row()

        self.id_selecionado = int(self.tabela.item(linha, 0).text())
        self.campo_nome.setText(self.tabela.item(linha, 1).text())
        self.campo_telefone.setText(self.tabela.item(linha, 2).text())
        self.campo_endereco.setText(self.tabela.item(linha, 3).text())
        self.campo_numero.setText(self.tabela.item(linha, 4).text())
        self.campo_bairro.setText(self.tabela.item(linha, 5).text())
        self.campo_cidade.setText(self.tabela.item(linha, 6).text())

        self.botao_salvar.setText("Atualizar")

        self.carregar_pedidos_cliente(self.id_selecionado)

    def selecionar_cliente_por_id(self, cliente_id):

        for linha in range(self.tabela.rowCount()):
            if int(self.tabela.item(linha, 0).text()) == cliente_id:
                self.tabela.selectRow(linha)
                return

    def carregar_pedidos_cliente(self, cliente_id):

        if cliente_id is None:
            self.tabela_pedidos_cliente.setRowCount(0)
            self.label_pedidos_cliente.setText("Pedidos do cliente:")
            return

        pedidos = self.pedido_controller.listar_pedidos_por_cliente(cliente_id)

        nome_cliente = self.campo_nome.text()
        self.label_pedidos_cliente.setText(f"Pedidos de {nome_cliente}:")

        self.tabela_pedidos_cliente.setRowCount(len(pedidos))

        for linha, pedido in enumerate(pedidos):
            self.tabela_pedidos_cliente.setItem(linha, 0, QTableWidgetItem(str(pedido["id"])))
            self.tabela_pedidos_cliente.setItem(
                linha, 1, QTableWidgetItem(f"R$ {pedido['total']:.2f}")
            )
            self.tabela_pedidos_cliente.setItem(
                linha, 2, QTableWidgetItem("Emitido" if pedido["emitido"] else "Rascunho")
            )
            self.tabela_pedidos_cliente.setItem(
                linha, 3, QTableWidgetItem(formatar_data_hora(pedido["data_emissao"]) or "—")
            )

    def abrir_detalhes_pedido(self, item_tabela):

        linha = item_tabela.row()
        pedido_id = int(self.tabela_pedidos_cliente.item(linha, 0).text())

        dialogo = DetalhesPedidoDialog(self.banco, pedido_id, self)
        dialogo.pedido_excluido.connect(lambda _id: self.carregar_pedidos_cliente(self.id_selecionado))
        dialogo.pedido_emitido.connect(lambda _id: self.carregar_pedidos_cliente(self.id_selecionado))
        dialogo.exec()

    def limpar_formulario(self):

        self.id_selecionado = None
        self.campo_nome.clear()
        self.campo_telefone.clear()
        self.campo_endereco.clear()
        self.campo_numero.clear()
        self.campo_bairro.clear()
        self.campo_cidade.clear()
        self.botao_salvar.setText("Cadastrar")
        self.tabela.clearSelection()
        self.carregar_pedidos_cliente(None)

    def salvar_cliente(self):

        nome = self.campo_nome.text().strip()
        telefone = self.campo_telefone.text().strip()
        endereco = self.campo_endereco.text().strip()
        numero = self.campo_numero.text().strip()
        bairro = self.campo_bairro.text().strip()
        cidade = self.campo_cidade.text().strip()

        if not nome:
            QMessageBox.warning(self, "Campo obrigatório", "Informe o nome do cliente.")
            return

        if not telefone:
            QMessageBox.warning(self, "Campo obrigatório", "Informe o telefone do cliente.")
            return

        if self.id_selecionado is None:
            self.controller.cadastrar_cliente(
                nome, telefone, endereco, numero, bairro, cidade
            )
        else:
            self.controller.atualizar_cliente(
                self.id_selecionado, nome, telefone, endereco, numero, bairro, cidade
            )

        self.limpar_formulario()
        self.carregar_clientes()

    def excluir_cliente(self):

        if self.id_selecionado is None:
            QMessageBox.warning(self, "Nenhum cliente selecionado", "Selecione um cliente na tabela.")
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar exclusão",
            "Deseja realmente excluir este cliente?",
        )

        if resposta != QMessageBox.Yes:
            return

        self.controller.excluir_cliente(self.id_selecionado)
        self.limpar_formulario()
        self.carregar_clientes()
