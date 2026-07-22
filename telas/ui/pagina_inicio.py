from pathlib import Path

from PySide6.QtCore import QDate, QLocale, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

CAMINHO_LOGO = Path(__file__).resolve().parent.parent.parent / "imagens" / "logo.jpeg"


class PaginaInicio(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)

        pixmap = QPixmap(str(CAMINHO_LOGO))
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaledToWidth(320, Qt.SmoothTransformation))

        boas_vindas = QLabel("Bem-vindo!")
        boas_vindas.setAlignment(Qt.AlignCenter)
        boas_vindas.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
            color:#2E7D32;
        """)

        locale_pt_br = QLocale(QLocale.Portuguese, QLocale.Brazil)
        texto_data = locale_pt_br.toString(
            QDate.currentDate(), "dddd, d 'de' MMMM 'de' yyyy"
        )

        data = QLabel(texto_data.capitalize())
        data.setAlignment(Qt.AlignCenter)
        data.setStyleSheet("""
            font-size:16px;
            color:#666666;
        """)

        layout.addStretch()
        layout.addWidget(logo)
        layout.addWidget(boas_vindas)
        layout.addWidget(data)
        layout.addStretch()
