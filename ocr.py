import os
import re
import concurrent.futures
from pdf2image import convert_from_path
import pytesseract

# ==========================================
# CONFIGURAÇÕES DO SISTEMA
# ==========================================
CAMINHO_POPPLER = r'poppler\Library\bin'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

PASTA_ORIGEM = "pdfs_originais"
PASTA_DESTINO = "textos_ocr"
WORKERS_SIMULTANEOS = 12 

def limpar_texto_ocr(texto):
    blocos = re.split(r'(\n\s*\n|--- PÁGINA \d+ ---)', texto)
    blocos_processados = []
    
    for bloco in blocos:
        if "--- PÁGINA" in bloco:
            blocos_processados.append(bloco.strip())
            continue
        if not bloco.strip():
            continue

        conteudo = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', bloco)
        conteudo = conteudo.replace('\n', ' ')
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
            return f"PULANDO: '{arquivo}' (Erro ao remover: {e})"
        
    try:
        # --- NOVO: Print de Início ---
        print(f"[PROCESSO] Iniciando: {arquivo}")

        # 1. Converte PDF para Imagens
        print(f"  > [{arquivo}] Convertendo PDF para imagens...")
        paginas = convert_from_path(
            caminho_pdf, 
            dpi=150, 
            poppler_path=CAMINHO_POPPLER,
            grayscale=True,
            thread_count=1 
        )
        
        texto_bruto = ""
        total_paginas = len(paginas)
        
        # 2. Aplica OCR em cada página
        for num_pagina, imagem in enumerate(paginas):
            # Print de progresso das páginas (opcional, pode poluir se forem muitos PDFs)
            print(f"  > [{arquivo}] OCR na página {num_pagina + 1}/{total_paginas}")
            texto_pagina = pytesseract.image_to_string(imagem, lang='por')
            texto_bruto += f"\n--- PÁGINA {num_pagina + 1} ---\n"
            texto_bruto += texto_pagina
            
        # 3. Limpa a formatação
        print(f"  > [{arquivo}] Formatando e limpando texto...")
        texto_limpo = limpar_texto_ocr(texto_bruto)
            
        # 4. Salva o resultado
        with open(caminho_txt, 'w', encoding='utf-8') as f:
            f.write(texto_limpo)
            
        # 5. Remove o PDF original
        if os.path.exists(caminho_pdf):
            os.remove(caminho_pdf)
            
        return f"FINALIZADO: '{arquivo}'"
        
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

    print(f"[*] Total de arquivos: {total}")
    print(f"[*] Utilizando {WORKERS_SIMULTANEOS} processos simultâneos.")
    print("-" * 50)

    with concurrent.futures.ProcessPoolExecutor(max_workers=WORKERS_SIMULTANEOS) as executor:
        futuros = {executor.submit(processar_pdf, arquivo): arquivo for arquivo in arquivos_pdf}
        
        processados = 0
        for futuro in concurrent.futures.as_completed(futuros):
            processados += 1
            resultado = futuro.result()
            # Print de conclusão de cada arquivo
            print(f"[{processados}/{total}] {resultado}")

if __name__ == "__main__":
    aplicar_ocr_em_lote_paralelo()
    print("\n" + "="*50)
    print("[OK] Tudo pronto! Todos os textos foram extraídos e limpos.")
    print("="*50)