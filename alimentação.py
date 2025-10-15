#sitema de alimentação do pou
class SistemaDeAlimentacao: 
    def __init__(self, nivel_inicial=100):
        self.nivel = nivel_inicial  # Nível de alimentação (0 a 100)

    def alimentar(self, qtd): # Aumenta o nível de alimentação
        self.nivel = min(100, self.nivel + qtd)

    def consumir(self, qtd): # Diminui o nível de alimentação
        self.nivel = max(0, self.nivel - qtd)

    def get_nivel(self): # Retorna o nível atual de alimentação
        return self.nivel 
    
    def verificar_fome(self): # Verifica se o Pou está com fome
        if self.nivel < 30:  # Se o nível estiver abaixo de 30, considera que o Pou está com fome
            return True
        return False
    
#sitema de perca de alimentação com o tempo
    def perder_com_tempo(self, qtd): # Diminui o nível de alimentação com o tempo
        self.consumir(qtd)
        if self.nivel == 0: # Se o nível chegar a 0, alerta que o Pou está com muita fome
            print("O teu Pou vai morrer de fome. Da-lhe de comer.")
        elif self.nivel < 30: # Se o nível estiver abaixo de 20, alerta que o Pou está com fome
            print("O teu Pou está com fome. Dá-lhe de comer.")
