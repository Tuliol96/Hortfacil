from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from controllers.configuracao_controller import ConfiguracaoController


class PaginaConfiguracoes(QWidget):

    def __init__(self, banco):
        super().__init__()

        self.controller = ConfiguracaoController(banco)

        self.montar_interface()
        self.carregar_configuracao()

    def showEvent(self, evento):
        super().showEvent(evento)
        self.carregar_configuracao()

    def montar_interface(self):

        layout = QVBoxLayout(self)

        titulo = QLabel("Configurações")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size:24px; font-weight:bold;")
        layout.addWidget(titulo)

        subtitulo = QLabel(
            "Dados da empresa (aparecem na impressão de PDF e cupom)"
        )
        subtitulo.setAlignment(Qt.AlignCenter)
        subtitulo.setStyleSheet("color:#666;")
        layout.addWidget(subtitulo)

        formulario = QFormLayout()

        self.campo_nome_empresa = QLineEdit()
        self.campo_cnpj = QLineEdit()
        self.campo_endereco = QLineEdit()
        self.campo_telefone = QLineEdit()

        formulario.addRow("Nome da empresa:", self.campo_nome_empresa)
        formulario.addRow("CNPJ:", self.campo_cnpj)
        formulario.addRow("Endereço:", self.campo_endereco)
        formulario.addRow("Telefone:", self.campo_telefone)

        layout.addLayout(formulario)

        self.botao_salvar = QPushButton("Salvar")
        self.botao_salvar.clicked.connect(self.salvar_configuracao)
        layout.addWidget(self.botao_salvar)

        layout.addStretch()

    def carregar_configuracao(self):

        configuracao = self.controller.obter_configuracao()

        if configuracao is None:
            return

        self.campo_nome_empresa.setText(configuracao["nome_empresa"])
        self.campo_cnpj.setText(configuracao["cnpj"])
        self.campo_endereco.setText(configuracao["endereco"])
        self.campo_telefone.setText(configuracao["telefone"])

    def salvar_configuracao(self):

        self.controller.salvar_configuracao(
            self.campo_nome_empresa.text(),
            self.campo_cnpj.text(),
            self.campo_endereco.text(),
            self.campo_telefone.text(),
        )

        QMessageBox.information(self, "Salvo", "Dados da empresa salvos com sucesso!")
