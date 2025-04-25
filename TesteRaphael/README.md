# Chat Criptográfico Multithread

Este projeto implementa um chat criptográfico multithread com as seguintes características:
- Criptografia assimétrica (RSA) para troca de chaves
- Criptografia simétrica (AES) para mensagens
- Suporte a múltiplos clientes simultâneos
- Sistema de teste de stress configurável

## Requisitos

- Python 3.7+
- Bibliotecas Python listadas em `requirements.txt`

## Instalação

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

### Servidor

Existem duas formas de iniciar o servidor:

#### Diretamente:
```bash
# Iniciar com 10 threads (padrão)
python server.py

# Iniciar com número específico de threads
python server.py 100
```

#### Usando o script auxiliar:
```bash
python iniciar_servidor.py
```
Este script mostra um menu para selecionar o número de threads desejado.

### Cliente

Existem duas formas de iniciar o cliente:

#### Diretamente:
```bash
python client.py
```
O cliente solicitará um nome de usuário e se conectará ao servidor local na porta 5000.

#### Usando o script auxiliar para múltiplos clientes:
```bash
python iniciar_clientes.py
```
Este script permite iniciar múltiplos clientes de uma vez para facilitar os testes.

### Comandos do cliente:
- Digite uma mensagem e pressione Enter para enviar
- Digite 'sair' para desconectar
- Ctrl+C para encerrar o programa

### Teste de Stress

O script de teste de stress permite avaliar o desempenho do servidor com diferentes configurações:
- Número de threads no pool do servidor (10, 100, 500)
- Número de conexões simultâneas (10, 100, 500)
- Número de pacotes por conexão (10, 100, 1000)
- Tamanho do pacote (100 bytes, 1KB, 10KB)

Para executar os testes:
```bash
python stress_test.py
```

Os resultados serão salvos em arquivos JSON com o formato:
`results_[threads]_[connections]_[packets]_[size].json`

## Protocolo

### Conexão e Identificação
1. Cliente conecta com servidor e recebe a chave pública
2. Cliente gera chave secreta, criptografa com a pública e envia para o servidor
3. Cliente envia nome criptografado
4. Servidor decriptografa e gera mensagem "(Usuário X) conectado"
5. Servidor envia a mensagem para todos os clientes, criptografando para cada um

### Envio de Mensagem
1. Cliente envia mensagem criptografada para o servidor
2. Servidor decriptografa a mensagem e anexa a origem: "(Usuário X): mensagem"
3. Servidor envia a mensagem para todos os clientes, criptografando para cada um

### Recepção Assíncrona no Cliente
1. Cliente recebe mensagem criptografada do servidor
2. Cliente decriptografa a mensagem com sua chave secreta

## Solução de Problemas

### Problema com o Terminal Travar
- Se o terminal do cliente ou servidor travar, utilize os scripts auxiliares `iniciar_servidor.py` e `iniciar_clientes.py` que gerenciam os processos em subprocessos separados.
- Outra opção é usar terminais diferentes para servidor e cada cliente. 