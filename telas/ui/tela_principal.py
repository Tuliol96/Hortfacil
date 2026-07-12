from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from telas.ui.pagina_clientes import PaginaClientes
from telas.ui.pagina_configuracoes import PaginaConfiguracoes
from telas.ui.pagina_fechamentos import PaginaFechamentos
from telas.ui.pagina_inicio import PaginaInicio
from telas.ui.pagina_pedidos import PaginaPedidos
from telas.ui.pagina_produtos import PaginaProdutos


def _pagina_em_construcao(titulo):

    pagina = QWidget()
    layout = QVBoxLayout(pagina)

    label = QLabel(f"{titulo}\n\n(em construção)")
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("""
        font-size:20px;
        color:#888;
    """)

    layout.addStretch()
    layout.addWidget(label)
    layout.addStretch()

    return pagina


class TelaPrincipal(QMainWindow):

    # Itens do menu, na ordem em que aparecem, e a página correspondente.
    ITENS_MENU = [
        "📋 Pedidos",
        "👥 Clientes",
        "🥬 Produtos",
        "📦 Estoque",
        "💰 Financeiro",
        "📊 Relatórios",
        "⚙ Configurações",
    ]

    def __init__(self, banco):
        super().__init__()

        self.banco = banco

        self.setWindowTitle("Sistema da Distribuidora")
        self.resize(1200, 700)

        self.montar_interface()

    def montar_interface(self):

        central = QWidget()
        self.setCentralWidget(central)

        layout_principal = QHBoxLayout()
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ==========================
        # Menu lateral
        # ==========================

        menu = QListWidget()
        menu.addItems(self.ITENS_MENU)
        menu.setFixedWidth(220)

        menu.setStyleSheet("""
            QListWidget{
                background:#2d3436;
                color:white;
                border:none;
                font-size:15px;
                padding:8px;
            }

            QListWidget::item{
                padding:12px;
            }

            QListWidget::item:selected{
                background:#00a884;
                border-radius:6px;
            }
        """)

        # ==========================
        # Área principal (páginas)
        # ==========================

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background:white;")

        self.stack.addWidget(PaginaInicio())
        self.stack.addWidget(PaginaPedidos())
        self.stack.addWidget(PaginaClientes())
        self.stack.addWidget(PaginaProdutos(self.banco))
        self.stack.addWidget(_pagina_em_construcao("Estoque"))
        self.stack.addWidget(PaginaFechamentos())
        self.stack.addWidget(_pagina_em_construcao("Relatórios"))
        self.stack.addWidget(PaginaConfiguracoes())

        menu.currentRowChanged.connect(
            lambda linha: self.stack.setCurrentIndex(linha + 1)
        )

        layout_principal.addWidget(menu)
        layout_principal.addWidget(self.stack)

        central.setLayout(layout_principal)
