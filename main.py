import tkinter as tk
from tkinter import ttk, messagebox
import math
import random
from PIL import Image, ImageTk  # para rotação do caminhão PNG


# ============================================================
#  SISTEMA COMPLETO DE GRAFOS + ANIMAÇÃO COM CAMINHÃO REAL
# ============================================================

class GraphDeliveryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Grafos - Entregas")

        self.canvas_size = 700
        self.node_radius = 20
        self.node_font_size = 12
        self.edge_weight_font_size = 9

        # --- model ---
        self.n_nodes = 0
        self.positions = {}
        self.adj = {}
        self.node_items = {}
        self.node_label_items = {}
        self.edge_items = {}
        self.edge_weight_items = {}   # mapa key->text_id para pesos desenhados
        self.selected_edge = None     # key da aresta selecionada (para destacar)
        self.current_path = None

        # Caminhão animado
        self.truck_id = None
        self.truck_image = None
        self.truck_original = None

        # Paleta "flat" / modern (cores reutilizadas pelo app)
        self.color_bg = "#2D3436"             # fundo geral (dark mode)
        self.color_node = "#3498db"           # node normal (flat blue)
        self.color_origin = "#e74c3c"         # origem (red)
        self.color_destination = "#2ecc71"    # destino (green)
        self.color_node_on_path = "#f1c40f"   # node on route (yellowish)
        self.color_edge = "#95a5a6"           # soft gray for edges
        self.color_edge_highlight = "#2ecc71" # highlight color for path edges
        self.color_selected = "#2980b9"       # selected edge (blue)
        self.label_color = "#ecf0f1"          # labels/text color (light)
        self.edge_weight_color = "#ffffff"    # peso das arestas (contraste)

        # aplicar dark mode ao root e configurar estilos ttk
        try:
            self.root.configure(bg=self.color_bg)
        except:
            pass
        style = ttk.Style(self.root)
        try:
            style.theme_use('default')
        except:
            pass
        style.configure('TLabel', background=self.color_bg, foreground=self.label_color)
        style.configure('TCheckbutton', background=self.color_bg, foreground=self.label_color)
        style.configure('TFrame', background=self.color_bg)
        style.configure('TButton', background="#3b3b3b", foreground=self.label_color)
        # tentar unificar OptionMenu/Combobox visualmente
        style.configure('TMenubutton', background=self.color_bg, foreground=self.label_color)
        style.configure('TCombobox', fieldbackground='#3d3d3d', background='#3d3d3d', foreground=self.label_color)
        style.map('TButton', background=[('active', '#4b4b4b')])
        # estilo flat para botões (usar TButton global)
        # cores para botões flat (usar em tk.Button)
        self.btn_bg = "#4a69bd"       # destaque sóbrio
        self.btn_active = "#3b59a3"
        self.btn_fg = "white"

        # usar tk.Frame para permitir bg consistente com dark mode
        main = tk.Frame(root, bg=self.color_bg, padx=10, pady=10)
        main.grid(row=0, column=0, sticky="nw")

        left = tk.Frame(main, bg=self.color_bg)
        left.grid(row=0, column=0, sticky="nw")

        right = tk.Frame(main, bg=self.color_bg)
        right.grid(row=0, column=1, padx=10, sticky="n")

        # ---------------- NODE CONTROLS ----------------
        ttk.Label(left, text="Nº de Nós:").grid(row=0, column=0)
        self.node_count_var = tk.IntVar(value=6)
        ttk.Spinbox(left, from_=2, to=50, width=5,
                    textvariable=self.node_count_var).grid(row=0, column=1)

        ttk.Label(left, text="Layout:").grid(row=0, column=2)
        self.layout_var = tk.StringVar(value="Círculo")
        ttk.OptionMenu(left, self.layout_var, "Círculo", "Círculo", "Aleatório").grid(row=0, column=3)

        self.directed_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, text="Direcionado", variable=self.directed_var).grid(row=0, column=4)

        # botão flat modern
        self._make_button(left, "Criar Nós", self.create_nodes, row=0, column=5, padx=5)

        # ---------------- EDGE CONTROLS ----------------
        ttk.Label(left, text="Aresta (u, v, w):").grid(row=1, column=0, pady=5)

        self.u_var = tk.StringVar()
        self.v_var = tk.StringVar()
        self.weight_var = tk.StringVar(value="1")

        self.u_menu = ttk.OptionMenu(left, self.u_var, "")
        self.v_menu = ttk.OptionMenu(left, self.v_var, "")
        self.u_menu.grid(row=1, column=1)
        self.v_menu.grid(row=1, column=2)
        # usar tk.Entry para permitir bg/fg personalizados (cursor, contraste)
        self.weight_entry = tk.Entry(left, width=5, textvariable=self.weight_var,
                                     bg="#3d3d3d", fg="white", insertbackground="white", relief="flat")
        self.weight_entry.grid(row=1, column=3)

        self._make_button(left, "Adicionar", self.add_edge_from_controls, row=1, column=4)

        # LISTA DE ARESTAS
        ttk.Label(left, text="Arestas:").grid(row=2, column=0, pady=5)
        # Listbox com fundo escuro / texto branco
        self.edge_listbox = tk.Listbox(left, width=28, height=8,
                                       bg="#3d3d3d", fg="white",
                                       selectbackground="#505050", selectforeground="white",
                                       highlightthickness=0, relief="flat", bd=0)
        self.edge_listbox.grid(row=3, column=0, columnspan=4)
        self._make_button(left, "Remover", self.remove_selected_edge, row=3, column=4)

        # ---------------- PATH CONTROLS ----------------
        ttk.Label(left, text="Origem:").grid(row=4, column=0)
        self.source_var = tk.StringVar()
        self.source_menu = ttk.OptionMenu(left, self.source_var, "")
        self.source_menu.grid(row=4, column=1)

        ttk.Label(left, text="Destinos:").grid(row=4, column=2, sticky="n")
        # frame escuro ao redor do destino (ttk frame já estilizado, mas usamos tk.Frame para bg consistente)
        target_frame = tk.Frame(left, bg=self.color_bg)
        target_frame.grid(row=4, column=3, sticky="w")
        # Listbox e Scrollbar em cores escuras; seleção mais contrastante (visível)
        self.target_listbox = tk.Listbox(target_frame, selectmode=tk.MULTIPLE, height=4, exportselection=False, width=6,
                                         bg="#3d3d3d", fg="white",
                                         selectbackground="#2980b9", selectforeground="white",
                                         highlightthickness=0, relief="flat", bd=0)
        # usar tk.Scrollbar para permitir ajuste de cores
        self.target_scroll = tk.Scrollbar(target_frame, orient="vertical", command=self.target_listbox.yview,
                                         bg="#3d3d3d", activebackground="#4b4b4b")
        self.target_listbox.config(yscrollcommand=self.target_scroll.set)
        self.target_listbox.grid(row=0, column=0, sticky="w")
        self.target_scroll.grid(row=0, column=1, sticky="ns")
        # manter var única para compatibilidade ocasional
        self.target_var = tk.StringVar()
        # evitar que origem e destino sejam iguais: bind do listbox e trace na origem
        self.target_listbox.bind("<<ListboxSelect>>", self.on_target_select)
        self.source_var.trace_add("write", lambda *a: self.on_source_change())

        # Ao clicar em "Menor Caminho" agora calcula E anima automaticamente
        self._make_button(left, "Menor Caminho", self.find_shortest_path, row=5, column=0, columnspan=3, pady=5)
        self._make_button(left, "Simular Falha", self.simulate_failure_and_reroute, row=5, column=3, columnspan=2)

        # Novo: botão para criar tudo aleatoriamente (nós, arestas, origem/destino)
        self._make_button(left, "Criar Aleatório (Completo)", self.create_random_complete, row=0, column=6, padx=5)

        # Velocidade da animação
        ttk.Label(left, text="Velocidade:").grid(row=6, column=0, pady=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        # usar tk.Scale para permitir bg/fg personalizados e melhor integração com o tema escuro
        self.speed_scale = tk.Scale(left, from_=0.2, to=3.0, orient="horizontal",
                                    resolution=0.01, variable=self.speed_var,
                                    bg=self.color_bg, fg=self.label_color, troughcolor="#3d3d3d",
                                    highlightthickness=0, bd=0, length=180)
        self.speed_scale.grid(row=6, column=1, columnspan=3, sticky="we")

        # NOTE: removido o botão "Animar Caminhão" — animação agora ocorre ao calcular o menor caminho.

        # ---------------- LEGEND E EXPLICAÇÃO ----------------
        # legenda compacta (ícones menores, labels menores para economizar espaço)
        legend = tk.Frame(left, bg=self.color_bg, padx=4, pady=6)
        legend.grid(row=7, column=0, columnspan=6, sticky="w")
        tk.Label(legend, text="Legenda:", bg=self.color_bg, fg=self.label_color,
                 font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w")
        # separar itens para evitar sobreposição
        row = 1
        def add_legend_item(color, text):
            nonlocal row
            # ícone menor e label compacto
            c = tk.Canvas(legend, width=14, height=14, highlightthickness=0, bg=self.color_bg)
            c.grid(row=row, column=0, sticky="w", padx=(2,6))
            c.create_oval(2,2,12,12, fill=color, outline=color)
            tk.Label(legend, text=text, bg=self.color_bg, fg=self.label_color,
                     font=("Arial", 9)).grid(row=row, column=1, sticky="w")
            row += 1
        add_legend_item(self.color_origin, "Origem (vermelho)")
        add_legend_item(self.color_destination, "Destino (verde)")
        add_legend_item(self.color_node_on_path, "Nó no caminho")
         # aresta do caminho
        c2 = tk.Canvas(legend, width=40, height=18, highlightthickness=0, bg=self.color_bg)
        c2.grid(row=row, column=0, sticky="w", padx=(2,6))
        c2.create_line(2,9,38,9, fill=self.color_edge_highlight, width=4)
        tk.Label(legend, text="Aresta do caminho", bg=self.color_bg, fg=self.label_color,
                 font=("Arial", 9)).grid(row=row, column=1, sticky="w")
        row += 1

        # Explicação do checkbox "Direcionado"
        ttk.Label(left, text="(Direcionado: arestas u→v quando marcado)").grid(row=8, column=0, columnspan=5, sticky="w", pady=(5,0))

        # ---------------- CANVAS ----------------
        # Dark background canvas (modern look)
        self.canvas = tk.Canvas(right, width=self.canvas_size, height=self.canvas_size, bg=self.color_bg, highlightthickness=0)
        self.canvas.pack()
        # estado para arrastar nós
        self.drag_data = {"item": None}
        # estado para criar aresta com Ctrl+clique (primeiro nó)
        self.edge_creation_start = None
        # Bind para eventos do canvas: clique, arrastar e soltar
        self.canvas.bind("<Button-1>", self.on_canvas_button1)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Dica discreta abaixo do canvas
        self.tip_label = tk.Label(right,
                                  text="DICA: Arraste os nós para organizar. Segure CTRL + Clique Esquerdo do mouse em um nó e em outro para criar conexões.",
                                  bg=self.color_bg, fg="#b2bec3", font=("Arial", 9))
        self.tip_label.pack(pady=(8,0))

        self.status_var = tk.StringVar(value="Pronto")
        ttk.Label(root, textvariable=self.status_var).grid(row=1, column=0)

        # Carregar imagem PNG do caminhão
        try:
            # carregar e forçar canal alfa
            img = Image.open("truck.gif").convert("RGBA")
            # tornar transparente a cor do pixel (0,0) para remover fundo sólido (MakeTransparent equivalente)
            try:
                bg_col = img.getpixel((0, 0))[:3]
                datas = []
                for px in img.getdata():
                    if px[:3] == bg_col:
                        datas.append((255, 255, 255, 0))
                    else:
                        datas.append(px)
                img.putdata(datas)
            except Exception:
                pass
            self.truck_original = img
        except Exception:
            messagebox.showwarning("Aviso", "truck.gif não encontrado ou inválido. Usando placeholder transparente.")
            self.truck_original = Image.new("RGBA", (60, 30), (0, 0, 0, 0))

        self.create_nodes()

    # ============================================================
    # CRIAÇÃO DE NÓS
    # ============================================================

    def create_nodes(self):
        self.clear_graph()

        n = self.node_count_var.get()
        self.n_nodes = n

        # ajustar escala antes de gerar layout e desenhar nós
        self._adjust_scale()
        
        for i in range(n):
            self.adj[i] = {}

        if self.layout_var.get() == "Círculo":
            self.generate_circle_layout()
        else:
            self.generate_random_layout()

        for i in range(n):
            x, y = self.positions[i]
            self.draw_node(i, x, y)

        self.update_menus()
        self.status_var.set("Nós criados.")

    def clear_graph(self):
        self.canvas.delete("all")
        self.positions.clear()
        self.adj.clear()
        self.node_items.clear()
        self.node_label_items.clear()
        self.edge_items.clear()
        self.edge_weight_items.clear()
        self.current_path = None

        if self.truck_id:
            self.canvas.delete(self.truck_id)
            self.truck_id = None

    def generate_circle_layout(self):
        R = self.canvas_size / 2 - 60
        cx = cy = self.canvas_size / 2

        for i in range(self.n_nodes):
            ang = 2 * math.pi * i / self.n_nodes
            x = cx + R * math.cos(ang)
            y = cy + R * math.sin(ang)
            self.positions[i] = (x, y)

    def generate_random_layout(self):
        # gera posições com tentativa de espaçamento mínimo para evitar sobreposição das labels
        n = self.n_nodes
        # min_dist adaptado ao tamanho do nó (evita números encostados)
        min_dist = max(20, int(self.node_radius * 4), int(160 / max(6, n)))
        positions = []
        attempts = 0
        for i in range(n):
            placed = False
            for _ in range(200):
                x = random.randint(40, self.canvas_size - 40)
                y = random.randint(40, self.canvas_size - 40)
                ok = True
                for (ox, oy) in positions:
                    if math.hypot(ox - x, oy - y) < min_dist:
                        ok = False
                        break
                if ok:
                    positions.append((x, y))
                    placed = True
                    break
            if not placed:
                # fallback: aceita posição mesmo assim
                positions.append((random.randint(40, self.canvas_size - 40), random.randint(40, self.canvas_size - 40)))
            attempts += 1
        for i, pos in enumerate(positions):
            self.positions[i] = pos

    def _adjust_scale(self):
        # escala contínua baseada na área disponível por nó (valores aumentados para maior legibilidade)
        # diameter ~ k * sqrt(area_per_node); aumentamos k e limites para evitar nós muito pequenos
        n = max(1, self.n_nodes)
        effective = max(10, self.canvas_size - 80)
        area_per_node = (effective * effective) / n
        k = 0.20  # aumentado de 0.12 para deixar nós maiores
        # limites maiores: min diâmetro 20, max diâmetro 72
        diameter = int(max(20, min(72, k * math.sqrt(area_per_node))))
        self.node_radius = max(10, diameter // 2)
        self.node_font_size = max(9, int(self.node_radius * 0.7))
        self.edge_weight_font_size = max(8, int(self.node_radius * 0.45))
        # atualizar gráficos existentes (se houver) para refletir nova escala
        try:
            self._update_node_graphics()
            # redesenhar arestas para reposicionar pesos conforme novo centro
            self.redraw_edges()
        except Exception:
            pass

    def _update_node_graphics(self):
        # atualiza posições/fonte/raio dos nós já desenhados sem recriar dados
        for i, oval_id in list(self.node_items.items()):
            if i not in self.positions:
                continue
            x, y = self.positions[i]
            r = self.node_radius
            try:
                # atualizar oval
                self.canvas.coords(oval_id, x - r, y - r, x + r, y + r)
                # atualizar texto: posição e fonte
                txt_id = self.node_label_items.get(i)
                if txt_id:
                    self.canvas.coords(txt_id, x, y)
                    self.canvas.itemconfig(txt_id, font=("Arial", self.node_font_size, "bold"))
            except Exception:
                pass

    def draw_node(self, i, x, y):
        r = self.node_radius
        # flat node: sem borda 3D, preenchimento plano. labels em cor clara.
        node_id = self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=self.color_node, outline=self.color_node)
        label_id = self.canvas.create_text(x, y, text=str(i), font=("Arial", self.node_font_size, "bold"), fill=self.label_color)
        self.node_items[i] = node_id
        self.node_label_items[i] = label_id

    # ============================================================
    # MENUS E ARESTAS
    # ============================================================

    def update_menus(self):
        nodes = [str(i) for i in range(self.n_nodes)]

        for menu, var in [(self.u_menu, self.u_var),
                          (self.v_menu, self.v_var),
                          (self.source_menu, self.source_var)]:

            menu["menu"].delete(0, "end")
            for n in nodes:
                menu["menu"].add_command(label=n, command=lambda v=n, vv=var: vv.set(v))

            if nodes:
                var.set(nodes[0])
        # popular listbox de destinos (multi-select)
        try:
            self.target_listbox.delete(0, tk.END)
            for n in nodes:
                self.target_listbox.insert(tk.END, n)
        except Exception:
            pass
        # garantir origem padrão
        if nodes:
            self.source_var.set(nodes[0])
        # ajustar escala visual conforme número de nós
        self._adjust_scale()
        self.update_node_colors()

    def add_edge_from_controls(self):
        try:
            u = int(self.u_var.get())
            v = int(self.v_var.get())
            w = float(self.weight_var.get())
        except:
            messagebox.showerror("Erro", "Dados inválidos.")
            return

        self.add_edge(u, v, w)
        self.update_edge_list()

    def add_edge(self, u, v, w):
        # Não permitir arestas que liguem um nó a si mesmo (self-loop)
        if u == v:
            messagebox.showerror("Erro", "Arestas que ligam um nó a si mesmo não são permitidas.")
            return

        directed = self.directed_var.get()
        self.adj[u][v] = w
        if not directed:
            self.adj[v][u] = w
        self.draw_edge(u, v)

    def draw_edge(self, u, v):
        x1, y1 = self.positions[u]
        x2, y2 = self.positions[v]

        # Use chave consistente para armazenamento: para grafos não direcionados usamos par ordenado menor->maior
        key = (u, v) if self.directed_var.get() else tuple(sorted((u, v)))

        if key in self.edge_items:
            # apagar linha e texto de peso existentes
            try:
                self.canvas.delete(self.edge_items[key])
            except:
                pass
            if key in self.edge_weight_items:
                try:
                    self.canvas.delete(self.edge_weight_items[key])
                except:
                    pass

        # se o grafo estiver marcado como direcionado, desenhar seta
        if self.directed_var.get():
            line = self.canvas.create_line(x1, y1, x2, y2, width=2, fill=self.color_edge, arrow=tk.LAST, smooth=True)
        else:
            line = self.canvas.create_line(x1, y1, x2, y2, width=2, fill=self.color_edge)
        self.edge_items[key] = line

        # adicionar label com peso no meio da aresta
        # obter peso (usar self.adj[u][v] já que estamos iterando nessa direção)
        w = self.adj.get(u, {}).get(v, None)
        if w is None:
            # tenta o contrário (caso grafo não direcionado e armazenado no outro sentido)
            w = self.adj.get(v, {}).get(u, "")
        try:
            midx = (x1 + x2) / 2
            midy = (y1 + y2) / 2
            # peso das arestas em cor clara para alto contraste (acessibilidade)
            txt = self.canvas.create_text(midx, midy, text=str(w), fill=self.edge_weight_color,
                                          font=("Arial", max(7, self.edge_weight_font_size), "bold"))
            self.edge_weight_items[key] = txt
        except Exception:
            pass

    def update_edge_list(self):
        self.edge_listbox.delete(0, tk.END)
        seen = set()

        for u in self.adj:
            for v in self.adj[u]:
                key = tuple(sorted((u, v)))
                if key in seen and not self.directed_var.get():
                    continue
                seen.add(key)
                self.edge_listbox.insert(tk.END, f"{u} - {v} : {self.adj[u][v]}")
        # bind seleção (após atualizar)
        self.edge_listbox.bind("<<ListboxSelect>>", self.on_edge_list_select)

    def highlight_single_edge(self, key):
        """Destaca somente a aresta `key` e restaura todas as outras ao estilo padrão."""
        # resetar todas as arestas/textos
        for k, line_id in self.edge_items.items():
            try:
                self.canvas.itemconfig(line_id, fill=self.color_edge, width=2)
            except:
                pass
            txt_id = self.edge_weight_items.get(k)
            if txt_id:
                try:
                    self.canvas.itemconfig(txt_id, fill=self.label_color)
                except:
                    pass

        # aplicar destaque apenas na aresta selecionada
        if key in self.edge_items:
            try:
                self.canvas.itemconfig(self.edge_items[key], fill=self.color_selected, width=4)
            except:
                pass
        if key in self.edge_weight_items:
            try:
                self.canvas.itemconfig(self.edge_weight_items[key], fill=self.color_selected)
            except:
                pass

        self.selected_edge = key

        # sincronizar seleção na Listbox (se existir)
        try:
            entries = self.edge_listbox.get(0, tk.END)
            ukey, vkey = key if isinstance(key, tuple) else (None, None)
            target = None
            for i, txt in enumerate(entries):
                left = txt.split(":")[0].strip()
                if left == f"{ukey} - {vkey}" or left == f"{vkey} - {ukey}":
                    target = i
                    break
            if target is not None:
                self.edge_listbox.selection_clear(0, tk.END)
                self.edge_listbox.selection_set(target)
                self.edge_listbox.see(target)
        except Exception:
            pass

    # agora handler mínimo que usa highlight_single_edge
    def on_edge_list_select(self, event):
        sel = event.widget.curselection()
        if not sel:
            return
        text = event.widget.get(sel[0])
        u, v = text.split(":")[0].split("-")
        u = int(u.strip()); v = int(v.strip())
        key = (u, v) if self.directed_var.get() else tuple(sorted((u, v)))
        self.highlight_single_edge(key)

    def remove_selected_edge(self):
        sel = self.edge_listbox.curselection()
        if not sel:
            return

        text = self.edge_listbox.get(sel[0])
        u, v = text.split(":")[0].split("-")
        u = int(u.strip())
        v = int(v.strip())

        directed = self.directed_var.get()

        if v in self.adj[u]:
            del self.adj[u][v]
        if not directed and u in self.adj[v]:
            del self.adj[v][u]

        # limpar seleção guardada caso seja a aresta removida
        key_candidate = (u, v) if directed else tuple(sorted((u, v)))
        if self.selected_edge == key_candidate:
            self.selected_edge = None
        self.redraw_edges()
        self.update_edge_list()

    def redraw_edges(self):
        # apagar linhas e textos de pesos existentes
        for line in self.edge_items.values():
            self.canvas.delete(line)
        for txt in self.edge_weight_items.values():
            self.canvas.delete(txt)
        self.edge_items.clear()
        self.edge_weight_items.clear()

        for u in self.adj:
            for v in self.adj[u]:
                if not self.directed_var.get() and v < u:
                    continue
                self.draw_edge(u, v)

    def update_node_colors(self):
        # colore todos os nós com a cor padrão, depois aplica origem/destinos e mantém caminho se existir
        for n, oval in self.node_items.items():
            # reset fill/outline
            self.canvas.itemconfig(oval, fill=self.color_node, outline=self.color_node, width=1)
        # origem
        try:
            s = int(self.source_var.get())
            if s in self.node_items:
                self.canvas.itemconfig(self.node_items[s], fill=self.color_origin, outline=self.label_color, width=2)
        except Exception:
            pass
        # destinos (multi)
        try:
            sels = self.target_listbox.curselection()
            for i in sels:
                d = int(self.target_listbox.get(i))
                if d in self.node_items and (not (hasattr(self, 'source_var') and str(d) == self.source_var.get())):
                    # destacar destino com contorno para ficar mais visível
                    self.canvas.itemconfig(self.node_items[d], fill=self.color_destination, outline=self.label_color, width=2)
        except Exception:
            pass
        # se existe nodo marcado como inicio de criação de aresta, mantê-lo destacado
        try:
            if self.edge_creation_start is not None and self.edge_creation_start in self.node_items:
                oid = self.node_items[self.edge_creation_start]
                self.canvas.itemconfig(oid, outline=self.color_selected, width=3)
        except Exception:
            pass
        # se existe caminho atual, highlight por cima
        if self.current_path:
            for n in self.current_path:
                if n in self.node_items:
                    self.canvas.itemconfig(self.node_items[n], fill=self.color_node_on_path)
            if self.current_path:
                self.canvas.itemconfig(self.node_items[self.current_path[0]], fill=self.color_origin)
                self.canvas.itemconfig(self.node_items[self.current_path[-1]], fill=self.color_destination)

    def on_source_change(self, *args):
        # quando origem muda, remover destino igual (se selecionado) e atualizar cores
        try:
            s = int(self.source_var.get())
        except Exception:
            return
        # remover s das seleções de destino
        try:
            sels = list(self.target_listbox.curselection())
            for i in sels:
                val = int(self.target_listbox.get(i))
                if val == s:
                    self.target_listbox.selection_clear(i)
            # atualizar cores
            self.update_node_colors()
        except Exception:
            pass

    def on_target_select(self, event):
        # garante que origem não seja selecionada como destino
        try:
            s = int(self.source_var.get())
        except Exception:
            s = None
        sels = list(self.target_listbox.curselection())
        for i in sels:
            try:
                val = int(self.target_listbox.get(i))
                if s is not None and val == s:
                    # desmarcar e avisar brevemente
                    self.target_listbox.selection_clear(i)
                    # não desprezível: mostrar mensagem breve (não modal)
                    self.status_var.set("Origem não pode ser também destino; seleção removida.")
                    self.root.after(1500, lambda: self.status_var.set("Pronto"))
            except Exception:
                pass
        self.update_node_colors()

    # ============================================================
    # DIJKSTRA
    # ============================================================

    def dijkstra(self, src):
        """Dijkstra simples (O(n^2)).
        Retorna (dist, prev) onde dist[n] é a distância mínima de src a n e prev permite reconstruir caminhos."""
        INF = float("inf")
        dist = {node: INF for node in self.adj.keys()}
        dist[src] = 0
        prev = {}
        visited = set()

        while True:
            # escolher nodo não visitado com menor distância
            u = None
            u_dist = INF
            for node, d in dist.items():
                if node not in visited and d < u_dist:
                    u = node
                    u_dist = d
            if u is None:
                break
            visited.add(u)

            for v, w in self.adj[u].items():
                if v in visited:
                    continue
                nd = dist[u] + w
                if nd < dist[v]:
                    dist[v] = nd
                    prev[v] = u

        return dist, prev

    def find_shortest_path(self):
        try:
            src = int(self.source_var.get())
        except:
            return

        # ler destinos selecionados (lista). Se vazio, tenta usar target_var como fallback (compatibilidade)
        dests = []
        try:
            sels = self.target_listbox.curselection()
            for i in sels:
                dests.append(int(self.target_listbox.get(i)))
        except Exception:
            dests = []

        if not dests:
            # fallback compatível com uso antigo (OptionMenu)
            try:
                tgt = int(self.target_var.get())
                dests = [tgt]
            except:
                messagebox.showerror("Erro", "Selecione pelo menos um destino.")
                return
        # percorrer destinos na ordem selecionada: calcular caminho sequencial src->d1, d1->d2, ...
        total_path = []
        total_dist = 0.0
        cur_start = src
        for dest in dests:
            dist, prev = self.dijkstra(cur_start)
            if dest not in dist or dist[dest] == float("inf"):
                messagebox.showerror("Erro", f"Destino {dest} não alcançável a partir de {cur_start}.")
                return
            # reconstruir segmento
            seg = []
            c = dest
            while c != cur_start:
                seg.append(c)
                c = prev.get(c)
                if c is None:
                    messagebox.showerror("Erro", "Erro ao reconstruir caminho.")
                    return
            seg.append(cur_start)
            seg.reverse()
            # concatenar sem duplicar o nó de ligação
            if total_path:
                # remover último nó pois será igual ao primeiro de seg
                if total_path[-1] == seg[0]:
                    total_path.pop()
            total_path.extend(seg)
            total_dist += dist[dest]
            cur_start = dest

        self.current_path = total_path
        self.highlight_path(total_path)
        # animar
        self.animate_route()
        self.status_var.set(f"Caminho calculado (dist total={total_dist:.2f}).")
        # manter seleção visual (se houver)
        if self.selected_edge:
            self.highlight_selected_edge(self.selected_edge)

    # ============================================================
    # DESTACAR CAMINHO
    # ============================================================

    def highlight_path(self, path):
        self.clear_highlight()

        directed = self.directed_var.get()

        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            key = (u, v) if directed else tuple(sorted((u, v)))

            if key in self.edge_items:
                self.canvas.itemconfig(self.edge_items[key], fill=self.color_edge_highlight, width=4)

        for n in path:
            self.canvas.itemconfig(self.node_items[n], fill=self.color_node_on_path)
            # labels remain readable in light color
            lid = self.node_label_items.get(n)
            if lid:
                self.canvas.itemconfig(lid, fill=self.label_color)

        self.canvas.itemconfig(self.node_items[path[0]], fill=self.color_origin)
        self.canvas.itemconfig(self.node_items[path[-1]], fill=self.color_destination)
        # ensure origin/dest labels visible
        try:
            self.canvas.itemconfig(self.node_label_items[path[0]], fill=self.label_color)
            self.canvas.itemconfig(self.node_label_items[path[-1]], fill=self.label_color)
        except Exception:
            pass

    def clear_highlight(self):
        for k, line in self.edge_items.items():
            self.canvas.itemconfig(line, fill=self.color_edge, width=2)

        for _, oval in self.node_items.items():
            self.canvas.itemconfig(oval, fill=self.color_node)
        # ensure labels use light color
        for _, tid in self.node_label_items.items():
            try:
                self.canvas.itemconfig(tid, fill=self.label_color)
            except:
                pass

    # ============================================================
    # FALHA E ROTA ALTERNATIVA
    # ============================================================

    def simulate_failure_and_reroute(self):
        if not self.current_path or len(self.current_path) < 2:
            messagebox.showerror("Erro", "Calcule primeiro o caminho.")
            return

        idx = random.randint(0, len(self.current_path)-2)
        u = self.current_path[idx]
        v = self.current_path[idx+1]

        directed = self.directed_var.get()

        removed = False
        if v in self.adj[u]:
            del self.adj[u][v]
            removed = True
        if not directed and u in self.adj.get(v, {}):
            del self.adj[v][u]

        if removed:
            self.status_var.set(f"Aresta {u}-{v} removida.")
            self.redraw_edges()

        # recalcula e anima automaticamente
        self.find_shortest_path()

    # ============================================================
    # ANIMAÇÃO DO CAMINHÃO
    # ============================================================

    def animate_route(self):
        if not self.current_path:
            messagebox.showerror("Erro", "Nenhuma rota para animar.")
            return

        # Remover caminhão antigo
        if self.truck_id:
            self.canvas.delete(self.truck_id)

        # Ponto inicial (centrado)
        x, y = self.positions[self.current_path[0]]

        # Criar caminhão
        self.truck_image = ImageTk.PhotoImage(self.truck_original)
        self.truck_id = self.canvas.create_image(x, y, image=self.truck_image, anchor="center")

        self.animate_segment(0)

    def animate_segment(self, index):
        if index >= len(self.current_path)-1:
            self.status_var.set("Entrega concluída!")
            return

        u = self.current_path[index]
        v = self.current_path[index+1]

        x1, y1 = self.positions[u]
        x2, y2 = self.positions[v]

        # ângulo de rotação
        dx = x2 - x1
        dy = y2 - y1
        ang = math.degrees(math.atan2(dy, dx))

        # Rotaciona a imagem
        rotated = self.truck_original.rotate(-ang, expand=True)
        self.truck_image = ImageTk.PhotoImage(rotated)
        self.canvas.itemconfig(self.truck_id, image=self.truck_image)

        steps = int(35 / self.speed_var.get())  # muda recuperação
        delay = int(18 / self.speed_var.get())

        self.animate_move(x1, y1, x2, y2, steps, delay,
                          callback=lambda: self.animate_segment(index+1))

    def animate_move(self, x1, y1, x2, y2, steps, delay, callback):
        # proteger contra passos inválidos / ausência do caminhão
        if steps <= 0:
            callback()
            return
        if not self.truck_id:
            callback()
            return

        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps

        def step(i=0):
            # item pode ter sido removido durante animação
            if not self.truck_id:
                callback()
                return
            if i >= steps:
                # garantir posição final exata
                try:
                    self.canvas.coords(self.truck_id, x2, y2)
                except:
                    pass
                callback()
                return

            # ler posição atual e aplicar deslocamento incremental
            try:
                coords = self.canvas.coords(self.truck_id)
                if coords and len(coords) >= 2:
                    cx, cy = coords[0], coords[1]
                    self.canvas.coords(self.truck_id, cx + dx, cy + dy)
                else:
                    # fallback: definir diretamente em função do passo
                    newx = x1 + dx * (i + 1)
                    newy = y1 + dy * (i + 1)
                    self.canvas.coords(self.truck_id, newx, newy)
            except Exception:
                # em caso de erro com coords, avançar sem travar
                pass

            self.canvas.after(delay, lambda: step(i+1))

        step()

    def _make_button(self, parent, text, cmd, **grid_opts):
        """Cria um tk.Button flat com hover e aplica grid usando grid_opts."""
        b = tk.Button(parent, text=text, command=cmd,
                      bg=getattr(self, "btn_bg", "#4a69bd"),
                      fg=getattr(self, "btn_fg", "white"),
                      activebackground=getattr(self, "btn_active", "#3b59a3"),
                      activeforeground=getattr(self, "btn_fg", "white"),
                      relief="flat", bd=0, highlightthickness=0)
        def on_enter(e):
            try:
                b.configure(bg=getattr(self, "btn_active", "#3b59a3"))
            except:
                pass
        def on_leave(e):
            try:
                b.configure(bg=getattr(self, "btn_bg", "#4a69bd"))
            except:
                pass
        b.bind("<Enter>", on_enter)
        b.bind("<Leave>", on_leave)
        # aplicar grid se fornecido
        if grid_opts:
            b.grid(**grid_opts)
        return b

    # Novo: cria grafo aleatório conectado, com arestas e define origem/destino automaticamente
    def create_random_complete(self):
        # criar nós com layout aleatório
        n = self.node_count_var.get()
        self.clear_graph()
        self.n_nodes = n
        for i in range(n):
            self.adj[i] = {}
        # ajustar escala antes de gerar layout/descrições
        self._adjust_scale()
        self.generate_random_layout()
        for i in range(n):
            x, y = self.positions[i]
            self.draw_node(i, x, y)

        # garantir conectividade: criar uma árvore geradora aleatória
        for i in range(1, n):
            j = random.randint(0, i-1)
            w = round(random.uniform(1.0, 10.0), 1)
            # adicionar aresta em ambos sentidos para garantir conectividade (se não direcionado)
            self.adj[i][j] = w
            if not self.directed_var.get():
                self.adj[j][i] = w

        # adicionar algumas arestas extras aleatórias
        extra_prob = 0.25
        for u in range(n):
            for v in range(u+1, n):
                if random.random() < extra_prob:
                    w = round(random.uniform(1.0, 10.0), 1)
                    self.adj[u][v] = w
                    if not self.directed_var.get():
                        self.adj[v][u] = w

        # desenhar arestas
        self.redraw_edges()
        self.update_edge_list()
        self.update_menus()

        # escolher origem e destino distintos
        if n >= 2:
            s = random.randint(0, n-1)
            t = s
            while t == s:
                t = random.randint(0, n-1)
            self.source_var.set(str(s))
            self.target_var.set(str(t))

            # NOTA: não iniciar animação automática aqui.
            self.status_var.set("Grafo aleatório criado. Clique em 'Menor Caminho' para iniciar.")
        # atualizar cores após criação
        self.update_node_colors()

    def on_canvas_click(self, event):
        # encontra a aresta mais próxima do clique e a destaca
        best = None
        bestd = float("inf")
        px, py = event.x, event.y
        for key in list(self.edge_items.keys()):
            # key pode ser (u,v) se direcionado, ou tuple(sorted((u,v))) se não
            try:
                u, v = key
            except Exception:
                continue
            x1, y1 = self.positions.get(u, (None, None))
            x2, y2 = self.positions.get(v, (None, None))
            if x1 is None or x2 is None:
                continue
            d = self._point_segment_distance(px, py, x1, y1, x2, y2)
            if d < bestd:
                bestd = d
                best = key
        # tolerância em pixels para evitar selecionar por engano
        if best is not None and bestd <= 10:
            # destacar apenas a aresta clicada
            self.highlight_single_edge(best)

    def _point_segment_distance(self, px, py, x1, y1, x2, y2):
        # distância do ponto (px,py) ao segmento (x1,y1)-(x2,y2)
        vx = x2 - x1
        vy = y2 - y1
        wx = px - x1
        wy = py - y1
        vv = vx*vx + vy*vy
        if vv == 0:
            return math.hypot(px - x1, py - y1)
        t = (vx*wx + vy*wy) / vv
        t = max(0.0, min(1.0, t))
        cx = x1 + t*vx
        cy = y1 + t*vy
        return math.hypot(px - cx, py - cy)

    # ---------------------------
    # Drag & Drop dos nós no Canvas
    # ---------------------------
    def on_canvas_button1(self, event):
        """Mouse down:
        - Se Ctrl pressionado: iniciar/confirmar criação de aresta (primeiro/segundo nó).
        - Caso contrário: se clicou em nó inicia arrasto; senão tenta selecionar aresta.
        """
        # procurar nó clicado (verifica pontos internos usando coords dos ovais)
        found = None
        for node, oval_id in self.node_items.items():
            try:
                x1, y1, x2, y2 = self.canvas.coords(oval_id)
            except Exception:
                continue
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            r = (x2 - x1) / 2
            if math.hypot(event.x - cx, event.y - cy) <= r:
                found = node
                break

        # detectar Ctrl (bit 0x4); tentar ambos métodos de máscara por compatibilidade
        ctrl = (event.state & 0x4) != 0 or (event.state & 0x0004) != 0
        if ctrl:
            # Ctrl+click para criar aresta: primeiro Ctrl-click define início, segundo cria aresta
            if found is None:
                # clicar fora cancela início
                if self.edge_creation_start is not None:
                    # reset visual
                    try:
                        oid = self.node_items.get(self.edge_creation_start)
                        if oid:
                            self.canvas.itemconfig(oid, outline=self.color_node, width=1)
                    except:
                        pass
                    self.edge_creation_start = None
                return

            if self.edge_creation_start is None:
                # marcar primeiro nó
                self.edge_creation_start = found
                # destacar visualmente
                try:
                    oid = self.node_items[found]
                    self.canvas.itemconfig(oid, outline=self.color_selected, width=3)
                except:
                    pass
                self.status_var.set(f"Selecionado nó {found} como início da aresta (Ctrl+click no segundo nó).")
                return
            else:
                # segundo nó: criar aresta entre edge_creation_start e found (se diferente)
                a = self.edge_creation_start
                b = found
                if a != b:
                    try:
                        w = float(self.weight_var.get())
                    except:
                        w = 1.0
                    # usar add_edge (isso também desenha)
                    self.add_edge(a, b, w)
                    self.update_edge_list()
                    self.status_var.set(f"Aresta criada: {a} - {b} (peso={w})")
                # resetar destaque do nó inicial
                try:
                    oid = self.node_items.get(self.edge_creation_start)
                    if oid:
                        self.canvas.itemconfig(oid, outline=self.color_node, width=1)
                except:
                    pass
                self.edge_creation_start = None
                return

        if found is not None:
            # iniciar arrasto
            self.drag_data["item"] = found
            # opcional: armazenar offset se quiser fixar ponto de clique relativo ao centro
            self.drag_data["offset_x"] = event.x - cx
            self.drag_data["offset_y"] = event.y - cy
        else:
            # não clicou em nó: comport. anterior (seleção de aresta)
            try:
                self.on_canvas_click(event)
            except Exception:
                pass

    def on_canvas_drag(self, event):
        """Ao arrastar (B1-Motion):
        - Atualiza posição do nó em self.positions.
        - Move o oval/texto do nó e atualiza arestas/pesos conectados chamando update_all_edges_positions.
        """
        node = self.drag_data.get("item")
        if node is None:
            return
        # nova posição centrada no mouse (usar offset para manter posição relativa)
        ox = self.drag_data.get("offset_x", 0)
        oy = self.drag_data.get("offset_y", 0)
        newx = event.x - ox
        newy = event.y - oy
        # limitar dentro do canvas (opcional)
        margin = self.node_radius + 4
        newx = max(margin, min(self.canvas_size - margin, newx))
        newy = max(margin, min(self.canvas_size - margin, newy))

        # atualizar modelo
        self.positions[node] = (newx, newy)
        # atualizar oval e label
        oval_id = self.node_items.get(node)
        txt_id = self.node_label_items.get(node)
        r = self.node_radius
        try:
            if oval_id:
                self.canvas.coords(oval_id, newx - r, newy - r, newx + r, newy + r)
            if txt_id:
                self.canvas.coords(txt_id, newx, newy)
        except Exception:
            pass

        # atualizar todas as arestas/pesos conectados (simples e robusto)
        self.update_all_edges_positions()

    def on_canvas_release(self, event):
        """Mouse up: finaliza arrasto."""
        self.drag_data["item"] = None
        # remover offsets
        self.drag_data.pop("offset_x", None)
        self.drag_data.pop("offset_y", None)

    def update_all_edges_positions(self):
        """Recalcula coordenadas de linhas (ou loops) e textos de peso para acompanhar posições atualizadas dos nós."""
        try:
            for key, line_id in list(self.edge_items.items()):
                # obter nós u,v a partir da key (key foi (u,v) ou tuple(sorted))
                try:
                    u, v = key
                except Exception:
                    continue
                p1 = self.positions.get(u)
                p2 = self.positions.get(v)
                if not p1 or not p2:
                    continue
                x1, y1 = p1
                x2, y2 = p2
                # atualizar linha
                try:
                    self.canvas.coords(line_id, x1, y1, x2, y2)
                except Exception:
                    pass
                # atualizar texto do peso (se existir)
                txt_id = self.edge_weight_items.get(key)
                if txt_id:
                    try:
                        midx = (x1 + x2) / 2
                        midy = (y1 + y2) / 2
                        self.canvas.coords(txt_id, midx, midy)
                    except Exception:
                        pass
        except Exception:
            # segurança: ignorar erros durante movimento para não travar UI
            pass


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    GraphDeliveryApp(root)
    root.mainloop()
