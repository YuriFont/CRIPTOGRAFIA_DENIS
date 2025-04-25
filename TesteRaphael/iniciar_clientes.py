import subprocess
import sys
import os
import time

def iniciar_cliente(nome_usuario):
    """Inicia um cliente com o nome de usuário especificado."""
    try:
        # Criar um arquivo temporário com o nome do usuário
        temp_filename = f"temp_{nome_usuario}.txt"
        with open(temp_filename, 'w') as f:
            f.write(f"{nome_usuario}\n")  # Nome do usuário
            
        # Iniciar o cliente redirecionando o arquivo temporário como entrada
        cliente = subprocess.Popen(
            ['python', 'client.py'],
            stdin=open(temp_filename, 'r'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Aguardar um pouco para conexão ser estabelecida
        time.sleep(1)
        
        # Remover o arquivo temporário
        try:
            os.remove(temp_filename)
        except:
            pass
            
        return cliente
    except Exception as e:
        print(f"Erro ao iniciar cliente: {e}")
        return None

def mostrar_menu():
    """Mostra as opções disponíveis."""
    print("\n======= CLIENTES DE CHAT CRIPTOGRÁFICO =======")
    print("1. Iniciar um único cliente")
    print("2. Iniciar 10 clientes")
    print("3. Iniciar 50 clientes")
    print("4. Iniciar outro número de clientes")
    print("5. Sair")
    print("=============================================")
    
def limpar_tela():
    """Limpa a tela do terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clientes = []
    
    while True:
        try:
            mostrar_menu()
            escolha = input("Escolha uma opção: ")
            
            if escolha == '1':
                nome = input("Digite o nome do usuário: ")
                cliente = iniciar_cliente(nome)
                if cliente:
                    clientes.append(cliente)
                    print(f"Cliente '{nome}' iniciado.")
                
            elif escolha == '2':
                for i in range(10):
                    nome = f"Cliente_{i+1}"
                    cliente = iniciar_cliente(nome)
                    if cliente:
                        clientes.append(cliente)
                print(f"10 clientes iniciados.")
                
            elif escolha == '3':
                for i in range(50):
                    nome = f"Cliente_{i+1}"
                    cliente = iniciar_cliente(nome)
                    if cliente:
                        clientes.append(cliente)
                print(f"50 clientes iniciados.")
                
            elif escolha == '4':
                try:
                    num_clientes = int(input("Digite o número de clientes: "))
                    for i in range(num_clientes):
                        nome = f"Cliente_{i+1}"
                        cliente = iniciar_cliente(nome)
                        if cliente:
                            clientes.append(cliente)
                    print(f"{num_clientes} clientes iniciados.")
                except ValueError:
                    print("Número inválido. Tente novamente.")
                    
            elif escolha == '5':
                break
                
            else:
                print("Opção inválida. Tente novamente.")
                
        except KeyboardInterrupt:
            break
    
    # Encerrar todos os clientes
    print("\nEncerrando clientes...")
    for cliente in clientes:
        try:
            cliente.terminate()
            cliente.wait()
        except:
            pass
    print(f"{len(clientes)} clientes encerrados.")

if __name__ == "__main__":
    main() 