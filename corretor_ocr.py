import os
import re
import concurrent.futures

# ==========================================
# CONFIGURAÇÕES
# ==========================================
PASTA_TEXTOS = "textos_ocr"

# --- OTIMIZAÇÃO ---
# Como é apenas processamento de texto (leve), podemos usar mais workers.
WORKERS_SIMULTANEOS = os.cpu_count() or 8

def limpar_texto_ocr(texto):
    """
    Mesma lógica de limpeza aplicada no script principal.
    """
    # 1. Divide o texto em blocos (parágrafos ou marcadores de página)
    blocos = re.split(r'(\n\s*\n|--- PÁGINA \d+ ---)', texto)
    
    blocos_processados = []
    
    for bloco in blocos:
        if "--- PÁGINA" in bloco:
            blocos_processados.append(bloco.strip())
            continue
            
        if not bloco.strip():
            continue

        # A. Trata hifenização de fim de linha: "es-\ncrito" -> "escrito"
        conteudo = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', bloco)
        
        # B. Transforma quebras de linha simples restantes em espaços
        conteudo = conteudo.replace('\n', ' ')
        
        # C. Limpa espaços múltiplos
        conteudo = re.sub(r'\s+', ' ', conteudo).strip()
        
        if conteudo:
            blocos_processados.append(conteudo)
    
    # Reagrupa os blocos
    resultado = ""
    for b in blocos_processados:
        if "--- PÁGINA" in b:
            resultado += f"\n\n{b}\n\n"
        else:
            resultado += f"{b}\n\n"
            
    return resultado.strip()

def processar_arquivo_txt(nome_arquivo):
    """
    Lê, limpa e sobrescreve o arquivo de texto.
    """
    caminho_arquivo = os.path.join(PASTA_TEXTOS, nome_arquivo)
    
    try:
        # Lê o conteúdo atual
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            conteudo_original = f.read()
        
        # Verifica se já parece estar formatado (opcional, para evitar re-processamento)
        # Se preferir forçar a limpeza em todos, ignore verificações.
        
        conteudo_corrigido = limpar_texto_ocr(conteudo_original)
        
        # Sobrescreve com a nova versão
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo_corrigido)
            
        return f"CORRIGIDO: '{nome_arquivo}'"
    except Exception as e:
        return f"ERRO ao corrigir '{nome_arquivo}': {e}"

def executar_correcao_em_lote():
    if not os.path.exists(PASTA_TEXTOS):
        print(f"[!] A pasta '{PASTA_TEXTOS}' não foi encontrada.")
        return

    arquivos_txt = [f for f in os.listdir(PASTA_TEXTOS) if f.endswith('.txt')]
    total = len(arquivos_txt)
    
    if total == 0:
        print("[!] Nenhum arquivo .txt encontrado para corrigir.")
        return

    print(f"[*] Iniciando correção de {total} arquivos usando {WORKERS_SIMULTANEOS} workers...")

    # Usamos ThreadPoolExecutor aqui pois a tarefa é I/O Bound (leitura/escrita) e o processamento de texto é rápido
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS_SIMULTANEOS) as executor:
        futuros = {executor.submit(processar_arquivo_txt, arq): arq for arq in arquivos_txt}
        
        sucessos = 0
        for futuro in concurrent.futures.as_completed(futuros):
            resultado = futuro.result()
            print(resultado)
            if "CORRIGIDO" in resultado:
                sucessos += 1

    print(f"\n[OK] Finalizado! {sucessos} arquivos foram atualizados.")

if __name__ == "__main__":
    print("=== UTILITÁRIO DE CORREÇÃO DE FORMATAÇÃO OCR ===")
    executar_correcao_em_lote()