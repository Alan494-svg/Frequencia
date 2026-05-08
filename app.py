from deepface import DeepFace
import cv2
import pandas as pd
from datetime import datetime
import numpy as np # Importar numpy para np.inf
import os

cap = cv2.VideoCapture(0)

# Configura a câmera para tentar capturar em 30 FPS e define uma resolução padrão
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

frame_count = 0
rostos_detectados = [] # Lista para armazenar múltiplos rostos detectados
csv_path = "frequencia_presenca.csv"

# Define um limiar de distância para considerar um rosto como reconhecido.
# Valores menores significam maior rigor. Para Facenet com euclidean_l2, um bom ponto de partida é entre 0.6 e 0.8. Ajuste conforme necessário.
VERIFICATION_THRESHOLD = 0.6

# Lista de alunos cadastrados (Nome: Caminho da Imagem)
ALUNOS_CADASTRADOS = {
    "Alan": "pessoas/Alan.jpg", # Corrigido para 'alan.jpg' (minúsculo) para corresponder ao arquivo fornecido
    "Crist": "pessoas/Cris.jpg",
}

def registrar_presenca(nome):
    data_atual = datetime.now().strftime('%d/%m/%Y')
    hora_atual = datetime.now().strftime('%H:%M:%S')
    
    # Carregar planilha existente ou criar uma nova
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame(columns=['Nome', 'Data', 'Hora'])

    # Verifica se a pessoa já foi registrada hoje para evitar duplicidade
    ja_registrado = not df[(df['Nome'] == nome) & (df['Data'] == data_atual)].empty

    if not ja_registrado:
        novo_registro = pd.DataFrame({'Nome': [nome], 'Data': [data_atual], 'Hora': [hora_atual]})
        df = pd.concat([df, novo_registro], ignore_index=True)
        df.to_csv(csv_path, index=False)
        print(f"Frequência registrada para: {nome}")

while True:
    ret, frame = cap.read()

    frame = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)

    frame_count += 1

    # Aumentamos o intervalo para 30 frames (aprox. 1 vez por segundo).
    # Isso permite que a câmera exiba mais quadros por segundo sem interrupção.
    if frame_count % 30 == 0:
        try:
            # Detecta todos os rostos presentes no frame
            faces = DeepFace.extract_faces(img_path=frame, detector_backend='opencv', enforce_detection=False)
            
            rostos_detectados = []
            for face_obj in faces:
                # Aumentamos a confiança para 0.8 para evitar "rostos fantasmas" no cenário
                if face_obj['confidence'] < 0.8:
                    continue

                area = face_obj['facial_area']
                x, y, w, h = area['x'], area['y'], area['w'], area['h']
                
                nome_encontrado = None
                menor_distancia = np.inf # Inicia com infinito para garantir que qualquer distância real seja menor
                face_roi = frame[y:y+h, x:x+w]
                
                # Procura o melhor match (menor distância) entre os alunos cadastrados
                for nome_aluno, caminho_img in ALUNOS_CADASTRADOS.items():
                    try:
                        verificacao = DeepFace.verify(img1_path=face_roi, img2_path=caminho_img, 
                                                     model_name="Facenet", detector_backend="opencv", 
                                                     enforce_detection=False, silent=True,
                                                     distance_metric='euclidean_l2') # Explicitamente definir a métrica
                        
                        # Sempre consideramos a menor distância, independentemente do 'verified' inicial
                        if verificacao['distance'] < menor_distancia:
                            menor_distancia = verificacao['distance']
                            nome_encontrado = nome_aluno
                    except Exception as e:
                        # print(f"Erro ao verificar rosto com {nome_aluno}: {e}") # Descomente para depuração
                        continue

                # Verifica se o nome já foi identificado neste frame para evitar duplicidade
                # Esta verificação deve ser feita APÓS decidir se o rosto é conhecido e antes de adicionar à lista
                
                # Após verificar todos os alunos, decide se o melhor match é válido e se a distância é aceitável
                if nome_encontrado and menor_distancia < VERIFICATION_THRESHOLD:
                    nomes_identificados = [r['nome'] for r in rostos_detectados]
                    if nome_encontrado in nomes_identificados:
                        continue # Já identificamos essa pessoa neste frame, pular
                    # Rosto cadastrado: Verde e registra
                    rostos_detectados.append({"coords": (x, y, w, h), "nome": nome_encontrado, "cor": (0, 255, 0)})
                    registrar_presenca(nome_encontrado)
                else:
                    # Rosto desconhecido: Vermelho e sem registro
                    rostos_detectados.append({"coords": (x, y, w, h), "nome": "Desconhecido", "cor": (0, 0, 255)})

        except:
            rostos_detectados = []

    # Desenha o contorno e o nome para cada rosto na lista
    for rosto in rostos_detectados:
        x, y, w, h = rosto["coords"]
        cv2.rectangle(frame, (x, y), (x + w, y + h), rosto["cor"], 2)
        cv2.putText(frame, rosto["nome"], (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, rosto["cor"], 2)

    cv2.imshow("Reconhecimento Facial", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()