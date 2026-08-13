import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path
import json

import matplotlib
matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))

from alert_engine import (
    RainfallInput,
    LakeAreaInput,
    SimulatedWaterLevelInput,
    run_alert_engine,
)


# ============================================================
# THULAGI LAKE GLOF EWS - PROTOTYPE
# ============================================================


class GLOFEWSApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Thulagi Lake GLOF EWS - Prototype")
        self.geometry("1280x900")
        self.minsize(1050, 720)

        try:
            self.state("zoomed")
        except Exception:
            pass

        self.entries = {}
        self.water_rows = []
        self.last_calculation_result = None

        self.configure(bg="#f8fafc")

        self.configure_styles()

        self.build_scrollable_container()
        self.build_header()
        self.build_top_portals()
        self.build_middle_portals()
        self.build_action_bar()
        self.build_result_section()
        self.build_footer()

        self.setup_default_telemetry_rows(5)


    # ========================================================
    # STYLES
    # ========================================================

    def configure_styles(self):

        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 20, "bold"),
            foreground="#0f172a"
        )

        style.configure(
            "Subtitle.TLabel",
            font=("Segoe UI", 10),
            foreground="#64748b"
        )

        style.configure(
            "Section.TLabelframe.Label",
            font=("Segoe UI", 11, "bold"),
            foreground="#1e3a8a"
        )

        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=8
        )

        style.configure(
            "Footer.TLabel",
            font=("Segoe UI", 10, "bold"),
            foreground="#64748b"
        )


    # ========================================================
    # SCROLLABLE MAIN CONTAINER
    # ========================================================

    def build_scrollable_container(self):

        self.canvas = tk.Canvas(
            self,
            borderwidth=0,
            highlightthickness=0,
            bg="#f8fafc"
        )

        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )

        self.scroll_frame = ttk.Frame(
            self.canvas,
            padding=18
        )

        self.scroll_frame.bind(
            "<Configure>",
            lambda event: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
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

        self.canvas.bind(
            "<Configure>",
            self.resize_scroll_frame
        )

        self.bind_all(
            "<MouseWheel>",
            self.mousewheel_scroll
        )


    def resize_scroll_frame(self, event):

        self.canvas.itemconfig(
            self.canvas_window,
            width=event.width
        )


    def mousewheel_scroll(self, event):

        self.canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )


    # ========================================================
    # HEADER
    # ========================================================

    def build_header(self):

        header = ttk.Frame(self.scroll_frame)
        header.pack(fill="x", pady=(0, 12))

        ttk.Label(
            header,
            text="THULAGI LAKE GLOF EARLY WARNING SYSTEM",
            style="Title.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            header,
            text="Prototype Decision-Support Dashboard",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(2, 0))


    # ========================================================
    # GENERIC INPUT
    # ========================================================

    def add_input(
        self,
        parent,
        label_text,
        key,
        default=""
    ):

        row = ttk.Frame(parent)
        row.pack(fill="x", pady=3)

        ttk.Label(
            row,
            text=label_text,
            width=34,
            anchor="w"
        ).pack(side="left")

        entry = ttk.Entry(
            row,
            width=20
        )

        entry.insert(
            0,
            default
        )

        entry.pack(
            side="left",
            padx=5
        )

        self.entries[key] = entry


    # ========================================================
    # TOP PORTALS
    # ========================================================

    def build_top_portals(self):

        grid = ttk.Frame(self.scroll_frame)
        grid.pack(fill="x", pady=5)

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)


        # ----------------------------------------------------
        # RAINFALL
        # ----------------------------------------------------

        rainfall_frame = ttk.LabelFrame(
            grid,
            text=" 1. REAL RAINFALL ",
            padding=12,
            style="Section.TLabelframe"
        )

        rainfall_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 6)
        )

        self.add_input(
            rainfall_frame,
            "Daily rainfall (mm):",
            "daily",
            "10.47"
        )

        self.add_input(
            rainfall_frame,
            "3-day rainfall (mm):",
            "rain3",
            "46.50"
        )

        self.add_input(
            rainfall_frame,
            "7-day rainfall (mm):",
            "rain7",
            "132.45"
        )

        self.add_input(
            rainfall_frame,
            "Historical 7-day percentile (0–100):",
            "percentile",
            "97.84"
        )


        # ----------------------------------------------------
        # LAKE AREA
        # ----------------------------------------------------

        lake_frame = ttk.LabelFrame(
            grid,
            text=" 2. SATELLITE LAKE AREA ",
            padding=12,
            style="Section.TLabelframe"
        )

        lake_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(6, 0)
        )

        self.add_input(
            lake_frame,
            "Latest lake area (km²):",
            "latest_area",
            "0.9291"
        )

        self.add_input(
            lake_frame,
            "Previous lake area (km²):",
            "previous_area",
            "0.9167"
        )

        self.add_input(
            lake_frame,
            "Years between observations:",
            "years",
            "1"
        )


    # ========================================================
    # WATER LEVEL + GRAPH
    # ========================================================

    def build_middle_portals(self):

        grid = ttk.Frame(self.scroll_frame)
        grid.pack(fill="x", pady=10)

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)


        # ----------------------------------------------------
        # WATER LEVEL
        # ----------------------------------------------------

        water_frame = ttk.LabelFrame(
            grid,
            text=" 3. WATER-LEVEL TELEMETRY ",
            padding=12,
            style="Section.TLabelframe"
        )

        water_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 6)
        )

        date_row = ttk.Frame(water_frame)
        date_row.pack(
            fill="x",
            pady=(0, 8)
        )

        ttk.Label(
            date_row,
            text="Observation Date:",
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        self.base_date_entry = ttk.Entry(
            date_row,
            width=15
        )

        self.base_date_entry.insert(
            0,
            datetime.now().strftime("%Y-%m-%d")
        )

        self.base_date_entry.pack(
            side="left",
            padx=8
        )


        self.water_input_container = ttk.Frame(
            water_frame
        )

        self.water_input_container.pack(
            fill="x"
        )


        # Header

        header = ttk.Frame(
            self.water_input_container
        )

        header.pack(
            fill="x",
            pady=2
        )

        ttk.Label(
            header,
            text="#",
            width=4,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        ttk.Label(
            header,
            text="Time",
            width=15,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        ttk.Label(
            header,
            text="Water Level (m)",
            width=18,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")


        # Buttons

        button_row = ttk.Frame(
            water_frame
        )

        button_row.pack(
            fill="x",
            pady=(8, 0)
        )

        ttk.Button(
            button_row,
            text="+ Add Row",
            command=self.add_water_observation_row
        ).pack(side="left")

        ttk.Button(
            button_row,
            text="Reset to 5 Rows",
            command=lambda: self.setup_default_telemetry_rows(5)
        ).pack(
            side="left",
            padx=5
        )


        # ----------------------------------------------------
        # GRAPH
        # ----------------------------------------------------

        graph_frame = ttk.LabelFrame(
            grid,
            text=" WATER-LEVEL TREND ",
            padding=10,
            style="Section.TLabelframe"
        )

        graph_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(6, 0)
        )

        self.fig = Figure(
            figsize=(5.5, 3.3),
            dpi=100
        )

        self.ax = self.fig.add_subplot(111)

        self.ax.set_title(
            "Water Level Telemetry",
            fontsize=10
        )

        self.ax.set_xlabel(
            "Time",
            fontsize=9
        )

        self.ax.set_ylabel(
            "Water Level (m)",
            fontsize=9
        )

        self.ax.grid(
            True,
            linestyle="--",
            alpha=0.4
        )

        self.fig.tight_layout()

        self.plot_canvas = FigureCanvasTkAgg(
            self.fig,
            master=graph_frame
        )

        self.plot_canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )


    # ========================================================
    # WATER LEVEL ROWS
    # ========================================================

    def setup_default_telemetry_rows(
        self,
        count=5
    ):

        for widget in self.water_input_container.winfo_children()[1:]:
            widget.destroy()

        self.water_rows.clear()

        default_times = [
            "08:00",
            "10:00",
            "12:00",
            "14:00",
            "16:00"
        ]

        default_levels = [
            "4.20",
            "4.32",
            "4.45",
            "4.60",
            "4.74"
        ]

        for i in range(count):

            time_value = (
                default_times[i]
                if i < len(default_times)
                else "18:00"
            )

            level_value = (
                default_levels[i]
                if i < len(default_levels)
                else "4.85"
            )

            self.create_water_row(
                i + 1,
                time_value,
                level_value
            )


    def add_water_observation_row(self):

        index = len(self.water_rows) + 1

        self.create_water_row(
            index,
            "",
            ""
        )


    def create_water_row(
        self,
        index,
        default_time,
        default_level
    ):

        row = ttk.Frame(
            self.water_input_container
        )

        row.pack(
            fill="x",
            pady=2
        )

        ttk.Label(
            row,
            text=f"{index}.",
            width=4
        ).pack(side="left")

        time_entry = ttk.Entry(
            row,
            width=15
        )

        time_entry.insert(
            0,
            default_time
        )

        time_entry.pack(
            side="left"
        )

        level_entry = ttk.Entry(
            row,
            width=18
        )

        level_entry.insert(
            0,
            default_level
        )

        level_entry.pack(
            side="left",
            padx=4
        )

        self.water_rows.append(
            (
                time_entry,
                level_entry
            )
        )


    # ========================================================
    # ACTION BAR
    # ========================================================

    def build_action_bar(self):

        bar = ttk.Frame(
            self.scroll_frame
        )

        bar.pack(
            fill="x",
            pady=10
        )

        ttk.Button(
            bar,
            text="CALCULATE ALERT",
            style="Accent.TButton",
            command=self.calculate
        ).pack(
            side="left",
            padx=(0, 8)
        )

        ttk.Button(
            bar,
            text="Export Report",
            command=self.export_report
        ).pack(
            side="left"
        )

        ttk.Button(
            bar,
            text="EXIT",
            command=self.destroy
        ).pack(
            side="right"
        )


    # ========================================================
    # RESULT SECTION
    # ========================================================

    def build_result_section(self):

        self.result_frame = tk.LabelFrame(
            self.scroll_frame,
            text=" ALERT ASSESSMENT ",
            font=("Segoe UI", 11, "bold"),
            bg="#f8fafc",
            fg="#1e293b",
            padx=15,
            pady=15
        )

        self.result_frame.pack(
            fill="x",
            pady=(5, 10)
        )


        self.alert_badge = tk.Label(
            self.result_frame,
            text="NO CALCULATION",
            font=("Segoe UI", 22, "bold"),
            bg="#e2e8f0",
            fg="#475569",
            padx=20,
            pady=12
        )

        self.alert_badge.pack(
            fill="x",
            pady=(0, 10)
        )


        self.score_label = tk.Label(
            self.result_frame,
            text="Enter data and click CALCULATE ALERT.",
            font=("Segoe UI", 11),
            bg="#f8fafc",
            fg="#475569"
        )

        self.score_label.pack(
            anchor="w",
            pady=(0, 8)
        )


        self.details_label = tk.Label(
            self.result_frame,
            text="",
            justify="left",
            anchor="w",
            bg="#f8fafc",
            fg="#1e293b",
            font=("Consolas", 10),
            wraplength=1150
        )

        self.details_label.pack(
            fill="x",
            anchor="w"
        )


    # ========================================================
    # FOOTER
    # ========================================================

    def build_footer(self):

        ttk.Separator(
            self.scroll_frame,
            orient="horizontal"
        ).pack(
            fill="x",
            pady=(10, 8)
        )

        ttk.Label(
            self.scroll_frame,
            text="This is a prototype.",
            style="Footer.TLabel"
        ).pack(
            anchor="center",
            pady=(0, 15)
        )


    # ========================================================
    # GET FLOAT
    # ========================================================

    def get_float(self, key):

        value = self.entries[key].get().strip()

        if not value:
            raise ValueError(
                f"Missing value: {key}"
            )

        return float(value)


    # ========================================================
    # WATER LEVEL PROCESSING
    # ========================================================

    def calculate_water_level(self):

        date_text = (
            self.base_date_entry
            .get()
            .strip()
        )

        if not date_text:

            raise ValueError(
                "Please enter the observation date."
            )

        observations = []

        for time_entry, level_entry in self.water_rows:

            time_text = time_entry.get().strip()
            level_text = level_entry.get().strip()

            if not time_text or not level_text:
                continue

            timestamp = datetime.strptime(
                f"{date_text} {time_text}",
                "%Y-%m-%d %H:%M"
            )

            level = float(level_text)

            observations.append(
                (
                    timestamp,
                    level
                )
            )

        if len(observations) < 2:

            raise ValueError(
                "Enter at least two water-level observations."
            )

        observations.sort(
            key=lambda x: x[0]
        )

        latest_time, latest_level = observations[-1]

        previous_time, previous_level = observations[-2]

        dt_hours = (
            latest_time - previous_time
        ).total_seconds() / 3600

        if dt_hours <= 0:

            raise ValueError(
                "Water-level times must be increasing."
            )

        # Automatically calculated.
        rate = (
            latest_level - previous_level
        ) / dt_hours

        if rate > 0:
            trend = "RISING"
        elif rate < 0:
            trend = "FALLING"
        else:
            trend = "STABLE"

        if len(observations) >= 3:

            t1, l1 = observations[-3]
            t2, l2 = observations[-2]

            previous_dt = (
                t2 - t1
            ).total_seconds() / 3600

            if previous_dt > 0:

                previous_rate = (
                    l2 - l1
                ) / previous_dt

                acceleration = (
                    rate - previous_rate
                ) / dt_hours

            else:
                acceleration = 0.0

        else:

            acceleration = 0.0

        change_10hr = rate * 10

        water = SimulatedWaterLevelInput(
            current_level_m=latest_level,
            change_10hr_m=change_10hr,
            latest_rate_m_per_hr=rate,
            latest_acceleration_m_per_hr2=acceleration,
            trend=trend
        )

        return water, observations


    # ========================================================
    # UPDATE GRAPH
    # ========================================================

    def update_plot(
        self,
        observations
    ):

        self.ax.clear()

        times = [
            item[0].strftime("%H:%M")
            for item in observations
        ]

        levels = [
            item[1]
            for item in observations
        ]

        self.ax.plot(
            times,
            levels,
            marker="o",
            linewidth=2
        )

        self.ax.set_title(
            "Water Level Telemetry",
            fontsize=10,
            fontweight="bold"
        )

        self.ax.set_xlabel(
            "Time"
        )

        self.ax.set_ylabel(
            "Water Level (m)"
        )

        self.ax.grid(
            True,
            linestyle="--",
            alpha=0.4
        )

        self.fig.tight_layout()

        self.plot_canvas.draw()


    # ========================================================
    # COLOR ALERT
    # ========================================================

    def set_alert_color(
        self,
        level
    ):

        level = level.upper()

        if level == "NORMAL":

            bg = "#22c55e"
            fg = "white"

        elif level == "WATCH":

            bg = "#f59e0b"
            fg = "white"

        elif level == "ALERT":

            bg = "#dc2626"
            fg = "white"

        else:

            bg = "#64748b"
            fg = "white"

        self.alert_badge.config(
            text=f"PROTOTYPE ALERT: {level}",
            bg=bg,
            fg=fg
        )


    # ========================================================
    # CALCULATE ALERT
    # ========================================================

    def calculate(self):

        try:

            # ------------------------------------------------
            # Rainfall
            # ------------------------------------------------

            rainfall = RainfallInput(
                daily_mm=self.get_float("daily"),
                rainfall_3day_mm=self.get_float("rain3"),
                rainfall_7day_mm=self.get_float("rain7"),
                historical_7day_percentile=self.get_float(
                    "percentile"
                )
            )


            # ------------------------------------------------
            # Lake
            # ------------------------------------------------

            lake = LakeAreaInput(
                latest_area_km2=self.get_float(
                    "latest_area"
                ),
                previous_area_km2=self.get_float(
                    "previous_area"
                ),
                years_between_observations=self.get_float(
                    "years"
                )
            )


            # ------------------------------------------------
            # Water
            # ------------------------------------------------

            water, observations = (
                self.calculate_water_level()
            )

            self.update_plot(
                observations
            )


            # ------------------------------------------------
            # Alert engine
            # ------------------------------------------------

            result = run_alert_engine(
                rainfall,
                lake,
                water
            )


            # ------------------------------------------------
            # Lake change
            # ------------------------------------------------

            lake_change = (
                (
                    lake.latest_area_km2
                    -
                    lake.previous_area_km2
                )
                /
                lake.previous_area_km2
            ) * 100


            # ------------------------------------------------
            # Alert color
            # ------------------------------------------------

            self.set_alert_color(
                result.level
            )


            self.score_label.config(
                text=(
                    f"Prototype score: "
                    f"{result.score}/"
                    f"{result.max_score}"
                )
            )


            # ------------------------------------------------
            # Details
            # ------------------------------------------------

            details = (
                "INDICATOR SCORES\n"
                "--------------------------------------------------\n"
                f"Rainfall:   "
                f"{result.rainfall_score}/2\n"
                f"            {result.rainfall_status}\n\n"

                f"Lake area:  "
                f"{result.lake_growth_score}/2\n"
                f"            {result.lake_growth_status}\n"
                f"            Latest change: "
                f"{lake_change:+.2f}%\n\n"

                "WATER-LEVEL TELEMETRY\n"
                "--------------------------------------------------\n"
                f"Latest level:     "
                f"{water.current_level_m:.2f} m\n"
                f"Calculated rate:  "
                f"{water.latest_rate_m_per_hr:+.3f} m/hr\n"
                f"Calculated trend: "
                f"{water.trend}\n"
                f"Calculated acceleration: "
                f"{water.latest_acceleration_m_per_hr2:+.3f} m/hr²\n\n"

                "PRIMARY DRIVERS\n"
                "--------------------------------------------------\n"
            )


            if result.primary_drivers:

                details += "\n".join(
                    f"- {driver}"
                    for driver in result.primary_drivers
                )

            else:

                details += (
                    "- No individual indicator "
                    "elevated above baseline."
                )


            details += (
                "\n\n"
                "--------------------------------------------------\n"
                "Water-level telemetry is displayed separately "
                "and does not contribute to the prototype alert score."
            )


            self.details_label.config(
                text=details
            )


            # ------------------------------------------------
            # Save result for export
            # ------------------------------------------------

            self.last_calculation_result = {

                "timestamp":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                "alert_level":
                    result.level,

                "score":
                    f"{result.score}/{result.max_score}",

                "rainfall_score":
                    result.rainfall_score,

                "lake_area_score":
                    result.lake_growth_score,

                "latest_lake_area_km2":
                    lake.latest_area_km2,

                "previous_lake_area_km2":
                    lake.previous_area_km2,

                "lake_change_percent":
                    lake_change,

                "latest_water_level_m":
                    water.current_level_m,

                "calculated_water_level_rate_m_per_hr":
                    water.latest_rate_m_per_hr,

                "calculated_water_level_trend":
                    water.trend,

                "details":
                    details
            }


        except ValueError as e:

            messagebox.showerror(
                "Invalid Input",
                str(e)
            )

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Could not calculate alert:\n\n{e}"
            )


    # ========================================================
    # EXPORT
    # ========================================================

    def export_report(self):

        if not self.last_calculation_result:

            messagebox.showwarning(
                "No Result",
                "Calculate an alert first."
            )

            return


        path = filedialog.asksaveasfilename(

            title="Export Prototype Alert Report",

            defaultextension=".txt",

            filetypes=[
                ("Text File", "*.txt"),
                ("JSON File", "*.json")
            ]
        )


        if not path:
            return


        if path.lower().endswith(".json"):

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    self.last_calculation_result,
                    f,
                    indent=4
                )

        else:

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(
                    "THULAGI LAKE GLOF EWS - PROTOTYPE\n"
                )

                f.write(
                    "=" * 60 + "\n\n"
                )

                f.write(
                    f"Alert Level: "
                    f"{self.last_calculation_result['alert_level']}\n"
                )

                f.write(
                    f"Score: "
                    f"{self.last_calculation_result['score']}\n\n"
                )

                f.write(
                    self.last_calculation_result[
                        "details"
                    ]
                )


        messagebox.showinfo(
            "Export Successful",
            f"Report saved to:\n{path}"
        )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    app = GLOFEWSApp()

    app.mainloop()