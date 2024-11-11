import cv2
import pytesseract
import re
import os
import numpy as np
import mysql.connector

def verificar_placa_no_banco(placa):
    try:
        # Conecta ao banco de dados
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='OCR'
        )
        cursor = conn.cursor()

        # Executa a consulta para verificar se a placa está no banco de dados
        cursor.execute("SELECT placa FROM Placas WHERE placa = %s", (placa,))
        resultado = cursor.fetchone()

        # Fecha o cursor e a conexão
        cursor.close()
        conn.close()

        # Retorna True se a placa foi encontrada, False caso contrário
        if resultado is not None:
            print(f"Placa {placa} encontrada no banco de dados.")
            return True
        else:
            print(f"Placa {placa} não encontrada no banco de dados.")
            return False
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        return False

# Diretório para salvar imagens recortadas das placas
output_dir = "placas_recortadas"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Dicionário com caracteres válidos para placas (letras e números)
caracteres_validos = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

# Função para extrair texto da placa usando Tesseract OCR com melhorias
def extrair_texto_da_placa(roi):
    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    roi_bin = cv2.adaptiveThreshold(roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    kernel = np.ones((3, 3), np.uint8)
    roi_bin = cv2.morphologyEx(roi_bin, cv2.MORPH_CLOSE, kernel)

    # Realiza a extração de texto usando Tesseract
    texto_extraido = pytesseract.image_to_string(roi_bin, config='--psm 8')

    # Filtra caracteres válidos
    texto_filtrado = ''.join(char for char in texto_extraido.upper() if char in caracteres_validos)
    return texto_filtrado

# Função para limpar as imagens existentes
def limpar_imagens():
    for filename in os.listdir(output_dir):
        file_path = os.path.join(output_dir, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

# Inicializa a captura de vídeo com resolução reduzida
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # Largura
cap.set(4, 480)  # Altura

frame_count = 0  # Contador de frames para limitar a frequência de processamento

while True:
    # Limpa imagens anteriores
    limpar_imagens()

    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # Processa apenas a cada 5 frames (ajuste conforme necessário)
    if frame_count % 5 == 0:
        # Conversão do frame para escala de cinza
        cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Limiarização para melhorar os contornos
        _, bin = cv2.threshold(cinza, 100, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Aplicação de desfoque para reduzir ruídos
        desfoque = cv2.GaussianBlur(bin, (5, 5), 0)

        # Detector de bordas de Canny
        bordas = cv2.Canny(desfoque, 50, 150)

        # Encontrar contornos
        contornos, _ = cv2.findContours(bordas, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Variável para controlar se uma placa foi detectada
        placa_detectada = False

        # Processar cada contorno
        for c in contornos:
            perimetro = cv2.arcLength(c, True)
            if perimetro > 120:
                aprox = cv2.approxPolyDP(c, 0.02 * perimetro, True)
                if len(aprox) == 4:
                    (x, y, lar, alt) = cv2.boundingRect(aprox)
                    aspect_ratio = lar / float(alt)

                    if 2 <= aspect_ratio <= 5:
                        area = cv2.contourArea(c)
                        if 1000 < area < 15000:
                            roi = frame[y:y + alt, x:x + lar]
                            placa_texto = extrair_texto_da_placa(roi)

                            # Verifica se o texto extraído tem exatamente 7 caracteres
                            if len(placa_texto) == 7:
                                # Verificar se a placa está no banco de dados
                                if verificar_placa_no_banco(placa_texto):
                                    print("Placa detectada no banco de dados!")
                                    # Exibe a imagem da placa em uma nova janela
                                    cv2.imshow("Placa Detectada", roi)
                                
                                filename = os.path.join(output_dir, f"placa_{placa_texto}.png")
                                cv2.imwrite(filename, roi)
                                print(f"Imagem da placa salva: {filename}")
                                print("Texto extraído da placa:", placa_texto)
                                cv2.rectangle(frame, (x, y), (x + lar, y + alt), (0, 255, 0), 2)
                                cv2.putText(frame, placa_texto, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                                # Marcar que uma placa foi detectada
                                placa_detectada = True
                                break  # Quebrar o loop após detectar a placa

        # Se não houver placas detectadas, continue a detecção nos próximos frames
        if not placa_detectada:
            continue

    # Exibir o frame processado
    cv2.imshow('frame', frame)

    # Sai do loop se a tecla 'q' for pressionada
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera a captura e fecha janelas
cap.release()
cv2.destroyAllWindows()
