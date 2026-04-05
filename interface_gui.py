import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from threading import Thread
from busca_otimizada import buscar_local_txt_otimizado, inicializar_indice

# CONFIGURAÇÕES

JANELA_TITULO = "🔍 Busca DOE - Polícia Civil Pará"

# FUNÇÕES AUXILIARES


def formatar_resultado(resultados):
    """Formata os resultados para exibição"""
    
    if not resultados:
        return "❌ Nenhum resultado encontrado.\n\nVerifique:\n• Digitação do nome\n• Se existem arquivos em 'textos_ocr/'"
    
    texto = f"✅ Encontrados {len(resultados)} resultado(s):\n"
    texto += "=" * 80 + "\n\n"
    
    for i, resultado in enumerate(resultados, 1):
        data = resultado['data']
        arquivo = resultado['arquivo']
        
        texto += f"{i}. Data do DOE: {data}\n"
        texto += f"   Arquivo: {arquivo}\n"
        texto += "-" * 80 + "\n"
    
    return texto

# CLASSE DA INTERFACE GRÁFICA

class InterfaceBuscaDOE:
    def __init__(self, root):
        self.root = root
        self.root.title(JANELA_TITULO)
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # Cores
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.accent_color = "#0066CC"
        self.success_color = "#00CC66"
        self.error_color = "#FF6B6B"
        
        self.root.configure(bg=self.bg_color)
        
        # Estado
        self.indice_pronto = False
        
        self.criar_widgets()
        self.inicializar_indice_background()
    
    def criar_widgets(self):
        """Cria todos os widgets da interface"""
        
        # CABEÇALHO 
        frame_header = tk.Frame(self.root, bg=self.accent_color, height=60)
        frame_header.pack(fill=tk.X, padx=0, pady=0)
        frame_header.pack_propagate(False)
        
        label_header = tk.Label(
            frame_header,
            text="🔍 BUSCA DE DIÁRIO OFICIAL - POLÍCIA CIVIL",
            font=("Arial", 14, "bold"),
            bg=self.accent_color,
            fg=self.fg_color
        )
        label_header.pack(pady=15)
        
        # ENTRADA
        frame_entrada = tk.Frame(self.root, bg=self.bg_color)
        frame_entrada.pack(fill=tk.X, padx=20, pady=20)
        
        # Label e campo Nome
        tk.Label(frame_entrada, text="Nome:", font=("Arial", 10), 
                bg=self.bg_color, fg=self.fg_color).grid(row=0, column=0, sticky=tk.W, pady=10)
        self.entry_nome = tk.Entry(frame_entrada, font=("Arial", 11), width=50)
        self.entry_nome.grid(row=0, column=1, sticky=tk.W+tk.E, padx=10)
        self.entry_nome.bind('<Return>', lambda e: self.executar_busca())
        self.entry_nome.focus()
        
        # Label e campo CPF
        tk.Label(frame_entrada, text="CPF (opcional):", font=("Arial", 10), 
                bg=self.bg_color, fg=self.fg_color).grid(row=1, column=0, sticky=tk.W, pady=10)
        self.entry_cpf = tk.Entry(frame_entrada, font=("Arial", 11), width=50)
        self.entry_cpf.grid(row=1, column=1, sticky=tk.W+tk.E, padx=10)
        self.entry_cpf.bind('<Return>', lambda e: self.executar_busca())
        
        # Configurar peso das colunas
        frame_entrada.columnconfigure(1, weight=1)
        
        # FRAME DE BOTÕES
        frame_botoes = tk.Frame(self.root, bg=self.bg_color)
        frame_botoes.pack(fill=tk.X, padx=20, pady=10)
        
        self.btn_buscar = tk.Button(
            frame_botoes,
            text="🔍 Buscar",
            font=("Arial", 10, "bold"),
            bg=self.accent_color,
            fg=self.fg_color,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.executar_busca
        )
        self.btn_buscar.pack(side=tk.LEFT, padx=5)
        
        self.btn_limpar = tk.Button(
            frame_botoes,
            text="🧹 Limpar",
            font=("Arial", 10, "bold"),
            bg="#555555",
            fg=self.fg_color,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.limpar_campos
        )
        self.btn_limpar.pack(side=tk.LEFT, padx=5)
        
        self.btn_sair = tk.Button(
            frame_botoes,
            text="❌ Sair",
            font=("Arial", 10, "bold"),
            bg=self.error_color,
            fg=self.fg_color,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.root.quit
        )
        self.btn_sair.pack(side=tk.LEFT, padx=5)
        
        # FRAME DE RESULTADOS
        frame_resultado = tk.Frame(self.root, bg=self.bg_color)
        frame_resultado.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(frame_resultado, text="RESULTADOS:", font=("Arial", 11, "bold"),
                bg=self.bg_color, fg="#FFFF00").pack(anchor=tk.W, pady=(0, 5))
        
        # Text widget com scrollbar
        self.text_resultado = scrolledtext.ScrolledText(
            frame_resultado,
            font=("Courier", 9),
            bg="#0a0a0a",
            fg="#00FF00",
            height=15,
            width=100,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.text_resultado.pack(fill=tk.BOTH, expand=True)
        
        # Status
        frame_status = tk.Frame(self.root, bg=self.bg_color)
        frame_status.pack(fill=tk.X, padx=20, pady=10)
        
        self.label_status = tk.Label(
            frame_status,
            text="⏳ Carregando arquivos (primeira vez pode demorar)...",
            font=("Arial", 9),
            bg=self.bg_color,
            fg="#FFAA00"
        )
        self.label_status.pack(anchor=tk.W)
    
    def inicializar_indice_background(self):
        """Inicializa o índice em background"""
        def init():
            try:
                print("Inicializando arquivos...")
                inicializar_indice()
                self.indice_pronto = True
                self.atualizar_status(
                    "✅ Arquivos pronto! Pressione Enter ou clique em 'Buscar'",
                    "#00CC66"
                )
            except Exception as e:
                self.indice_pronto = False
                self.atualizar_status(f"⚠️ Erro ao inicializar: {str(e)}", self.error_color)
        
        thread = Thread(target=init)
        thread.daemon = True
        thread.start()
    
    def atualizar_status(self, mensagem, cor="#87CEEB"):
        """Atualiza o label de status"""
        self.label_status.config(text=mensagem, fg=cor)
        self.root.update()
    
    def limpar_campos(self):
        """Limpa todos os campos"""
        self.entry_nome.delete(0, tk.END)
        self.entry_cpf.delete(0, tk.END)
        self.text_resultado.config(state=tk.NORMAL)
        self.text_resultado.delete(1.0, tk.END)
        self.text_resultado.config(state=tk.DISABLED)
        self.label_status.config(text="Campos limpos.", fg="#87CEEB")
        self.entry_nome.focus()
    
    def executar_busca(self):
        """Executa a busca"""
        
        # Verificar se índice está pronto
        if not self.indice_pronto:
            messagebox.showwarning("Aviso", "Os arquivos ainda estão sendo inicializados.\nEspere um momento...")
            return
        
        nome = self.entry_nome.get().strip()
        cpf = self.entry_cpf.get().strip()
        
        # Validação
        if not nome:
            self.atualizar_status("⚠️ Digite um nome para buscar!", self.error_color)
            messagebox.showwarning("Aviso", "Digite um nome para buscar!")
            return
        
        if len(nome) < 2:
            self.atualizar_status("⚠️ Nome muito curto (mínimo 2 caracteres)", self.error_color)
            messagebox.showwarning("Aviso", "Nome muito curto (mínimo 2 caracteres)")
            return
        
        # Desabilitar botão e mostrar status
        self.btn_buscar.config(state=tk.DISABLED)
        self.atualizar_status("⏳ Buscando...", "#FFFF00")
        
        # Executar busca em thread separada
        thread = Thread(target=self._buscar_thread, args=(nome, cpf))
        thread.daemon = True
        thread.start()
    
    def _buscar_thread(self, nome, cpf):
        """Executa a busca em background"""
        try:
            import time
            inicio = time.time()
            
            resultados = buscar_local_txt_otimizado(nome, cpf if cpf else None)
            
            tempo = time.time() - inicio
            texto_resultado = formatar_resultado(resultados)
            
            # Atualizar interface
            self.text_resultado.config(state=tk.NORMAL)
            self.text_resultado.delete(1.0, tk.END)
            self.text_resultado.insert(1.0, texto_resultado)
            self.text_resultado.config(state=tk.DISABLED)
            
            if resultados:
                self.atualizar_status(
                    f"✅ Busca concluída! {len(resultados)} resultado(s) em {tempo:.2f}s",
                    self.success_color
                )
            else:
                self.atualizar_status("❌ Nenhum resultado encontrado", self.error_color)
        
        except Exception as e:
            self.atualizar_status(f"❌ Erro: {str(e)}", self.error_color)
            self.text_resultado.config(state=tk.NORMAL)
            self.text_resultado.delete(1.0, tk.END)
            self.text_resultado.insert(1.0, f"Erro: {str(e)}")
            self.text_resultado.config(state=tk.DISABLED)
        
        finally:
            self.btn_buscar.config(state=tk.NORMAL)

# EXECUÇÃO

if __name__ == "__main__":
    print("=" * 60)
    print("INICIANDO INTERFACE DE BUSCA DOE OTIMIZADA")
    print("=" * 60)
    
    root = tk.Tk()
    app = InterfaceBuscaDOE(root)
    root.mainloop()