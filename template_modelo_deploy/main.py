import json
import base64
import io
from PIL import Image
from ultralytics import YOLO

def init_context(context):
    """
    Carrega o modelo YOLOv8s uma única vez quando o contêiner é iniciado.
    """
    context.logger.info("Inicializando o modelo YOLOv8s para detecção de mono_flakes...")
    
    # O arquivo deve estar no mesmo diretório de trabalho após o COPY
    model_path = "/opt/nuclio/best.pt" 
    
    try:
        model = YOLO(model_path)
        context.user_data.model = model 
        context.logger.info("Modelo carregado com sucesso!")
    except Exception as e:
        context.logger.error(f"Erro ao carregar o modelo: {e}")
        raise e

def handler(context, event):
    """
    Processa a imagem enviada pelo CVAT e retorna as bounding boxes.
    """
    context.logger.info("Processando imagem para detecção...")
    
    try:
        # Garante que o body seja convertido de JSON (bytes/str) para Dict Python
        if isinstance(event.body, (bytes, str)):
            data = json.loads(event.body)
        else:
            data = event.body
        
        # Decodifica a imagem recebida em base64
        image_bytes = base64.b64decode(data["image"])
        image = Image.open(io.BytesIO(image_bytes))
        
        model = context.user_data.model
        
        # Executa a inferência
        results = model(image, conf=0.6766766766766766)
        
        encoded_results = []
        
        for r in results:
            for box in r.boxes:
                # Coordenadas: [x_min, y_min, x_max, y_max]
                b = box.xyxy[0].tolist()
                
                # Confiança
                conf = float(box.conf[0])
                label_name = "mono_flakes"
                
                encoded_results.append({
                    "confidence": str(conf),
                    "label": label_name,
                    "points": b,
                    "type": "rectangle"
                })

        return context.Response(body=json.dumps(encoded_results),
                                headers={},
                                content_type='application/json',
                                status_code=200)

    except Exception as e:
        context.logger.error(f"Erro durante a inferência: {e}")
        return context.Response(body=f"Erro interno no processamento: {e}",
                                headers={},
                                status_code=500)