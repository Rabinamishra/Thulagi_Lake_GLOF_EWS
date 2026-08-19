import sys
import csv
import inspect
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont

import matplotlib
matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# ============================================================
# OPTIONAL ALERT ENGINE
# ============================================================

alert_engine = None
RainfallInput = None
LakeAreaInput = None
SimulatedWaterLevelInput = None
run_alert_engine = None
demo_operational_extension = None
ALERT_ENGINE_IMPORT_ERROR = None

try:
    import alert_engine

    RainfallInput = getattr(
        alert_engine,
        "RainfallInput",
        None
    )

    LakeAreaInput = getattr(
        alert_engine,
        "LakeAreaInput",
        None
    )

    SimulatedWaterLevelInput = getattr(
        alert_engine,
        "SimulatedWaterLevelInput",
        getattr(
            alert_engine,
            "WaterLevelInput",
            None
        )
    )

    run_alert_engine = getattr(
        alert_engine,
        "run_alert_engine",
        None
    )

    demo_operational_extension = getattr(
        alert_engine,
        "demo_operational_extension",
        None
    )

except Exception as e:
    ALERT_ENGINE_IMPORT_ERROR = str(e)


# ============================================================
# OPTIONAL PDF SUPPORT
# ============================================================

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle
    )
    from reportlab.lib import colors

    PDF_AVAILABLE = True

except ImportError:
    PDF_AVAILABLE = False


# ============================================================
# COLOR PALETTE
# ============================================================

BG = "#f4f7fb"
CARD = "#ffffff"
TEXT = "#172033"
MUTED = "#64748b"
BORDER = "#dbe3ef"

BLUE = "#2563eb"
BLUE_DARK = "#1e40af"

GREEN = "#16a34a"
GREEN_BG = "#dcfce7"

ORANGE = "#ea580c"
ORANGE_BG = "#ffedd5"

RED = "#dc2626"
RED_BG = "#fee2e2"

YELLOW = "#ca8a04"
YELLOW_BG = "#fef9c3"

LIGHT_BLUE = "#dbeafe"

SKETCH_BLUE = "#3b82f6"
SKETCH_ORANGE = "#f97316"


# ============================================================
# APPLICATION
# ============================================================

class GLOFEWSApp(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title(
            "Thulagi Lake GLOF — Decision-Support Prototype"
        )

        self.geometry("1420x980")
        self.minsize(1100, 760)

        self.FONT = self._pick_font()

        self.entries = {}
        self.water_rows = []

        self.last_calculation_result = None
        self.last_demo_result = None

        # Local calculated values.
        # These are the actual source of truth for the dashboard.
        self.current_metrics = {
            "current_level": None,
            "latest_rate": None,
            "trend": None,
            "acceleration": None,
            "change_10hr": None,
            "rain7": None,
            "rain_percentile": None,
            "lake_area": None,
            "lake_previous": None,
            "lake_change": None,
            "lake_change_percent": None,
            "assessment": None,
            "score": None,
            "description": ""
        }

        self._configure_styles()
        self._build_menu_bar()
        self._build_scrollable_container()

        self._build_header()
        self._build_kpi_cards()
        self._build_upper_input_sections()
        self._build_telemetry_and_graph_section()
        self._build_action_bar()
        self._build_assessment_and_map_section()
        self._build_horizontal_derived_indicators()

        self.bind(
            "<Control-r>",
            lambda e: self.calculate_alert()
        )

        self.bind(
            "<Control-o>",
            lambda e: self.load_telemetry_csv()
        )

        self.bind(
            "<Escape>",
            lambda e: self.quit()
        )

        self._setup_default_telemetry_rows(5)

        self.after(
            100,
            self._update_scroll_region
        )


    # ========================================================
    # FONT
    # ========================================================

    def _pick_font(self):

        available = set(
            tkfont.families()
        )

        for candidate in (
            "Segoe UI",
            "Inter",
            "Helvetica Neue",
            "Arial"
        ):

            if candidate in available:
                return candidate

        return "TkDefaultFont"


    # ========================================================
    # STYLES
    # ========================================================

    def _configure_styles(self):

        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            ".",
            font=(self.FONT, 10),
            background=BG,
            foreground=TEXT
        )

        style.configure(
            "TFrame",
            background=BG
        )

        style.configure(
            "Card.TLabelframe",
            background=CARD,
            bordercolor=BORDER,
            relief="solid",
            borderwidth=1
        )

        style.configure(
            "Card.TLabelframe.Label",
            background=CARD,
            foreground=BLUE_DARK,
            font=(self.FONT, 11, "bold")
        )

        style.configure(
            "TEntry",
            padding=6
        )

        style.configure(
            "Primary.TButton",
            font=(self.FONT, 10, "bold"),
            padding=(18, 10),
            foreground="white",
            background=BLUE
        )

        style.map(
            "Primary.TButton",
            background=[
                ("active", BLUE_DARK),
                ("pressed", BLUE_DARK)
            ]
        )

        style.configure(
            "Secondary.TButton",
            font=(self.FONT, 10),
            padding=(10, 6)
        )

        style.configure(
            "Danger.TButton",
            font=(self.FONT, 9, "bold"),
            padding=(4, 2),
            foreground=RED
        )


    # ========================================================
    # MENU
    # ========================================================

    def _build_menu_bar(self):

        menubar = tk.Menu(self)

        file_menu = tk.Menu(
            menubar,
            tearoff=0
        )

        file_menu.add_command(
            label="Load Telemetry CSV... (Ctrl+O)",
            command=self.load_telemetry_csv
        )

        file_menu.add_command(
            label="Export Report (PDF)...",
            command=self.export_pdf_report
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="Exit",
            command=self.quit
        )

        menubar.add_cascade(
            label="File",
            menu=file_menu
        )

        run_menu = tk.Menu(
            menubar,
            tearoff=0
        )

        run_menu.add_command(
            label="Run Assessment (Ctrl+R)",
            command=self.calculate_alert
        )

        run_menu.add_command(
            label="Reset Inputs",
            command=lambda: self._reset_all_inputs()
        )

        menubar.add_cascade(
            label="Engine",
            menu=run_menu
        )

        self.config(
            menu=menubar
        )


    # ========================================================
    # RESET
    # ========================================================

    def _reset_all_inputs(self):

        defaults = {
            "daily": "10.47",
            "rain3": "46.50",
            "rain7": "132.45",
            "percentile": "98.08",
            "latest_area": "0.9291",
            "previous_area": "0.9167",
            "years": "1.0"
        }

        for key, value in defaults.items():

            if key in self.entries:

                self.entries[key].delete(
                    0,
                    tk.END
                )

                self.entries[key].insert(
                    0,
                    value
                )

        self._setup_default_telemetry_rows(5)

        self._clear_results()


    def _clear_results(self):

        self.current_metrics = {
            "current_level": None,
            "latest_rate": None,
            "trend": None,
            "acceleration": None,
            "change_10hr": None,
            "rain7": None,
            "rain_percentile": None,
            "lake_area": None,
            "lake_previous": None,
            "lake_change": None,
            "lake_change_percent": None,
            "assessment": None,
            "score": None,
            "description": ""
        }

        self.kpi_status["value"].config(
            text="NOT CALCULATED",
            fg=TEXT
        )

        self.kpi_status["subtitle"].config(
            text="Run an assessment"
        )

        self.kpi_rain["value"].config(
            text="—"
        )

        self.kpi_lake["value"].config(
            text="—"
        )

        self.kpi_water["value"].config(
            text="—"
        )

        self.alert_badge.config(
            text="PENDING CALCULATION",
            bg="#f1f5f9",
            fg=MUTED
        )

        self._set_reasoning(
            "Click 'Run Integrated Assessment' to calculate the prototype assessment."
        )

        for key in self.water_evidence:

            self.water_evidence[key]["value"].config(
                text="—"
            )

        self._update_graph([], [])


    # ========================================================
    # SCROLLABLE CONTAINER
    # ========================================================

    def _build_scrollable_container(self):

        self.canvas = tk.Canvas(
            self,
            background=BG,
            highlightthickness=0,
            borderwidth=0
        )

        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )

        self.scroll_frame = tk.Frame(
            self.canvas,
            background=BG
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scroll_frame,
            anchor="nw"
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar.set
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.scrollbar.pack(
            side="right",
            fill="y"
        )

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self._update_scroll_region()
        )

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(
                self.canvas_window,
                width=e.width
            )
        )

        self.canvas.bind_all(
            "<MouseWheel>",
            self._on_mousewheel
        )

        self.canvas.bind_all(
            "<Button-4>",
            self._on_mousewheel
        )

        self.canvas.bind_all(
            "<Button-5>",
            self._on_mousewheel
        )


    def _update_scroll_region(self):

        try:
            self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        except Exception:
            pass


    def _on_mousewheel(self, event):

        try:

            if event.num == 4:
                self.canvas.yview_scroll(
                    -3,
                    "units"
                )

            elif event.num == 5:
                self.canvas.yview_scroll(
                    3,
                    "units"
                )

            elif event.delta:

                self.canvas.yview_scroll(
                    int(-event.delta / 120) * 3,
                    "units"
                )

        except Exception:
            pass


    # ========================================================
    # HEADER
    # ========================================================

    def _build_header(self):

        header = tk.Frame(
            self.scroll_frame,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=28,
            pady=20
        )

        header.pack(
            fill="x",
            padx=22,
            pady=(20, 12)
        )

        left = tk.Frame(
            header,
            bg=CARD
        )

        left.pack(
            side="left",
            fill="x",
            expand=True
        )

        tk.Label(
            left,
            text="THULAGI LAKE",
            font=(self.FONT, 10, "bold"),
            fg=BLUE,
            bg=CARD
        ).pack(anchor="w")

        tk.Label(
            left,
            text="GLOF Early-Warning Decision-Support Prototype",
            font=(self.FONT, 22, "bold"),
            fg=TEXT,
            bg=CARD
        ).pack(
            anchor="w",
            pady=(2, 2)
        )

        tk.Label(
            left,
            text=(
                "Multi-indicator assessment using rainfall, "
                "satellite lake-area change, and water-level telemetry"
            ),
            font=(self.FONT, 10),
            fg=MUTED,
            bg=CARD
        ).pack(anchor="w")

        tk.Label(
            header,
            text="PROTOTYPE",
            font=(self.FONT, 9, "bold"),
            fg=BLUE_DARK,
            bg=LIGHT_BLUE,
            padx=12,
            pady=6
        ).pack(
            side="right",
            anchor="n"
        )


    # ========================================================
    # KPI CARDS
    # ========================================================

    def _build_kpi_cards(self):

        container = tk.Frame(
            self.scroll_frame,
            bg=BG
        )

        container.pack(
            fill="x",
            padx=22,
            pady=(0, 12)
        )

        for i in range(4):

            container.columnconfigure(
                i,
                weight=1
            )

        self.kpi_status = self._create_kpi(
            container,
            0,
            "ASSESSMENT",
            "NOT CALCULATED",
            "Run an assessment"
        )

        self.kpi_rain = self._create_kpi(
            container,
            1,
            "7-DAY RAINFALL",
            "—",
            "mm"
        )

        self.kpi_lake = self._create_kpi(
            container,
            2,
            "LAKE AREA",
            "—",
            "km²"
        )

        self.kpi_water = self._create_kpi(
            container,
            3,
            "WATER LEVEL",
            "—",
            "m"
        )


    def _create_kpi(
        self,
        parent,
        column,
        title,
        value,
        subtitle
    ):

        card = tk.Frame(
            parent,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=16,
            pady=14
        )

        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=5
        )

        tk.Label(
            card,
            text=title,
            font=(self.FONT, 9, "bold"),
            fg=MUTED,
            bg=CARD
        ).pack(anchor="w")

        val_lbl = tk.Label(
            card,
            text=value,
            font=(self.FONT, 18, "bold"),
            fg=TEXT,
            bg=CARD
        )

        val_lbl.pack(
            anchor="w",
            pady=(4, 1)
        )

        sub_lbl = tk.Label(
            card,
            text=subtitle,
            font=(self.FONT, 9),
            fg=MUTED,
            bg=CARD
        )

        sub_lbl.pack(
            anchor="w"
        )

        return {
            "card": card,
            "value": val_lbl,
            "subtitle": sub_lbl
        }


    # ========================================================
    # INPUT SECTIONS
    # ========================================================

    def _build_upper_input_sections(self):

        outer = tk.Frame(
            self.scroll_frame,
            bg=BG
        )

        outer.pack(
            fill="x",
            padx=22,
            pady=5
        )

        outer.columnconfigure(
            0,
            weight=1
        )

        outer.columnconfigure(
            1,
            weight=1
        )

        rainfall = ttk.LabelFrame(
            outer,
            text=" 1  RAINFALL TELEMETRY ",
            style="Card.TLabelframe",
            padding=14
        )

        rainfall.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 6)
        )

        self._add_input(
            rainfall,
            "Daily rainfall",
            "daily",
            "10.47",
            "mm"
        )

        self._add_input(
            rainfall,
            "3-day accumulation",
            "rain3",
            "46.50",
            "mm"
        )

        self._add_input(
            rainfall,
            "7-day accumulation",
            "rain7",
            "132.45",
            "mm"
        )

        self._add_input(
            rainfall,
            "Historical 7-day percentile",
            "percentile",
            "98.08",
            "0–100"
        )

        lake = ttk.LabelFrame(
            outer,
            text=" 2  SATELLITE LAKE AREA ",
            style="Card.TLabelframe",
            padding=14
        )

        lake.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(6, 0)
        )

        self._add_input(
            lake,
            "Latest lake area",
            "latest_area",
            "0.9291",
            "km²"
        )

        self._add_input(
            lake,
            "Previous lake area",
            "previous_area",
            "0.9167",
            "km²"
        )

        self._add_input(
            lake,
            "Years between observations",
            "years",
            "1.0",
            "years"
        )


    def _add_input(
        self,
        parent,
        label,
        key,
        default,
        unit
    ):

        row = tk.Frame(
            parent,
            bg=CARD
        )

        row.pack(
            fill="x",
            pady=4
        )

        tk.Label(
            row,
            text=label,
            font=(self.FONT, 9),
            fg=TEXT,
            bg=CARD,
            width=26,
            anchor="w"
        ).pack(side="left")

        entry = ttk.Entry(
            row,
            width=16
        )

        entry.insert(
            0,
            default
        )

        entry.pack(
            side="left",
            padx=5
        )

        tk.Label(
            row,
            text=unit,
            font=(self.FONT, 9),
            fg=MUTED,
            bg=CARD,
            width=8,
            anchor="w"
        ).pack(side="left")

        self.entries[key] = entry


    # ========================================================
    # TELEMETRY + GRAPH
    # ========================================================

    def _build_telemetry_and_graph_section(self):

        container = tk.Frame(
            self.scroll_frame,
            bg=BG
        )

        container.pack(
            fill="x",
            padx=22,
            pady=8
        )

        container.columnconfigure(
            0,
            weight=1
        )

        container.columnconfigure(
            1,
            weight=1
        )

        water_card = ttk.LabelFrame(
            container,
            text=" 3  WATER-LEVEL TELEMETRY ",
            style="Card.TLabelframe",
            padding=14
        )

        water_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 6)
        )

        date_row = tk.Frame(
            water_card,
            bg=CARD
        )

        date_row.pack(
            fill="x",
            pady=(0, 8)
        )

        tk.Label(
            date_row,
            text="Date:",
            font=(self.FONT, 9, "bold"),
            bg=CARD,
            fg=TEXT
        ).pack(side="left")

        self.base_date_entry = ttk.Entry(
            date_row,
            width=12
        )

        self.base_date_entry.insert(
            0,
            datetime.now().strftime("%Y-%m-%d")
        )

        self.base_date_entry.pack(
            side="left",
            padx=6
        )

        ctrl_frame = tk.Frame(
            date_row,
            bg=CARD
        )

        ctrl_frame.pack(
            side="right"
        )

        ttk.Button(
            ctrl_frame,
            text="+ Add Row",
            style="Secondary.TButton",
            command=self.add_water_observation_row
        ).pack(
            side="left",
            padx=2
        )

        ttk.Button(
            ctrl_frame,
            text="Load CSV",
            style="Secondary.TButton",
            command=self.load_telemetry_csv
        ).pack(
            side="left",
            padx=2
        )

        tbl_hdr = tk.Frame(
            water_card,
            bg=CARD
        )

        tbl_hdr.pack(
            fill="x",
            pady=(4, 2)
        )

        tk.Label(
            tbl_hdr,
            text="#",
            font=(self.FONT, 8, "bold"),
            fg=MUTED,
            bg=CARD,
            width=3
        ).pack(side="left")

        tk.Label(
            tbl_hdr,
            text="TIME / TIMESTAMP",
            font=(self.FONT, 8, "bold"),
            fg=MUTED,
            bg=CARD,
            width=20,
            anchor="w"
        ).pack(
            side="left",
            padx=4
        )

        tk.Label(
            tbl_hdr,
            text="WATER LEVEL (m)",
            font=(self.FONT, 8, "bold"),
            fg=MUTED,
            bg=CARD,
            width=18,
            anchor="w"
        ).pack(
            side="left",
            padx=4
        )

        tk.Label(
            tbl_hdr,
            text="DEL",
            font=(self.FONT, 8, "bold"),
            fg=MUTED,
            bg=CARD,
            width=4
        ).pack(side="right")

        self.water_rows_container = tk.Frame(
            water_card,
            bg=CARD
        )

        self.water_rows_container.pack(
            fill="x",
            expand=True
        )

        # GRAPH

        graph_card = tk.Frame(
            container,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        graph_card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(6, 0)
        )

        tk.Label(
            graph_card,
            text="WATER-LEVEL TREND CHART",
            font=(self.FONT, 11, "bold"),
            fg=TEXT,
            bg=CARD
        ).pack(
            anchor="w",
            padx=14,
            pady=(12, 0)
        )

        self.fig = Figure(
            figsize=(5, 3.0),
            dpi=100,
            facecolor=CARD
        )

        self.ax = self.fig.add_subplot(111)

        self._style_graph()

        self.canvas_plot = FigureCanvasTkAgg(
            self.fig,
            master=graph_card
        )

        self.canvas_plot.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=8,
            pady=(0, 8)
        )


    # ========================================================
    # ACTION BAR
    # ========================================================

    def _build_action_bar(self):

        bar = tk.Frame(
            self.scroll_frame,
            bg=BG
        )

        bar.pack(
            fill="x",
            padx=22,
            pady=12
        )

        ttk.Button(
            bar,
            text="⚡ Run Integrated Assessment",
            style="Primary.TButton",
            command=self.calculate_alert
        ).pack(side="left")

        ttk.Button(
            bar,
            text="Export Report (PDF)",
            style="Secondary.TButton",
            command=self.export_pdf_report
        ).pack(side="right")


    # ========================================================
    # ASSESSMENT + MAP
    # ========================================================

    def _build_assessment_and_map_section(self):

        container = tk.Frame(
            self.scroll_frame,
            bg=BG
        )

        container.pack(
            fill="x",
            padx=22,
            pady=8
        )

        container.columnconfigure(
            0,
            weight=1
        )

        container.columnconfigure(
            1,
            weight=1
        )

        self.assessment_card = tk.Frame(
            container,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=16,
            pady=14
        )

        self.assessment_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 6)
        )

        tk.Label(
            self.assessment_card,
            text="ALERT ASSESSMENT RESULTS",
            font=(self.FONT, 11, "bold"),
            fg=TEXT,
            bg=CARD
        ).pack(anchor="w")

        self.alert_badge = tk.Label(
            self.assessment_card,
            text="PENDING CALCULATION",
            font=(self.FONT, 12, "bold"),
            bg="#f1f5f9",
            fg=MUTED,
            padx=12,
            pady=6
        )

        self.alert_badge.pack(
            anchor="w",
            pady=(10, 8)
        )

        # NEW: DESCRIPTION
        tk.Label(
            self.assessment_card,
            text="DESCRIPTION",
            font=(self.FONT, 8, "bold"),
            fg=MUTED,
            bg=CARD
        ).pack(
            anchor="w",
            pady=(2, 2)
        )

        self.description_label = tk.Label(
            self.assessment_card,
            text="Run the assessment to generate a condition description.",
            font=(self.FONT, 10),
            fg=TEXT,
            bg="#f8fafc",
            justify="left",
            anchor="w",
            wraplength=560,
            padx=10,
            pady=8
        )

        self.description_label.pack(
            fill="x",
            pady=(0, 10)
        )

        tk.Label(
            self.assessment_card,
            text="EVIDENCE & REASONING",
            font=(self.FONT, 8, "bold"),
            fg=MUTED,
            bg=CARD
        ).pack(
            anchor="w",
            pady=(2, 2)
        )

        self.reasoning_text = tk.Text(
            self.assessment_card,
            height=7,
            wrap="word",
            font=(self.FONT, 9),
            bg="#f8fafc",
            fg=TEXT,
            relief="solid",
            borderwidth=1,
            highlightthickness=0,
            padx=10,
            pady=8
        )

        self.reasoning_text.pack(
            fill="both",
            expand=True
        )

        self._set_reasoning(
            "Click 'Run Integrated Assessment' to execute the prototype calculation."
        )

        # MAP

        map_card = tk.Frame(
            container,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=16,
            pady=14
        )

        map_card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(6, 0)
        )

        tk.Label(
            map_card,
            text="GLOF SYSTEM SCHEMATIC",
            font=(self.FONT, 11, "bold"),
            fg=TEXT,
            bg=CARD
        ).pack(anchor="w")

        canvas = tk.Canvas(
            map_card,
            bg="#0f172a",
            height=250,
            highlightthickness=0
        )

        canvas.pack(
            fill="both",
            expand=True,
            pady=(8, 0)
        )

        lake_polygon = [
            30, 100,
            70, 60,
            130, 70,
            160, 110,
            130, 140,
            70, 150
        ]

        canvas.create_polygon(
            lake_polygon,
            fill=SKETCH_BLUE,
            outline="#93c5fd",
            width=2
        )

        canvas.create_text(
            95,
            105,
            text="Glacial Lake\n(Thulagi)",
            fill="white",
            font=(self.FONT, 8, "bold"),
            justify="center"
        )

        canvas.create_rectangle(
            155,
            95,
            170,
            125,
            fill=SKETCH_ORANGE,
            outline="white"
        )

        canvas.create_text(
            162,
            78,
            text="Moraine Dam",
            fill="#fdba74",
            font=(self.FONT, 7, "bold")
        )

        river_pts = [
            (170, 110),
            (250, 110),
            (330, 140),
            (420, 160),
            (520, 170)
        ]

        canvas.create_line(
            river_pts,
            fill="#38bdf8",
            width=5,
            smooth=True
        )

        buffer_pts = [
            (170, 95),
            (250, 95),
            (330, 125),
            (420, 145),
            (520, 155),
            (520, 185),
            (420, 175),
            (330, 155),
            (250, 125),
            (170, 125)
        ]

        canvas.create_polygon(
            buffer_pts,
            fill="#ef4444",
            stipple="gray25",
            outline=""
        )

        canvas.create_oval(
            325,
            135,
            335,
            145,
            fill=RED,
            outline="white",
            width=2
        )

        canvas.create_text(
            330,
            120,
            text="Downstream Zone",
            fill="white",
            font=(self.FONT, 8, "bold")
        )

        canvas.create_oval(
            445,
            158,
            455,
            168,
            fill=RED,
            outline="white",
            width=2
        )

        canvas.create_text(
            450,
            145,
            text="Settlement",
            fill="white",
            font=(self.FONT, 8, "bold")
        )


    # ========================================================
    # DERIVED WATER INDICATORS
    # ========================================================

    def _build_horizontal_derived_indicators(self):

        evidence_card = tk.Frame(
            self.scroll_frame,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=16,
            pady=14
        )

        evidence_card.pack(
            fill="x",
            padx=22,
            pady=(8, 20)
        )

        tk.Label(
            evidence_card,
            text="DERIVED WATER-LEVEL INDICATORS",
            font=(self.FONT, 11, "bold"),
            fg=TEXT,
            bg=CARD
        ).pack(anchor="w")

        horiz_frame = tk.Frame(
            evidence_card,
            bg=CARD
        )

        horiz_frame.pack(
            fill="x",
            pady=(10, 0)
        )

        for i in range(5):

            horiz_frame.columnconfigure(
                i,
                weight=1
            )

        self.water_evidence = {}

        evidence_items = [
            ("CURRENT LEVEL", "—", "m"),
            ("LATEST RISE RATE", "—", "m/hour"),
            ("TREND", "—", "category"),
            ("ACCELERATION", "—", "m/hour²"),
            ("10-HOUR CHANGE", "—", "m")
        ]

        for col, (title, value, unit) in enumerate(
            evidence_items
        ):

            box = tk.Frame(
                horiz_frame,
                bg="#f8fafc",
                highlightbackground=BORDER,
                highlightthickness=1,
                padx=10,
                pady=8
            )

            box.grid(
                row=0,
                column=col,
                sticky="nsew",
                padx=4
            )

            tk.Label(
                box,
                text=title,
                font=(self.FONT, 8, "bold"),
                fg=MUTED,
                bg="#f8fafc"
            ).pack(anchor="w")

            val_lbl = tk.Label(
                box,
                text=value,
                font=(self.FONT, 12, "bold"),
                fg=TEXT,
                bg="#f8fafc"
            )

            val_lbl.pack(
                anchor="w",
                pady=(2, 0)
            )

            unit_lbl = tk.Label(
                box,
                text=unit,
                font=(self.FONT, 7),
                fg=MUTED,
                bg="#f8fafc"
            )

            unit_lbl.pack(
                anchor="w"
            )

            self.water_evidence[title] = {
                "value": val_lbl,
                "unit": unit_lbl,
                "frame": box
            }


    # ========================================================
    # TELEMETRY ROW MANAGEMENT
    # ========================================================

    def _setup_default_telemetry_rows(
        self,
        count=5
    ):

        for widget in self.water_rows_container.winfo_children():
            widget.destroy()

        self.water_rows.clear()

        base_levels = [
            22.41,
            22.48,
            22.57,
            22.72,
            23.05
        ]

        for i in range(count):

            hour = 8 + i * 2

            if i < len(base_levels):
                level = base_levels[i]
            else:
                level = (
                    base_levels[-1]
                    +
                    (i - 4) * 0.05
                )

            self._create_row_ui(
                f"{hour:02d}:00",
                f"{level:.2f}"
            )


    def add_water_observation_row(self):

        self._create_row_ui(
            "",
            ""
        )

        self._reindex_rows()
        self._update_scroll_region()


    def _create_row_ui(
        self,
        default_time,
        default_level
    ):

        row_frame = tk.Frame(
            self.water_rows_container,
            bg=CARD
        )

        row_frame.pack(
            fill="x",
            pady=2
        )

        lbl_idx = tk.Label(
            row_frame,
            text="",
            font=(self.FONT, 9),
            width=3,
            bg=CARD,
            fg=MUTED
        )

        lbl_idx.pack(
            side="left"
        )

        time_entry = ttk.Entry(
            row_frame,
            width=20
        )

        if default_time:
            time_entry.insert(
                0,
                default_time
            )

        time_entry.pack(
            side="left",
            padx=4
        )

        level_entry = ttk.Entry(
            row_frame,
            width=16
        )

        if default_level:
            level_entry.insert(
                0,
                default_level
            )

        level_entry.pack(
            side="left",
            padx=4
        )

        del_btn = ttk.Button(
            row_frame,
            text="×",
            width=3,
            style="Danger.TButton",
            command=lambda f=row_frame:
                self._delete_water_row(f)
        )

        del_btn.pack(
            side="right",
            padx=(0, 4)
        )

        self.water_rows.append(
            {
                "frame": row_frame,
                "time": time_entry,
                "level": level_entry,
                "idx_lbl": lbl_idx
            }
        )

        self._reindex_rows()


    def _delete_water_row(
        self,
        frame_to_remove
    ):

        self.water_rows = [
            r
            for r in self.water_rows
            if r["frame"] != frame_to_remove
        ]

        frame_to_remove.destroy()

        self._reindex_rows()
        self._update_scroll_region()


    def _reindex_rows(self):

        for i, row_data in enumerate(
            self.water_rows,
            start=1
        ):

            row_data["idx_lbl"].config(
                text=str(i)
            )


    # ========================================================
    # CSV LOADING
    # ========================================================

    def load_telemetry_csv(self):

        file_path = filedialog.askopenfilename(
            title="Open Water Telemetry CSV",
            filetypes=[
                ("CSV Files", "*.csv"),
                ("All Files", "*.*")
            ]
        )

        if not file_path:
            return

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8-sig",
                newline=""
            ) as f:

                reader = csv.reader(f)
                rows = list(reader)

            if not rows:

                messagebox.showwarning(
                    "CSV Empty",
                    "The selected file contains no telemetry data."
                )

                return

            first = [
                str(x).strip().lower()
                for x in rows[0]
            ]

            header_words = (
                "time",
                "timestamp",
                "date",
                "water",
                "level",
                "water_level"
            )

            has_header = any(
                any(
                    word in cell
                    for word in header_words
                )
                for cell in first
            )

            data_rows = (
                rows[1:]
                if has_header
                else rows
            )

            for widget in (
                self.water_rows_container.winfo_children()
            ):
                widget.destroy()

            self.water_rows.clear()

            loaded = 0

            for row in data_rows:

                if len(row) < 2:
                    continue

                time_value = row[0].strip()
                level_value = row[1].strip()

                if not time_value or not level_value:
                    continue

                self._create_row_ui(
                    time_value,
                    level_value
                )

                loaded += 1

            self._update_scroll_region()

            if loaded == 0:

                messagebox.showwarning(
                    "No Valid Telemetry",
                    "No valid time/water-level records were found."
                )

                return

            # Automatically try to extract the date from a full
            # timestamp and use it for the base date field.

            first_time = (
                self.water_rows[0]["time"]
                .get()
                .strip()
            )

            parsed_first = self._parse_timestamp(
                first_time
            )

            if parsed_first:

                self.base_date_entry.delete(
                    0,
                    tk.END
                )

                self.base_date_entry.insert(
                    0,
                    parsed_first.strftime("%Y-%m-%d")
                )

            messagebox.showinfo(
                "Success",
                f"Successfully loaded {loaded} telemetry records."
            )

        except Exception as e:

            messagebox.showerror(
                "Error Reading CSV",
                f"Could not parse CSV file:\n\n{str(e)}"
            )


    # ========================================================
    # TIMESTAMP PARSER
    # ========================================================

    def _parse_timestamp(
        self,
        value
    ):

        value = str(value).strip()

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y/%m/%dT%H:%M:%S",
            "%Y/%m/%dT%H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M"
        ]

        for fmt in formats:

            try:

                return datetime.strptime(
                    value,
                    fmt
                )

            except ValueError:
                continue

        return None


    # ========================================================
    # BUILD TELEMETRY DATA
    # ========================================================

    def _collect_telemetry(self):

        base_date = (
            self.base_date_entry
            .get()
            .strip()
        )

        try:

            base_dt = datetime.strptime(
                base_date,
                "%Y-%m-%d"
            )

        except ValueError:

            raise ValueError(
                "Base date must be in YYYY-MM-DD format."
            )

        observations = []

        for row in self.water_rows:

            t_str = (
                row["time"]
                .get()
                .strip()
            )

            l_str = (
                row["level"]
                .get()
                .strip()
            )

            if not t_str and not l_str:
                continue

            if not t_str or not l_str:

                raise ValueError(
                    "Every telemetry row must contain both "
                    "time/timestamp and water level."
                )

            try:

                level = float(l_str)

            except ValueError:

                raise ValueError(
                    f"Invalid water level: {l_str}"
                )

            # Full timestamp?
            dt = self._parse_timestamp(
                t_str
            )

            if dt is None:

                # Try HH:MM
                for fmt in (
                    "%H:%M",
                    "%H:%M:%S"
                ):

                    try:

                        time_only = datetime.strptime(
                            t_str,
                            fmt
                        ).time()

                        dt = datetime.combine(
                            base_dt.date(),
                            time_only
                        )

                        break

                    except ValueError:
                        continue

            if dt is None:

                raise ValueError(
                    f"Invalid telemetry time/timestamp:\n{t_str}"
                )

            observations.append(
                {
                    "datetime": dt,
                    "level": level
                }
            )

        if len(observations) < 2:

            raise ValueError(
                "At least 2 valid water-level observations "
                "are required."
            )

        observations.sort(
            key=lambda x: x["datetime"]
        )

        # Remove duplicate timestamps.
        cleaned = []

        for obs in observations:

            if cleaned and (
                obs["datetime"]
                ==
                cleaned[-1]["datetime"]
            ):

                cleaned[-1] = obs

            else:

                cleaned.append(obs)

        observations = cleaned

        if len(observations) < 2:

            raise ValueError(
                "At least 2 unique telemetry timestamps are required."
            )

        return observations


    # ========================================================
    # CALCULATE WATER METRICS
    # ========================================================

    def _calculate_water_metrics(
        self,
        observations
    ):

        current = observations[-1]

        previous = observations[-2]

        dt_last = (
            current["datetime"]
            -
            previous["datetime"]
        ).total_seconds() / 3600.0

        if dt_last <= 0:

            raise ValueError(
                "Telemetry timestamps must be increasing."
            )

        latest_rate = (
            current["level"]
            -
            previous["level"]
        ) / dt_last

        # Previous rate
        acceleration = 0.0

        if len(observations) >= 3:

            prev = observations[-3]

            dt_prev = (
                previous["datetime"]
                -
                prev["datetime"]
            ).total_seconds() / 3600.0

            if dt_prev > 0:

                previous_rate = (
                    previous["level"]
                    -
                    prev["level"]
                ) / dt_prev

                acceleration = (
                    latest_rate
                    -
                    previous_rate
                ) / (
                    (dt_last + dt_prev) / 2.0
                )

        # Trend
        if latest_rate > 0.05:

            trend = "RISING FAST"

        elif latest_rate > 0.01:

            trend = "RISING"

        elif latest_rate < -0.05:

            trend = "FALLING"

        elif latest_rate < -0.01:

            trend = "FALLING"

        else:

            trend = "STABLE"

        # Actual 10-hour change.
        target_time = (
            current["datetime"]
            .timestamp()
            - 10 * 3600
        )

        target_dt = datetime.fromtimestamp(
            target_time
        )

        earlier = None

        for obs in observations:

            if obs["datetime"] <= target_dt:

                earlier = obs

            else:
                break

        if earlier is None:

            # Not enough history for 10 hours.
            change_10hr = (
                current["level"]
                -
                observations[0]["level"]
            )

        else:

            change_10hr = (
                current["level"]
                -
                earlier["level"]
            )

        return {
            "current_level": current["level"],
            "latest_rate": latest_rate,
            "trend": trend,
            "acceleration": acceleration,
            "change_10hr": change_10hr,
            "current_datetime": current["datetime"]
        }


    # ========================================================
    # DYNAMIC CLASS INSTANTIATION
    # ========================================================

    def _instantiate_class_dynamically(
        self,
        target_cls,
        candidate_dict
    ):

        if target_cls is None:

            raise RuntimeError(
                "Required input class was not found."
            )

        try:

            sig = inspect.signature(
                target_cls
            )

        except Exception:

            sig = inspect.signature(
                target_cls.__init__
            )

        kwargs = {}

        for name, param in sig.parameters.items():

            if name == "self":
                continue

            if name in candidate_dict:

                kwargs[name] = candidate_dict[name]

        missing = []

        for name, param in sig.parameters.items():

            if name == "self":
                continue

            if (
                param.default is inspect.Parameter.empty
                and name not in kwargs
                and param.kind in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY
                )
            ):

                missing.append(name)

        if missing:

            raise RuntimeError(
                f"{target_cls.__name__} requires: "
                + ", ".join(missing)
            )

        return target_cls(
            **kwargs
        )


    # ========================================================
    # ENGINE COMPATIBILITY
    # ========================================================

    def _run_engine_compatibly(
        self,
        rainfall,
        lake,
        water
    ):

        if run_alert_engine is None:

            raise RuntimeError(
                "run_alert_engine() is unavailable."
            )

        sig = inspect.signature(
            run_alert_engine
        )

        params = sig.parameters

        candidates = {}

        for name in params:

            low = name.lower()

            if (
                "rain" in low
                and rainfall is not None
            ):

                candidates[name] = rainfall

            elif (
                "lake" in low
                and lake is not None
            ):

                candidates[name] = lake

            elif (
                "water" in low
                or "level" in low
                or "telemetry" in low
            ) and water is not None:

                candidates[name] = water

        missing = []

        for name, param in params.items():

            if name == "self":
                continue

            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD
            ):
                continue

            if (
                param.default is inspect.Parameter.empty
                and name not in candidates
            ):

                missing.append(name)

        if missing:

            required = [
                p for p in params.values()
                if (
                    p.name != "self"
                    and p.default is inspect.Parameter.empty
                    and p.kind in (
                        inspect.Parameter.POSITIONAL_ONLY,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD
                    )
                )
            ]

            if len(required) == 3:

                return run_alert_engine(
                    rainfall,
                    lake,
                    water
                )

            raise RuntimeError(
                "Could not match alert_engine inputs.\n\n"
                f"Engine parameters: {', '.join(params.keys())}"
            )

        return run_alert_engine(
            **candidates
        )


    # ========================================================
    # SAFE RESULT ACCESS
    # ========================================================

    def _get_value(
        self,
        obj,
        names,
        default=None
    ):

        if obj is None:
            return default

        if isinstance(obj, dict):

            for name in names:

                if name in obj:
                    return obj[name]

        else:

            for name in names:

                try:

                    value = getattr(
                        obj,
                        name
                    )

                    if value is not None:
                        return value

                except Exception:
                    pass

        return default


    def _get_reasoning(
        self,
        result
    ):

        reasoning = self._get_value(
            result,
            [
                "reasoning",
                "reasons",
                "evidence",
                "explanation"
            ],
            []
        )

        if reasoning is None:
            return []

        if isinstance(
            reasoning,
            str
        ):

            return [reasoning]

        try:

            return list(reasoning)

        except Exception:

            return [str(reasoning)]


    # ========================================================
    # LOCAL PROTOTYPE ASSESSMENT
    #
    # Used as a reliable fallback if alert_engine.py
    # cannot be connected.
    # ========================================================

    def _local_prototype_assessment(
        self,
        rain_percentile,
        latest_rate,
        acceleration,
        lake_change_percent
    ):

        score = 0
        reasons = []

        # Rainfall evidence
        if rain_percentile >= 95:

            score += 2

            reasons.append(
                f"Rainfall HIGH: 7-day rainfall is at "
                f"the {rain_percentile:.1f}th historical percentile."
            )

        elif rain_percentile >= 80:

            score += 1

            reasons.append(
                f"Rainfall ELEVATED: 7-day rainfall is at "
                f"the {rain_percentile:.1f}th historical percentile."
            )

        else:

            reasons.append(
                f"Rainfall is below the elevated threshold "
                f"({rain_percentile:.1f}th percentile)."
            )

        # Water-level evidence
        if latest_rate > 0.05:

            score += 2

            reasons.append(
                f"Water level is rising rapidly at "
                f"{latest_rate:.3f} m/hour."
            )

        elif latest_rate > 0.01:

            score += 1

            reasons.append(
                f"Water level is rising at "
                f"{latest_rate:.3f} m/hour."
            )

        elif latest_rate < -0.01:

            reasons.append(
                f"Water level is falling at "
                f"{abs(latest_rate):.3f} m/hour."
            )

        else:

            reasons.append(
                "Water level is approximately stable."
            )

        # Acceleration
        if acceleration > 0.01:

            score += 1

            reasons.append(
                f"Positive water-level acceleration detected "
                f"({acceleration:.4f} m/hour²)."
            )

        # Lake-area evidence
        if lake_change_percent > 1.0:

            score += 1

            reasons.append(
                f"Latest lake area increased by "
                f"{lake_change_percent:.2f}% compared with "
                f"the previous observation."
            )

        elif lake_change_percent > 0:

            reasons.append(
                f"Latest lake area shows a small increase "
                f"of {lake_change_percent:.2f}%."
            )

        elif lake_change_percent < 0:

            reasons.append(
                f"Latest lake area decreased by "
                f"{abs(lake_change_percent):.2f}%."
            )

        else:

            reasons.append(
                "No lake-area change detected."
            )

        # Final level
        if score >= 4:

            level = "ALERT"

        elif score >= 2:

            level = "WATCH"

        else:

            level = "NORMAL"

        # Primary trigger
        if rain_percentile >= 95:

            trigger = "High rainfall evidence"

        elif latest_rate > 0.05:

            trigger = "Rapid water-level rise"

        elif lake_change_percent > 1:

            trigger = "Lake-area increase"

        else:

            trigger = "No dominant trigger"

        return {
            "alert_level": level,
            "score": score,
            "reasoning": reasons,
            "primary_trigger": trigger
        }


    # ========================================================
    # MAIN CALCULATION
    # ========================================================

    def calculate_alert(self):

        try:

            # ------------------------------------------------
            # RAINFALL
            # ------------------------------------------------

            daily = float(
                self.entries["daily"].get()
            )

            rain3 = float(
                self.entries["rain3"].get()
            )

            rain7 = float(
                self.entries["rain7"].get()
            )

            percentile = float(
                self.entries["percentile"].get()
            )

            if not 0 <= percentile <= 100:

                raise ValueError(
                    "Historical percentile must be between 0 and 100."
                )

            # ------------------------------------------------
            # LAKE AREA
            # ------------------------------------------------

            latest_area = float(
                self.entries["latest_area"].get()
            )

            previous_area = float(
                self.entries["previous_area"].get()
            )

            years = float(
                self.entries["years"].get()
            )

            if years <= 0:

                raise ValueError(
                    "Years between observations must be greater than zero."
                )

            lake_change = (
                latest_area
                -
                previous_area
            )

            lake_change_percent = (
                lake_change
                /
                previous_area
                *
                100
                if previous_area != 0
                else 0
            )

            # ------------------------------------------------
            # WATER TELEMETRY
            # ------------------------------------------------

            observations = self._collect_telemetry()

            water_metrics = self._calculate_water_metrics(
                observations
            )

            current_level = water_metrics[
                "current_level"
            ]

            latest_rate = water_metrics[
                "latest_rate"
            ]

            trend = water_metrics[
                "trend"
            ]

            acceleration = water_metrics[
                "acceleration"
            ]

            change_10hr = water_metrics[
                "change_10hr"
            ]

            # ------------------------------------------------
            # SAVE LOCAL METRICS
            # ------------------------------------------------

            self.current_metrics.update(
                {
                    "current_level": current_level,
                    "latest_rate": latest_rate,
                    "trend": trend,
                    "acceleration": acceleration,
                    "change_10hr": change_10hr,
                    "rain7": rain7,
                    "rain_percentile": percentile,
                    "lake_area": latest_area,
                    "lake_previous": previous_area,
                    "lake_change": lake_change,
                    "lake_change_percent": lake_change_percent
                }
            )

            # ------------------------------------------------
            # UPDATE WATER UI FIRST
            #
            # This is the important fix.
            # The dashboard no longer waits for the engine
            # to return water metrics.
            # ------------------------------------------------

            self._update_water_indicators(
                current_level,
                latest_rate,
                trend,
                acceleration,
                change_10hr
            )

            # ------------------------------------------------
            # UPDATE BASIC KPIs
            # ------------------------------------------------

            self.kpi_rain["value"].config(
                text=f"{rain7:.1f}"
            )

            self.kpi_lake["value"].config(
                text=f"{latest_area:.4f}"
            )

            self.kpi_water["value"].config(
                text=f"{current_level:.2f}"
            )

            # ------------------------------------------------
            # BUILD ENGINE INPUTS
            # ------------------------------------------------

            engine_result = None

            if (
                RainfallInput is not None
                and LakeAreaInput is not None
                and SimulatedWaterLevelInput is not None
                and run_alert_engine is not None
            ):

                try:

                    rain_candidates = {
                        "daily_mm": daily,
                        "daily": daily,

                        "rain_3day_mm": rain3,
                        "rainfall_3day_mm": rain3,
                        "rain3_mm": rain3,
                        "rain3": rain3,

                        "rain_7day_mm": rain7,
                        "rainfall_7day_mm": rain7,
                        "rain7_mm": rain7,
                        "rain7": rain7,

                        "historical_7day_percentile": percentile,
                        "percentile_7day": percentile,
                        "percentile": percentile
                    }

                    rain_obj = (
                        self._instantiate_class_dynamically(
                            RainfallInput,
                            rain_candidates
                        )
                    )

                    lake_candidates = {
                        "latest_area_km2": latest_area,
                        "latest_area": latest_area,

                        "previous_area_km2": previous_area,
                        "previous_area": previous_area,

                        "years_between": years,
                        "years_between_observations": years,
                        "years": years,
                        "years_span": years
                    }

                    lake_obj = (
                        self._instantiate_class_dynamically(
                            LakeAreaInput,
                            lake_candidates
                        )
                    )

                    engine_observations = [
                        {
                            "timestamp": obs["datetime"].strftime(
                                "%Y-%m-%d %H:%M"
                            ),
                            "water_level_m": obs["level"]
                        }
                        for obs in observations
                    ]

                    water_candidates = {
                        "current_level_m": current_level,
                        "current_level": current_level,

                        "change_10hr_m": change_10hr,
                        "change_10h_m": change_10hr,
                        "change_10hr": change_10hr,

                        "latest_rate_m_per_hr": latest_rate,
                        "latest_rate": latest_rate,
                        "rate_m_per_hour": latest_rate,

                        "latest_acceleration_m_per_hr2": acceleration,
                        "acceleration_m_per_hr2": acceleration,
                        "acceleration": acceleration,

                        "trend": trend,
                        "trend_category": trend,

                        "observations": engine_observations
                    }

                    water_obj = (
                        self._instantiate_class_dynamically(
                            SimulatedWaterLevelInput,
                            water_candidates
                        )
                    )

                    engine_result = (
                        self._run_engine_compatibly(
                            rain_obj,
                            lake_obj,
                            water_obj
                        )
                    )

                except Exception:
                    # The dashboard remains functional even if
                    # alert_engine.py has an incompatible API.
                    engine_result = None

            # ------------------------------------------------
            # FALLBACK / LOCAL ASSESSMENT
            # ------------------------------------------------

            local_result = (
                self._local_prototype_assessment(
                    percentile,
                    latest_rate,
                    acceleration,
                    lake_change_percent
                )
            )

            # ------------------------------------------------
            # Prefer external engine's alert level if available.
            # But ALWAYS keep local water calculations.
            # ------------------------------------------------

            final_level = local_result["alert_level"]
            final_score = local_result["score"]
            final_reasoning = local_result["reasoning"]
            final_trigger = local_result["primary_trigger"]

            if engine_result is not None:

                external_level = self._get_value(
                    engine_result,
                    [
                        "alert_level",
                        "level",
                        "alert",
                        "status",
                        "prototype_alert_level"
                    ],
                    None
                )

                external_score = self._get_value(
                    engine_result,
                    [
                        "total_score",
                        "score",
                        "risk_score",
                        "evidence_score"
                    ],
                    None
                )

                external_reasoning = (
                    self._get_reasoning(
                        engine_result
                    )
                )

                external_trigger = self._get_value(
                    engine_result,
                    [
                        "primary_trigger",
                        "trigger",
                        "main_trigger"
                    ],
                    None
                )

                if external_level:

                    normalized = self._normalize_alert_level(
                        external_level
                    )

                    if normalized:

                        final_level = normalized

                if external_score is not None:

                    try:
                        final_score = float(
                            external_score
                        )
                    except Exception:
                        pass

                if external_reasoning:

                    final_reasoning = external_reasoning

                if external_trigger:

                    final_trigger = external_trigger

            # ------------------------------------------------
            # DESCRIPTION
            # ------------------------------------------------

            description = self._make_description(
                final_level,
                percentile,
                latest_rate,
                trend,
                acceleration,
                lake_change_percent,
                current_level
            )

            self.current_metrics.update(
                {
                    "assessment": final_level,
                    "score": final_score,
                    "description": description
                }
            )

            self.last_calculation_result = {
                "alert_level": final_level,
                "total_score": final_score,
                "primary_trigger": final_trigger,
                "reasoning": final_reasoning
            }

            self.last_demo_result = None

            # ------------------------------------------------
            # UPDATE ASSESSMENT UI
            # ------------------------------------------------

            self._update_assessment_ui(
                final_level,
                final_score,
                final_trigger,
                final_reasoning,
                description
            )

            # ------------------------------------------------
            # GRAPH
            # ------------------------------------------------

            times = [
                obs["datetime"].strftime(
                    "%H:%M"
                )
                for obs in observations
            ]

            levels = [
                obs["level"]
                for obs in observations
            ]

            self._update_graph(
                times,
                levels
            )

        except ValueError as e:

            messagebox.showerror(
                "Input Error",
                f"Invalid input:\n\n{str(e)}"
            )

        except Exception as e:

            messagebox.showerror(
                "Assessment Error",
                f"An unexpected error occurred:\n\n{str(e)}"
            )


    # ========================================================
    # ALERT LEVEL NORMALIZATION
    # ========================================================

    def _normalize_alert_level(
        self,
        value
    ):

        text = str(
            value
        ).upper().strip()

        if text in (
            "GREEN",
            "NORMAL",
            "LOW"
        ):

            return "NORMAL"

        if text in (
            "YELLOW",
            "WATCH",
            "ELEVATED"
        ):

            return "WATCH"

        if text in (
            "ORANGE",
            "ALERT",
            "RED",
            "CRITICAL"
        ):

            return "ALERT"

        return None


    # ========================================================
    # DESCRIPTION
    # ========================================================

    def _make_description(
        self,
        level,
        percentile,
        rate,
        trend,
        acceleration,
        lake_change_percent,
        current_level
    ):

        if level == "ALERT":

            opening = (
                "Multiple indicators show elevated conditions "
                "requiring close attention."
            )

        elif level == "WATCH":

            opening = (
                "One or more indicators show elevated conditions "
                "that should be monitored closely."
            )

        else:

            opening = (
                "Current indicators do not show a strong "
                "multi-indicator escalation signal."
            )

        rainfall_text = (
            f"7-day rainfall is at the "
            f"{percentile:.1f}th historical percentile."
        )

        water_text = (
            f"Water level is {trend.lower()} at "
            f"{rate:.3f} m/hour, with a current level of "
            f"{current_level:.2f} m."
        )

        if acceleration > 0.01:

            acceleration_text = (
                "The rise rate is also accelerating."
            )

        elif acceleration < -0.01:

            acceleration_text = (
                "The rise rate is decreasing."
            )

        else:

            acceleration_text = (
                "No strong acceleration signal is present."
            )

        lake_text = (
            f"Latest lake area is "
            f"{lake_change_percent:+.2f}% relative to "
            f"the previous observation."
        )

        return (
            f"{opening} "
            f"{rainfall_text} "
            f"{water_text} "
            f"{acceleration_text} "
            f"{lake_text}"
        )


    # ========================================================
    # WATER INDICATORS UPDATE
    # ========================================================

    def _update_water_indicators(
        self,
        current,
        rate,
        trend,
        acceleration,
        change_10hr
    ):

        self.water_evidence[
            "CURRENT LEVEL"
        ]["value"].config(
            text=f"{current:.2f}"
        )

        self.water_evidence[
            "LATEST RISE RATE"
        ]["value"].config(
            text=f"{rate:.3f}"
        )

        self.water_evidence[
            "TREND"
        ]["value"].config(
            text=str(trend)
        )

        self.water_evidence[
            "ACCELERATION"
        ]["value"].config(
            text=f"{acceleration:.4f}"
        )

        self.water_evidence[
            "10-HOUR CHANGE"
        ]["value"].config(
            text=f"{change_10hr:+.2f}"
        )


    # ========================================================
    # ASSESSMENT UI
    # ========================================================

    def _update_assessment_ui(
        self,
        level,
        score,
        trigger,
        reasoning,
        description
    ):

        if level == "NORMAL":

            bg = GREEN_BG
            fg = GREEN

        elif level == "WATCH":

            bg = YELLOW_BG
            fg = YELLOW

        else:

            bg = ORANGE_BG
            fg = ORANGE

        self.kpi_status["value"].config(
            text=level,
            fg=fg
        )

        self.kpi_status["subtitle"].config(
            text=f"Score: {score}"
        )

        self.alert_badge.config(
            text=f"ALERT LEVEL: {level}",
            bg=bg,
            fg=fg
        )

        self.description_label.config(
            text=description
        )

        self._set_reasoning(
            f"PRIMARY TRIGGER:\n"
            f"{trigger}\n\n"
            f"REASONING & EVIDENCE:\n"
            +
            "\n".join(
                f"• {x}"
                for x in reasoning
            )
        )


    def _set_reasoning(
        self,
        text
    ):

        self.reasoning_text.config(
            state="normal"
        )

        self.reasoning_text.delete(
            "1.0",
            tk.END
        )

        self.reasoning_text.insert(
            "1.0",
            text
        )

        self.reasoning_text.config(
            state="disabled"
        )


    # ========================================================
    # GRAPH
    # ========================================================

    def _style_graph(self):

        self.ax.set_facecolor(
            CARD
        )

        self.ax.tick_params(
            colors=MUTED,
            labelsize=8
        )

        for spine in self.ax.spines.values():

            spine.set_color(
                BORDER
            )

        self.ax.grid(
            True,
            linestyle="--",
            alpha=0.5,
            color=BORDER
        )

        self.ax.set_ylabel(
            "Water Level (m)",
            color=MUTED,
            fontsize=8
        )


    def _update_graph(
        self,
        times,
        levels
    ):

        self.ax.clear()

        self._style_graph()

        if len(times) > 1:

            x_vals = list(
                range(len(times))
            )

            self.ax.plot(
                x_vals,
                levels,
                color=BLUE,
                marker="o",
                linewidth=2,
                markersize=5,
                label="Observed Level"
            )

            self.ax.set_xticks(
                x_vals
            )

            self.ax.set_xticklabels(
                times,
                rotation=30,
                ha="right",
                fontsize=7
            )

            lower = min(levels) - 0.05
            upper = max(levels) + 0.05

            if lower == upper:

                lower -= 0.1
                upper += 0.1

            self.ax.set_ylim(
                lower,
                upper
            )

            self.ax.fill_between(
                x_vals,
                lower,
                levels,
                color=LIGHT_BLUE,
                alpha=0.4
            )

            self.ax.legend(
                loc="upper left",
                fontsize=7
            )

        else:

            self.ax.text(
                0.5,
                0.5,
                "Run assessment to display telemetry trend",
                ha="center",
                va="center",
                transform=self.ax.transAxes,
                color=MUTED,
                fontsize=9
            )

        self.fig.tight_layout()

        self.canvas_plot.draw()


    # ========================================================
    # PDF REPORT
    # ========================================================

    def export_pdf_report(self):

        if not self.last_calculation_result:

            messagebox.showwarning(
                "No Data",
                "Please run an assessment before exporting a PDF report."
            )

            return

        if not PDF_AVAILABLE:

            messagebox.showerror(
                "Missing Module",
                "ReportLab is required for PDF generation."
            )

            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[
                ("PDF File", "*.pdf")
            ],
            initialfile=(
                "Thulagi_GLOF_Assessment_"
                +
                datetime.now().strftime(
                    "%Y%m%d_%H%M"
                )
                +
                ".pdf"
            )
        )

        if not file_path:
            return

        try:

            doc = SimpleDocTemplate(
                file_path,
                pagesize=A4,
                rightMargin=15 * mm,
                leftMargin=15 * mm,
                topMargin=15 * mm,
                bottomMargin=15 * mm
            )

            styles = getSampleStyleSheet()

            story = []

            metrics = self.current_metrics

            story.append(
                Paragraph(
                    "<b>THULAGI LAKE GLOF "
                    "EARLY-WARNING PROTOTYPE REPORT</b>",
                    styles["Title"]
                )
            )

            story.append(
                Paragraph(
                    "Generated on: "
                    +
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    styles["Normal"]
                )
            )

            story.append(
                Spacer(
                    1,
                    8 * mm
                )
            )

            summary = [
                [
                    "Indicator / Metric",
                    "Value / Status"
                ],
                [
                    "Assessment Level",
                    str(
                        metrics["assessment"]
                    )
                ],
                [
                    "Evidence Score",
                    str(
                        metrics["score"]
                    )
                ],
                [
                    "7-Day Rainfall",
                    f"{metrics['rain7']:.2f} mm"
                ],
                [
                    "Rainfall Percentile",
                    f"{metrics['rain_percentile']:.2f}%"
                ],
                [
                    "Lake Area",
                    f"{metrics['lake_area']:.4f} km²"
                ],
                [
                    "Lake Area Change",
                    f"{metrics['lake_change_percent']:+.2f}%"
                ],
                [
                    "Current Water Level",
                    f"{metrics['current_level']:.2f} m"
                ],
                [
                    "Rise Rate",
                    f"{metrics['latest_rate']:.3f} m/hour"
                ],
                [
                    "Trend",
                    str(metrics["trend"])
                ],
                [
                    "Acceleration",
                    f"{metrics['acceleration']:.4f} m/hour²"
                ],
                [
                    "10-Hour Change",
                    f"{metrics['change_10hr']:+.2f} m"
                ]
            ]

            table = Table(
                summary,
                colWidths=[
                    65 * mm,
                    105 * mm
                ]
            )

            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.HexColor(BLUE)
                        ),
                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            colors.white
                        ),
                        (
                            "FONTNAME",
                            (0, 0),
                            (-1, 0),
                            "Helvetica-Bold"
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.HexColor(BORDER)
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP"
                        )
                    ]
                )
            )

            story.append(table)

            story.append(
                Spacer(
                    1,
                    8 * mm
                )
            )

            story.append(
                Paragraph(
                    "<b>Description</b>",
                    styles["Heading2"]
                )
            )

            story.append(
                Paragraph(
                    metrics["description"],
                    styles["Normal"]
                )
            )

            story.append(
                Spacer(
                    1,
                    5 * mm
                )
            )

            story.append(
                Paragraph(
                    "<b>Decision Engine Evidence</b>",
                    styles["Heading2"]
                )
            )

            for reason in self._get_reasoning(
                self.last_calculation_result
            ):

                story.append(
                    Paragraph(
                        f"• {reason}",
                        styles["Normal"]
                    )
                )

            doc.build(
                story
            )

            messagebox.showinfo(
                "Export Successful",
                "Assessment PDF report successfully saved to:\n"
                +
                file_path
            )

        except Exception as e:

            messagebox.showerror(
                "PDF Export Error",
                f"Failed to generate PDF:\n\n{str(e)}"
            )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    app = GLOFEWSApp()

    app.mainloop()