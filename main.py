import sys

from PySide6.QtWidgets import QApplication

from banco.banco import Banco
from telas.tela_principal import TelaPrincipal


def main():

    banco = Banco()
    banco.criar_tabelas()

    app = QApplication(sys.argv)

    janela = TelaPrincipal()
    janela.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()