import cv2
import pytesseract
import re
import os
import time
import numpy as np

# Diretório para salvar imagens recortadas das placas
output_dir = "placas_recortadas"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Configuração do intervalo de captura (em segundos)
intervalo_captura = 3
ultima_captura_tempo = 0

# Lista para armazenar placas detectadas recentemente
placas_detectadas = set()

# Função para extrair texto da placa usando Tesseract OCR com melhorias
def extrair_texto_da_placa(roi):
    # Converter a ROI para escala de cinza
    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Aplicar limiarização adaptativa para lidar com variações de iluminação
    roi_bin = cv2.adaptiveThreshold(roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Aplicar uma operação morfológica para melhorar a definição dos caracteres
    kernel = np.ones((3, 3), np.uint8)
    roi_bin = cv2.morphologyEx(roi_bin, cv2.MORPH_CLOSE, kernel)
    
    # Ajuste do Tesseract OCR para reconhecer uma linha de caracteres
    text = pytesseract.image_to_string(roi_bin, config='--psm 8')
    
    # Filtrar apenas letras e números
    text = re.sub(r'[^A-Z0-9]', '', text)
    return text.upper()

# Inicializa a captura de vídeo
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Verifica o tempo desde a última captura
    tempo_atual = time.time()
    if tempo_atual - ultima_captura_tempo < intervalo_captura:
        continue

    # Conversão do frame para escala de cinza
    cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Ajuste fino da limiarização para melhorar os contornos
    _, bin = cv2.threshold(cinza, 100, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Aplicação de desfoque para reduzir ruídos
    desfoque = cv2.GaussianBlur(bin, (7, 7), 0)

    # Detector de bordas de Canny (ajuste dos parâmetros)
    bordas = cv2.Canny(desfoque, 50, 150)

    # Encontrar contornos
    contornos, hier = cv2.findContours(bordas, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Processar cada contorno
    for c in contornos:
        perimetro = cv2.arcLength(c, True)
        if perimetro > 120:
            aprox = cv2.approxPolyDP(c, 0.02 * perimetro, True)

            # Verifica se o contorno possui 4 lados
            if len(aprox) == 4:
                (x, y, lar, alt) = cv2.boundingRect(aprox)
                aspect_ratio = lar / float(alt)

                # Verificar se a relação de aspecto está dentro do esperado
                if 2 <= aspect_ratio <= 5:
                    area = cv2.contourArea(c)
                    if 1000 < area < 15000:
                        roi = frame[y:y + alt, x:x + lar]
                        placa_texto = extrair_texto_da_placa(roi)

                        # Verifica se o texto extraído tem pelo menos 7 caracteres e é novo
                        if len(placa_texto) >= 7 and placa_texto not in placas_detectadas:
                            placas_detectadas.add(placa_texto)
                            ultima_captura_tempo = tempo_atual  # Atualiza o tempo da última captura
                            filename = os.path.join(output_dir, f"placa_{placa_texto}.png")
                            cv2.imwrite(filename, roi)
                            print(f"Imagem da placa salva: {filename}")
                            print("Texto extraído da placa:", placa_texto)
                            # Exibir retângulo e texto no frame
                            cv2.rectangle(frame, (x, y), (x + lar, y + alt), (0, 255, 0), 2)
                            cv2.putText(frame, placa_texto, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Exibir o frame processado
    cv2.imshow('frame', frame)

    # Sai do loop se a tecla 'q' for pressionada
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera a captura e destrói todas as janelas
cap.release()
cv2.destroyAllWindows()
