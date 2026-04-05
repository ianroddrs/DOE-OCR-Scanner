import os
import re
import pickle
import time
from datetime import datetime
from pathlib import Path

PASTA_OCR_LOCAL = "textos_ocr"
CACHE_FILE = ".busca_cache.pkl"
CACHE_TEMPO_MAX = 3600

class IndiceOCR:
    
    def __init__(self, pasta_ocr=PASTA_OCR_LOCAL, arquivo_cache=CACHE_FILE):
        self.pasta_ocr = pasta_ocr
        self.arquivo_cache = arquivo_cache
        self.indice = {}
        self.timestamp_criacao = None
        self.carregado = False
        
    def deveria_recarregar(self):
        if not os.path.exists(self.arquivo_cache):
            return True
        
        if self.timestamp_criacao is None:
            return True
        
        tempo_decorrido = time.time() - self.timestamp_criacao
        if tempo_decorrido > CACHE_TEMPO_MAX:
            return True
        
        return False
    
    def carregar_do_disco(self):
        if os.path.exists(self.arquivo_cache):
            try:
                with open(self.arquivo_cache, 'rb') as f:
                    self.indice = pickle.load(f)
                    self.timestamp_criacao = time.time()
                    self.carregado = True
                    print(f"✅ Cache carregado ({len(self.indice)} nomes indexados)")
                    return True
            except Exception as e:
                print(f"Aviso: Não conseguiu carregar cache ({e})")
                return False
        return False
    
    def salvar_no_disco(self):
        try:
            with open(self.arquivo_cache, 'wb') as f:
                pickle.dump(self.indice, f)
                print(f"✅ Cache salvo ({len(self.indice)} nomes indexados)")
        except Exception as e:
            print(f"Aviso: Não conseguiu salvar cache ({e})")
    
    def ler_arquivo_com_encoding(self, caminho):
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'ascii']
        
        for encoding in encodings:
            try:
                with open(caminho, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue
        
        try:
            with open(caminho, 'rb') as f:
                conteudo = f.read()
                return conteudo.decode('utf-8', errors='ignore')
        except:
            return None
    
    def normalizar_texto(self, texto):
        if not texto:
            return ""
        texto = texto.lower()
        texto = re.sub(r'[^a-z0-9\s]', '', texto)
        return re.sub(r'\s+', ' ', texto).strip()
    
    def extrair_data_doe(self, nome_arquivo):
        try:
            nome_sem_ext = nome_arquivo.replace('_ocr.txt', '')
            partes = nome_sem_ext.split('.')
            if len(partes) >= 3:
                ano, mes, dia = partes[0], partes[1], partes[2]
                return f"{dia}/{mes}/{ano}"
        except:
            pass
        return None
    
    def construir_indice(self):
        if not os.path.exists(self.pasta_ocr):
            print(f"❌ Pasta '{self.pasta_ocr}' não encontrada")
            return False
        
        print(f"🔨 Construindo índice (primeira vez, pode demorar...)...")
        
        self.indice = {}
        arquivos = [f for f in os.listdir(self.pasta_ocr) if f.endswith('.txt')]
        total = len(arquivos)
        
        for i, arquivo in enumerate(arquivos):
            if (i + 1) % 500 == 0:
                print(f"  Processando {i + 1}/{total}...")
            
            caminho = os.path.join(self.pasta_ocr, arquivo)
            conteudo = self.ler_arquivo_com_encoding(caminho)
            
            if conteudo is None:
                continue
            
            conteudo_norm = self.normalizar_texto(conteudo)
            palavras = set(conteudo_norm.split())
            
            data = self.extrair_data_doe(arquivo)
            if not data:
                continue
            
            for palavra in palavras:
                if len(palavra) >= 2:
                    if palavra not in self.indice:
                        self.indice[palavra] = []
                    self.indice[palavra].append({
                        'arquivo': arquivo,
                        'data': data
                    })
        
        for palavra in self.indice:
            visto = {}
            for item in self.indice[palavra]:
                chave = f"{item['arquivo']}"
                visto[chave] = item
            self.indice[palavra] = list(visto.values())
        
        self.timestamp_criacao = time.time()
        self.carregado = True
        
        print(f"✅ Índice construído! {len(self.indice)} nomes únicos indexados")
        self.salvar_no_disco()
        return True
    
    def buscar(self, nome, cpf=None):
        nome_norm = self.normalizar_texto(nome)
        cpf_norm = re.sub(r'\D', '', cpf) if cpf else None
        
        if not nome_norm:
            return []
        
        if not self.carregado:
            if self.deveria_recarregar():
                self.carregar_do_disco()
            if not self.carregado:
                return []
        
        resultados_set = set()
        
        palavras_busca = nome_norm.split()
        
        if palavras_busca[0] in self.indice:
            candidatos = self.indice[palavras_busca[0]]
            
            if len(palavras_busca) > 1 and palavras_busca[1] in self.indice:
                candidatos_2 = set(
                    f"{item['arquivo']}" for item in self.indice[palavras_busca[1]]
                )
                candidatos = [
                    item for item in candidatos 
                    if f"{item['arquivo']}" in candidatos_2
                ]
            
            for item in candidatos:
                resultados_set.add((item['data'], item['arquivo']))
        
        if not resultados_set:
            for arquivo in os.listdir(self.pasta_ocr):
                if not arquivo.endswith('.txt'):
                    continue
                
                caminho = os.path.join(self.pasta_ocr, arquivo)
                conteudo = self.ler_arquivo_com_encoding(caminho)
                
                if conteudo is None:
                    continue
                
                conteudo_norm = self.normalizar_texto(conteudo)
                
                if nome_norm in conteudo_norm:
                    if cpf_norm and cpf_norm not in conteudo_norm:
                        continue
                    
                    data = self.extrair_data_doe(arquivo)
                    if data:
                        resultados_set.add((data, arquivo))
        
        resultados = list(resultados_set)
        resultados.sort(
            key=lambda x: datetime.strptime(x[0], '%d/%m/%Y'),
            reverse=True
        )
        
        return resultados

_indice_global = None

def inicializar_indice():
    global _indice_global
    if _indice_global is None:
        _indice_global = IndiceOCR()
        
        if not _indice_global.carregar_do_disco():
            _indice_global.construir_indice()

def buscar_local_txt_otimizado(nome, cpf=None):
    global _indice_global
    
    if _indice_global is None:
        inicializar_indice()
    
    if not _indice_global.carregado:
        print("Aviso: Índice não disponível, usando busca lenta")
        return buscar_local_txt_lenta(nome, cpf)
    
    resultados_brutos = _indice_global.buscar(nome, cpf)
    
    resultados = [
        {
            'data': data,
            'arquivo': arquivo,
            'encontrado': True
        }
        for data, arquivo in resultados_brutos
    ]
    
    return resultados

def buscar_local_txt_lenta(nome, cpf=None):
    def normalizar_texto(texto):
        if not texto:
            return ""
        texto = texto.lower()
        texto = re.sub(r'[^a-z0-9\s]', '', texto)
        return re.sub(r'\s+', ' ', texto).strip()
    
    def ler_arquivo_com_encoding(caminho):
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'ascii']
        for encoding in encodings:
            try:
                with open(caminho, 'r', encoding=encoding) as f:
                    return f.read()
            except:
                continue
        try:
            with open(caminho, 'rb') as f:
                return f.read().decode('utf-8', errors='ignore')
        except:
            return None
    
    nome_norm = normalizar_texto(nome)
    cpf_norm = re.sub(r'\D', '', cpf) if cpf else None
    resultados = []
    
    if not os.path.exists(PASTA_OCR_LOCAL):
        return resultados
    
    for arquivo in os.listdir(PASTA_OCR_LOCAL):
        if not arquivo.endswith('.txt'):
            continue
        
        caminho = os.path.join(PASTA_OCR_LOCAL, arquivo)
        conteudo = ler_arquivo_com_encoding(caminho)
        
        if conteudo is None:
            continue
        
        conteudo_norm = normalizar_texto(conteudo)
        
        if nome_norm in conteudo_norm:
            if cpf_norm and cpf_norm not in conteudo_norm:
                continue
            
            try:
                nome_sem_ext = arquivo.replace('_ocr.txt', '')
                partes = nome_sem_ext.split('.')
                if len(partes) >= 3:
                    ano, mes, dia = partes[0], partes[1], partes[2]
                    data = f"{dia}/{mes}/{ano}"
                    resultados.append({
                        'data': data,
                        'arquivo': arquivo,
                        'encontrado': True
                    })
            except:
                pass
    
    resultados.sort(
        key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y'),
        reverse=True
    )
    
    return resultados