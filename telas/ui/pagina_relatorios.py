import re
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.cliente_controller import ClienteController
from telas.ui.dialogo_detalhes_pedido import _nome_arquivo_seguro

# Mesma pasta onde pagina_fechamentos.py salva os relatórios em PDF, uma
# subpasta por cliente.
PASTA_RELATORIOS = Path(__file__).resolve().parent.parent.parent / "relatorios"

COLUNAS = ["Período", "Gerado em"]

CAMINHO_ARQUIVO = Qt.UserRole


def _periodo_do_nome_arquivo(nome_arquivo):
    """'Relatorio 01-07-2026 a 03-08-2026' -> '01/07/2026 a 03/08/2026'"""

    texto = re.sub(r"^Relatorio\s+", "", nome_arquivo)
    return re.sub(r"(\d{2})-(\d{2})-(\d{4})", r"\1/\2/\3", texto)


class PaginaRelatorios(QWidget):

    def __init__(self, banco):
        super().__init__()

        self.banco = banco
        self.cliente_controller = ClienteController(banco)

        self.montar_interface()
        self.carregar_clientes()

    def showEvent(self, evento):
        super().showEvent(evento)
        self.carregar_clientes()

    def montar_interface(self):

        layout = QVBoxLayout(self)

        titulo = QLabel("Relatórios")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size:24px; font-weight:bold;")
        layout.addWidget(titulo)

        # ==========================
        # Busca por cliente
        # ==========================

        linha_filtro = QHBoxLayout()
        linha_filtro.addWidget(QLabel("Cliente:"))

        self.combo_cliente = QComboBox()
        self.combo_cliente.setEditable(True)
        self.combo_cliente.setInsertPolicy(QComboBox.NoInsert)
        self.combo_cliente.lineEdit().setPlaceholderText("Digite para pesquisar o cliente...")

        completador = self.combo_cliente.completer()
        completador.setCompletionMode(QCompleter.PopupCompletion)
        completador.setFilterMode(Qt.MatchContains)
        completador.setCaseSensitivity(Qt.CaseInsensitive)

        self.combo_cliente.currentIndexChanged.connect(self.buscar_relatorios)
        linha_filtro.addWidget(self.combo_cliente, 1)

        layout.addLayout(linha_filtro)

        # ==========================
        # Relatórios do cliente selecionado, por data
        # ==========================

        self.label_status = QLabel("Selecione um cliente para ver os relatórios gerados.")
        self.label_status.setStyleSheet("color:#888;")
        layout.addWidget(self.label_status)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(len(COLUNAS))
        self.tabela.setHorizontalHeaderLabels(COLUNAS)
        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.itemDoubleClicked.connect(self._abrir_selecionado)
        self.tabela.setVisible(False)
        layout.addWidget(self.tabela)

    def carregar_clientes(self):

        cliente_atual = self.combo_cliente.currentData()

        self.combo_cliente.blockSignals(True)
        self.combo_cliente.clear()
        for cliente in self.cliente_controller.listar_clientes():
            self.combo_cliente.addItem(cliente["nome"], cliente["id"])

        indice = -1
        if cliente_atual is not None:
            indice = self.combo_cliente.findData(cliente_atual)

        self.combo_cliente.setCurrentIndex(indice)
        if indice < 0:
            self.combo_cliente.lineEdit().clear()

        self.combo_cliente.blockSignals(False)

        self.buscar_relatorios()

    def buscar_relatorios(self):

        self.tabela.setRowCount(0)

        cliente_id = self.combo_cliente.currentData()

        if cliente_id is None:
            self._mostrar_status("Selecione um cliente para ver os relatórios gerados.")
            return

        nome_cliente = self.combo_cliente.currentText()
        pasta_cliente = PASTA_RELATORIOS / _nome_arquivo_seguro(nome_cliente)

        arquivos = []
        if pasta_cliente.exists():
            arquivos = sorted(
                pasta_cliente.glob("*.pdf"),
                key=lambda arquivo: arquivo.stat().st_mtime,
                reverse=True,
            )

        if not arquivos:
            self._mostrar_status(
                f"Nenhum relatório gerado ainda para \"{nome_cliente}\" — "
                "use \"Gerar Relatório\" na aba Financeiro."
            )
            return

        self.label_status.setVisible(False)
        self.tabela.setVisible(True)
        self.tabela.setRowCount(len(arquivos))

        for linha, arquivo in enumerate(arquivos):
            item_periodo = QTableWidgetItem(_periodo_do_nome_arquivo(arquivo.stem))
            item_periodo.setData(CAMINHO_ARQUIVO, str(arquivo))
            self.tabela.setItem(linha, 0, item_periodo)

            gerado_em = datetime.fromtimestamp(arquivo.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
            self.tabela.setItem(linha, 1, QTableWidgetItem(gerado_em))

    def _mostrar_status(self, texto):
        self.label_status.setText(texto)
        self.label_status.setVisible(True)
        self.tabela.setVisible(False)

    def _abrir_selecionado(self, item_tabela):

        linha = item_tabela.row()
        caminho = self.tabela.item(linha, 0).data(CAMINHO_ARQUIVO)

        if not caminho:
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(caminho))
