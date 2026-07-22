from models.configuracao import Configuracao
from repositories.configuracao_repository import ConfiguracaoRepository


class ConfiguracaoController:

    def __init__(self, banco):
        self.repository = ConfiguracaoRepository(banco)

    def obter_configuracao(self):
        return self.repository.obter()

    def salvar_configuracao(self, nome_empresa, cnpj, endereco, telefone):

        configuracao = Configuracao(
            nome_empresa=nome_empresa.strip(),
            cnpj=cnpj.strip(),
            endereco=endereco.strip(),
            telefone=telefone.strip(),
        )

        self.repository.salvar(configuracao)
