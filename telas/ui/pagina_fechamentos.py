from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
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
from telas.ui.dialogo_resumo_produtos import ResumoProdutosDialog
from util.formatacao import formatar_data_hora

COLUNAS = ["Nota #", "Data", "Total"]


class PaginaFechamentos(QWidget):

    def __init__(self, banco):
        super().__init__()

        self.banco = banco
        self.cliente_controller = ClienteController(banco)
        self.pedido_controller = PedidoController(banco)

        self.montar_interface()
        self.carregar_clientes()

    def showEvent(self, evento):
        super().showEvent(evento)
        self.carregar_clientes()

    def montar_interface(self):

        layout = QVBoxLayout(self)

        titulo = QLabel("Fechamentos")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size:24px; font-weight:bold;")
        layout.addWidget(titulo)

        # ==========================
        # Filtros
        # ==========================

        linha_filtros = QHBoxLayout()

        linha_filtros.addWidget(QLabel("Cliente:"))
        self.combo_cliente = QComboBox()
        linha_filtros.addWidget(self.combo_cliente, 1)

        linha_filtros.addWidget(QLabel("De:"))
        self.data_inicio = QDateEdit()
        self.data_inicio.setCalendarPopup(True)
        self.data_inicio.setDisplayFormat("dd/MM/yyyy")
        self.data_inicio.setDate(QDate.currentDate().addMonths(-1))
        linha_filtros.addWidget(self.data_inicio)

        linha_filtros.addWidget(QLabel("Até:"))
        self.data_fim = QDateEdit()
        self.data_fim.setCalendarPopup(True)
        self.data_fim.setDisplayFormat("dd/MM/yyyy")
        self.data_fim.setDate(QDate.currentDate())
        linha_filtros.addWidget(self.data_fim)

        self.botao_buscar = QPushButton("Buscar")
        self.botao_buscar.clicked.connect(self.buscar_pedidos)
        linha_filtros.addWidget(self.botao_buscar)

        layout.addLayout(linha_filtros)

        # ==========================
        # Notas fiscais (pedidos) no período
        # ==========================

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(len(COLUNAS))
        self.tabela.setHorizontalHeaderLabels(COLUNAS)
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.itemDoubleClicked.connect(self.abrir_detalhes_pedido)
        layout.addWidget(self.tabela)

        self.label_total = QLabel("Total do período: R$ 0,00")
        self.label_total.setAlignment(Qt.AlignRight)
        self.label_total.setStyleSheet("font-size:16px; font-weight:bold;")
        layout.addWidget(self.label_total)

        self.botao_detalhes = QPushButton("Detalhes")
        self.botao_detalhes.clicked.connect(self.abrir_resumo_produtos)
        layout.addWidget(self.botao_detalhes)

    def carregar_clientes(self):

        cliente_atual = self.combo_cliente.currentData()
        self.combo_cliente.clear()
        for cliente in self.cliente_controller.listar_clientes():
            self.combo_cliente.addItem(cliente["nome"], cliente["id"])
        if cliente_atual is not None:
            indice = self.combo_cliente.findData(cliente_atual)
            if indice >= 0:
                self.combo_cliente.setCurrentIndex(indice)

    def _periodo_selecionado(self):

        if self.data_inicio.date() > self.data_fim.date():
            QMessageBox.warning(
                self, "Intervalo inválido",
                "A data inicial não pode ser depois da data final."
            )
            return None

        return (
            self.data_inicio.date().toString("yyyy-MM-dd"),
            self.data_fim.date().toString("yyyy-MM-dd"),
        )

    def buscar_pedidos(self):

        cliente_id = self.combo_cliente.currentData()

        if cliente_id is None:
            QMessageBox.warning(self, "Nenhum cliente", "Cadastre e selecione um cliente.")
            return

        periodo = self._periodo_selecionado()
        if periodo is None:
            return

        data_inicio, data_fim = periodo

        pedidos = self.pedido_controller.listar_pedidos_por_cliente_periodo(
            cliente_id, data_inicio, data_fim
        )

        self.tabela.setRowCount(len(pedidos))

        total = 0.0

        for linha, pedido in enumerate(pedidos):
            self.tabela.setItem(linha, 0, QTableWidgetItem(str(pedido["id"])))
            self.tabela.setItem(linha, 1, QTableWidgetItem(formatar_data_hora(pedido["data_emissao"])))
            self.tabela.setItem(linha, 2, QTableWidgetItem(f"R$ {pedido['total']:.2f}"))
            total += pedido["total"]

        self.label_total.setText(f"Total do período: R$ {total:.2f}")

    def abrir_detalhes_pedido(self, item_tabela):

        linha = item_tabela.row()
        pedido_id = int(self.tabela.item(linha, 0).text())

        dialogo = DetalhesPedidoDialog(self.banco, pedido_id, self)
        dialogo.pedido_excluido.connect(lambda _id: self.buscar_pedidos())
        dialogo.pedido_emitido.connect(lambda _id: self.buscar_pedidos())
        dialogo.exec()

    def abrir_resumo_produtos(self):

        cliente_id = self.combo_cliente.currentData()

        if cliente_id is None:
            QMessageBox.warning(self, "Nenhum cliente", "Cadastre e selecione um cliente.")
            return

        periodo = self._periodo_selecionado()
        if periodo is None:
            return

        data_inicio, data_fim = periodo

        dialogo = ResumoProdutosDialog(
            self.banco, cliente_id, self.combo_cliente.currentText(),
            data_inicio, data_fim, self
        )
        dialogo.exec()
