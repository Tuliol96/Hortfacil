from models.configuracao import Configuracao


class ConfiguracaoRepository:

    def __init__(self, banco):
        self.banco = banco

    def obter(self):

        self.banco.cursor.execute("""
            SELECT nome_empresa, cnpj, endereco, telefone
            FROM configuracoes
            WHERE id = 1
        """)

        return self.banco.cursor.fetchone()

    def salvar(self, configuracao: Configuracao):

        self.banco.cursor.execute("""
            UPDATE configuracoes
            SET
                nome_empresa = ?,
                cnpj = ?,
                endereco = ?,
                telefone = ?,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (
            configuracao.nome_empresa,
            configuracao.cnpj,
            configuracao.endereco,
            configuracao.telefone,
        ))

        self.banco.conexao.commit()
