import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import time
from threading import Thread
from datetime import datetime
from busca_otimizada import buscar_local_txt_otimizado, inicializar_indice

class EstiloUI:
    CORES = {
        'principal': '#0055A4',
        'principal_hover': '#0070D2',
        'fundo_app': '#F0F2F5',
        'fundo_card': '#FFFFFF',
        'texto_primario': '#111827',
        'texto_secundario': '#4B5563',
        'borda': '#D1D5DB',
        'borda_foco': '#0055A4',
        'sucesso': '#10B981',
        'erro': '#EF4444',
        'alerta': '#F59E0B',
        'botao_secundario': '#6B7280',
        'botao_secundario_hover': '#4B5563'
    }

    FONTES = {
        'titulo': ('Segoe UI', 18, 'bold'),
        'subtitulo': ('Segoe UI', 10),
        'label': ('Segoe UI', 9, 'bold'),
        'hint': ('Segoe UI', 8, 'italic'),
        'input': ('Segoe UI', 11),
        'botao': ('Segoe UI', 10, 'bold'),
        'resultado_header': ('Segoe UI', 11, 'bold'),
        'resultado_texto': ('Consolas', 10),
        'status': ('Segoe UI', 9)
    }

class ComponentesUI:
    @staticmethod
    def criar_card(parent):
        frame = tk.Frame(parent, bg=EstiloUI.CORES['fundo_card'], bd=1, relief=tk.SOLID)
        frame.configure(highlightbackground=EstiloUI.CORES['borda'], highlightthickness=1, bd=0)
        return frame

    @staticmethod
    def aplicar_hover_botao(botao, cor_normal, cor_hover):
        botao.bind("<Enter>", lambda e: botao.config(bg=cor_hover))
        botao.bind("<Leave>", lambda e: botao.config(bg=cor_normal))

    @staticmethod
    def aplicar_foco_entry(entry):
        entry.bind("<FocusIn>", lambda e: entry.config(bg='#F8FAFC', highlightcolor=EstiloUI.CORES['borda_foco'], highlightthickness=1))
        entry.bind("<FocusOut>", lambda e: entry.config(bg=EstiloUI.CORES['fundo_card'], highlightthickness=1, highlightbackground=EstiloUI.CORES['borda']))

class BDOEApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BDOE - Buscador de Diário Oficial (Polícia Civil)")
        self.root.geometry("1100x850")
        self.root.minsize(900, 700)
        self.root.configure(bg=EstiloUI.CORES['fundo_app'])
        
        self.indice_pronto = False
        
        self._configurar_estilos_ttk()
        self.construir_interface()
        self.iniciar_backend()

    def _configurar_estilos_ttk(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", thickness=15, background=EstiloUI.CORES['sucesso'], troughcolor=EstiloUI.CORES['borda'])

    def construir_interface(self):
        frame_header = tk.Frame(self.root, bg=EstiloUI.CORES['principal'], height=80)
        frame_header.pack(fill=tk.X, side=tk.TOP)
        frame_header.pack_propagate(False)
        
        container_header = tk.Frame(frame_header, bg=EstiloUI.CORES['principal'])
        container_header.pack(fill=tk.BOTH, expand=True, padx=30, pady=15)
        
        tk.Label(container_header, text="BDOE", font=('Segoe UI', 22, 'bold'), bg=EstiloUI.CORES['principal'], fg="#FFFFFF").pack(side=tk.LEFT)
        tk.Label(container_header, text="Buscador de Diário Oficial do Estado", font=('Segoe UI', 12), bg=EstiloUI.CORES['principal'], fg="#E5E7EB").pack(side=tk.LEFT, padx=(10, 0), pady=(8,0))
        tk.Label(container_header, text="POLÍCIA CIVIL DO PARÁ", font=('Segoe UI', 10, 'bold'), bg=EstiloUI.CORES['principal'], fg="#93C5FD").pack(side=tk.RIGHT, pady=(10,0))

        frame_status = tk.Frame(self.root, bg="#E5E7EB", height=40)
        frame_status.pack(fill=tk.X, side=tk.BOTTOM)
        frame_status.pack_propagate(False)
        
        self.lbl_status = tk.Label(frame_status, text="Inicializando sistema BDOE...", font=EstiloUI.FONTES['status'], bg="#E5E7EB", fg=EstiloUI.CORES['texto_secundario'])
        self.lbl_status.pack(side=tk.LEFT, padx=20, pady=10)
        
        self.progress_bar = ttk.Progressbar(frame_status, mode='determinate', length=200)

        main_container = tk.Frame(self.root, bg=EstiloUI.CORES['fundo_app'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        card_busca = ComponentesUI.criar_card(main_container)
        card_busca.pack(fill=tk.X, pady=(0, 20))
        
        inner_busca = tk.Frame(card_busca, bg=EstiloUI.CORES['fundo_card'])
        inner_busca.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        tk.Label(inner_busca, text="Parâmetros de Investigação", font=EstiloUI.FONTES['titulo'], bg=EstiloUI.CORES['fundo_card'], fg=EstiloUI.CORES['texto_primario']).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 15))

        tk.Label(inner_busca, text="Nome Completo do Alvo *", font=EstiloUI.FONTES['label'], bg=EstiloUI.CORES['fundo_card'], fg=EstiloUI.CORES['texto_primario']).grid(row=1, column=0, columnspan=2, sticky=tk.W)
        self.entry_nome = tk.Entry(inner_busca, font=EstiloUI.FONTES['input'], width=55, relief=tk.FLAT, highlightbackground=EstiloUI.CORES['borda'], highlightthickness=1)
        self.entry_nome.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 15), ipady=5)
        ComponentesUI.aplicar_foco_entry(self.entry_nome)
        
        tk.Label(inner_busca, text="Pressione ENTER para buscar rápido", font=EstiloUI.FONTES['hint'], bg=EstiloUI.CORES['fundo_card'], fg=EstiloUI.CORES['texto_secundario']).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 10), ipady=0)

        tk.Label(inner_busca, text="CPF (Opcional)", font=EstiloUI.FONTES['label'], bg=EstiloUI.CORES['fundo_card'], fg=EstiloUI.CORES['texto_primario']).grid(row=1, column=2, sticky=tk.W, padx=(20, 0))
        self.entry_cpf = tk.Entry(inner_busca, font=EstiloUI.FONTES['input'], width=25, relief=tk.FLAT, highlightbackground=EstiloUI.CORES['borda'], highlightthickness=1)
        self.entry_cpf.grid(row=2, column=2, sticky=tk.W, padx=(20, 0), pady=(5, 15), ipady=5)
        ComponentesUI.aplicar_foco_entry(self.entry_cpf)

        tk.Label(inner_busca, text="Filtro de Data (Opcional)", font=EstiloUI.FONTES['label'], bg=EstiloUI.CORES['fundo_card'], fg=EstiloUI.CORES['texto_primario']).grid(row=4, column=0, columnspan=4, sticky=tk.W, pady=(10, 5))
        
        frame_datas = tk.Frame(inner_busca, bg=EstiloUI.CORES['fundo_card'])
        frame_datas.grid(row=5, column=0, columnspan=4, sticky=tk.W)
        
        tk.Label(frame_datas, text="Dia:", font=EstiloUI.FONTES['subtitulo'], bg=EstiloUI.CORES['fundo_card']).pack(side=tk.LEFT)
        self.entry_dia = tk.Entry(frame_datas, font=EstiloUI.FONTES['input'], width=6, justify='center', relief=tk.FLAT, highlightbackground=EstiloUI.CORES['borda'], highlightthickness=1)
        self.entry_dia.pack(side=tk.LEFT, padx=(5, 20), ipady=4)
        ComponentesUI.aplicar_foco_entry(self.entry_dia)
        
        tk.Label(frame_datas, text="Mês:", font=EstiloUI.FONTES['subtitulo'], bg=EstiloUI.CORES['fundo_card']).pack(side=tk.LEFT)
        self.entry_mes = tk.Entry(frame_datas, font=EstiloUI.FONTES['input'], width=6, justify='center', relief=tk.FLAT, highlightbackground=EstiloUI.CORES['borda'], highlightthickness=1)
        self.entry_mes.pack(side=tk.LEFT, padx=(5, 20), ipady=4)
        ComponentesUI.aplicar_foco_entry(self.entry_mes)
        
        tk.Label(frame_datas, text="Ano (Ex: 2021):", font=EstiloUI.FONTES['subtitulo'], bg=EstiloUI.CORES['fundo_card']).pack(side=tk.LEFT)
        self.entry_ano = tk.Entry(frame_datas, font=EstiloUI.FONTES['input'], width=8, justify='center', relief=tk.FLAT, highlightbackground=EstiloUI.CORES['borda'], highlightthickness=1)
        self.entry_ano.pack(side=tk.LEFT, padx=(5, 0), ipady=4)
        ComponentesUI.aplicar_foco_entry(self.entry_ano)

        frame_botoes = tk.Frame(inner_busca, bg=EstiloUI.CORES['fundo_card'])
        frame_botoes.grid(row=6, column=0, columnspan=4, sticky=tk.W, pady=(25, 0))

        self.btn_buscar = tk.Button(frame_botoes, text="🔍 INICIAR BUSCA", font=EstiloUI.FONTES['botao'], bg=EstiloUI.CORES['principal'], fg="#FFFFFF", relief=tk.FLAT, padx=25, pady=10, cursor="hand2", command=self.iniciar_busca)
        self.btn_buscar.pack(side=tk.LEFT, padx=(0, 15))
        ComponentesUI.aplicar_hover_botao(self.btn_buscar, EstiloUI.CORES['principal'], EstiloUI.CORES['principal_hover'])

        self.btn_limpar = tk.Button(frame_botoes, text="LIMPAR DADOS", font=EstiloUI.FONTES['botao'], bg=EstiloUI.CORES['botao_secundario'], fg="#FFFFFF", relief=tk.FLAT, padx=20, pady=10, cursor="hand2", command=self.limpar_campos)
        self.btn_limpar.pack(side=tk.LEFT)
        ComponentesUI.aplicar_hover_botao(self.btn_limpar, EstiloUI.CORES['botao_secundario'], EstiloUI.CORES['botao_secundario_hover'])

        for entry in [self.entry_nome, self.entry_cpf, self.entry_dia, self.entry_mes, self.entry_ano]:
            entry.bind('<Return>', lambda e: self.iniciar_busca())

        card_resultados = ComponentesUI.criar_card(main_container)
        card_resultados.pack(fill=tk.BOTH, expand=True)
        
        header_resultado = tk.Frame(card_resultados, bg="#F9FAFB", bd=1, relief=tk.SOLID)
        header_resultado.config(highlightbackground=EstiloUI.CORES['borda'], highlightthickness=1, bd=0)
        header_resultado.pack(fill=tk.X)
        
        self.lbl_contador_resultados = tk.Label(header_resultado, text="Resultados da Busca (0)", font=EstiloUI.FONTES['resultado_header'], bg="#F9FAFB", fg=EstiloUI.CORES['texto_primario'], pady=10, padx=20)
        self.lbl_contador_resultados.pack(anchor=tk.W)

        self.text_resultado = scrolledtext.ScrolledText(card_resultados, font=EstiloUI.FONTES['resultado_texto'], bg=EstiloUI.CORES['fundo_card'], fg=EstiloUI.CORES['texto_primario'], state=tk.DISABLED, wrap=tk.WORD, relief=tk.FLAT, bd=0, padx=20, pady=15)
        self.text_resultado.pack(fill=tk.BOTH, expand=True)

    def atualizar_status(self, mensagem, cor=EstiloUI.CORES['texto_primario'], show_progress=False, progress_mode='indeterminate'):
        def _update():
            self.lbl_status.config(text=mensagem, fg=cor)
            if show_progress:
                self.progress_bar.config(mode=progress_mode)
                self.progress_bar.pack(side=tk.RIGHT, padx=20, pady=10)
                if progress_mode == 'indeterminate':
                    self.progress_bar.start(10)
            else:
                self.progress_bar.stop()
                self.progress_bar.pack_forget()
        self.root.after(0, _update)

    def callback_progresso_sqlite(self, atual, total):
        pct = (atual / total) * 100 if total > 0 else 0
        msg = f"Montando Banco de Dados Inteligente: {pct:.1f}% ({atual}/{total})"
        
        def _update_prog():
            self.lbl_status.config(text=msg, fg=EstiloUI.CORES['alerta'])
            self.progress_bar.config(mode='determinate', maximum=total, value=atual)
            self.progress_bar.pack(side=tk.RIGHT, padx=20, pady=10)
        self.root.after(0, _update_prog)

    def iniciar_backend(self):
        def _init_thread():
            try:
                self.atualizar_status("Verificando Banco de Dados...", EstiloUI.CORES['alerta'], True, 'indeterminate')
                inicializar_indice(progress_callback=self.callback_progresso_sqlite)
                self.indice_pronto = True
                self.atualizar_status("✓ BDOE Operacional. Banco de dados pronto para consultas rápidas.", EstiloUI.CORES['sucesso'], False)
                self.root.after(100, lambda: self.entry_nome.focus())
            except Exception as e:
                self.atualizar_status(f"Erro Crítico de Banco de Dados: {str(e)}", EstiloUI.CORES['erro'], False)
                self.indice_pronto = False

        Thread(target=_init_thread, daemon=True).start()

    def limpar_campos(self):
        for entry in [self.entry_nome, self.entry_cpf, self.entry_dia, self.entry_mes, self.entry_ano]:
            entry.delete(0, tk.END)
        
        self.text_resultado.config(state=tk.NORMAL)
        self.text_resultado.delete(1.0, tk.END)
        self.text_resultado.config(state=tk.DISABLED)
        
        self.lbl_contador_resultados.config(text="Resultados da Busca (0)")
        self.atualizar_status("Formulário limpo. Pronto para nova busca.", EstiloUI.CORES['texto_secundario'])
        self.entry_nome.focus()

    def iniciar_busca(self):
        if not self.indice_pronto:
            messagebox.showwarning("Atenção", "O Banco de Dados ainda está sendo inicializado.\nPor favor, aguarde o status indicar 'Operacional'.")
            return
            
        nome = self.entry_nome.get().strip()
        cpf = self.entry_cpf.get().strip()
        dia = self.entry_dia.get().strip()
        mes = self.entry_mes.get().strip()
        ano = self.entry_ano.get().strip()

        if len(nome) < 2:
            self.atualizar_status("Erro: Digite um nome com pelo menos 2 caracteres.", EstiloUI.CORES['erro'])
            self.entry_nome.focus()
            return

        self.btn_buscar.config(state=tk.DISABLED, text="BUSCANDO...")
        self.atualizar_status(f"Buscando cruzamento de dados para '{nome}'...", EstiloUI.CORES['alerta'], True, 'indeterminate')
        self.text_resultado.config(state=tk.NORMAL)
        self.text_resultado.delete(1.0, tk.END)
        self.text_resultado.config(state=tk.DISABLED)

        Thread(target=self._executar_backend_busca, args=(nome, cpf, dia, mes, ano), daemon=True).start()

    def _executar_backend_busca(self, nome, cpf, dia, mes, ano):
        try:
            inicio_timer = time.time()
            
            resultados = buscar_local_txt_otimizado(
                nome=nome, 
                cpf=cpf if cpf else None, 
                ano=ano if ano else None, 
                mes=mes if mes else None, 
                dia=dia if dia else None
            )
            
            tempo_total = time.time() - inicio_timer
            texto_formatado = self._formatar_relatorio(resultados)

            def _concluir_ui():
                self.text_resultado.config(state=tk.NORMAL)
                self.text_resultado.insert(1.0, texto_formatado)
                self.text_resultado.config(state=tk.DISABLED)
                
                self.lbl_contador_resultados.config(text=f"Resultados Encontrados ({len(resultados)})")
                
                if resultados:
                    self.atualizar_status(f"✓ Busca concluída com sucesso. Tempo de resposta: {tempo_total:.3f} segundos.", EstiloUI.CORES['sucesso'], False)
                else:
                    self.atualizar_status("Nenhuma ocorrência encontrada para os parâmetros informados.", EstiloUI.CORES['erro'], False)
                
                self.btn_buscar.config(state=tk.NORMAL, text="🔍 INICIAR BUSCA")

            self.root.after(0, _concluir_ui)

        except Exception as e:
            def _erro_ui():
                self.atualizar_status(f"Falha na busca: {str(e)}", EstiloUI.CORES['erro'], False)
                self.btn_buscar.config(state=tk.NORMAL, text="🔍 INICIAR BUSCA")
            self.root.after(0, _erro_ui)

    def _formatar_relatorio(self, resultados):
        if not resultados:
            return "\n   Nenhum registro encontrado nas bases de dados indexadas.\n\n   Dicas:\n   - Verifique a ortografia do nome.\n   - Se utilizou filtros de data (Ano/Mês/Dia), tente buscar sem eles para ampliar o escopo."
            
        relatorio = ""
        for i, res in enumerate(resultados, 1):
            data = res['data']
            arquivo = res['arquivo']
            pagina = res.get('pagina', 'Desconhecida')
            
            relatorio += f"   OCORRÊNCIA #{i:03d}\n"
            relatorio += f"   Data de Publicação : {data}\n"
            relatorio += f"   Página Detectada   : {pagina}\n"
            relatorio += f"   Arquivo Fonte      : {arquivo}\n"
            relatorio += "-" * 90 + "\n"
            
        return relatorio

if __name__ == "__main__":
    root = tk.Tk()
    
    window_width = 1100
    window_height = 850
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width / 2)
    center_y = int(screen_height/2 - window_height / 2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    app = BDOEApp(root)
    root.mainloop()