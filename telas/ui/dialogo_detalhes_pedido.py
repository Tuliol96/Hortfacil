import re

from PySide6.QtCore import QDate, QMarginsF, QSizeF, Qt, Signal
from PySide6.QtGui import QFont, QPageLayout, QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.configuracao_controller import ConfiguracaoController
from controllers.pedido_controller import PedidoController
from controllers.produto_controller import ProdutoController
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
        self.produto_controller = ProdutoController(banco)
        self.pedido_id = pedido_id
        self.pedido = self.controller.buscar_pedido(pedido_id)
        self.itens = self.controller.listar_itens(pedido_id)
        self.configuracao = self.configuracao_controller.obter_configuracao()

        self.modo_edicao = False
        self.itens_edicao = []
        self.indice_item_selecionado = None

        self.setWindowTitle(f"Pedido #{pedido_id}")
        self.resize(600, 550)

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

        # ==========================
        # Data de emissão (editável enquanto for rascunho, padrão hoje)
        # ==========================

        self.linha_data_emissao = QWidget()
        linha_data_emissao_layout = QHBoxLayout(self.linha_data_emissao)
        linha_data_emissao_layout.setContentsMargins(0, 0, 0, 0)

        linha_data_emissao_layout.addWidget(QLabel("Data de emissão:"))

        self.campo_data_emissao = QDateEdit()
        self.campo_data_emissao.setCalendarPopup(True)
        self.campo_data_emissao.setDisplayFormat("dd/MM/yyyy")
        self.campo_data_emissao.setDate(QDate.currentDate())
        linha_data_emissao_layout.addWidget(self.campo_data_emissao)
        linha_data_emissao_layout.addStretch()

        layout.addWidget(self.linha_data_emissao)
        self.linha_data_emissao.setVisible(not self.pedido["emitido"])

        # ==========================
        # Adicionar/editar item (só visível em modo de edição)
        # ==========================

        self.painel_edicao_item = QWidget()
        linha_item = QHBoxLayout(self.painel_edicao_item)
        linha_item.setContentsMargins(0, 0, 0, 0)

        self.combo_produto = QComboBox()
        self.combo_produto.currentIndexChanged.connect(self._auto_preencher_preco)

        self.campo_quantidade = QLineEdit()
        self.campo_quantidade.setPlaceholderText("Quantidade")
        self.campo_quantidade.setFixedWidth(100)

        self.campo_preco_unitario = QLineEdit()
        self.campo_preco_unitario.setPlaceholderText("Preço unit.")
        self.campo_preco_unitario.setFixedWidth(100)

        self.checkbox_sp = QCheckBox("SP")
        self.checkbox_sp.setToolTip("Produto de origem paulista, com preço à parte")
        self.checkbox_sp.toggled.connect(self._ao_alternar_sp)

        self.botao_adicionar_item = QPushButton("Adicionar item")
        self.botao_adicionar_item.clicked.connect(self.salvar_item_edicao)

        self.botao_cancelar_edicao_item = QPushButton("Cancelar edição do item")
        self.botao_cancelar_edicao_item.setProperty("perigo", True)
        self.botao_cancelar_edicao_item.clicked.connect(self.limpar_selecao_item)
        self.botao_cancelar_edicao_item.setVisible(False)

        linha_item.addWidget(self.combo_produto, 1)
        linha_item.addWidget(self.campo_quantidade)
        linha_item.addWidget(self.campo_preco_unitario)
        linha_item.addWidget(self.checkbox_sp)
        linha_item.addWidget(self.botao_adicionar_item)
        linha_item.addWidget(self.botao_cancelar_edicao_item)

        layout.addWidget(self.painel_edicao_item)
        self.painel_edicao_item.setVisible(False)

        # ==========================
        # Tabela de itens
        # ==========================

        self.tabela_itens = QTableWidget()
        self.tabela_itens.setColumnCount(len(COLUNAS))
        self.tabela_itens.setHorizontalHeaderLabels(COLUNAS)
        self.tabela_itens.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabela_itens.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela_itens.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela_itens.itemSelectionChanged.connect(self.selecionar_item)
        layout.addWidget(self.tabela_itens)

        self.botao_remover_item = QPushButton("Remover item selecionado")
        self.botao_remover_item.setProperty("perigo", True)
        self.botao_remover_item.clicked.connect(self.remover_item_selecionado)
        self.botao_remover_item.setVisible(False)
        layout.addWidget(self.botao_remover_item)

        self.label_total = QLabel()
        self.label_total.setAlignment(Qt.AlignRight)
        self.label_total.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(self.label_total)

        self.atualizar_tabela_itens()

        self.botao_emitir = QPushButton("Emitir Pedido")
        self.botao_emitir.clicked.connect(self.emitir_pedido)
        layout.addWidget(self.botao_emitir)

        linha_edicao_pedido = QHBoxLayout()

        self.botao_editar_pedido = QPushButton("Editar Pedido")
        self.botao_editar_pedido.setProperty("limpar", True)
        self.botao_editar_pedido.clicked.connect(self.entrar_modo_edicao)

        self.botao_salvar_edicao = QPushButton("Salvar Alterações")
        self.botao_salvar_edicao.clicked.connect(self.salvar_edicao_pedido)
        self.botao_salvar_edicao.setVisible(False)

        self.botao_cancelar_edicao_pedido = QPushButton("Cancelar Edição")
        self.botao_cancelar_edicao_pedido.setProperty("perigo", True)
        self.botao_cancelar_edicao_pedido.clicked.connect(self.cancelar_edicao_pedido)
        self.botao_cancelar_edicao_pedido.setVisible(False)

        linha_edicao_pedido.addWidget(self.botao_editar_pedido)
        linha_edicao_pedido.addWidget(self.botao_salvar_edicao)
        linha_edicao_pedido.addWidget(self.botao_cancelar_edicao_pedido)
        layout.addLayout(linha_edicao_pedido)

        linha_botoes_1 = QHBoxLayout()

        self.botao_pdf = QPushButton("Imprimir PDF")
        self.botao_pdf.clicked.connect(self.imprimir_pdf)

        self.botao_cupom = QPushButton("Imprimir Cupom")
        self.botao_cupom.clicked.connect(self.imprimir_cupom)

        self.botao_ver_cliente = QPushButton("Ver Cliente")
        self.botao_ver_cliente.clicked.connect(self.ver_cliente)

        linha_botoes_1.addWidget(self.botao_pdf)
        linha_botoes_1.addWidget(self.botao_cupom)
        linha_botoes_1.addWidget(self.botao_ver_cliente)
        layout.addLayout(linha_botoes_1)

        linha_botoes_2 = QHBoxLayout()

        self.botao_excluir = QPushButton("Excluir Pedido")
        self.botao_excluir.setProperty("perigo", True)
        self.botao_excluir.clicked.connect(self.excluir_pedido)

        self.botao_fechar = QPushButton("Fechar")
        self.botao_fechar.clicked.connect(self.close)

        linha_botoes_2.addWidget(self.botao_excluir)
        linha_botoes_2.addWidget(self.botao_fechar)
        layout.addLayout(linha_botoes_2)

        self._atualizar_estado_emissao()

    def _atualizar_estado_emissao(self):

        emitido = bool(self.pedido["emitido"])

        self.botao_emitir.setVisible(not emitido and not self.modo_edicao)
        self.botao_editar_pedido.setVisible(not emitido and not self.modo_edicao)
        self.botao_pdf.setEnabled(emitido)
        self.botao_cupom.setEnabled(emitido)

        dica = "" if emitido else "Emita o pedido para liberar a impressão."
        self.botao_pdf.setToolTip(dica)
        self.botao_cupom.setToolTip(dica)

    # ==========================
    # Tabela de itens (leitura e edição)
    # ==========================

    def atualizar_tabela_itens(self):

        itens = self.itens_edicao if self.modo_edicao else self.itens

        self.tabela_itens.setRowCount(len(itens))

        total = 0.0

        for linha, item in enumerate(itens):
            nome = item["nome"] if self.modo_edicao else item["produto_nome"]
            unidade = item["unidade"] if self.modo_edicao else item["produto_unidade"]
            quantidade = item["quantidade"]
            preco_unitario = item["preco_unitario"]
            subtotal = round(quantidade * preco_unitario, 2)
            total += subtotal

            if item["sp"]:
                nome += " (SP)"

            self.tabela_itens.setItem(linha, 0, QTableWidgetItem(nome))
            self.tabela_itens.setItem(linha, 1, QTableWidgetItem(unidade))
            self.tabela_itens.setItem(linha, 2, QTableWidgetItem(f"{quantidade:g}"))
            self.tabela_itens.setItem(linha, 3, QTableWidgetItem(f"R$ {preco_unitario:.2f}"))
            self.tabela_itens.setItem(linha, 4, QTableWidgetItem(f"R$ {subtotal:.2f}"))

        self.label_total.setText(f"Total: R$ {total:.2f}")

    # ==========================
    # Edição do pedido (só liberada enquanto for rascunho)
    # ==========================

    @staticmethod
    def _texto_preco(preco):
        if preco is None:
            return "preço variável"
        return f"R$ {preco:.2f}"

    def _carregar_combo_produtos(self):

        produto_atual = self.combo_produto.currentData()

        self.combo_produto.clear()
        for produto in self.produto_controller.listar_produtos():
            texto = f"{produto['nome']} ({produto['unidade']}) - {self._texto_preco(produto['preco'])}"
            self.combo_produto.addItem(texto, dict(produto))

        if produto_atual is not None:
            indice = self._indice_combo_produto(produto_atual["id"])
            if indice >= 0:
                self.combo_produto.setCurrentIndex(indice)

    def _indice_combo_produto(self, produto_id):
        for i in range(self.combo_produto.count()):
            dado = self.combo_produto.itemData(i)
            if dado and dado["id"] == produto_id:
                return i
        return -1

    def _auto_preencher_preco(self, _indice):

        # não sobrescreve o preço enquanto estamos editando um item já lançado
        if self.indice_item_selecionado is not None:
            return

        produto = self.combo_produto.currentData()

        if produto is None or produto["preco"] is None:
            self.campo_preco_unitario.clear()
        else:
            self.campo_preco_unitario.setText(f"{produto['preco']:.2f}")

    def _ao_alternar_sp(self, marcado):

        if not marcado:
            return

        produto = self.combo_produto.currentData()
        nome = produto["nome"] if produto else "produto"

        texto_preco_atual = self.campo_preco_unitario.text().strip().replace(",", ".")
        try:
            valor_inicial = float(texto_preco_atual)
        except ValueError:
            valor_inicial = 0.0

        preco, confirmado = QInputDialog.getDouble(
            self,
            "Preço SP",
            f"Informe o novo preço (SP) para \"{nome}\":",
            valor_inicial,
            0.0,
            999999.0,
            2,
        )

        if not confirmado:
            self.checkbox_sp.blockSignals(True)
            self.checkbox_sp.setChecked(False)
            self.checkbox_sp.blockSignals(False)
            return

        self.campo_preco_unitario.setText(f"{preco:.2f}")

    def _marcar_sp_sem_perguntar(self, marcado):
        """Ajusta o checkbox SP ao selecionar um item já lançado, sem
        reabrir o prompt de preço (que é só para quando o usuário marca)."""

        self.checkbox_sp.blockSignals(True)
        self.checkbox_sp.setChecked(marcado)
        self.checkbox_sp.blockSignals(False)

    def entrar_modo_edicao(self):

        if self.pedido["emitido"]:
            return

        self.itens_edicao = [
            {
                "produto_id": item["produto_id"],
                "nome": item["produto_nome"],
                "unidade": item["produto_unidade"],
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
                "sp": bool(item["sp"]),
            }
            for item in self.itens
        ]
        self.indice_item_selecionado = None
        self.modo_edicao = True

        self._carregar_combo_produtos()

        self.painel_edicao_item.setVisible(True)
        self.botao_remover_item.setVisible(True)
        self.botao_salvar_edicao.setVisible(True)
        self.botao_cancelar_edicao_pedido.setVisible(True)
        self.botao_excluir.setEnabled(False)
        self.botao_ver_cliente.setEnabled(False)

        self.atualizar_tabela_itens()
        self._atualizar_estado_emissao()

    def _sair_modo_edicao(self):

        self.modo_edicao = False
        self.itens_edicao = []
        self.limpar_selecao_item()

        self.painel_edicao_item.setVisible(False)
        self.botao_remover_item.setVisible(False)
        self.botao_salvar_edicao.setVisible(False)
        self.botao_cancelar_edicao_pedido.setVisible(False)
        self.botao_excluir.setEnabled(True)
        self.botao_ver_cliente.setEnabled(True)

        self.atualizar_tabela_itens()
        self._atualizar_estado_emissao()

    def cancelar_edicao_pedido(self):

        resposta = QMessageBox.question(
            self,
            "Cancelar edição",
            "Descartar as alterações feitas neste pedido?",
        )

        if resposta != QMessageBox.Yes:
            return

        self._sair_modo_edicao()

    def salvar_edicao_pedido(self):

        if not self.itens_edicao:
            QMessageBox.warning(self, "Pedido vazio", "O pedido precisa ter ao menos um item.")
            return

        itens = [
            (item["produto_id"], item["quantidade"], item["preco_unitario"], item["sp"])
            for item in self.itens_edicao
        ]

        self.controller.atualizar_pedido(self.pedido_id, itens)

        self.pedido = self.controller.buscar_pedido(self.pedido_id)
        self.itens = self.controller.listar_itens(self.pedido_id)

        self._sair_modo_edicao()

        QMessageBox.information(self, "Pedido atualizado", "As alterações foram salvas com sucesso!")

    # ==========================
    # Itens do pedido em edição
    # ==========================

    def selecionar_item(self):

        if not self.modo_edicao:
            return

        linhas = self.tabela_itens.selectionModel().selectedRows()

        if not linhas:
            self.indice_item_selecionado = None
            self.botao_adicionar_item.setText("Adicionar item")
            self.botao_cancelar_edicao_item.setVisible(False)
            return

        indice = linhas[0].row()
        item = self.itens_edicao[indice]

        self.indice_item_selecionado = indice

        indice_combo = self._indice_combo_produto(item["produto_id"])
        if indice_combo >= 0:
            self.combo_produto.setCurrentIndex(indice_combo)

        self.campo_quantidade.setText(f"{item['quantidade']:g}")
        self.campo_preco_unitario.setText(f"{item['preco_unitario']:.2f}")
        self._marcar_sp_sem_perguntar(item.get("sp", False))

        self.botao_adicionar_item.setText("Atualizar item")
        self.botao_cancelar_edicao_item.setVisible(True)

    def limpar_selecao_item(self):

        self.indice_item_selecionado = None
        self.campo_quantidade.clear()
        self.campo_preco_unitario.clear()
        self._marcar_sp_sem_perguntar(False)
        self.tabela_itens.clearSelection()
        self.botao_adicionar_item.setText("Adicionar item")
        self.botao_cancelar_edicao_item.setVisible(False)

    def salvar_item_edicao(self):

        produto = self.combo_produto.currentData()

        if produto is None:
            QMessageBox.warning(
                self, "Nenhum produto",
                "Cadastre ao menos um produto antes de editar o pedido."
            )
            return

        texto_quantidade = self.campo_quantidade.text().strip().replace(",", ".")

        try:
            quantidade = float(texto_quantidade)
        except ValueError:
            QMessageBox.warning(self, "Quantidade inválida", "Informe uma quantidade numérica válida.")
            return

        if quantidade <= 0:
            QMessageBox.warning(self, "Quantidade inválida", "A quantidade deve ser maior que zero.")
            return

        texto_preco = self.campo_preco_unitario.text().strip().replace(",", ".")

        if not texto_preco:
            QMessageBox.warning(self, "Preço obrigatório", "Informe o preço unitário deste item.")
            return

        try:
            preco_unitario = float(texto_preco)
        except ValueError:
            QMessageBox.warning(self, "Preço inválido", "Informe um preço numérico válido.")
            return

        if preco_unitario < 0:
            QMessageBox.warning(self, "Preço inválido", "O preço não pode ser negativo.")
            return

        item = {
            "produto_id": produto["id"],
            "nome": produto["nome"],
            "unidade": produto["unidade"],
            "quantidade": quantidade,
            "preco_unitario": preco_unitario,
            "sp": self.checkbox_sp.isChecked(),
        }

        if self.indice_item_selecionado is not None:
            self.itens_edicao[self.indice_item_selecionado] = item
        else:
            self.itens_edicao.append(item)

        self.limpar_selecao_item()
        self.atualizar_tabela_itens()

    def remover_item_selecionado(self):

        linhas = self.tabela_itens.selectionModel().selectedRows()

        if not linhas:
            return

        indice = linhas[0].row()
        del self.itens_edicao[indice]
        self.limpar_selecao_item()
        self.atualizar_tabela_itens()

    # ==========================
    # Emitir
    # ==========================

    def emitir_pedido(self):

        data_emissao = self.campo_data_emissao.date().toString("yyyy-MM-dd")

        resposta = QMessageBox.question(
            self,
            "Emitir pedido",
            f"Emitir o pedido #{self.pedido_id} com data de emissão "
            f"{self.campo_data_emissao.date().toString('dd/MM/yyyy')}?\n"
            "Depois de emitido, a impressão fica liberada.",
        )

        if resposta != QMessageBox.Yes:
            return

        self.controller.emitir_pedido(self.pedido_id, data_emissao)
        self.pedido = self.controller.buscar_pedido(self.pedido_id)

        self.label_status.setText(self._texto_status())
        self.linha_data_emissao.setVisible(False)
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
            f"<td>{item['produto_nome']}{' (SP)' if item['sp'] else ''}</td>"
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

    # Tomate MDK-082: bobina de 80mm. Usamos a largura cheia do papel —
    # como o conteúdo é montado com tabelas de largura 100% (não mais
    # caracteres fixos), ele se ajusta sozinho à área real que o driver
    # liberar, sem risco de estourar e cortar texto.
    LARGURA_IMPRIMIVEL_MM = 80

    # Espaço extra deixado após o total antes do corte automático da
    # guilhotina — pequeno o bastante para não desperdiçar papel, grande
    # o bastante para a lâmina não cortar em cima do texto do total.
    MARGEM_CORTE_MM = 4

    def _html_cupom(self):

        contato_empresa = "".join(
            f"{linha}<br>" for linha in self._linhas_contato_empresa()
        )

        linhas_itens = "".join(
            f"<tr><td colspan='2'>{item['produto_nome']}{' (SP)' if item['sp'] else ''}</td></tr>"
            f"<tr><td>{item['quantidade']:g} x R$ {item['preco_unitario']:.2f}</td>"
            f"<td align='right'>R$ {item['subtotal']:.2f}</td></tr>"
            for item in self.itens
        )

        return f"""
        <div style="font-family:'Courier New'; font-size:9pt; text-align:center;">
            <b>{self._nome_empresa()}</b><br>
            {contato_empresa}
        </div>
        <hr>
        <div style="font-family:'Courier New'; font-size:9pt;">
            Pedido #{self.pedido_id}<br>
            Cliente: {self.pedido['cliente_nome']}<br>
            Emissão: {formatar_data_hora(self.pedido['data_emissao'])}
        </div>
        <hr>
        <table width="100%" style="font-family:'Courier New'; font-size:9pt;" cellspacing="0" cellpadding="0">
            {linhas_itens}
        </table>
        <hr>
        <table width="100%" style="font-family:'Courier New'; font-size:9pt;">
            <tr><td align="right"><b>TOTAL: R$ {self.pedido['total']:.2f}</b></td></tr>
        </table>
        <hr>
        """

    def imprimir_cupom(self):

        nome_cliente = _nome_arquivo_seguro(self.pedido["cliente_nome"])

        documento = QTextDocument()
        documento.setDefaultFont(QFont("Courier New", 9))
        documento.setHtml(self._html_cupom())

        # a altura precisa ser calculada e aplicada ANTES de abrir o diálogo
        # de impressão: em impressoras físicas reais (ao contrário de um
        # "Microsoft Print to PDF"), o driver trava o tamanho de página
        # assim que o diálogo é aberto, então ajustar depois de aceito é
        # ignorado e o conteúdo restante vai para uma segunda página/corte.
        largura_pt = self.LARGURA_IMPRIMIVEL_MM * 72.0 / 25.4
        documento.setTextWidth(largura_pt)
        altura_mm = (documento.size().height() * 25.4 / 72.0) + self.MARGEM_CORTE_MM

        impressora = QPrinter(QPrinter.PrinterMode.HighResolution)
        impressora.setPageSize(
            QPageSize(QSizeF(self.LARGURA_IMPRIMIVEL_MM, altura_mm), QPageSize.Unit.Millimeter)
        )
        impressora.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
        impressora.setDocName(f"Pedido {self.pedido_id} - {nome_cliente}")

        dialogo = QPrintDialog(impressora, self)
        dialogo.setWindowTitle("Imprimir cupom")

        if dialogo.exec() != QDialog.Accepted:
            return

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
