# Guia de Utilização - Raspberry Pi 4 do Robô

Tutorial de como preparar o ambiente, estabelecer a conexão de rede e executar a programação principal de visão e integração da Raspberry Pi 4 com o bloco EV3.

### Preparação do Ambiente e Arquivos

Para começar, você deve organizar os arquivos de trabalho no seu computador:
* Extraia ou mova da pasta principal `Gabi_fullcode` as seguintes pastas para a sua **Área de Trabalho**:
  * **`PASTA_RASP`**: Contém os scripts e arquivos da Raspberry Pi do robô.
  * **`Update_Segu`**: Contém os arquivos que servem para o EV3.

**Ponto Importante:** O arquivo `envia.bat` já está configurado por padrão para o novo IP da Raspberry. Não é necessário fazer alterações manuais nele para o envio de arquivos.

### Alimentação de Energia

Caso você vá utilizar a Raspberry apenas para **testar a programação** e o robô não for realizar movimentos gigantescos ou rotinas pesadas de motor, recomenda-se:
* Utilizar a alimentação através de um **carregador USB-C** direto na tomada.
* Isso permite que você deixe a Raspberry ligada por horas de desenvolvimento contínuo sem precisar se preocupar em drenar ou trocar as baterias do robô.

### Conexão de Rede e Internet

Logo após você ligar a placa, ela irá criar uma rede Wi-Fi (Access Point) dedicada para comunicação estável entre o robô e qualquer computador.

* **SSID (Nome da Rede):** `new`
* **Senha padrão:** `senha123`
* **IP padrão da Raspberry:** `10.42.0.1` *(Você pode confirmar isso no gerenciamento de rede do seu PC; o IP do roteador listado lá será o IP do robô).*

**Atenção sobre a Internet:**
Quando você se conecta à rede do robô, você **não** terá acesso à internet para navegar em sites por padrão. A rede serve puramente para estabilidade de comunicação. Para dar acesso à internet (necessário para baixar ou atualizar bibliotecas), você tem duas opções com um cabo de rede (RJ45) conectado ao seu roteador:

1. **Cabo conectado na Raspberry (Recomendado):** A Raspberry receberá internet e irá *rotear* o sinal para a rede `new`. Assim, tanto a placa quanto o seu PC conectado no Wi-Fi terão internet.
2. **Cabo conectado no PC:** Apenas o seu computador terá acesso à internet, e a placa continuará isolada.

### Acesso Remoto via SSH

Quando estiver conectado à rede do robô, você precisará logar no terminal da placa via SSH:

1. Aperte as teclas `Win + R`, digite `cmd` e dê enter para abrir o terminal do seu computador.
2. Digite o seguinte comando para iniciar a conexão:

        ssh -y new@10.42.0.1

3. Quando solicitado, digite a senha: `senha123`

Assim que o login for efetuado, você estará dentro do terminal do robô e pronto para ativar as programações.

### Executando a Programação e Dashboard

Para iniciar os sistemas do robô, você precisa acessar o diretório correto e rodar o script em Python.

1. Digite o comando `ls` para listar as pastas do sistema.
2. Entre na pasta onde estão as programações digitando:

        cd programacao_rasp4/

Dentro desse diretório, você encontrará todas as programações, mas os dois arquivos principais são:
* `RaspNewforEv3.py` (Código principal de visão e controle da Raspberry).
* `dashboard_server.py` (Servidor Flask da interface local).

**Para iniciar a execução e testar erros:**
Recomenda-se rodar a programação manualmente chamando o Python. (A versão de utilizar o loop automático via `start.sh` está apresentando algumas falhas pois a programação ainda não está 100% completa).

Certifique-se de estar dentro da pasta `programacao_rasp4/` e execute:

        python3 RaspNewforEv3.py

**Acessando as Câmeras (Dashboard):**
Assim que o script principal estiver rodando, o servidor local (Flask) será iniciado. Você pode verificar as câmeras, funções e telemetria do robô acessando o seguinte endereço no navegador do seu computador:
👉 http://100.88.179.72:5000
### Como Atualizar a Programação
Para enviar novas atualizações de código do seu computador para o robô, o processo é muito fácil e automatizado. Siga estes passos para garantir que não haja erros de corrupção de arquivo:

1. **Pare a execução atual no robô:** Antes de enviar a nova versão, vá no terminal SSH onde o script está rodando e pare a execução pressionando `Ctrl + C`. Isso é essencial para que a programação chegue completinha e sem erros de sobrescrita.

2. **Edite e Salve o Código:** Abra a pasta local `PASTA_RASP` no seu editor (como o VS Code) e faça as modificações na programação principal.

   > ⚠️ **MUITO IMPORTANTE:** Nunca esqueça de salvar o arquivo pressionando `Ctrl + S`. Se você não salvar, o sistema enviará a versão antiga para a Raspberry!

3. **Execute o arquivo de envio:** Dentro da pasta `PASTA_RASP`, execute o arquivo `envia.bat`.
   * Se estiver usando o VS Code, ao executar o `.bat`, ele abrirá o terminal integrado.

4. **Autenticação:** O terminal irá pedir a senha da Raspberry Pi. Digite `senha123` e pressione Enter.

5. **Pronto!** O script fará o envio automaticamente. Assim que concluir, basta voltar ao terminal do robô e rodar o comando:
        
        python3 RaspNewforEv3.py
