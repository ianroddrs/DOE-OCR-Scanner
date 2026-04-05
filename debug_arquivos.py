import os
import re

PASTA_OCR_LOCAL = "textos_ocr"

def normalizar_texto(texto):
    """Remove pontuação e converte para minúsculas"""
    if not texto:
        return ""
    texto = texto.lower()
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    return re.sub(r'\s+', ' ', texto).strip()

def ler_arquivo_com_encoding(caminho):
    """Tenta ler arquivo com múltiplos encodings"""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'ascii']
    
    for encoding in encodings:
        try:
            with open(caminho, 'r', encoding=encoding) as f:
                return f.read(), encoding
        except (UnicodeDecodeError, LookupError):
            continue
    
    try:
        with open(caminho, 'rb') as f:
            conteudo = f.read()
            return conteudo.decode('utf-8', errors='ignore'), 'binary-utf8-ignore'
    except:
        return None, None

print("=" * 80)
print("DEBUG: VERIFICANDO ARQUIVOS NA PASTA textos_ocr/")
print("=" * 80)

if not os.path.exists(PASTA_OCR_LOCAL):
    print(f"❌ Pasta '{PASTA_OCR_LOCAL}' não encontrada!")
    exit(1)

arquivos = sorted([f for f in os.listdir(PASTA_OCR_LOCAL) if f.endswith('.txt')])

print(f"\n✅ Encontrados {len(arquivos)} arquivos TXT\n")

if len(arquivos) > 0:
    # Mostrar primeiros 5 arquivos
    print("Primeiros 5 arquivos:")
    for i, arquivo in enumerate(arquivos[:5], 1):
        print(f"  {i}. {arquivo}")
    
    if len(arquivos) > 5:
        print(f"  ... e mais {len(arquivos) - 5} arquivos")

print("\n" + "=" * 80)
print("TESTANDO LEITURA DO PRIMEIRO ARQUIVO")
print("=" * 80)

if len(arquivos) > 0:
    primeiro_arquivo = os.path.join(PASTA_OCR_LOCAL, arquivos[0])
    conteudo, encoding = ler_arquivo_com_encoding(primeiro_arquivo)
    
    print(f"\nArquivo: {arquivos[0]}")
    print(f"Encoding detectado: {encoding}")
    
    if conteudo:
        tamanho = len(conteudo)
        print(f"Tamanho: {tamanho} caracteres")
        
        print(f"\nPrimeiros 500 caracteres:")
        print("-" * 80)
        print(conteudo[:500])
        print("-" * 80)
        
        # Buscar "helio" no arquivo
        print(f"\n🔍 Procurando 'helio' no arquivo...")
        conteudo_norm = normalizar_texto(conteudo)
        
        if 'helio' in conteudo_norm:
            print(f"✅ ENCONTRADO 'helio' no arquivo!")
            # Mostrar contexto
            idx = conteudo_norm.find('helio')
            inicio = max(0, idx - 100)
            fim = min(len(conteudo_norm), idx + 100)
            print(f"\nContexto (100 chars antes e depois):")
            print(f"...{conteudo_norm[inicio:fim]}...")
        else:
            print(f"❌ NÃO encontrado 'helio' no arquivo normalizado")
            
            # Verificar se 'helio' existe no texto original
            if 'helio' in conteudo.lower():
                print(f"⚠️  Mas 'helio' EXISTE no texto original (problema na normalização?)")
                # Mostrar todas as ocorrências
                import re as regex
                matches = list(regex.finditer(r'helio', conteudo.lower()))
                print(f"\nEncontradas {len(matches)} ocorrências de 'helio':")
                for m in matches[:5]:
                    inicio = max(0, m.start() - 50)
                    fim = min(len(conteudo), m.end() + 50)
                    print(f"  ...{conteudo[inicio:fim]}...")
            else:
                print(f"❌ 'helio' NÃO existe em nenhuma forma no arquivo")

print("\n" + "=" * 80)
print("TESTANDO EM TODOS OS ARQUIVOS")
print("=" * 80)

helio_encontrado = False
arquivos_com_helio = []

for arquivo in arquivos:
    caminho = os.path.join(PASTA_OCR_LOCAL, arquivo)
    conteudo, _ = ler_arquivo_com_encoding(caminho)
    
    if conteudo:
        conteudo_norm = normalizar_texto(conteudo)
        if 'helio' in conteudo_norm:
            arquivos_com_helio.append(arquivo)
            helio_encontrado = True

if helio_encontrado:
    print(f"\n✅ 'helio' encontrado em {len(arquivos_com_helio)} arquivo(s):")
    for arq in arquivos_com_helio[:10]:
        print(f"  • {arq}")
    if len(arquivos_com_helio) > 10:
        print(f"  ... e mais {len(arquivos_com_helio) - 10}")
else:
    print(f"\n❌ 'helio' NÃO foi encontrado em nenhum arquivo")
    
    # Mostrar algumas palavras que existem nos arquivos
    print(f"\nProcurando por outras palavras nos primeiros 2 arquivos...")
    for arquivo in arquivos[:2]:
        caminho = os.path.join(PASTA_OCR_LOCAL, arquivo)
        conteudo, _ = ler_arquivo_com_encoding(caminho)
        
        if conteudo:
            conteudo_norm = normalizar_texto(conteudo)
            palavras = conteudo_norm.split()[:20]  # Primeiras 20 palavras
            print(f"\n{arquivo}:")
            print(f"  Primeiras palavras: {' '.join(palavras)}")

print("\n" + "=" * 80)