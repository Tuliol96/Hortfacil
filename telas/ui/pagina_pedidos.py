from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from controllers.cliente_controller import ClienteController
from controllers.pedido_controller import PedidoController
from controllers.produto_controller import ProdutoController
from servicos.interpretador_pedidos import interpretar_pedido
from telas.ui.dialogo_detalhes_pedido import DetalhesPedidoDialog
from util.formatacao import formatar_data_hora

COLUNAS_ITENS = ["Produto", "Unidade", "Quantidade", "Preço Unit.", "Subtotal"]
COLUNAS_PEDIDOS = ["ID", "Cliente", "Total", "Status", "Data Emissão"]


class PaginaPedidos(QWidget):

    solicitou_ver_cliente = Signal(int)

    def __init__(self, banco):
        super().__init__()

        self.banco = banco
        self.cliente_controller = ClienteController(banco)
        self.produto_controller = ProdutoController(banco)
        self.pedido_controller = PedidoController(banco)

        # cada item: produto_id, nome, unidade, quantidade, preco_unitario
        self.itens_pedido = []
        self.indice_item_selecionado = None

        self.montar_interface()
        self.carregar_combos()
        self.carregar_pedidos()

    def showEvent(self, evento):
        super().showEvent(evento)
        self.carregar_combos()

    def montar_interface(self):

        layout = QVBoxLayout(self)

        titulo = QLabel("Pedidos")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size:24px; font-weight:bold;")
        layout.addWidget(titulo)

        # ==========================
        # Cliente
        # ==========================

        linha_cliente = QHBoxLayout()
        linha_cliente.addWidget(QLabel("Cliente:"))
        self.combo_cliente = QComboBox()
        linha_cliente.addWidget(self.combo_cliente, 1)
        layout.addLayout(linha_cliente)

        # ==========================
        # Colar pedido do WhatsApp
        # ==========================

        layout.addWidget(QLabel("Colar pedido do WhatsApp:"))

        self.texto_whatsapp = QTextEdit()
        self.texto_whatsapp.setFixedHeight(120)
        self.texto_whatsapp.setPlaceholderText(
            "Cole aqui o texto do pedido recebido pelo WhatsApp..."
        )
        layout.addWidget(self.texto_whatsapp)

        self.botao_processar = QPushButton("Processar pedido do texto")
        self.botao_processar.clicked.connect(self.processar_texto_whatsapp)
        layout.addWidget(self.botao_processar)

        # ==========================
        # Adicionar / editar item
        # ==========================

        linha_item = QHBoxLayout()

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
        self.botao_adicionar_item.clicked.connect(self.salvar_item)

        self.botao_cancelar_edicao_item = QPushButton("Cancelar edição")
        self.botao_cancelar_edicao_item.setProperty("perigo", True)
        self.botao_cancelar_edicao_item.clicked.connect(self.limpar_selecao_item)
        self.botao_cancelar_edicao_item.setVisible(False)

        linha_item.addWidget(self.combo_produto, 1)
        linha_item.addWidget(self.campo_quantidade)
        linha_item.addWidget(self.campo_preco_unitario)
        linha_item.addWidget(self.checkbox_sp)
        linha_item.addWidget(self.botao_adicionar_item)
        linha_item.addWidget(self.botao_cancelar_edicao_item)
        layout.addLayout(linha_item)

        # ==========================
        # Tabela de itens do pedido atual
        # ==========================

        self.tabela_itens = QTableWidget()
        self.tabela_itens.setColumnCount(len(COLUNAS_ITENS))
        self.tabela_itens.setHorizontalHeaderLabels(COLUNAS_ITENS)
        self.tabela_itens.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabela_itens.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela_itens.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela_itens.itemSelectionChanged.connect(self.selecionar_item)
        layout.addWidget(self.tabela_itens)

        self.botao_remover_item = QPushButton("Remover item selecionado")
        self.botao_remover_item.setProperty("perigo", True)
        self.botao_remover_item.clicked.connect(self.remover_item_selecionado)
        layout.addWidget(self.botao_remover_item)

        self.label_total = QLabel("Total: R$ 0,00")
        self.label_total.setAlignment(Qt.AlignRight)
        self.label_total.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(self.label_total)

        linha_acoes_pedido = QHBoxLayout()

        self.botao_salvar = QPushButton("Salvar Pedido")
        self.botao_salvar.clicked.connect(self.salvar_pedido)

        self.botao_cancelar_pedido = QPushButton("Cancelar Pedido")
        self.botao_cancelar_pedido.setProperty("perigo", True)
        self.botao_cancelar_pedido.clicked.connect(self.cancelar_pedido)

        linha_acoes_pedido.addWidget(self.botao_salvar)
        linha_acoes_pedido.addWidget(self.botao_cancelar_pedido)
        layout.addLayout(linha_acoes_pedido)

        # ==========================
        # Pedidos já realizados
        # ==========================

        layout.addWidget(QLabel("Pedidos realizados:"))

        self.tabela_pedidos = QTableWidget()
        self.tabela_pedidos.setColumnCount(len(COLUNAS_PEDIDOS))
        self.tabela_pedidos.setHorizontalHeaderLabels(COLUNAS_PEDIDOS)
        self.tabela_pedidos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela_pedidos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela_pedidos.itemDoubleClicked.connect(self.abrir_detalhes_pedido)
        layout.addWidget(self.tabela_pedidos)

    # ==========================
    # Carregamento de dados
    # ==========================

    def carregar_combos(self):

        cliente_atual = self.combo_cliente.currentData()
        self.combo_cliente.clear()
        for cliente in self.cliente_controller.listar_clientes():
            self.combo_cliente.addItem(cliente["nome"], cliente["id"])
        if cliente_atual is not None:
            indice = self.combo_cliente.findData(cliente_atual)
            if indice >= 0:
                self.combo_cliente.setCurrentIndex(indice)

        produto_atual = self.combo_produto.currentData()
        self.combo_produto.clear()
        for produto in self.produto_controller.listar_produtos():
            texto = f"{produto['nome']} ({produto['unidade']}) - {self._texto_preco(produto['preco'])}"
            self.combo_produto.addItem(texto, dict(produto))
        if produto_atual is not None:
            indice = self._indice_combo_produto(produto_atual["id"])
            if indice >= 0:
                self.combo_produto.setCurrentIndex(indice)

    def carregar_pedidos(self):

        pedidos = self.pedido_controller.listar_pedidos()

        self.tabela_pedidos.setRowCount(len(pedidos))

        for linha, pedido in enumerate(pedidos):
            self.tabela_pedidos.setItem(linha, 0, QTableWidgetItem(str(pedido["id"])))
            self.tabela_pedidos.setItem(linha, 1, QTableWidgetItem(pedido["cliente_nome"]))
            self.tabela_pedidos.setItem(
                linha, 2, QTableWidgetItem(f"R$ {pedido['total']:.2f}")
            )
            self.tabela_pedidos.setItem(
                linha, 3, QTableWidgetItem("Emitido" if pedido["emitido"] else "Rascunho")
            )
            self.tabela_pedidos.setItem(
                linha, 4, QTableWidgetItem(formatar_data_hora(pedido["data_emissao"]) or "—")
            )

    def abrir_detalhes_pedido(self, item_tabela):

        linha = item_tabela.row()
        pedido_id = int(self.tabela_pedidos.item(linha, 0).text())

        dialogo = DetalhesPedidoDialog(self.banco, pedido_id, self)
        dialogo.pedido_excluido.connect(lambda _id: self.carregar_pedidos())
        dialogo.pedido_emitido.connect(lambda _id: self.carregar_pedidos())
        dialogo.ver_cliente_solicitado.connect(self.solicitou_ver_cliente.emit)
        dialogo.exec()

    @staticmethod
    def _texto_preco(preco):
        if preco is None:
            return "preço variável"
        return f"R$ {preco:.2f}"

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

    # ==========================
    # Preço na hora do pedido (produto com preço variável)
    # ==========================

    def _obter_preco(self, nome, unidade, preco_catalogo, preco_sugerido=None):
        """
        Retorna o preço a usar no pedido. Se o produto tiver preço fixo
        cadastrado, usa ele direto. Senão, pergunta ao usuário na hora.
        Retorna None se o usuário cancelar a pergunta.
        """

        if preco_catalogo is not None:
            return preco_catalogo

        valor_inicial = preco_sugerido if preco_sugerido is not None else 0.0

        preco, confirmado = QInputDialog.getDouble(
            self,
            "Preço necessário",
            f"O produto \"{nome}\" foi cadastrado sem preço fixo.\n"
            f"Informe o preço por {unidade} para este pedido:",
            valor_inicial,
            0.0,
            999999.0,
            2,
        )

        if not confirmado:
            return None

        return preco

    # ==========================
    # Produto SP (origem paulista, com preço à parte)
    # ==========================

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

    # ==========================
    # Produto ambíguo (texto do pedido bateu com mais de um cadastrado)
    # ==========================

    def _escolher_produto_ambiguo(self, item_ambiguo):
        """
        Pergunta ao usuário qual produto usar quando uma linha do pedido
        bate com mais de um produto cadastrado (ex.: "crespa" bate com
        "Alface Crespa" e "Salsa Crespa"). Retorna None se cancelado.
        """

        nomes_candidatos = [produto["nome"] for produto in item_ambiguo.candidatos]

        escolha, confirmado = QInputDialog.getItem(
            self,
            "Produto ambíguo",
            f"A linha \"{item_ambiguo.linha_original}\" bateu com mais de um "
            "produto cadastrado.\nQual produto devo usar?",
            nomes_candidatos,
            0,
            False,
        )

        if not confirmado:
            return None

        return next(
            produto for produto in item_ambiguo.candidatos
            if produto["nome"] == escolha
        )

    # ==========================
    # Itens do pedido atual
    # ==========================

    def selecionar_item(self):

        linhas = self.tabela_itens.selectionModel().selectedRows()

        if not linhas:
            self.indice_item_selecionado = None
            self.botao_adicionar_item.setText("Adicionar item")
            self.botao_cancelar_edicao_item.setVisible(False)
            return

        indice = linhas[0].row()
        item = self.itens_pedido[indice]

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
        self._auto_preencher_preco(self.combo_produto.currentIndex())
        self._marcar_sp_sem_perguntar(False)
        self.tabela_itens.clearSelection()
        self.botao_adicionar_item.setText("Adicionar item")
        self.botao_cancelar_edicao_item.setVisible(False)

    def _avisar_se_produto_duplicado(self, produto_id, nome, indice_ignorar=None):
        """Não bloqueia — é comum lançar o mesmo produto mais de uma vez de
        propósito, mas costuma ser engano de digitação. Só chama atenção."""

        ja_existe = any(
            item["produto_id"] == produto_id
            for indice, item in enumerate(self.itens_pedido)
            if indice != indice_ignorar
        )

        if not ja_existe:
            return

        QMessageBox.warning(
            self,
            "Produto repetido",
            f"<b>\"{nome}\" já está neste pedido.</b>",
        )

    def adicionar_item(self, produto_id, nome, unidade, quantidade, preco_unitario, sp=False):

        self._avisar_se_produto_duplicado(produto_id, nome)

        self.itens_pedido.append({
            "produto_id": produto_id,
            "nome": nome,
            "unidade": unidade,
            "quantidade": quantidade,
            "preco_unitario": preco_unitario,
            "sp": sp,
        })
        self.atualizar_tabela_itens()

    def salvar_item(self):

        produto = self.combo_produto.currentData()

        if produto is None:
            QMessageBox.warning(
                self, "Nenhum produto",
                "Cadastre ao menos um produto antes de montar um pedido."
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

        self._avisar_se_produto_duplicado(
            produto["id"], produto["nome"], self.indice_item_selecionado
        )

        if self.indice_item_selecionado is not None:
            self.itens_pedido[self.indice_item_selecionado] = item
        else:
            self.itens_pedido.append(item)

        self.limpar_selecao_item()
        self.atualizar_tabela_itens()

    def remover_item_selecionado(self):

        linhas = self.tabela_itens.selectionModel().selectedRows()

        if not linhas:
            return

        indice = linhas[0].row()
        del self.itens_pedido[indice]
        self.limpar_selecao_item()
        self.atualizar_tabela_itens()

    def atualizar_tabela_itens(self):

        self.tabela_itens.setRowCount(len(self.itens_pedido))

        total = 0.0

        for linha, item in enumerate(self.itens_pedido):
            subtotal = item["quantidade"] * item["preco_unitario"]
            total += subtotal

            nome = item["nome"] + (" (SP)" if item.get("sp") else "")

            self.tabela_itens.setItem(linha, 0, QTableWidgetItem(nome))
            self.tabela_itens.setItem(linha, 1, QTableWidgetItem(item["unidade"]))
            self.tabela_itens.setItem(linha, 2, QTableWidgetItem(f"{item['quantidade']:g}"))
            self.tabela_itens.setItem(
                linha, 3, QTableWidgetItem(f"R$ {item['preco_unitario']:.2f}")
            )
            self.tabela_itens.setItem(linha, 4, QTableWidgetItem(f"R$ {subtotal:.2f}"))

        self.label_total.setText(f"Total: R$ {total:.2f}")

    # ==========================
    # Texto colado do WhatsApp
    # ==========================

    def processar_texto_whatsapp(self):

        texto = self.texto_whatsapp.toPlainText().strip()

        if not texto:
            QMessageBox.warning(self, "Nada para processar", "Cole o texto do pedido antes de processar.")
            return

        produtos = self.produto_controller.listar_produtos()
        clientes = self.cliente_controller.listar_clientes()

        if not produtos:
            QMessageBox.warning(
                self, "Sem produtos cadastrados",
                "Cadastre produtos antes de processar um pedido."
            )
            return

        resultado = interpretar_pedido(texto, produtos, clientes)

        if resultado.cliente_id is not None:
            indice = self.combo_cliente.findData(resultado.cliente_id)
            if indice >= 0:
                self.combo_cliente.setCurrentIndex(indice)
        elif resultado.cliente_nome_detectado:
            QMessageBox.information(
                self,
                "Cliente não identificado",
                f"O texto indica o cliente \"{resultado.cliente_nome_detectado}\", "
                "mas não encontrei ninguém cadastrado com esse nome.\n\n"
                "Selecione o cliente manualmente.",
            )

        itens_sem_preco_informado = []

        for item in resultado.itens:
            preco_unitario = self._obter_preco(
                item.produto_nome, item.produto_unidade, item.preco_unitario
            )

            if preco_unitario is None:
                itens_sem_preco_informado.append(item.produto_nome)
                continue

            self.adicionar_item(
                item.produto_id,
                item.produto_nome,
                item.produto_unidade,
                item.quantidade,
                preco_unitario,
            )

        itens_ambiguos_ignorados = []

        for item_ambiguo in resultado.itens_ambiguos:
            produto_escolhido = self._escolher_produto_ambiguo(item_ambiguo)

            if produto_escolhido is None:
                itens_ambiguos_ignorados.append(item_ambiguo.linha_original)
                continue

            preco_unitario = self._obter_preco(
                produto_escolhido["nome"],
                produto_escolhido["unidade"],
                produto_escolhido["preco"],
            )

            if preco_unitario is None:
                itens_sem_preco_informado.append(produto_escolhido["nome"])
                continue

            self.adicionar_item(
                produto_escolhido["id"],
                produto_escolhido["nome"],
                produto_escolhido["unidade"],
                item_ambiguo.quantidade,
                preco_unitario,
            )

        avisos = []

        if itens_ambiguos_ignorados:
            lista = "\n".join(f"- {linha}" for linha in itens_ambiguos_ignorados)
            avisos.append(
                "Os itens abaixo bateram com mais de um produto e não foram "
                f"adicionados porque a escolha foi cancelada:\n\n{lista}"
            )

        if resultado.nao_reconhecidos:
            lista = "\n".join(f"- {linha}" for linha in resultado.nao_reconhecidos)
            avisos.append(
                "Os itens abaixo não bateram com nenhum produto cadastrado "
                f"e precisam ser adicionados manualmente:\n\n{lista}"
            )

        if itens_sem_preco_informado:
            lista = "\n".join(f"- {nome}" for nome in itens_sem_preco_informado)
            avisos.append(
                "Os itens abaixo não foram adicionados porque o preço não foi "
                f"informado:\n\n{lista}"
            )

        if avisos:
            QMessageBox.warning(self, "Atenção", "\n\n".join(avisos))

    # ==========================
    # Salvar pedido
    # ==========================

    def salvar_pedido(self):

        cliente_id = self.combo_cliente.currentData()

        if cliente_id is None:
            QMessageBox.warning(self, "Cliente obrigatório", "Selecione um cliente antes de salvar o pedido.")
            return

        if not self.itens_pedido:
            QMessageBox.warning(self, "Pedido vazio", "Adicione ao menos um item ao pedido.")
            return

        itens = [
            (item["produto_id"], item["quantidade"], item["preco_unitario"], item.get("sp", False))
            for item in self.itens_pedido
        ]

        self.pedido_controller.criar_pedido(cliente_id, itens)

        QMessageBox.information(self, "Pedido salvo", "Pedido registrado com sucesso!")

        self.itens_pedido = []
        self.texto_whatsapp.clear()
        self.limpar_selecao_item()
        self.atualizar_tabela_itens()
        self.carregar_pedidos()

    def cancelar_pedido(self):

        if not self.itens_pedido and not self.texto_whatsapp.toPlainText().strip():
            return

        resposta = QMessageBox.question(
            self,
            "Cancelar pedido",
            "Deseja realmente cancelar este pedido? Todos os itens adicionados serão perdidos.",
        )

        if resposta != QMessageBox.Yes:
            return

        self.itens_pedido = []
        self.texto_whatsapp.clear()
        self.limpar_selecao_item()
        self.atualizar_tabela_itens()
