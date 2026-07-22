import re

from PySide6.QtCore import QSizeF, Qt, Signal
from PySide6.QtGui import QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from controllers.configuracao_controller import ConfiguracaoController
from controllers.pedido_controller import PedidoController
from util.formatacao import formatar_data_hora

COLUNAS = ["Produto", "Unidade", "Quantidade", "Preço Unit.", "Subtotal"]

NOME_EMPRESA_PADRAO = "HORTFÁCIL"


def _nome_arquivo_seguro(texto):
    texto = re.sub(r'[\\/:*?"<>|]', "", texto).strip()
    return texto or "cliente"


class DetalhesPedidoDialog(QDialog):

    pedido_excluido = Signal(int)
    pedido_emitido = Signal(int)
    ver_cliente_solicitado = Signal(int)

    def __init__(self, banco, pedido_id, parent=None):
        super().__init__(parent)

        self.controller = PedidoController(banco)
        self.configuracao_controller = ConfiguracaoController(banco)
        self.pedido_id = pedido_id
        self.pedido = self.controller.buscar_pedido(pedido_id)
        self.itens = self.controller.listar_itens(pedido_id)
        self.configuracao = self.configuracao_controller.obter_configuracao()

        self.setWindowTitle(f"Pedido #{pedido_id}")
        self.resize(600, 500)

        self.montar_interface()

    def _texto_status(self):
        if self.pedido["emitido"]:
            return f"Status: Emitido em {formatar_data_hora(self.pedido['data_emissao'])}"
        return f"Status: Rascunho (salvo em {formatar_data_hora(self.pedido['criado_em'])})"

    def montar_interface(self):

        layout = QVBoxLayout(self)

        titulo = QLabel(f"Pedido #{self.pedido_id}")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size:20px; font-weight:bold;")
        layout.addWidget(titulo)

        layout.addWidget(QLabel(f"Cliente: {self.pedido['cliente_nome']}"))

        self.label_status = QLabel(self._texto_status())
        self.label_status.setStyleSheet("font-weight:bold;")
        layout.addWidget(self.label_status)

        tabela = QTableWidget()
        tabela.setColumnCount(len(COLUNAS))
        tabela.setHorizontalHeaderLabels(COLUNAS)
        tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        tabela.setRowCount(len(self.itens))

        for linha, item in enumerate(self.itens):
            tabela.setItem(linha, 0, QTableWidgetItem(item["produto_nome"]))
            tabela.setItem(linha, 1, QTableWidgetItem(item["produto_unidade"]))
            tabela.setItem(linha, 2, QTableWidgetItem(f"{item['quantidade']:g}"))
            tabela.setItem(linha, 3, QTableWidgetItem(f"R$ {item['preco_unitario']:.2f}"))
            tabela.setItem(linha, 4, QTableWidgetItem(f"R$ {item['subtotal']:.2f}"))

        layout.addWidget(tabela)

        label_total = QLabel(f"Total: R$ {self.pedido['total']:.2f}")
        label_total.setAlignment(Qt.AlignRight)
        label_total.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(label_total)

        self.botao_emitir = QPushButton("Emitir Pedido")
        self.botao_emitir.clicked.connect(self.emitir_pedido)
        layout.addWidget(self.botao_emitir)

        linha_botoes_1 = QHBoxLayout()

        self.botao_pdf = QPushButton("Imprimir PDF")
        self.botao_pdf.clicked.connect(self.imprimir_pdf)

        self.botao_cupom = QPushButton("Imprimir Cupom")
        self.botao_cupom.clicked.connect(self.imprimir_cupom)

        botao_ver_cliente = QPushButton("Ver Cliente")
        botao_ver_cliente.clicked.connect(self.ver_cliente)

        linha_botoes_1.addWidget(self.botao_pdf)
        linha_botoes_1.addWidget(self.botao_cupom)
        linha_botoes_1.addWidget(botao_ver_cliente)
        layout.addLayout(linha_botoes_1)

        linha_botoes_2 = QHBoxLayout()

        botao_excluir = QPushButton("Excluir Pedido")
        botao_excluir.setProperty("perigo", True)
        botao_excluir.clicked.connect(self.excluir_pedido)

        botao_fechar = QPushButton("Fechar")
        botao_fechar.clicked.connect(self.close)

        linha_botoes_2.addWidget(botao_excluir)
        linha_botoes_2.addWidget(botao_fechar)
        layout.addLayout(linha_botoes_2)

        self._atualizar_estado_emissao()

    def _atualizar_estado_emissao(self):

        emitido = bool(self.pedido["emitido"])

        self.botao_emitir.setVisible(not emitido)
        self.botao_pdf.setEnabled(emitido)
        self.botao_cupom.setEnabled(emitido)

        dica = "" if emitido else "Emita o pedido para liberar a impressão."
        self.botao_pdf.setToolTip(dica)
        self.botao_cupom.setToolTip(dica)

    # ==========================
    # Emitir
    # ==========================

    def emitir_pedido(self):

        resposta = QMessageBox.question(
            self,
            "Emitir pedido",
            f"Emitir o pedido #{self.pedido_id} com a data de hoje?\n"
            "Depois de emitido, a impressão fica liberada.",
        )

        if resposta != QMessageBox.Yes:
            return

        self.controller.emitir_pedido(self.pedido_id)
        self.pedido = self.controller.buscar_pedido(self.pedido_id)

        self.label_status.setText(self._texto_status())
        self._atualizar_estado_emissao()

        self.pedido_emitido.emit(self.pedido_id)

    # ==========================
    # Dados da empresa (config)
    # ==========================

    def _nome_empresa(self):
        if self.configuracao and self.configuracao["nome_empresa"]:
            return self.configuracao["nome_empresa"]
        return NOME_EMPRESA_PADRAO

    def _linhas_contato_empresa(self):
        """Endereço, CNPJ e telefone configurados, só os que estiverem preenchidos."""

        if not self.configuracao:
            return []

        linhas = []

        if self.configuracao["endereco"]:
            linhas.append(self.configuracao["endereco"])
        if self.configuracao["cnpj"]:
            linhas.append(f"CNPJ: {self.configuracao['cnpj']}")
        if self.configuracao["telefone"]:
            linhas.append(f"Tel: {self.configuracao['telefone']}")

        return linhas

    # ==========================
    # Impressão em PDF
    # ==========================

    def _html_pedido(self):

        linhas_itens = "".join(
            f"<tr>"
            f"<td>{item['produto_nome']}</td>"
            f"<td>{item['produto_unidade']}</td>"
            f"<td align='right'>{item['quantidade']:g}</td>"
            f"<td align='right'>R$ {item['preco_unitario']:.2f}</td>"
            f"<td align='right'>R$ {item['subtotal']:.2f}</td>"
            f"</tr>"
            for item in self.itens
        )

        contato_empresa = " | ".join(self._linhas_contato_empresa())
        cabecalho_contato = f"<p align='center'>{contato_empresa}</p>" if contato_empresa else ""

        return f"""
        <h1 align="center">{self._nome_empresa()}</h1>
        {cabecalho_contato}
        <hr>
        <h2>Pedido #{self.pedido_id}</h2>
        <p>
            <b>Cliente:</b> {self.pedido['cliente_nome']}<br>
            <b>Data de emissão:</b> {formatar_data_hora(self.pedido['data_emissao'])}
        </p>
        <table width="100%" border="1" cellspacing="0" cellpadding="4">
            <tr>
                <th>Produto</th><th>Unidade</th><th>Quantidade</th>
                <th>Preço Unit.</th><th>Subtotal</th>
            </tr>
            {linhas_itens}
        </table>
        <h3 align="right">Total: R$ {self.pedido['total']:.2f}</h3>
        """

    def imprimir_pdf(self):

        nome_cliente = _nome_arquivo_seguro(self.pedido["cliente_nome"])
        nome_sugerido = f"Pedido {self.pedido_id} - {nome_cliente}.pdf"

        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar pedido em PDF",
            nome_sugerido,
            "PDF (*.pdf)",
        )

        if not caminho:
            return

        impressora = QPrinter(QPrinter.PrinterMode.HighResolution)
        impressora.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        impressora.setOutputFileName(caminho)

        documento = QTextDocument()
        documento.setHtml(self._html_pedido())
        documento.print_(impressora)

        QMessageBox.information(self, "PDF gerado", f"Pedido salvo em:\n{caminho}")

    # ==========================
    # Impressão em cupom térmico
    # ==========================

    def _texto_cupom(self, largura=40):

        linhas = []
        linhas.append(self._nome_empresa().center(largura))

        for linha_contato in self._linhas_contato_empresa():
            linhas.append(linha_contato.center(largura))

        linhas.append("=" * largura)
        linhas.append(f"Pedido #{self.pedido_id}")
        linhas.append(f"Cliente: {self.pedido['cliente_nome']}")
        linhas.append(f"Emissão: {formatar_data_hora(self.pedido['data_emissao'])}")
        linhas.append("-" * largura)

        for item in self.itens:
            nome = item["produto_nome"]
            linhas.append(nome[:largura])
            detalhe = f"{item['quantidade']:g} x R$ {item['preco_unitario']:.2f}"
            subtotal = f"R$ {item['subtotal']:.2f}"
            espacos = max(1, largura - len(detalhe) - len(subtotal))
            linhas.append(detalhe + (" " * espacos) + subtotal)

        linhas.append("-" * largura)
        total_texto = f"TOTAL: R$ {self.pedido['total']:.2f}"
        linhas.append(total_texto.rjust(largura))
        linhas.append("=" * largura)

        return "\n".join(linhas)

    def imprimir_cupom(self):

        nome_cliente = _nome_arquivo_seguro(self.pedido["cliente_nome"])

        impressora = QPrinter(QPrinter.PrinterMode.HighResolution)
        impressora.setPageSize(QPageSize(QSizeF(80, 200), QPageSize.Unit.Millimeter))
        impressora.setDocName(f"Pedido {self.pedido_id} - {nome_cliente}")

        dialogo = QPrintDialog(impressora, self)
        dialogo.setWindowTitle("Imprimir cupom")

        if dialogo.exec() != QDialog.Accepted:
            return

        documento = QTextDocument()
        documento.setDefaultFont(self.font())
        documento.setHtml(
            "<pre style='font-family:Courier New; font-size:9pt;'>"
            f"{self._texto_cupom()}"
            "</pre>"
        )
        documento.print_(impressora)

    # ==========================
    # Excluir / navegar para cliente
    # ==========================

    def excluir_pedido(self):

        resposta = QMessageBox.question(
            self,
            "Excluir pedido",
            f"Deseja realmente excluir o pedido #{self.pedido_id}? Essa ação não pode ser desfeita.",
        )

        if resposta != QMessageBox.Yes:
            return

        self.controller.excluir_pedido(self.pedido_id)
        self.pedido_excluido.emit(self.pedido_id)
        self.close()

    def ver_cliente(self):
        self.ver_cliente_solicitado.emit(self.pedido["cliente_id"])
        self.close()
