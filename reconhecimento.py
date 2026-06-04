import os
import sys
from datetime import datetime
import cv2
import numpy as np
from deepface import DeepFace
import database

# =========================================================
# CONFIGURAÇÕES
# =========================================================
VERIFICATION_THRESHOLD = 0.35  # Limiar para aceitar reconhecimento
FRAME_SKIP = 15                # Processa 1 a cada 15 frames para melhor performance
MODEL_NAME = "ArcFace"         # Modelo de reconhecimento
DETECTOR_BACKEND = "retinaface" # Detector de rostos

# =========================================================
# BANCO DE DADOS E CARREGAMENTO
# =========================================================

def carregar_alunos_e_gerar_embeddings():
    """Busca alunos no banco e gera embeddings iniciais das fotos."""
    try:
        conn = database.conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nome, foto_path
            FROM alunos
        """)

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("[ERRO] Nenhum aluno cadastrado no banco de dados.")
            return {}

        print(f"Iniciando processamento de {len(rows)} alunos...")
        embeddings_alunos = {}

        for row in rows:
            nome = row["nome"]
            caminho = row["foto_path"]

            if caminho and os.path.exists(caminho):
                try:
                    # Gera embedding uma única vez no início
                    embedding = DeepFace.represent(
                        img_path=caminho,
                        model_name=MODEL_NAME,
                        detector_backend=DETECTOR_BACKEND,
                        enforce_detection=True
                    )[0]["embedding"]

                    embeddings_alunos[nome] = np.array(embedding)
                    print(f"[OK] Embedding gerado: {nome}")
                except Exception as e:
                    print(f"[AVISO] Erro ao processar foto de {nome}: {e}")
            else:
                print(f"[AVISO] Foto não encontrada para {nome}: {caminho}")

        return embeddings_alunos

    except Exception as e:
        print(f"[ERRO SQLITE] Falha ao carregar alunos: {e}")
        return {}

def registrar_presenca(nome):
    """Registra a presença no banco de dados se ainda não houver registro hoje."""
    try:
        conn = database.conectar()
        cursor = conn.cursor()

        # Busca ID do aluno pelo nome
        cursor.execute("SELECT id FROM alunos WHERE nome=?", (nome,))
        aluno = cursor.fetchone()

        if not aluno:
            print(f"[ERRO] Aluno não encontrado no banco SQLite: {nome}")
            conn.close()
            return

        aluno_id = aluno["id"]
        hoje = datetime.now().date()

        # Verifica se já existe presença hoje
        cursor.execute("""
            SELECT id FROM presencas 
            WHERE aluno_id=? AND data_presenca=?
        """, (aluno_id, str(hoje)))

        if not cursor.fetchone():
            hora_atual = datetime.now().strftime("%H:%M:%S")
            
            # Se o aluno tinha uma falta hoje (chamada fechada cedo), removemos a falta
            cursor.execute("""
                DELETE FROM faltas 
                WHERE aluno_id=? AND data_falta=?
            """, (aluno_id, str(hoje)))
            
            # Registra a presença
            cursor.execute("""
                INSERT INTO presencas (aluno_id, data_presenca, hora_presenca)
                VALUES (?, ?, ?)
            """, (aluno_id, str(hoje), hora_atual))
            conn.commit()
            print(f"[PRESENÇA] {nome} registrada às {hora_atual}")
        
        conn.close()
    except Exception as e:
        print(f"[ERRO SQLITE] Falha ao registrar presença para {nome}: {e}")

def cosine_distance(a, b):
    """Calcula a distância cosseno entre dois vetores."""
    a = np.array(a)
    b = np.array(b)
    return 1 - (np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# =========================================================
# EXECUÇÃO PRINCIPAL
# =========================================================

# =========================================================
# VARIÁVEIS DE CONTROLE
# =========================================================

frame_count = 0
rostos_detectados = []

# Carrega alunos e encerra se vazio
embeddings_alunos = carregar_alunos_e_gerar_embeddings()
if not embeddings_alunos:
    print("[ERRO CRÍTICO] Nenhum aluno válido carregado. O sistema será encerrado.")
    sys.exit()

# Inicializa Câmera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("[ERRO CRÍTICO] Não foi possível abrir a câmera.")
    sys.exit()

print(f"\nEmbeddings carregados: {len(embeddings_alunos)}")
print("Embeddings carregados com sucesso.\n")

# =========================================================
# LOOP DE RECONHECIMENTO
# =========================================================
print("Sistema iniciado.")
print("Pressione ESC para sair.\n")

while True:

    ret, frame = cap.read()

    if not ret:
        print("Erro ao capturar frame.")
        break

    frame_count += 1

    # =====================================================
    # RECONHECIMENTO
    # =====================================================

    if frame_count % FRAME_SKIP == 0 or frame_count == 1:
        try:
            # Detecta rostos no frame atual
            faces = DeepFace.extract_faces(
                img_path=frame,
                target_size=(224, 224),
                detector_backend=DETECTOR_BACKEND,
                enforce_detection=False
            )

            rostos_detectados = []

            for face_obj in faces:
                confianca = face_obj["confidence"]
                
                # Ignora detecções fracas
                if confianca < 0.95:
                    continue

                area = face_obj["facial_area"]
                x, y, w, h = area["x"], area["y"], area["w"], area["h"]

                # Face alinhada pelo DeepFace
                face_img = (face_obj["face"] * 255).astype(np.uint8)

                try:
                    # Gera embedding do rosto detectado (usa 'skip' pois já foi detectado)
                    embedding_face = DeepFace.represent(
                        img_path=face_img,
                        model_name=MODEL_NAME,
                        detector_backend="skip",
                        enforce_detection=False
                    )[0]["embedding"]
                    embedding_face = np.array(embedding_face)
                except:
                    continue

                # Compara com os alunos em memória
                menor_distancia = 999
                nome_encontrado = "Desconhecido"

                for nome_aluno, embedding_aluno in embeddings_alunos.items():
                    distancia = cosine_distance(embedding_face, embedding_aluno)

                    if distancia < menor_distancia:
                        menor_distancia = distancia
                        nome_encontrado = nome_aluno

                # =================================================
                # VERIFICA SE PASSOU NO THRESHOLD
                # =================================================

                if menor_distancia < VERIFICATION_THRESHOLD:

                    # Evita duplicação no frame
                    nomes_ja_detectados = [r["nome"] for r in rostos_detectados]
                    if nome_encontrado not in nomes_ja_detectados:
                        rostos_detectados.append({
                            "coords": (x, y, w, h),
                            "nome": nome_encontrado,
                            "cor": (0, 255, 0)
                        })
                        # Tenta registrar presença no banco
                        registrar_presenca(nome_encontrado)
                else:
                    # Rosto não reconhecido
                    rostos_detectados.append({
                        "coords": (x, y, w, h),
                        "nome": "Desconhecido",
                        "cor": (0, 0, 255)
                    })

        except Exception as e:
            print(f"[ERRO DETECÇÃO] {e}")
            rostos_detectados = []

    # =====================================================
    # DESENHAR INTERFACE
    # =====================================================

    for rosto in rostos_detectados:
        x, y, w, h = rosto["coords"]
        nome = rosto["nome"]
        cor = rosto["cor"]

        cv2.rectangle(frame, (x, y), (x + w, y + h), cor, 2)
        
        cv2.putText(
            frame, nome, (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7,
            cor,
            2
        )

    # =====================================================
    # EXIBIÇÃO
    # =====================================================

    cv2.imshow("Reconhecimento Facial", frame)

    if cv2.waitKey(1) == 27: # ESC para sair
        break

# =========================================================
# FINALIZAÇÃO
# =========================================================

cap.release()
cv2.destroyAllWindows()

print("\nSistema encerrado.")