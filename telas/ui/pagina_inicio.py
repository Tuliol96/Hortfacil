from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PaginaInicio(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        titulo = QLabel("HORTFÁCIL")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("""
            font-size:32px;
            font-weight:bold;
            color:#2E7D32;
        """)

        subtitulo = QLabel("Sistema de Gestão para Hortifrúti")
        subtitulo.setAlignment(Qt.AlignCenter)
        subtitulo.setStyleSheet("""
            font-size:16px;
            color:#666666;
        """)

        layout.addStretch()
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        layout.addStretch()