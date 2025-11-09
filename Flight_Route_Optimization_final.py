import pandas as pd
import networkx as nx
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import datetime
from tkcalendar import DateEntry
import heapq

df = pd.read_csv('flights.csv')
df['Date_of_Journey'] = pd.to_datetime(df['Date_of_Journey'], format='%d-%m-%Y', errors='coerce')
df['Date_of_Journey'] = df['Date_of_Journey'].apply(lambda x: x.replace(year=2026) if pd.notnull(x) else x)

def duration_to_minutes(duration):
    parts = str(duration).strip().split()
    mins = 0
    for part in parts:
        if 'h' in part:
            mins += int(part.replace('h','')) * 60
        elif 'm' in part:
            mins += int(part.replace('m',''))
    return mins

df['Duration_mins'] = df['Duration'].apply(duration_to_minutes)
df['Price'] = pd.to_numeric(df['Price'], errors='coerce')

def normalize(series):
    return (series - series.min()) / (series.max() - series.min())

def display_route(route_str):
    return route_str.replace('?', '→').replace('  ', ' ').strip()

code_to_place = {
    "DEL": "New Delhi", "BLR": "Banglore", "BOM": "Mumbai", "MAA": "Chennai", "CCU": "Kolkata",
    "HYD": "Hyderabad", "COK": "Cochin", "PNQ": "Pune", "VTZ": "Visakhapatnam", "IXR": "Ranchi",
    "AMD": "Ahmedabad", "GOI": "Goa", "GAU": "Guwahati", "BBI": "Bhubaneswar", "VNS": "Varanasi",
    "PAT": "Patna", "JAI": "Jaipur", "KNU": "Kanpur", "NAG": "Nagpur", "IXC": "Chandigarh",
    "IXB": "Bagdogra", "IMF": "Imphal", "TRV": "Thiruvananthapuram", "IXM": "Madurai",
    "IXE": "Mangalore", "LKO": "Lucknow", "STV": "Surat", "IDR": "Indore", "IXU": "Aurangabad",
    "IXD": "Prayagraj (Allahabad)", "BHO": "Bhopal", "ATQ": "Amritsar", "IXA": "Agartala",
    "IXL": "Leh", "IXJ": "Jammu", "DIB": "Dibrugarh", "BDQ": "Vadodara", "IXS": "Silchar",
    "IXZ": "Port Blair", "RPR": "Raipur", "TIR": "Tirupati", "DHM": "Dharamshala", "SLV": "Shimla",
    "UDR": "Udaipur", "IXY": "Kandla", "JLR": "Jabalpur", "GWL": "Gwalior", "JDH": "Jodhpur",
    "JSA": "Jaisalmer", "BKB": "Bikaner", "IXG": "Belgaum", "IXI": "Lilabari", "PBD": "Porbandar",
    "IXW": "Jamshedpur", "TEE": "Tezpur", "SXR": "Srinagar", "LDA": "Ludhiana", "DMU": "Dimapur",
    "HJR": "Khajuraho", "SAG": "Shirdi", "JGB": "Jagdalpur", "CNN": "Kannur", "MYQ": "Mysore",
    "VGA": "Vijayawada", "RJA": "Rajahmundry", "JRH": "Jorhat", "GAY": "Gaya", "BUP": "Bathinda",
    "AJL": "Aizawl", "SHL": "Shillong", "KQH": "Kishangarh", "IXV": "Along", "TEZ": "Tezpur",
    "KUU": "Kullu Manali", "IXP": "Pathankot"
}

def place_to_code(place):
    for code, city in code_to_place.items():
        if city.lower() == place.lower():
            return code
    return place

def parse_route(route_str):
    return [r.strip() for r in route_str.replace('?', '').strip().split() if r.strip()]

def build_graph_with_stops(filtered_df, weight_choice, city_source, city_dest):
    G = nx.DiGraph()
    for idx, row in filtered_df.iterrows():
        stops = parse_route(row['Route'])
        duration = row['Duration_mins']
        price = row['Price']
        airline = row['Airline']
        dep_time = row['Dep_Time']
        src_code = place_to_code(row['Source'])
        dst_code = place_to_code(row['Destination'])
        layovers = [code for code in stops if code not in [src_code, dst_code]]
        nodes_full = [src_code] + layovers + [dst_code]
        pairs = zip(nodes_full, nodes_full[1:])
        seg_count = len(nodes_full) - 1
        dur_segment = duration // seg_count if seg_count else duration
        price_segment = price // seg_count if seg_count else price
        for i, (src, dst) in enumerate(pairs):
            if weight_choice == 'Duration':
                weight = dur_segment
            elif weight_choice == 'Price':
                weight = price_segment
            else:
                w_norm = normalize(filtered_df['Duration_mins'])
                p_norm = normalize(filtered_df['Price'])
                weight = w_norm.loc[idx] + p_norm.loc[idx]
            G.add_edge(src, dst, airline=airline, dep_time=dep_time,
                route=" -> ".join(nodes_full),
                route_csv=row['Route'],
                weight=weight, duration=dur_segment,
                price=price_segment, stops=" > ".join(nodes_full[1:-1]),
                date=row['Date_of_Journey'].date() if pd.notnull(row['Date_of_Journey']) else "",
                total_duration=duration, total_price=price, total_stops=row['Total_Stops'])
    return G

def networkx_to_adjlist(G):
    adj = {}
    for u, v, data in G.edges(data=True):
        if u not in adj:
            adj[u] = []
        adj[u].append((v, data['weight'], data))
    return adj

def dijkstra_manual(adj, source, target):
    heap = [(0, source, [])]
    visited = set()
    while heap:
        (cost, node, path) = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        path = path + [node]
        if node == target:
            return cost, path
        for neighbor, weight, data in adj.get(node, []):
            if neighbor not in visited:
                heapq.heappush(heap, (cost + weight, neighbor, path))
    return float('inf'), []

def all_paths_limited(adj, source, target, max_paths=3, max_depth=6):
    paths = []
    def dfs(path, cost):
        node = path[-1]
        if len(path) > max_depth:
            return
        if node == target:
            paths.append((cost, path[:]))
            return
        for neighbor, weight, data in adj.get(node, []):
            if neighbor not in path:
                path.append(neighbor)
                dfs(path, cost + weight)
                path.pop()
    dfs([source], 0)
    paths.sort(key=lambda x: x[0])
    return paths[:max_paths]

def path_to_segments(G, path):
    segments_details = []
    total_duration = None
    total_price = None
    total_stops = None
    for i in range(len(path) - 1):
        edge = G[path[i]][path[i+1]]
        segments_details.append({
            'from': path[i], 'to': path[i+1], 'airline': edge['airline'],
            'dep_time': edge['dep_time'], 'stops': edge['stops'], 'route': edge['route'],
            'route_csv': edge['route_csv'],
            'date': edge['date'], 'duration': edge['duration'], 'price': edge['price'],
            'total_duration': edge['total_duration'], 'total_price': edge['total_price'],
            'total_stops': edge['total_stops'],
        })
        total_duration = edge['total_duration']
        total_price = edge['total_price']
        total_stops = edge['total_stops']
    return {
        'segments': segments_details,
        'total_duration': total_duration,
        'total_price': total_price,
        'total_stops': total_stops,
        'route': segments_details[0]['route_csv'] if segments_details else "",
    }

def extract_structured_flight_row(row):
    route = display_route(row["Route"])
    return (
        route,
        row["Airline"],
        row["Dep_Time"],
        row["Date_of_Journey"].date() if pd.notnull(row["Date_of_Journey"]) else "",
        f'{row["Duration_mins"]} mins',
        f'₹{row["Price"]}',
        row["Total_Stops"]
    )

BG_BLUE = '#223142'
PANEL_BLUE = '#185486'
ACCENT_BLUE = '#1280c3'
FONT_WHITE = '#f8fafd'
LAYOVER_COLOR = '#FFE699'

class FlightOptimizerApp(tk.Tk):
    def __init__(self, df):
        super().__init__()
        self.title('Indian Domestic Flight Optimizer')
        self.geometry('1350x800')
        self.configure(bg=BG_BLUE)
        self.df = df
        self.create_sidebar()
        self.create_main_panel()

    def create_sidebar(self):
        style = ttk.Style()
        style.configure('TRadiobutton', font=('Segoe UI', 13))
        sidebar = tk.Frame(self, width=320, bg=PANEL_BLUE, height=800)
        sidebar.pack(expand=False, fill='y', side='left', anchor='nw')
        
        tk.Label(sidebar, text="Source", font=('Segoe UI', 13, 'bold'), bg=PANEL_BLUE, fg=FONT_WHITE).pack(pady=(15,0), anchor="w")
        self.src_var = tk.StringVar()
        src_options = sorted(self.df['Source'].dropna().unique().tolist())
        src_box = ttk.Combobox(sidebar, textvariable=self.src_var, values=src_options, font=('Segoe UI', 11))
        src_box.pack(fill="x", padx=25, pady=(0,8))
        tk.Label(sidebar, text="Destination", font=('Segoe UI', 13, 'bold'), bg=PANEL_BLUE, fg=FONT_WHITE).pack(anchor="w")
        self.dst_var = tk.StringVar()
        
        dst_options = sorted(self.df['Destination'].dropna().unique().tolist())
        dst_box = ttk.Combobox(sidebar, textvariable=self.dst_var, values=dst_options, font=('Segoe UI', 11))
        dst_box.pack(fill="x", padx=25, pady=(0,8))
        tk.Label(sidebar, text="Journey Date", font=('Segoe UI', 13, 'bold'), bg=PANEL_BLUE, fg=FONT_WHITE).pack(anchor="w")
        self.date_var = tk.StringVar()
        
        self.date_entry = DateEntry(sidebar, textvariable=self.date_var, font=('Segoe UI', 11),
                                    date_pattern='yyyy-mm-dd', background='lightblue', foreground='black')
        self.date_entry.pack(fill="x", padx=25, pady=(0,8))
        tk.Label(sidebar, text="Filter By", font=('Segoe UI', 13, 'bold'), bg=PANEL_BLUE, fg=FONT_WHITE).pack(anchor="w")
        filter_frame = tk.Frame(sidebar, bg=PANEL_BLUE)
        filter_frame.pack(fill="x", padx=25, pady=(0,8), anchor='w')
        self.filter_var = tk.StringVar(value='Duration')
        
        ttk.Radiobutton(filter_frame, text='Duration', variable=self.filter_var, value='Duration', style='TRadiobutton').pack(side='top', anchor="w", pady=3)
        ttk.Radiobutton(filter_frame, text='Price', variable=self.filter_var, value='Price', style='TRadiobutton').pack(side='top', anchor="w", pady=3)
        ttk.Radiobutton(filter_frame, text='Both', variable=self.filter_var, value='Both', style='TRadiobutton').pack(side='top', anchor="w", pady=3)
        tk.Button(sidebar, text="Optimize", command=self.optimize_flight,
                  bg=ACCENT_BLUE, fg=FONT_WHITE, font=('Segoe UI', 11, 'bold')).pack(pady=(33,0), padx=30, fill='x')
        
        self.legend_frame = tk.LabelFrame(sidebar, text="Graph Code Legend", bg=PANEL_BLUE, fg=FONT_WHITE, font=('Segoe UI', 11, 'bold'), relief=tk.FLAT)
        self.legend_frame.pack(fill="x", pady=(18,0), padx=15, anchor="n")
        self.legend_label = tk.Label(self.legend_frame, text="", bg=PANEL_BLUE, fg=FONT_WHITE, justify='left', font=('Segoe UI', 11))
        self.legend_label.pack(fill="x", padx=6, pady=(2,8), anchor="w")

    def create_main_panel(self):
        self.tabControl = ttk.Notebook(self)
        self.tabControl.pack(expand=1, fill="both")
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook.Tab', background=ACCENT_BLUE, foreground=FONT_WHITE, font=('Segoe UI', 14, 'bold'))
        style.map("TNotebook.Tab", background=[("selected", BG_BLUE)])
        style.configure("Treeview", background=BG_BLUE, foreground=FONT_WHITE, fieldbackground=BG_BLUE, rowheight=36, font=('Segoe UI', 13))
        style.map('Treeview', background=[('selected', ACCENT_BLUE)], foreground=[('selected', FONT_WHITE)])

        self.tab1 = ttk.Frame(self.tabControl)
        self.tab2 = ttk.Frame(self.tabControl)
        self.tab3 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab1, text='Flight Network')
        self.tabControl.add(self.tab2, text='Optimized Flights')
        self.tabControl.add(self.tab3, text='All Flights On Date')

        self.fig = plt.Figure(figsize=(8,7), dpi=100, facecolor=BG_BLUE)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tab1)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=12)
        columns = ("route", "airline", "dep_time", "date", "total_duration", "price", "stops")
        self.tree = ttk.Treeview(self.tab2, columns=columns, show='headings', style="Treeview")
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, anchor="center", width=145)
        self.tree.pack(fill='both', expand=True, padx=15, pady=18)
        self.allflights_tree = ttk.Treeview(self.tab3, columns=columns, show='headings', style="Treeview")
        for col in columns:
            self.allflights_tree.heading(col, text=col.replace("_", " ").title())
            self.allflights_tree.column(col, anchor="center", width=145)
        self.allflights_tree.pack(fill='both', expand=True, padx=15, pady=18)

    def optimize_flight(self):
        src = self.src_var.get().strip()
        dst = self.dst_var.get().strip()
        sel_date = self.date_var.get().strip()
        filter_choice = self.filter_var.get()
        try:
            base_date = datetime.datetime.strptime(sel_date, '%Y-%m-%d').date()
        except:
            messagebox.showerror("Invalid Date Format", "Please use YYYY-MM-DD.")
            return
        
        filter_dates = [base_date + datetime.timedelta(days=i) for i in range(6)]
        date_strs = [d.strftime('%Y-%m-%d') for d in filter_dates]
        filtered_df = self.df[self.df['Date_of_Journey'].dt.strftime('%Y-%m-%d').isin(date_strs)]
        filtered_df = filtered_df[
            (filtered_df['Source'].str.strip().str.lower() == src.strip().lower()) &
            (filtered_df['Destination'].str.strip().str.lower() == dst.strip().lower())
        ]
        if filtered_df.empty:
            messagebox.showinfo("No results", "No flights found for the selection.")
            self.fig.clear()
            self.canvas.draw()
            self.tree.delete(*self.tree.get_children())
            self.allflights_tree.delete(*self.allflights_tree.get_children())
            self.legend_label.config(text="")
            return

        src_code = place_to_code(src)
        dst_code = place_to_code(dst)
        G = build_graph_with_stops(filtered_df, filter_choice, src_code, dst_code)
        adj = networkx_to_adjlist(G)

        cost, dijkstra_path = dijkstra_manual(adj, src_code, dst_code)
        top_routes = []
        if dijkstra_path and len(dijkstra_path) > 1:
            top_routes.append(path_to_segments(G, dijkstra_path))

        top_k_paths = all_paths_limited(adj, src_code, dst_code, max_paths=3, max_depth=6)
        for c, p in top_k_paths:
            if p and len(p) > 1:
                route_obj = path_to_segments(G, p)
                # Avoid duplicates
                if route_obj['route'] not in [r['route'] for r in top_routes]:
                    top_routes.append(route_obj)

        self.fig.clear()
        ax = self.fig.add_subplot(111)
        node_colors = []
        layover_nodes = []
        node_labels = {node: node for node in G.nodes}
        for node in G.nodes:
            if node == src_code:
                node_colors.append('#57E2FF')
            elif node == dst_code:
                node_colors.append('#6CDAEE')
            else:
                node_colors.append(LAYOVER_COLOR)
                layover_nodes.append(node)
                
        pos = nx.spring_layout(G, seed=42, k=2)
        nx.draw(G, pos, ax=ax, labels=node_labels, node_color=node_colors,
                edge_color="#82B1ED", arrows=True, arrowsize=22, width=2, font_size=12)
        for (u, v, d) in G.edges(data=True):
            nx.draw_networkx_edges(G, pos, ax=ax, edgelist=[(u,v)], arrowstyle='-|>',
                                  arrowsize=22, edge_color="#469FD6", connectionstyle='arc3,rad=0.18')
        ax.set_facecolor(BG_BLUE)
        self.fig.subplots_adjust(left=0.09, right=0.93, top=0.90, bottom=0.13)
        self.canvas.draw()

        #Optimized flights
        self.tree.delete(*self.tree.get_children())
        for i, route in enumerate(top_routes):
            s = route['segments'][0]
            self.tree.insert('', 'end', values=(
                display_route(s['route_csv']),
                s['airline'],
                s['dep_time'],
                s['date'],
                f"{route['total_duration']} mins",
                f"₹{route['total_price']}",
                route['total_stops'],
            ))

        #All flights
        self.allflights_tree.delete(*self.allflights_tree.get_children())
        dfa = self.df[
            (self.df['Date_of_Journey'].dt.date == base_date) &
            (self.df['Source'].str.strip().str.lower() == src.strip().lower()) &
            (self.df['Destination'].str.strip().str.lower() == dst.strip().lower())
        ]
        for idx, row in dfa.iterrows():
            self.allflights_tree.insert('', 'end', values=extract_structured_flight_row(row))
        all_codes_used = set(G.nodes)
        legend_lines = [f"{code} - {code_to_place.get(code, '')}" for code in sorted(all_codes_used) if code in code_to_place]
        legend_text = "\n".join(legend_lines) if legend_lines else "No codes"
        self.legend_label.config(text=legend_text)

if __name__ == "__main__":
    app = FlightOptimizerApp(df)
    app.mainloop()
