from pathlib import Path

from PySide6.QtCore import QDate, QUrl, Qt
from PySide6.QtGui import QDesktopServices, QTextDocument
from PySide6.QtPrintSupport import QPrinter
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
from controllers.configuracao_controller import ConfiguracaoController
from controllers.pedido_controller import PedidoController
from telas.ui.dialogo_detalhes_pedido import (
    COR_ESCURA,
    NOME_EMPRESA_PADRAO,
    DetalhesPedidoDialog,
    _logo_data_uri,
    _nome_arquivo_seguro,
)
from telas.ui.dialogo_resumo_produtos import ResumoProdutosDialog
from util.formatacao import formatar_data, formatar_data_hora

COLUNAS = ["Nota #", "Data", "Total"]

# Relatórios em PDF ficam em uma subpasta por cliente, para a aba
# "Relatórios" conseguir listá-los já organizados (ver pagina_relatorios.py).
PASTA_RELATORIOS = Path(__file__).resolve().parent.parent.parent / "relatorios"


class PaginaFechamentos(QWidget):

    def __init__(self, banco):
        super().__init__()

        self.banco = banco
        self.cliente_controller = ClienteController(banco)
        self.pedido_controller = PedidoController(banco)
        self.configuracao_controller = ConfiguracaoController(banco)

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

        linha_acoes = QHBoxLayout()

        self.botao_detalhes = QPushButton("Detalhes")
        self.botao_detalhes.clicked.connect(self.abrir_resumo_produtos)
        linha_acoes.addWidget(self.botao_detalhes)

        self.botao_gerar_relatorio = QPushButton("Gerar Relatório")
        self.botao_gerar_relatorio.clicked.connect(self.gerar_relatorio)
        linha_acoes.addWidget(self.botao_gerar_relatorio)

        layout.addLayout(linha_acoes)

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

    # ==========================
    # Relatório em PDF (para enviar ao cliente)
    # ==========================

    def _html_relatorio(self, cliente_nome, data_inicio, data_fim, pedidos):

        configuracao = self.configuracao_controller.obter_configuracao()
        nome_empresa = (
            configuracao["nome_empresa"]
            if configuracao and configuracao["nome_empresa"]
            else NOME_EMPRESA_PADRAO
        )

        logo_uri = _logo_data_uri()
        logo_html = (
            f'<img src="{logo_uri}" width="140">'
            if logo_uri
            else f'<span style="font-size:20pt; font-weight:bold;">{nome_empresa}</span>'
        )

        linhas = "".join(
            f"<tr>"
            f"<td>{pedido['id']}</td>"
            f"<td>{formatar_data_hora(pedido['data_emissao'])}</td>"
            f"<td align='right'>R$ {pedido['total']:.2f}</td>"
            f"</tr>"
            for pedido in pedidos
        )

        total_periodo = sum(pedido["total"] for pedido in pedidos)

        return f"""
        {logo_html}
        <h2 align="center">Relatório de Pedidos</h2>
        <p align="center">
            <b>Cliente:</b> {cliente_nome}<br>
            <b>Período:</b> {formatar_data(data_inicio)} a {formatar_data(data_fim)}
        </p>
        <hr>
        <table width="100%" border="1" cellspacing="0" cellpadding="6">
            <tr style="background-color:{COR_ESCURA}; color:#FFFFFF;">
                <th>Nota #</th><th>Data</th><th>Valor</th>
            </tr>
            {linhas}
            <tr style="background-color:{COR_ESCURA}; color:#FFFFFF;">
                <td colspan="2" align="right"><b>TOTAL DO PERÍODO</b></td>
                <td align="right">
                    <span style="font-size:14pt;"><b>R$ {total_periodo:.2f}</b></span>
                </td>
            </tr>
        </table>
        """

    def gerar_relatorio(self):

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

        if not pedidos:
            QMessageBox.information(
                self, "Nada para gerar",
                "Não há pedidos emitidos para este cliente no período selecionado."
            )
            return

        cliente_nome = self.combo_cliente.currentText()

        html = self._html_relatorio(cliente_nome, data_inicio, data_fim, pedidos)

        nome_cliente_seguro = _nome_arquivo_seguro(cliente_nome)
        pasta_cliente = PASTA_RELATORIOS / nome_cliente_seguro
        pasta_cliente.mkdir(parents=True, exist_ok=True)

        periodo_arquivo = f"{formatar_data(data_inicio)} a {formatar_data(data_fim)}".replace("/", "-")
        caminho = pasta_cliente / f"Relatorio {periodo_arquivo}.pdf"

        impressora = QPrinter(QPrinter.PrinterMode.HighResolution)
        impressora.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        impressora.setOutputFileName(str(caminho))

        documento = QTextDocument()
        documento.setHtml(html)
        documento.print_(impressora)

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(caminho)))

        QMessageBox.information(
            self, "Relatório gerado",
            f"Relatório salvo e disponível na aba Relatórios:\n{caminho}"
        )
