# Guia de Utilização - Raspberry Pi 4 do Robô

Tutorial de como preparar o ambiente, estabelecer a conexão de rede (via Tailscale ou Wi-Fi Direto) e executar a programação principal de visão e integração da Raspberry Pi 4 com o bloco EV3.

### Preparação do Ambiente e Arquivos

Para começar, você deve organizar os arquivos de trabalho no seu computador:
* Extraia ou mova da pasta principal `Gabi_fullcode` as seguintes pastas para a sua **Área de Trabalho**:
  * **`PASTA_RASP`**: Contém os scripts e arquivos da Raspberry Pi do robô.
  * **`Update_Segu`**: Contém os arquivos que servem para o EV3.

**Ponto Importante:** O arquivo `envia.bat` já está configurado por padrão para o IP `100.88.179.72`. Não é necessário fazer alterações manuais nele para o envio de arquivos.

### Alimentação de Energia

Caso você vá utilizar a Raspberry apenas para **testar a programação** e o robô não for realizar movimentos gigantescos ou rotinas pesadas de motor, recomenda-se:
* Utilizar a alimentação através de um **carregador USB-C** direto na tomada.
* Isso permite que você deixe a Raspberry ligada por horas de desenvolvimento contínuo sem precisar se preocupar em drenar ou trocar as baterias do robô.

---

### Métodos de Conexão de Rede

Você pode se conectar ao robô de duas formas diferentes, mas **ambas utilizarão o mesmo IP padrão: `100.88.179.72`**.

#### MÉTODO 1: Via Tailscale (Para programar de qualquer lugar com Internet)
Este método permite que você acesse o robô mesmo se ele estiver em outra rede ou longe de você.
1. Certifique-se de que o aplicativo do Tailscale está instalado e ativo no seu computador.
2. Para conectar a sua conta, faça login no Tailscale escolhendo a opção **Sign in with GitHub** e utilize as seguintes credenciais:
   * **E-mail:** `newatom16@gmail.com`
   * **Senha:** `Gabi@git123`
3. Com o Tailscale conectado no PC, a comunicação com o robô estará liberada.

#### MÉTODO 2: Via Wi-Fi Direto da Raspberry (Sem precisar de Internet)
Se você estiver em um local sem internet, pode se conectar diretamente à rede sem fio que a própria Raspberry gera.
1. No seu computador, abra a lista de redes Wi-Fi disponíveis.
2. Conecte-se na rede do robô:
   * **Nome da Rede (SSID):** `new`
   * **Senha padrão:** `senha123`
3. Pronto. Mesmo por esse Wi-Fi local, o endereço de acesso da placa continuará sendo o mesmo IP.

---

### Acesso Remoto via SSH

Independentemente do método de rede escolhido acima, o acesso ao terminal é feito da mesma forma:

1. Aperte as teclas `Win + R`, digite `cmd` e dê Enter para abrir o terminal do seu computador.
2. Digite o seguinte comando para iniciar a conexão:


        ssh new@100.88.179.72



3. Quando solicitado, digite a senha padrão da Raspberry: `senha123`

---

### Executando a Programação e Dashboard

Para iniciar os sistemas do robô, acesse o diretório correto e rode o script em Python.

1. Entre na pasta onde estão as programações digitando:


        cd programacao_rasp4/



2. Execute o código principal manualmente chamando o Python:


        python3 RaspNewforEv3.py



**Acessando as Câmeras (Dashboard):**
Assim que o script estiver rodando, abra o navegador do seu computador e digite o seguinte endereço para ver o feed da câmera e a telemetria:

👉 **`http://100.88.179.72:5000`**



---

### Como Atualizar a Programação

1. **Pare a execução atual no robô:** No terminal SSH onde o script está rodando, pressione `Ctrl + C`.
2. **Edite e Salve o Código:** Faça as modificações na sua `PASTA_RASP` local pelo editor (como o VS Code) e salve com `Ctrl + S`.
3. **Execute o arquivo de envio:** Dentro da pasta `PASTA_RASP` do seu PC, dê dois cliques no arquivo `envia.bat`.
4. **Autenticação:** Quando o terminal pedir a senha da Raspberry Pi, digite `senha123` e pressione Enter.
5. **Rode novamente:** Volte ao seu terminal SSH do robô e execute o comando para iniciar a nova versão:


        python3 RaspNewforEv3.py

