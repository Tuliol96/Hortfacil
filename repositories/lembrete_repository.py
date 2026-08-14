from models.lembrete import Lembrete


class LembreteRepository:

    def __init__(self, banco):
        self.banco = banco

    def inserir(self, lembrete: Lembrete):

        sql = """
        INSERT INTO lembretes
        (
            mensagem,
            data_hora
        )
        VALUES (?, ?)
        """

        self.banco.cursor.execute(sql, (lembrete.mensagem, lembrete.data_hora))

        self.banco.conexao.commit()

    def listar_todos(self):

        self.banco.cursor.execute("""
            SELECT *
            FROM lembretes
            ORDER BY data_hora
        """)

        return self.banco.cursor.fetchall()

    def listar_nao_disparados(self):
        """Todos os lembretes ainda não exibidos, futuros ou já vencidos —
        usado pela tela pra listar o que pode ser excluído antes de disparar."""

        self.banco.cursor.execute("""
            SELECT *
            FROM lembretes
            WHERE disparado = 0
            ORDER BY data_hora
        """)

        return self.banco.cursor.fetchall()

    def listar_vencidos(self, agora_iso):
        """Lembretes não disparados cujo horário já chegou — usado pelo
        QTimer da tela principal pra decidir o que notificar agora."""

        self.banco.cursor.execute("""
            SELECT *
            FROM lembretes
            WHERE disparado = 0 AND data_hora <= ?
            ORDER BY data_hora
        """, (agora_iso,))

        return self.banco.cursor.fetchall()

    def marcar_disparado(self, id_lembrete):

        self.banco.cursor.execute("""
            UPDATE lembretes
            SET disparado = 1
            WHERE id = ?
        """, (id_lembrete,))

        self.banco.conexao.commit()

    def excluir(self, id_lembrete):

        self.banco.cursor.execute("""
            DELETE FROM lembretes
            WHERE id = ?
        """, (id_lembrete,))

        self.banco.conexao.commit()
