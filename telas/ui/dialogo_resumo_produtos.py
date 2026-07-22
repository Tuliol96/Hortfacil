from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from controllers.pedido_controller import PedidoController

COLUNAS = ["Produto", "Unidade", "Quantidade Total", "Valor Total"]


def _formatar_data_br(data_iso):
    ano, mes, dia = data_iso.split("-")
    return f"{dia}/{mes}/{ano}"


class ResumoProdutosDialog(QDialog):

    def __init__(self, banco, cliente_id, cliente_nome, data_inicio, data_fim, parent=None):
        super().__init__(parent)

        controller = PedidoController(banco)
        self.resumo = controller.resumo_produtos_por_cliente_periodo(
            cliente_id, data_inicio, data_fim
        )

        self.setWindowTitle("Resumo de produtos vendidos")
        self.resize(600, 450)

        layout = QVBoxLayout(self)

        titulo = QLabel("Resumo de Produtos Vendidos")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size:20px; font-weight:bold;")
        layout.addWidget(titulo)

        layout.addWidget(QLabel(f"Cliente: {cliente_nome}"))
        layout.addWidget(QLabel(
            f"Período: {_formatar_data_br(data_inicio)} até {_formatar_data_br(data_fim)}"
        ))

        tabela = QTableWidget()
        tabela.setColumnCount(len(COLUNAS))
        tabela.setHorizontalHeaderLabels(COLUNAS)
        tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        tabela.setRowCount(len(self.resumo))

        total_geral = 0.0

        for linha, produto in enumerate(self.resumo):
            tabela.setItem(linha, 0, QTableWidgetItem(produto["produto_nome"]))
            tabela.setItem(linha, 1, QTableWidgetItem(produto["produto_unidade"]))
            tabela.setItem(linha, 2, QTableWidgetItem(f"{produto['quantidade_total']:g}"))
            tabela.setItem(linha, 3, QTableWidgetItem(f"R$ {produto['valor_total']:.2f}"))
            total_geral += produto["valor_total"]

        layout.addWidget(tabela)

        if not self.resumo:
            aviso = QLabel("Nenhum produto vendido nesse período.")
            aviso.setAlignment(Qt.AlignCenter)
            layout.addWidget(aviso)

        label_total = QLabel(f"Total geral: R$ {total_geral:.2f}")
        label_total.setAlignment(Qt.AlignRight)
        label_total.setStyleSheet("font-size:16px; font-weight:bold;")
        layout.addWidget(label_total)

        botao_fechar = QPushButton("Fechar")
        botao_fechar.clicked.connect(self.close)
        layout.addWidget(botao_fechar)
