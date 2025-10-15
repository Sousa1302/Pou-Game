class SistemaDeMoedas:
    def __init__(self, moedas_iniciais=0):
        self.moedas = moedas_iniciais

#função para ganhar moedas
    def ganhar(self, qtd):
        self.moedas += qtd

#função para gastar moedas
    def gastar(self, qtd):
        if self.moedas >= qtd:
            self.moedas -= qtd
            return True
        else:
            print("Moedas insuficientes!")
            return False
#função para retornar o total de moedas
    def get_moedas(self):
        return self.moedas
