from PySide6.QtCore import QDate, Qt, QTime
from PySide6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from controllers.lembrete_controller import LembreteController
from util.formatacao import formatar_data_hora

COLUNAS = ["ID", "Mensagem", "Data/Hora agendada"]


class PaginaLembretes(QWidget):

    def __init__(self, banco):
        super().__init__()

        self.controller = LembreteController(banco)
        self.id_selecionado = None

        self.montar_interface()
        self.carregar_lembretes()

    def showEvent(self, evento):
        super().showEvent(evento)
        self.carregar_lembretes()

    def montar_interface(self):

        layout = QVBoxLayout(self)

        titulo = QLabel("Lembretes")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size:24px; font-weight:bold;")
        layout.addWidget(titulo)

        # ==========================
        # Novo lembrete
        # ==========================

        layout.addWidget(QLabel("Mensagem:"))

        self.campo_mensagem = QTextEdit()
        self.campo_mensagem.setFixedHeight(80)
        self.campo_mensagem.setPlaceholderText("Digite o lembrete...")
        layout.addWidget(self.campo_mensagem)

        linha_data_hora = QHBoxLayout()

        linha_data_hora.addWidget(QLabel("Data:"))
        self.campo_data = QDateEdit()
        self.campo_data.setCalendarPopup(True)
        self.campo_data.setDisplayFormat("dd/MM/yyyy")
        self.campo_data.setDate(QDate.currentDate())
        linha_data_hora.addWidget(self.campo_data)

        linha_data_hora.addWidget(QLabel("Horário:"))
        self.campo_hora = QTimeEdit()
        self.campo_hora.setDisplayFormat("HH:mm")
        self.campo_hora.setTime(QTime.currentTime())
        linha_data_hora.addWidget(self.campo_hora)

        layout.addLayout(linha_data_hora)

        self.botao_criar = QPushButton("Criar Lembrete")
        self.botao_criar.clicked.connect(self.criar_lembrete)
        layout.addWidget(self.botao_criar)

        # ==========================
        # Lembretes pendentes
        # ==========================

        layout.addWidget(QLabel("Lembretes pendentes:"))

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(len(COLUNAS))
        self.tabela.setHorizontalHeaderLabels(COLUNAS)
        self.tabela.setColumnHidden(0, True)
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.itemSelectionChanged.connect(self.selecionar_lembrete)
        layout.addWidget(self.tabela)

        self.botao_excluir = QPushButton("Excluir Lembrete Selecionado")
        self.botao_excluir.setProperty("perigo", True)
        self.botao_excluir.clicked.connect(self.excluir_lembrete)
        layout.addWidget(self.botao_excluir)

    def carregar_lembretes(self):

        lembretes = self.controller.listar_pendentes()

        self.tabela.setRowCount(len(lembretes))

        for linha, lembrete in enumerate(lembretes):
            self.tabela.setItem(linha, 0, QTableWidgetItem(str(lembrete["id"])))
            self.tabela.setItem(linha, 1, QTableWidgetItem(lembrete["mensagem"]))
            self.tabela.setItem(
                linha, 2, QTableWidgetItem(formatar_data_hora(lembrete["data_hora"]))
            )

        self.id_selecionado = None

    def selecionar_lembrete(self):

        linhas = self.tabela.selectionModel().selectedRows()

        if not linhas:
            self.id_selecionado = None
            return

        linha = linhas[0].row()
        self.id_selecionado = int(self.tabela.item(linha, 0).text())

    def criar_lembrete(self):

        mensagem = self.campo_mensagem.toPlainText().strip()

        if not mensagem:
            QMessageBox.warning(self, "Mensagem obrigatória", "Digite a mensagem do lembrete.")
            return

        data_hora = (
            f"{self.campo_data.date().toString('yyyy-MM-dd')} "
            f"{self.campo_hora.time().toString('HH:mm:ss')}"
        )

        self.controller.criar_lembrete(mensagem, data_hora)

        self.campo_mensagem.clear()
        self.campo_data.setDate(QDate.currentDate())
        self.campo_hora.setTime(QTime.currentTime())

        self.carregar_lembretes()

        QMessageBox.information(self, "Lembrete criado", "Lembrete agendado com sucesso!")

    def excluir_lembrete(self):

        if self.id_selecionado is None:
            QMessageBox.warning(
                self, "Nenhum lembrete selecionado",
                "Selecione um lembrete na lista para excluir."
            )
            return

        resposta = QMessageBox.question(
            self, "Excluir lembrete",
            "Deseja realmente excluir este lembrete?"
        )

        if resposta != QMessageBox.Yes:
            return

        self.controller.excluir_lembrete(self.id_selecionado)
        self.carregar_lembretes()
