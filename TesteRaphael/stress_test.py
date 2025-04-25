import time
import threading
from client import ChatClient
import statistics
from typing import List, Dict
import json

class StressTest:
    def __init__(self):
        self.results: Dict[str, List[float]] = {}
        self.clients: List[ChatClient] = []
        
    def run_client(self, client_id: int, num_packets: int, packet_size: int):
        client = ChatClient()
        if client.connect(f"test_client_{client_id}"):
            self.clients.append(client)
            
            # Enviar mensagens e medir tempo
            times = []
            message = "A" * packet_size
            
            for i in range(num_packets):
                start_time = time.time()
                client.send_message(message)
                end_time = time.time()
                times.append(end_time - start_time)
                time.sleep(0.01)  # Pequeno delay para não sobrecarregar
                
            # Armazenar resultados
            test_key = f"client_{client_id}"
            self.results[test_key] = times
            
    def run_test(self, num_threads: int, num_connections: int, num_packets: int, packet_size: int):
        print(f"\nIniciando teste com:")
        print(f"- Threads no servidor: {num_threads}")
        print(f"- Conexões: {num_connections}")
        print(f"- Pacotes por conexão: {num_packets}")
        print(f"- Tamanho do pacote: {packet_size} bytes")
        
        # Limpar resultados anteriores
        self.results.clear()
        self.clients.clear()
        
        # Criar e iniciar threads dos clientes
        threads = []
        for i in range(num_connections):
            thread = threading.Thread(
                target=self.run_client,
                args=(i, num_packets, packet_size)
            )
            thread.start()
            threads.append(thread)
            
        # Aguardar todas as threads terminarem
        for thread in threads:
            thread.join()
            
        # Calcular estatísticas
        all_times = []
        for times in self.results.values():
            all_times.extend(times)
            
        if all_times:
            avg_time = statistics.mean(all_times)
            min_time = min(all_times)
            max_time = max(all_times)
            
            results = {
                "configuracao": {
                    "num_threads": num_threads,
                    "num_connections": num_connections,
                    "num_packets": num_packets,
                    "packet_size": packet_size
                },
                "resultados": {
                    "tempo_medio": avg_time,
                    "tempo_minimo": min_time,
                    "tempo_maximo": max_time
                }
            }
            
            # Salvar resultados em arquivo
            filename = f"results_{num_threads}_{num_connections}_{num_packets}_{packet_size}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=4)
                
            print("\nResultados:")
            print(f"Tempo médio de resposta: {avg_time:.6f} segundos")
            print(f"Tempo mínimo: {min_time:.6f} segundos")
            print(f"Tempo máximo: {max_time:.6f} segundos")
            print(f"Resultados salvos em: {filename}")
            
        # Desconectar todos os clientes
        for client in self.clients:
            client.disconnect()
            
def main():
    stress_test = StressTest()
    
    # Configurações de teste
    thread_counts = [10, 100, 500]
    connection_counts = [10, 100, 500]
    packet_counts = [10, 100, 1000]
    packet_sizes = [100, 1024, 10240]  # 100B, 1KB, 10KB
    
    for num_threads in thread_counts:
        for num_connections in connection_counts:
            for num_packets in packet_counts:
                for packet_size in packet_sizes:
                    try:
                        stress_test.run_test(
                            num_threads,
                            num_connections,
                            num_packets,
                            packet_size
                        )
                    except Exception as e:
                        print(f"Erro no teste: {e}")
                        
if __name__ == "__main__":
    main() 