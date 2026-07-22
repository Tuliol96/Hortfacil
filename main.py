import sys

from PySide6.QtWidgets import QApplication

from banco.banco import Banco
from telas.ui.tela_principal import TelaPrincipal


def main():

    banco = Banco()
    banco.criar_tabelas()

    app = QApplication(sys.argv)

    # o estilo nativo do Windows ignora background-color de QPushButton;
    # o Fusion (estilo próprio do Qt) respeita o stylesheet por completo
    app.setStyle("Fusion")

    app.setStyleSheet("""
        QStackedWidget {
            background: white;
        }

        QPushButton {
            background-color: #A5D6A7;
            color: #1B5E20;
            border: 1px solid #81C784;
            border-radius: 6px;
            padding: 6px 14px;
        }

        QPushButton:hover {
            background-color: #93C793;
        }

        QPushButton:pressed {
            background-color: #7CB87C;
        }

        QPushButton:disabled {
            background-color: #E0E0E0;
            color: #9E9E9E;
            border: 1px solid #E0E0E0;
        }

        QPushButton[perigo="true"] {
            background-color: #EF9A9A;
            color: #B71C1C;
            border: 1px solid #E57373;
        }

        QPushButton[perigo="true"]:hover {
            background-color: #E57373;
        }

        QPushButton[perigo="true"]:pressed {
            background-color: #D32F2F;
            color: white;
        }

        QPushButton[limpar="true"] {
            background-color: #90CAF9;
            color: #0D47A1;
            border: 1px solid #64B5F6;
        }

        QPushButton[limpar="true"]:hover {
            background-color: #64B5F6;
        }

        QPushButton[limpar="true"]:pressed {
            background-color: #42A5F5;
            color: white;
        }
    """)

    janela = TelaPrincipal(banco)
    janela.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()