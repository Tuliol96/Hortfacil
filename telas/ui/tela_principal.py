from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)


class TelaPrincipal(QMainWindow):

    def __init__(self):
        super().__init__()

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

        menu.addItems([
            "📋 Pedidos",
            "👥 Clientes",
            "🥬 Produtos",
            "📦 Estoque",
            "💰 Financeiro",
            "📊 Relatórios",
            "⚙ Configurações"
        ])

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
        # Área principal
        # ==========================

        area = QFrame()

        area.setStyleSheet("""
            background:white;
        """)

        layout_area = QVBoxLayout()

        titulo = QLabel("Sistema da Distribuidora")

        titulo.setAlignment(Qt.AlignCenter)

        titulo.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
            margin-top:40px;
        """)

        subtitulo = QLabel(
            "Bem-vindo!\n\nEscolha uma opção no menu à esquerda."
        )

        subtitulo.setAlignment(Qt.AlignCenter)

        subtitulo.setStyleSheet("""
            font-size:16px;
            color:#666;
        """)

        layout_area.addStretch()
        layout_area.addWidget(titulo)
        layout_area.addWidget(subtitulo)
        layout_area.addStretch()

        area.setLayout(layout_area)

        layout_principal.addWidget(menu)
        layout_principal.addWidget(area)

        central.setLayout(layout_principal)