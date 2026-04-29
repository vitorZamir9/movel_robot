<div align="center">
  <img src="[<img width="830" height="744"  src="https://github.com/user-attachments/assets/acefdc68-4b8b-43fd-8b1b-efbaf6320b58" />
]" style="width:50%;" />
</div>
<img width="1325" height="950"  src="https://github.com/user-attachments/assets/e4f3ef25-246f-46e3-932f-bba93bd69158" />

<br/>
<br/>

<div align="center">
  <a href="[LINK_GITHUB_PEDRO]">
    <img src="https://img.shields.io/badge/CAD-Pedro_Henrique-blue" alt="Pedro Henrique">
  </a>
  
  <a href="[LINK_GITHUB_VINICIUS]">
    <img src="https://img.shields.io/badge/Mecânica-Vinicius_Deybson-blue" alt="Vinicius Deybson">
  </a>

  <a href="[LINK_GITHUB_JOAO]">
    <img src="https://img.shields.io/badge/Dev-Joao_Cardoso-blue" alt="Joao Cardoso">
  </a>

  <a href="[LINK_GITHUB_VITOR]">
    <img src="https://img.shields.io/badge/Mentor-Vitor_Zamir-purple" alt="Vitor Zamir">
  </a>
  
  <a href="[LINK_YOUTUBE_OU_INSTAGRAM]">
    <img src="https://img.shields.io/badge/YouTube-New_Atom-red?logo=youtube" alt="New Atom YouTube Channel">
  </a>
</div>

<br/>
<br/>

<p align="center">
  Este é o repositório oficial da equipa brasileira <b>New Atom</b>. Aqui documentamos o desenvolvimento do nosso robô <b>Gabi</b>, projetado para competir na modalidade de Resgate (Rescue Line / OBR).
</p>

## 📌 Sobre a Competição
<p align="center"><i>
  "A área de desastre é muito perigosa para os humanos alcançarem as vítimas. A sua equipa recebeu uma tarefa desafiadora. O robô deve ser capaz de realizar uma missão de resgate de forma totalmente autônoma, sem assistência humana. O robô deve ser durável e inteligente o suficiente para navegar por terrenos traiçoeiros com colinas, desníveis e destroços sem ficar preso. Ao alcançar as vítimas, ele deve transportá-las cuidadosamente para a área de evacuação..."
</i></p>

<div align="center">
  <img src="[LINK_IMAGEM_PISTA]" style="width:70%;"/>
</div>

<p align="justify">
  O objetivo da competição é desenvolver um robô autônomo capaz de superar obstáculos como redutores de velocidade, rampas, encruzilhadas (com marcadores verdes) e falhas na linha preta. Ao final do trajeto, o robô precisa identificar a entrada da zona de resgate (linha prata), varrer a área, identificar vítimas vivas e mortas e posicioná-las com segurança na área de evacuação, finalizando a missão de forma autônoma.
</p>

## 🤖 Sobre o Projeto "Gabi"
<img src="[<img width="1325" height="950" alt="Captura de tela 2026-04-29 121129" src="https://github.com/user-attachments/assets/170f62e0-1124-4ba6-a08e-ad3780ab8201" />]" align="right" style="width:26%;"/>
<img src="[<img width="3024" height="4032" alt="WhatsApp Image 2026-04-29 at 12 20 53" src="https://github.com/user-attachments/assets/6e340f5f-063d-4faa-b0b2-b2e2ab948d8d" />]" align="left" style="width:25%;"/>

<p align="center">
  Para cumprir todas as tarefas com precisão de nível WorldSkills, desenvolvemos a <b>Gabi</b> utilizando uma arquitetura híbrida de hardware: combinamos a robustez do controlo de motores do LEGO EV3 com o alto poder de processamento de IA e Visão Computacional de uma Raspberry Pi 4.
</p>

<p align="justify">
  Neste repositório, detalhamos o nosso sistema de seguir linha com PID Dinâmico (Freio Inteligente) e a nossa árvore de decisão baseada em processamento de imagem puro e redes neurais.
</p>

<br clear="both"/>

### ⚙️ Componentes Principais

<p align="justify">
  Além do chassi personalizado impresso em 3D e rodas adaptadas (com pneus moldados em silicone de alta aderência), utilizamos os seguintes componentes eletrônicos para garantir a máxima performance a 10.1V:
</p>

- 1x Bloco LEGO EV3 (Controlo de Motores e Malha PID)
- 1x Raspberry Pi 4 (8GB) (Processamento de Visão e IA)
- 1x Módulo Giroscópio MPU6050 (Via I2C)
- 1x Câmera PiCamera2 IMX500 (Leitura de Linha e Verdes - Fisicamente invertida)
- 1x Câmera USB IMX179 (Detecção de Vítimas via YOLO)
- 2x Motores LEGO EV3 Large (Tração a >200 RPM)
- 1x Step-Up Conversor XL6009 (Elevando a tensão para 10.1V)
- Sensores Multiplexados de Refletância
- [COLOQUE AQUI: Bateria LiPo ou de Íon de Lítio utilizada]
- [COLOQUE AQUI: Outros sensores, garra, ou servos utilizados]

## 💻 Software & Lógica

### Controlo de Baixo Nível (EV3 MicroPython)
<p align="justify">
  O cérebro de movimentação corre no EV3 utilizando MicroPython. Desenvolvemos um algoritmo de <b>PID com Freio Dinâmico</b>. O robô avalia a variável de erro: em retas, ele ignora ruídos através de uma <i>Zona Morta</i> e aplica 100% da velocidade. Ao detetar um erro alto (curvas), ele reduz proporcionalmente a base de velocidade de ambos os motores, realizando curvas perfeitas sem a inércia atirar o robô para fora da pista. O EV3 escuta continuamente via UART (Cabo Serial) os comandos de curva e telemetria enviados pela Raspberry.
</p>

### Visão Computacional (OpenCV)
<p align="justify">
  A câmera IMX500 inferior é responsável por guiar o robô em encruzilhadas e gaps. Usamos filtros HSV com <i>Gaussian Blur</i> e operações morfológicas para isolar a linha preta e os marcadores verdes. Uma árvore de decisão geométrica avalia a posição relativa entre a área verde e o centro de massa da linha para enviar comandos via serial (ex: <i>"1 verde esquerda antes da linha preta"</i>) para o EV3 executar manobras de 90 graus ou becos.
</p>

### Inteligência Artificial (YOLOv8)
<p align="justify">
  Ao detetar a fita prata de entrada do resgate, a Raspberry suspende a câmera inferior e ativa a câmera IMX179 acoplada à garra. Treinamos um modelo <b>YOLOv8</b> otimizado para CPU que deteta vítimas vivas (Silver Ball) e mortas (Black Ball) com alta confiança. O sistema calcula a área em píxeis e a posição (esquerda/meio/direita) da vítima no frame, enviando as coordenadas exatas para o EV3 realizar a aproximação final e o resgate.
</p>

## 👥 Sobre a Equipa New Atom

<p align="justify">
  A equipa <b>New Atom</b> é formada por estudantes apaixonados por robótica, com um histórico forte em competições como OBR, FLL, FTC e eventos técnicos. Dividimos as nossas funções para otimizar o desenvolvimento de um robô de alto nível:
</p>

- **Pedro Henrique** - <i>Engenheiro de CAD:</i> Responsável por toda a modelagem 3D, encaixes, suporte de sensores e estrutura física da Gabi.
- **Vinícius Deybson** - <i>Engenheiro Mecânico:</i> Especialista em montagem, sistemas de tração, fabricação das rodas (silicone Shore A) e integridade estrutural.
- **João Cardoso** - <i>Programador:</i> Desenvolvedor das lógicas de controlo, malhas de PID e processamento de imagem em Python.
- **Vitor Zamir** - <i>Mentor:</i> Estudante de Ciência da Computação na UniFBV, Embaixador FIRST e competidor da modalidade de Robótica Móvel (WorldSkills #23). Auxilia a equipa com arquitetura de software de alta performance e estratégia de prova.

### 🏆 Conquistas
- [Ex: 1º Lugar Regional OBR 202X]
- [Ex: Prémio de Melhor Design de Robô - Estadual OBR 202X]
- [Adicione mais conquistas aqui]

## 🔗 Links Úteis

- [COLOQUE AQUI: Link para o vídeo do robô Gabi na pista]
- [COLOQUE AQUI: Link do Dataset do YOLOv8 (Roboflow) se for público]

## 📄 Licença
Este projeto está licenciado sob a licença [COLOQUE A LICENÇA AQUI, ex: MIT ou GNU GPLv3] - veja o ficheiro [LICENSE](LICENSE) para detalhes.

---
*A equipa New Atom incentiva o compartilhamento de conhecimento. Sente-te à vontade para explorar o nosso código para entender como implementamos a integração serial entre Raspberry e EV3 e o uso de IA no resgate!*
