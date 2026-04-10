import os
from ultralytics import YOLO

# Configurações
base_model_path = "modelo/yolov8n.pt"  # modelo base
dataset_path = "treino"  # pasta onde as imagens e labels estarão organizadas (images/ e labels/)
classes = ["triangulo_verde", "triangulo_vermelho"]

# Criar arquivo data.yaml para o ultralytics
data_yaml_content = f"""
train: {os.path.abspath(os.path.join(dataset_path, 'images'))}
val: {os.path.abspath(os.path.join(dataset_path, 'images'))}  # para testes use mesmo treino, mas ideal ter validação real
nc: {len(classes)}
names: {classes}
"""

with open("data.yaml", "w") as f:
    f.write(data_yaml_content.strip())

print("Arquivo data.yaml criado!")

# Carregar modelo base YOLOv8n
model = YOLO(base_model_path)

# Treinar modelo
model.train(
    data="data.yaml",
    epochs=30,
    imgsz=384,
    batch=16,
    name="triangulo_yolov8n",
    save=True,
)

print("Treinamento finalizado! Modelo salvo na pasta runs/detect/triangulo_yolov8n/weights")
