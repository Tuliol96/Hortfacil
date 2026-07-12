from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PaginaClientes(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        titulo = QLabel("Cadastro de Clientes")
        titulo.setAlignment(Qt.AlignCenter)

        titulo.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
        """)

        layout.addStretch()
        layout.addWidget(titulo)
        layout.addStretch()