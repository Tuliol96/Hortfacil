from models.cliente import Cliente


class ClienteRepository:

    def __init__(self, banco):
        self.banco = banco

    def inserir(self, cliente: Cliente):

        sql = """
        INSERT INTO clientes
        (
            nome,
            telefone,
            endereco,
            numero,
            bairro,
            cidade,
            ativo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        self.banco.cursor.execute(
            sql,
            (
                cliente.nome,
                cliente.telefone,
                cliente.endereco,
                cliente.numero,
                cliente.bairro,
                cliente.cidade,
                int(cliente.ativo),
            ),
        )

        self.banco.conexao.commit()

    def listar(self):

        self.banco.cursor.execute("""
            SELECT *
            FROM clientes
            WHERE ativo = 1
            ORDER BY nome
        """)

        return self.banco.cursor.fetchall()

    def buscar_por_id(self, id_cliente):

        self.banco.cursor.execute("""
            SELECT *
            FROM clientes
            WHERE id = ?
        """, (id_cliente,))

        return self.banco.cursor.fetchone()

    def atualizar(self, cliente: Cliente):

        self.banco.cursor.execute("""
            UPDATE clientes
            SET
                nome = ?,
                telefone = ?,
                endereco = ?,
                numero = ?,
                bairro = ?,
                cidade = ?,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            cliente.nome,
            cliente.telefone,
            cliente.endereco,
            cliente.numero,
            cliente.bairro,
            cliente.cidade,
            cliente.id
        ))

        self.banco.conexao.commit()

    def desativar(self, id_cliente):

        self.banco.cursor.execute("""
            UPDATE clientes
            SET
                ativo = 0,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (id_cliente,))

        self.banco.conexao.commit()
