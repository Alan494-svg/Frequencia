from deepface import DeepFace
import cv2
import pandas as pd
from datetime import datetime
import numpy as np
import os

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

frame_count = 0
rostos_detectados = []
csv_path = "frequencia_presenca.csv"

VERIFICATION_THRESHOLD = 0.6

ALUNOS_CADASTRADOS = {
    "Alan": "pessoas/Alan.jpg",
    "Crist": "pessoas/Cris.jpg",
}

def registrar_presenca(nome):
    data_atual = datetime.now().strftime('%d/%m/%Y')
    hora_atual = datetime.now().strftime('%H:%M:%S')
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame(columns=['Nome', 'Data', 'Hora'])

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

    if frame_count % 30 == 0:
        try:
            faces = DeepFace.extract_faces(img_path=frame, detector_backend='opencv', enforce_detection=False)
            
            rostos_detectados = []
            for face_obj in faces:
                if face_obj['confidence'] < 0.8:
                    continue

                area = face_obj['facial_area']
                x, y, w, h = area['x'], area['y'], area['w'], area['h']
                
                nome_encontrado = None
                menor_distancia = np.inf
                face_roi = frame[y:y+h, x:x+w]
                
                for nome_aluno, caminho_img in ALUNOS_CADASTRADOS.items():
                    try:
                        verificacao = DeepFace.verify(img1_path=face_roi, img2_path=caminho_img, 
                                                     model_name="Facenet", detector_backend="opencv", 
                                                     enforce_detection=False, silent=True,
                                                     distance_metric='euclidean_l2')
                        
                        if verificacao['distance'] < menor_distancia:
                            menor_distancia = verificacao['distance']
                            nome_encontrado = nome_aluno
                    except:
                        continue

                if nome_encontrado and menor_distancia < VERIFICATION_THRESHOLD:
                    nomes_identificados = [r['nome'] for r in rostos_detectados]
                    if nome_encontrado in nomes_identificados:
                        continue
                    rostos_detectados.append({"coords": (x, y, w, h), "nome": nome_encontrado, "cor": (0, 255, 0)})
                    registrar_presenca(nome_encontrado)
                else:
                    rostos_detectados.append({"coords": (x, y, w, h), "nome": "Desconhecido", "cor": (0, 0, 255)})
        except:
            rostos_detectados = []

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