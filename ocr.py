import os
import re
import concurrent.futures
import multiprocessing
from pdf2image import convert_from_path
import pytesseract
import cv2
import numpy as np
import os
import re
import concurrent.futures
import multiprocessing
from pdf2image import convert_from_path
import pytesseract
import cv2
import numpy as np
import tempfile
import gc
from PIL import Image

# ==========================================
# CONFIGURAÇÕES DO SISTEMA E CAMINHOS
# ==========================================
CAMINHO_POPPLER = r'poppler\Library\bin'
CAMINHO_TESSERACT = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Aponta para o executável do Tesseract
pytesseract.pytesseract.tesseract_cmd = CAMINHO_TESSERACT

PASTA_ORIGEM = "pdfs_originais"
PASTA_DESTINO = "textos_ocr"

# Limita os núcleos para evitar MemoryError (máximo de 3 processos pesados simultâneos)
NUCLEOS_DISPONIVEIS = multiprocessing.cpu_count()
WORKERS_SIMULTANEOS = min(3, max(1, NUCLEOS_DISPONIVEIS - 2))

# Configuração avançada do Tesseract: 
# --oem 1 : Usa o motor de Rede Neural LSTM (Maior precisão)
# --psm 3 : Segmentação automática de página completa
CONFIG_TESSERACT = r'--oem 1 --psm 3'

def preprocessar_imagem(imagem_pil):
    """
    Aplica técnicas de Visão Computacional (OpenCV) para melhorar 
    drasticamente a imagem antes de enviá-la ao OCR.
    """
    # 1. Converte do formato PIL para o formato do OpenCV (Numpy Array)
    img_cv = np.array(imagem_pil)
    
    # 2. Converte para escala de cinza (caso ainda tenha alguma cor)
    if len(img_cv.shape) == 3:
        gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_cv
        
    # 3. Redução de ruído (Blur mediano suave para remover pontinhos na digitalização)
    blur = cv2.medianBlur(gray, 3)
    
    # 4. Binarização de Otsu (Aumenta o contraste: fundo perfeitamente branco, texto perfeitamente preto)
    # Isso resolve problemas de páginas amareladas, sombras e gradientes.
    _, imagem_binarizada = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return imagem_binarizada

def limpar_texto_ocr(texto):
    """
    Limpa e organiza o texto extraído, removendo quebras de linha quebradas e hifens soltos.
    """
    blocos = re.split(r'(\n\s*\n|--- PÁGINA \d+ ---)', texto)
    blocos_processados = []
    
    for bloco in blocos:
        if "--- PÁGINA" in bloco:
            blocos_processados.append(bloco.strip())
            continue
        if not bloco.strip():
            continue

        # Junta palavras separadas por hífen no fim da linha
        conteudo = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', bloco)
        # Troca quebras de linha simples por espaços
        conteudo = conteudo.replace('\n', ' ')
        # Remove espaços duplos
        conteudo = re.sub(r'\s+', ' ', conteudo).strip()
        
        if conteudo:
            blocos_processados.append(conteudo)
    
    resultado = ""
    for b in blocos_processados:
        if "--- PÁGINA" in b:
            resultado += f"\n\n{b}\n\n"
        else:
            resultado += f"{b}\n\n"
            
    return resultado.strip()

def processar_pdf(arquivo):
    caminho_pdf = os.path.join(PASTA_ORIGEM, arquivo)
    nome_base = arquivo.replace('.pdf', '')
    nome_txt = f"{nome_base}_ocr.txt"
    caminho_txt = os.path.join(PASTA_DESTINO, nome_txt)
    
    if os.path.exists(caminho_txt):
        try:
            if os.path.exists(caminho_pdf):
                os.remove(caminho_pdf)
            return f"PULANDO: '{arquivo}' (Já processado)"
        except Exception as e:
            return f"PULANDO: '{arquivo}' (Erro ao remover original: {e})"
        
    try:
        print(f"[PROCESSO] A iniciar processamento de alta precisão: {arquivo}")

        texto_bruto = ""
        
        # Usar pasta temporária joga a carga das imagens para o Disco (SSD/HDD) em vez da RAM
        with tempfile.TemporaryDirectory() as pasta_temp:
            
            # 1. Converte PDF para Imagens e salva os caminhos no disco temporário (paths_only=True)
            paginas_paths = convert_from_path(
                caminho_pdf, 
                dpi=300, 
                poppler_path=CAMINHO_POPPLER,
                grayscale=True,
                thread_count=1,
                output_folder=pasta_temp,
                paths_only=True
            )
            
            total_paginas = len(paginas_paths)
            
            # 2. Processa cada página individualmente carregando do disco
            for num_pagina, img_path in enumerate(paginas_paths):
                
                # Carrega apenas a página atual para a memória
                imagem = Image.open(img_path)
                
                # Melhora a imagem com OpenCV
                imagem_otimizada = preprocessar_imagem(imagem)
                
                # Aplica o Tesseract OCR na imagem otimizada
                texto_pagina = pytesseract.image_to_string(
                    imagem_otimizada, 
                    lang='por', 
                    config=CONFIG_TESSERACT
                )
                
                texto_bruto += f"\n--- PÁGINA {num_pagina + 1} ---\n"
                texto_bruto += texto_pagina
                
                # --- NOVO: Limpeza rigorosa da memória após cada página ---
                imagem.close()
                del imagem
                del imagem_otimizada
                gc.collect()
            
        # 3. Limpa a formatação
        texto_limpo = limpar_texto_ocr(texto_bruto)
            
        # 4. Salva o resultado
        with open(caminho_txt, 'w', encoding='utf-8') as f:
            f.write(texto_limpo)
            
        # 5. Remove o PDF original após o sucesso
        if os.path.exists(caminho_pdf):
            os.remove(caminho_pdf)
            
        return f"FINALIZADO COM SUCESSO: '{arquivo}'"
        
    except Exception as e:
        return f"ERRO em '{arquivo}': {e}"

def aplicar_ocr_em_lote_paralelo():
    if not os.path.exists(PASTA_ORIGEM):
        print(f"[!] Erro: A pasta '{PASTA_ORIGEM}' não existe.")
        return

    if not os.path.exists(PASTA_DESTINO):
        os.makedirs(PASTA_DESTINO)
        print(f"[*] Pasta '{PASTA_DESTINO}' criada.")

    arquivos_pdf = [f for f in os.listdir(PASTA_ORIGEM) if f.endswith('.pdf')]
    total = len(arquivos_pdf)
    
    if total == 0:
        print("[!] Nenhum PDF encontrado.")
        return

    print(f"[*] Total de ficheiros: {total}")
    print(f"[*] A utilizar {WORKERS_SIMULTANEOS} threads do processador (Máximo desempenho).")
    print(f"[*] Motor: Tesseract OCR Avançado + OpenCV Binarização (DPI 300)")
    print("-" * 50)

    # Processamento paralelo otimizado
    with concurrent.futures.ProcessPoolExecutor(max_workers=WORKERS_SIMULTANEOS) as executor:
        futuros = {executor.submit(processar_pdf, arquivo): arquivo for arquivo in arquivos_pdf}
        
        processados = 0
        for futuro in concurrent.futures.as_completed(futuros):
            processados += 1
            resultado = futuro.result()
            print(f"[{processados}/{total}] {resultado}")

if __name__ == "__main__":
    aplicar_ocr_em_lote_paralelo()
    print("\n" + "="*50)
    print("[OK] Tudo pronto! Todos os textos foram extraídos com precisão máxima.")
    print("="*50)
# ==========================================
# CONFIGURAÇÕES DO SISTEMA E CAMINHOS
# ==========================================
CAMINHO_POPPLER = r'poppler\Library\bin'
CAMINHO_TESSERACT = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Aponta para o executável do Tesseract
pytesseract.pytesseract.tesseract_cmd = CAMINHO_TESSERACT

PASTA_ORIGEM = "pdfs_originais"
PASTA_DESTINO = "textos_ocr"

# Usa todos os núcleos lógicos do processador (menos 1 para não travar o Windows)
NUCLEOS_DISPONIVEIS = multiprocessing.cpu_count()
WORKERS_SIMULTANEOS = max(1, NUCLEOS_DISPONIVEIS - 1)

# Configuração avançada do Tesseract: 
# --oem 1 : Usa o motor de Rede Neural LSTM (Maior precisão)
# --psm 3 : Segmentação automática de página completa
CONFIG_TESSERACT = r'--oem 1 --psm 3'

def preprocessar_imagem(imagem_pil):
    """
    Aplica técnicas de Visão Computacional (OpenCV) para melhorar 
    drasticamente a imagem antes de enviá-la ao OCR.
    """
    # 1. Converte do formato PIL para o formato do OpenCV (Numpy Array)
    img_cv = np.array(imagem_pil)
    
    # 2. Converte para escala de cinza (caso ainda tenha alguma cor)
    if len(img_cv.shape) == 3:
        gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_cv
        
    # 3. Redução de ruído (Blur mediano suave para remover pontinhos na digitalização)
    blur = cv2.medianBlur(gray, 3)
    
    # 4. Binarização de Otsu (Aumenta o contraste: fundo perfeitamente branco, texto perfeitamente preto)
    # Isso resolve problemas de páginas amareladas, sombras e gradientes.
    _, imagem_binarizada = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return imagem_binarizada

def limpar_texto_ocr(texto):
    """
    Limpa e organiza o texto extraído, removendo quebras de linha quebradas e hifens soltos.
    """
    blocos = re.split(r'(\n\s*\n|--- PÁGINA \d+ ---)', texto)
    blocos_processados = []
    
    for bloco in blocos:
        if "--- PÁGINA" in bloco:
            blocos_processados.append(bloco.strip())
            continue
        if not bloco.strip():
            continue

        # Junta palavras separadas por hífen no fim da linha
        conteudo = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', bloco)
        # Troca quebras de linha simples por espaços
        conteudo = conteudo.replace('\n', ' ')
        # Remove espaços duplos
        conteudo = re.sub(r'\s+', ' ', conteudo).strip()
        
        if conteudo:
            blocos_processados.append(conteudo)
    
    resultado = ""
    for b in blocos_processados:
        if "--- PÁGINA" in b:
            resultado += f"\n\n{b}\n\n"
        else:
            resultado += f"{b}\n\n"
            
    return resultado.strip()

def processar_pdf(arquivo):
    caminho_pdf = os.path.join(PASTA_ORIGEM, arquivo)
    nome_base = arquivo.replace('.pdf', '')
    nome_txt = f"{nome_base}_ocr.txt"
    caminho_txt = os.path.join(PASTA_DESTINO, nome_txt)
    
    if os.path.exists(caminho_txt):
        try:
            if os.path.exists(caminho_pdf):
                os.remove(caminho_pdf)
            return f"PULANDO: '{arquivo}' (Já processado)"
        except Exception as e:
            return f"PULANDO: '{arquivo}' (Erro ao remover original: {e})"
        
    try:
        print(f"[PROCESSO] A iniciar processamento de alta precisão: {arquivo}")

        # 1. Converte PDF para Imagens (DPI 300 é o ideal para OCR de alta precisão)
        paginas = convert_from_path(
            caminho_pdf, 
            dpi=300, 
            poppler_path=CAMINHO_POPPLER,
            grayscale=True,
            thread_count=1 
        )
        
        texto_bruto = ""
        total_paginas = len(paginas)
        
        # 2. Processa cada página
        for num_pagina, imagem in enumerate(paginas):
            
            # Melhora a imagem com OpenCV
            imagem_otimizada = preprocessar_imagem(imagem)
            
            # Aplica o Tesseract OCR na imagem otimizada
            texto_pagina = pytesseract.image_to_string(
                imagem_otimizada, 
                lang='por', 
                config=CONFIG_TESSERACT
            )
            
            texto_bruto += f"\n--- PÁGINA {num_pagina + 1} ---\n"
            texto_bruto += texto_pagina
            
        # 3. Limpa a formatação
        texto_limpo = limpar_texto_ocr(texto_bruto)
            
        # 4. Salva o resultado
        with open(caminho_txt, 'w', encoding='utf-8') as f:
            f.write(texto_limpo)
            
        # 5. Remove o PDF original após o sucesso
        if os.path.exists(caminho_pdf):
            os.remove(caminho_pdf)
            
        return f"FINALIZADO COM SUCESSO: '{arquivo}'"
        
    except Exception as e:
        return f"ERRO em '{arquivo}': {e}"

def aplicar_ocr_em_lote_paralelo():
    if not os.path.exists(PASTA_ORIGEM):
        print(f"[!] Erro: A pasta '{PASTA_ORIGEM}' não existe.")
        return

    if not os.path.exists(PASTA_DESTINO):
        os.makedirs(PASTA_DESTINO)
        print(f"[*] Pasta '{PASTA_DESTINO}' criada.")

    arquivos_pdf = [f for f in os.listdir(PASTA_ORIGEM) if f.endswith('.pdf')]
    total = len(arquivos_pdf)
    
    if total == 0:
        print("[!] Nenhum PDF encontrado.")
        return

    print(f"[*] Total de ficheiros: {total}")
    print(f"[*] A utilizar {WORKERS_SIMULTANEOS} threads do processador (Máximo desempenho).")
    print(f"[*] Motor: Tesseract OCR Avançado + OpenCV Binarização (DPI 300)")
    print("-" * 50)

    # Processamento paralelo otimizado
    with concurrent.futures.ProcessPoolExecutor(max_workers=WORKERS_SIMULTANEOS) as executor:
        futuros = {executor.submit(processar_pdf, arquivo): arquivo for arquivo in arquivos_pdf}
        
        processados = 0
        for futuro in concurrent.futures.as_completed(futuros):
            processados += 1
            resultado = futuro.result()
            print(f"[{processados}/{total}] {resultado}")

if __name__ == "__main__":
    aplicar_ocr_em_lote_paralelo()
    print("\n" + "="*50)
    print("[OK] Tudo pronto! Todos os textos foram extraídos com precisão máxima.")
    print("="*50)