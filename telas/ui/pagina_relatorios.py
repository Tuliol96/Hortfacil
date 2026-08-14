import re
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QDate, QUrl, Qt
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

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

# Quantos anos antes/depois do atual entram na busca por ano.
ANOS_PARA_TRAS = 5
ANOS_PARA_FRENTE = 1


def _periodo_do_nome_arquivo(nome_arquivo):
    """'Relatorio 01-07-2026 a 03-08-2026' -> '01/07/2026 a 03/08/2026'"""

    texto = re.sub(r"^Relatorio\s+", "", nome_arquivo)
    return re.sub(r"(\d{2})-(\d{2})-(\d{4})", r"\1/\2/\3", texto)


def _gerado_no_mes_ano(arquivo, mes, ano):
    """Filtra pela data em que o relatório foi gerado (data do arquivo),
    não pelo período que ele cobre — um relatório é gerado numa data só,
    enquanto o período que ele resume pode atravessar vários meses."""

    gerado_em = datetime.fromtimestamp(arquivo.stat().st_mtime)
    return gerado_em.month == mes and gerado_em.year == ano


def _configurar_busca(combo, placeholder):
    """Deixa o combo editável e pesquisável (digita e filtra as opções),
    igual ao combo de cliente — usado tanto para mês quanto para ano."""

    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.NoInsert)
    combo.lineEdit().setPlaceholderText(placeholder)

    completador = combo.completer()
    completador.setCompletionMode(QCompleter.PopupCompletion)
    completador.setFilterMode(Qt.MatchContains)
    completador.setCaseSensitivity(Qt.CaseInsensitive)


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
        _configurar_busca(self.combo_cliente, "Digite para pesquisar o cliente...")
        self.combo_cliente.currentIndexChanged.connect(self.buscar_relatorios)
        linha_filtro.addWidget(self.combo_cliente, 1)

        # ==========================
        # Busca por mês (nome) e ano, em barras separadas
        # ==========================

        linha_filtro.addWidget(QLabel("Mês:"))

        self.combo_mes = QComboBox()
        _configurar_busca(self.combo_mes, "Digite o mês...")
        for numero, nome in enumerate(MESES, start=1):
            self.combo_mes.addItem(nome, numero)
        # seleciona o mês atual como padrão ANTES de conectar o sinal, para
        # não disparar buscar_relatorios() antes da tabela existir (ela só é
        # criada mais abaixo, nesta mesma montar_interface()).
        self.combo_mes.setCurrentIndex(self.combo_mes.findData(QDate.currentDate().month()))
        self.combo_mes.currentIndexChanged.connect(self.buscar_relatorios)
        linha_filtro.addWidget(self.combo_mes)

        linha_filtro.addWidget(QLabel("Ano:"))

        self.combo_ano = QComboBox()
        _configurar_busca(self.combo_ano, "Digite o ano...")
        ano_atual = QDate.currentDate().year()
        for ano in range(ano_atual - ANOS_PARA_TRAS, ano_atual + ANOS_PARA_FRENTE + 1):
            self.combo_ano.addItem(str(ano), ano)
        self.combo_ano.setCurrentIndex(self.combo_ano.findData(ano_atual))
        self.combo_ano.currentIndexChanged.connect(self.buscar_relatorios)
        linha_filtro.addWidget(self.combo_ano)

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

        mes = self.combo_mes.currentData()
        ano = self.combo_ano.currentData()

        if mes is None or ano is None:
            self._mostrar_status("Selecione o mês e o ano para ver os relatórios gerados.")
            return

        nome_cliente = self.combo_cliente.currentText()
        pasta_cliente = PASTA_RELATORIOS / _nome_arquivo_seguro(nome_cliente)

        arquivos = []
        if pasta_cliente.exists():
            arquivos = sorted(
                (
                    arquivo for arquivo in pasta_cliente.glob("*.pdf")
                    if _gerado_no_mes_ano(arquivo, mes, ano)
                ),
                key=lambda arquivo: arquivo.stat().st_mtime,
                reverse=True,
            )

        if not arquivos:
            self._mostrar_status(
                f"Nenhum relatório gerado para \"{nome_cliente}\" em "
                f"{MESES[mes - 1]}/{ano}."
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
