import subprocess
import sys
import os

def iniciar_servidor(num_threads=10):
    """Inicia o servidor com o número especificado de threads."""
    try:
        print(f"Iniciando servidor com {num_threads} threads...")
        servidor = subprocess.Popen(['python', 'server.py', str(num_threads)])
        return servidor
    except Exception as e:
        print(f"Erro ao iniciar servidor: {e}")
        return None

def mostrar_menu():
    """Mostra as opções disponíveis."""
    print("\n======= SERVIDOR DE CHAT CRIPTOGRÁFICO =======")
    print("1. Iniciar servidor com 10 threads")
    print("2. Iniciar servidor com 100 threads")
    print("3. Iniciar servidor com 500 threads")
    print("4. Iniciar servidor com outro número de threads")
    print("5. Sair")
    print("=============================================")
    
def limpar_tela():
    """Limpa a tela do terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    servidor = None
    
    while True:
        try:
            mostrar_menu()
            escolha = input("Escolha uma opção: ")
            
            if escolha == '1':
                if servidor:
                    print("Servidor já está em execução. Encerre o atual primeiro.")
                else:
                    servidor = iniciar_servidor(10)
                    print("Servidor iniciado. Pressione Ctrl+C para encerrar.")
                    break
                    
            elif escolha == '2':
                if servidor:
                    print("Servidor já está em execução. Encerre o atual primeiro.")
                else:
                    servidor = iniciar_servidor(100)
                    print("Servidor iniciado. Pressione Ctrl+C para encerrar.")
                    break
                    
            elif escolha == '3':
                if servidor:
                    print("Servidor já está em execução. Encerre o atual primeiro.")
                else:
                    servidor = iniciar_servidor(500)
                    print("Servidor iniciado. Pressione Ctrl+C para encerrar.")
                    break
                    
            elif escolha == '4':
                if servidor:
                    print("Servidor já está em execução. Encerre o atual primeiro.")
                else:
                    try:
                        num_threads = int(input("Digite o número de threads: "))
                        servidor = iniciar_servidor(num_threads)
                        print("Servidor iniciado. Pressione Ctrl+C para encerrar.")
                        break
                    except ValueError:
                        print("Número inválido. Tente novamente.")
                        
            elif escolha == '5':
                print("Saindo...")
                sys.exit(0)
                
            else:
                print("Opção inválida. Tente novamente.")
                
        except KeyboardInterrupt:
            break
    
    try:
        if servidor:
            print("Servidor em execução. Pressione Ctrl+C para encerrar.")
            servidor.wait()
    except KeyboardInterrupt:
        if servidor:
            print("\nEncerrando servidor...")
            servidor.terminate()
            servidor.wait()
        print("Servidor encerrado.")

if __name__ == "__main__":
    main() 