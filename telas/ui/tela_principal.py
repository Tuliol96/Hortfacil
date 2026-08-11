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
from telas.ui.pagina_relatorios import PaginaRelatorios


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

        self.menu = QListWidget()
        menu = self.menu
        menu.addItems(self.ITENS_MENU)
        menu.setFixedWidth(220)

        # Evita que o Qt selecione a primeira linha sozinho quando a janela
        # ganha foco ao abrir, o que trocaria a página inicial pela primeira
        # aba do menu (Pedidos) sem o usuário clicar em nada.
        menu.setFocusPolicy(Qt.NoFocus)

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

        self.pagina_pedidos = PaginaPedidos(self.banco)
        self.pagina_clientes = PaginaClientes(self.banco)

        self.stack.addWidget(PaginaInicio())
        self.stack.addWidget(self.pagina_pedidos)
        self.stack.addWidget(self.pagina_clientes)
        self.stack.addWidget(PaginaProdutos(self.banco))
        self.stack.addWidget(_pagina_em_construcao("Estoque"))
        self.stack.addWidget(PaginaFechamentos(self.banco))
        self.stack.addWidget(PaginaRelatorios(self.banco))
        self.stack.addWidget(PaginaConfiguracoes(self.banco))

        self.pagina_pedidos.solicitou_ver_cliente.connect(self.mostrar_cliente)

        menu.currentRowChanged.connect(
            lambda linha: self.stack.setCurrentIndex(linha + 1)
        )

        layout_principal.addWidget(menu)
        layout_principal.addWidget(self.stack)

        central.setLayout(layout_principal)

    def mostrar_cliente(self, cliente_id):

        indice = self.stack.indexOf(self.pagina_clientes)
        self.stack.setCurrentIndex(indice)
        self.menu.setCurrentRow(indice - 1)
        self.pagina_clientes.selecionar_cliente_por_id(cliente_id)
