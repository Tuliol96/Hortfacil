from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

from controllers.produto_controller import ProdutoController

COLUNAS = ["ID", "Nome", "Categoria", "Unidade", "Preço", "Favorito"]

PRECO_VARIAVEL_TEXTO = "Variável"


def _formatar_preco(preco):
    if preco is None:
        return PRECO_VARIAVEL_TEXTO
    return f"R$ {preco:.2f}"


class PaginaProdutos(QWidget):

    def __init__(self, banco):
        super().__init__()

        self.controller = ProdutoController(banco)
        self.id_selecionado = None

        self.montar_interface()
        self.carregar_opcoes()
        self.carregar_produtos()

    def montar_interface(self):

        layout = QVBoxLayout(self)

        titulo = QLabel("Cadastro de Produtos")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size:24px; font-weight:bold;")
        layout.addWidget(titulo)

        # ==========================
        # Formulário
        # ==========================

        formulario = QFormLayout()

        self.campo_nome = QLineEdit()

        self.campo_categoria = QComboBox()
        self.campo_categoria.setEditable(True)
        self.campo_categoria.setInsertPolicy(QComboBox.NoInsert)

        self.campo_unidade = QComboBox()
        self.campo_unidade.setEditable(True)
        self.campo_unidade.setInsertPolicy(QComboBox.NoInsert)

        self.campo_preco = QLineEdit()
        self.campo_preco.setPlaceholderText("Deixe em branco se o preço variar")

        self.campo_favorito = QCheckBox("Produto favorito")

        formulario.addRow("Nome:", self.campo_nome)
        formulario.addRow("Categoria:", self.campo_categoria)
        formulario.addRow("Unidade:", self.campo_unidade)
        formulario.addRow("Preço:", self.campo_preco)
        formulario.addRow("", self.campo_favorito)

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

        self.botao_salvar.clicked.connect(self.salvar_produto)
        self.botao_excluir.clicked.connect(self.excluir_produto)
        self.botao_limpar.clicked.connect(self.limpar_formulario)

        botoes.addWidget(self.botao_salvar)
        botoes.addWidget(self.botao_excluir)
        botoes.addWidget(self.botao_limpar)

        layout.addLayout(botoes)

        # ==========================
        # Tabela
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
        self.tabela.itemSelectionChanged.connect(self.selecionar_produto)

        layout.addWidget(self.tabela)

    def carregar_opcoes(self):

        categoria_atual = self.campo_categoria.currentText()
        self.campo_categoria.clear()
        self.campo_categoria.addItems(self.controller.listar_categorias())
        self.campo_categoria.setCurrentText(categoria_atual)

        unidade_atual = self.campo_unidade.currentText()
        self.campo_unidade.clear()
        self.campo_unidade.addItems(self.controller.listar_unidades())
        self.campo_unidade.setCurrentText(unidade_atual)

    def carregar_produtos(self):

        produtos = self.controller.listar_produtos()

        self.tabela.setRowCount(len(produtos))

        for linha, produto in enumerate(produtos):
            self.tabela.setItem(linha, 0, QTableWidgetItem(str(produto["id"])))
            self.tabela.setItem(linha, 1, QTableWidgetItem(produto["nome"]))
            self.tabela.setItem(linha, 2, QTableWidgetItem(produto["categoria"]))
            self.tabela.setItem(linha, 3, QTableWidgetItem(produto["unidade"]))
            self.tabela.setItem(
                linha, 4, QTableWidgetItem(_formatar_preco(produto["preco"]))
            )
            self.tabela.setItem(
                linha, 5, QTableWidgetItem("Sim" if produto["favorito"] else "Não")
            )

    def selecionar_produto(self):

        linhas = self.tabela.selectionModel().selectedRows()

        if not linhas:
            return

        linha = linhas[0].row()

        self.id_selecionado = int(self.tabela.item(linha, 0).text())

        # busca os dados originais no banco em vez de reler a tabela,
        # pra não confundir o texto "Variável" com um preço de verdade
        produto = self.controller.buscar_produto(self.id_selecionado)

        self.campo_nome.setText(produto["nome"])
        self.campo_categoria.setCurrentText(produto["categoria"])
        self.campo_unidade.setCurrentText(produto["unidade"])
        self.campo_preco.setText(
            "" if produto["preco"] is None else f"{produto['preco']:.2f}"
        )
        self.campo_favorito.setChecked(bool(produto["favorito"]))

        self.botao_salvar.setText("Atualizar")

    def limpar_formulario(self):

        self.id_selecionado = None
        self.campo_nome.clear()
        self.campo_categoria.setCurrentText("")
        self.campo_unidade.setCurrentText("")
        self.campo_preco.clear()
        self.campo_favorito.setChecked(False)
        self.botao_salvar.setText("Cadastrar")
        self.tabela.clearSelection()

    def salvar_produto(self):

        nome = self.campo_nome.text().strip()
        categoria = self.campo_categoria.currentText().strip()
        unidade = self.campo_unidade.currentText().strip()
        preco_texto = self.campo_preco.text().strip().replace(",", ".")

        if not nome:
            QMessageBox.warning(self, "Campo obrigatório", "Informe o nome do produto.")
            return

        if not categoria:
            QMessageBox.warning(self, "Campo obrigatório", "Informe a categoria.")
            return

        if not unidade:
            QMessageBox.warning(self, "Campo obrigatório", "Informe a unidade.")
            return

        preco = None

        if preco_texto:
            try:
                preco = float(preco_texto)
            except ValueError:
                QMessageBox.warning(self, "Preço inválido", "Informe um preço numérico válido ou deixe em branco.")
                return

            if preco < 0:
                QMessageBox.warning(self, "Preço inválido", "O preço não pode ser negativo.")
                return

        favorito = self.campo_favorito.isChecked()

        if self.id_selecionado is None:
            self.controller.cadastrar_produto(nome, categoria, unidade, preco, favorito)
        else:
            self.controller.atualizar_produto(
                self.id_selecionado, nome, categoria, unidade, preco, favorito
            )

        self.limpar_formulario()
        self.carregar_opcoes()
        self.carregar_produtos()

    def excluir_produto(self):

        if self.id_selecionado is None:
            QMessageBox.warning(self, "Nenhum produto selecionado", "Selecione um produto na tabela.")
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar exclusão",
            "Deseja realmente excluir este produto?",
        )

        if resposta != QMessageBox.Yes:
            return

        self.controller.excluir_produto(self.id_selecionado)
        self.limpar_formulario()
        self.carregar_produtos()
