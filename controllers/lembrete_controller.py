from datetime import datetime

from models.lembrete import Lembrete
from repositories.lembrete_repository import LembreteRepository


class LembreteController:

    def __init__(self, banco):
        self.repository = LembreteRepository(banco)

    def criar_lembrete(self, mensagem, data_hora):

        lembrete = Lembrete(
            mensagem=mensagem.strip(),
            data_hora=data_hora,
        )

        self.repository.inserir(lembrete)

    def listar_lembretes(self):
        return self.repository.listar_todos()

    def listar_pendentes(self):
        return self.repository.listar_nao_disparados()

    def listar_vencidos(self):
        agora_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.repository.listar_vencidos(agora_iso)

    def marcar_disparado(self, id_lembrete):
        self.repository.marcar_disparado(id_lembrete)

    def excluir_lembrete(self, id_lembrete):
        self.repository.excluir(id_lembrete)
