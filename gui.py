import customtkinter as ctk
import browser_extractor
import os
import sys
import subprocess
import threading
import logging
import webbrowser
from tkinter import messagebox
from datetime import datetime
from PIL import Image
import analyzer  # Added for Insights Dashboard

# Configure logging for the GUI
logger = logging.getLogger("AdharshBrowserAuditorGUI")

VERSION = "v2.2.0-enterprise"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class MetricsCard(ctk.CTkFrame):
    def __init__(self, master, title, value, icon, color, **kwargs):
        super().__init__(master, fg_color="#1e293b", corner_radius=12, border_width=1, border_color="#334155", **kwargs)
        self.grid_columnconfigure(1, weight=1)
        self.icon_label = ctk.CTkLabel(self, text=icon, font=("Inter", 24), text_color=color)
        self.icon_label.grid(row=0, column=0, rowspan=2, padx=(15, 10), pady=15, sticky="w")
        self.title_label = ctk.CTkLabel(self, text=title.upper(), font=("Inter", 10, "bold"), text_color="#94a3b8")
        self.title_label.grid(row=0, column=1, padx=(0, 15), pady=(15, 0), sticky="nw")
        self.value_label = ctk.CTkLabel(self, text=value, font=("Inter", 20, "bold"), text_color="#f8fafc")
        self.value_label.grid(row=1, column=1, padx=(0, 15), pady=(0, 15), sticky="nw")

    def update_value(self, new_value):
        self.value_label.configure(text=new_value)


class BrowserExtractorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"Adharsh Browser Auditor {VERSION}")
        self.geometry("1400x850")

        icon_path = resource_path("app_logo.ico")
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except: pass

        # Premium Enterprise Design Tokens
        self.primary_color = "#3b82f6"
        self.success_color = "#10b981"
        self.warning_color = "#f59e0b"
        self.danger_color = "#ef4444"
        self.sidebar_color = "#0f172a"
        self.bg_color = "#020617"
        self.card_color = "#1e293b"
        self.border_color = "#334155"
        self.text_primary = "#f8fafc"
        self.text_muted = "#94a3b8"

        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=self.bg_color)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_analysis = None
        self.active_category_filter = None

        # ---------------- SIDEBAR ----------------
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=self.sidebar_color, border_width=0, border_color=self.border_color)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        # Logo Area
        self.logo_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, padx=20, pady=(30, 20), sticky="ew")

        logo_path = resource_path("app_logo.png")
        if os.path.exists(logo_path):
            try:
                logo_image = ctk.CTkImage(light_image=Image.open(logo_path), dark_image=Image.open(logo_path), size=(40, 40))
                self.logo_img_label = ctk.CTkLabel(self.logo_frame, image=logo_image, text="")
                self.logo_img_label.pack(side="left", padx=(0, 10))
            except Exception as e:
                logger.error(f"Failed to load sidebar logo: {e}")

        self.logo_label = ctk.CTkLabel(self.logo_frame, text="AUDITOR", font=ctk.CTkFont(family="Inter", size=20, weight="bold"), text_color=self.primary_color)
        self.logo_label.pack(side="left")

        # Privacy Banner in Sidebar
        self.privacy_banner = ctk.CTkFrame(self.sidebar_frame, fg_color="#0d2818", corner_radius=8, border_width=1, border_color="#166534")
        self.privacy_banner.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(self.privacy_banner, text="🔒 PRIVACY FIRST", font=("Inter", 10, "bold"), text_color="#22c55e").pack(anchor="w", padx=12, pady=(8, 0))
        ctk.CTkLabel(self.privacy_banner, text="All data stays on YOUR device.\nZero data leaves your computer.", font=("Inter", 9), text_color="#86efac", wraplength=230, justify="left").pack(anchor="w", padx=12, pady=(2, 8))

        # Profiles Header
        self.profiles_label = ctk.CTkLabel(self.sidebar_frame, text="DETECTED PROFILES", font=("Inter", 10, "bold"), text_color=self.text_muted)
        self.profiles_label.grid(row=2, column=0, padx=20, pady=(5, 5), sticky="w")

        # Profile List
        self.profile_list_frame = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent", corner_radius=0)
        self.profile_list_frame.grid(row=3, column=0, sticky="nsew", padx=10)
        self.sidebar_frame.grid_rowconfigure(3, weight=1)

        self.profile_buttons = {}
        self.current_browser = None

        # Bottom Sidebar
        self.bottom_sidebar = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.bottom_sidebar.grid(row=4, column=0, sticky="ew", padx=20, pady=20)

        self.creator_label = ctk.CTkLabel(self.bottom_sidebar, text="Developed by Adharsh Kumar Bachu", font=("Inter", 9, "italic"), text_color=self.text_muted)
        self.creator_label.pack(anchor="w", pady=(0, 15))

        self.theme_label = ctk.CTkLabel(self.bottom_sidebar, text="System Theme", font=("Inter", 10, "bold"), text_color=self.text_muted)
        self.theme_label.pack(anchor="w", pady=(0, 5))

        self.theme_menu = ctk.CTkOptionMenu(self.bottom_sidebar, values=["Dark", "Light", "System"], command=self.change_appearance, fg_color=self.card_color, button_color=self.border_color, button_hover_color=self.primary_color)
        self.theme_menu.pack(fill="x")
        self.theme_menu.set("Dark")

        # ---------------- MAIN CONTENT ----------------
        self.main_content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(2, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 30))
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.status_title = ctk.CTkLabel(self.header_frame, text="Overview", font=("Inter", 32, "bold"), text_color=self.text_primary)
        self.status_title.grid(row=0, column=0, sticky="w")

        self.status_subtitle = ctk.CTkLabel(self.header_frame, text="Select a profile to view insights from your environment.", font=("Inter", 14), text_color=self.text_muted)
        self.status_subtitle.grid(row=1, column=0, sticky="w")

        self.global_scan_btn = ctk.CTkButton(self.header_frame, text="Global Security Scan", command=self.start_scan, fg_color=self.primary_color, hover_color="#2563eb", font=("Inter", 14, "bold"), height=45, width=180, corner_radius=8)
        self.global_scan_btn.grid(row=0, column=1, rowspan=2, sticky="e")

        # Metrics Row
        self.metrics_row = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.metrics_row.grid(row=1, column=0, sticky="ew", pady=(0, 30))
        self.metrics_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="metric")

        self.card_history = MetricsCard(self.metrics_row, "History Items", "-", "🕒", self.primary_color)
        self.card_history.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.card_downloads = MetricsCard(self.metrics_row, "Downloads", "-", "📥", self.success_color)
        self.card_downloads.grid(row=0, column=1, sticky="ew", padx=(5, 10))

        self.card_extensions = MetricsCard(self.metrics_row, "Extensions", "-", "🧩", self.warning_color)
        self.card_extensions.grid(row=0, column=2, sticky="ew", padx=(5, 10))

        self.card_cache = MetricsCard(self.metrics_row, "Cache Size", "-", "💾", "#8b5cf6")
        self.card_cache.grid(row=0, column=3, sticky="ew", padx=(5, 0))

        # Main Dashboard — Split View
        self.dashboard_split_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.dashboard_split_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 20))

        # -------- LEFT COLUMN: INSIGHTS / WELLNESS / HEATMAP / TRENDS --------
        self.insights_dashboard_frame = ctk.CTkFrame(self.dashboard_split_frame, fg_color="transparent")
        self.insights_dashboard_frame.pack(side="left", fill="both", expand=True, padx=(0, 20))

        # Wellness Panel placeholder (dynamic)
        self.wellness_panel = ctk.CTkFrame(self.insights_dashboard_frame, fg_color="transparent", corner_radius=0)

        # Insights Container (scrollable, holds everything on the left)
        self.insights_container = ctk.CTkFrame(self.insights_dashboard_frame, fg_color=self.card_color, corner_radius=12, border_color=self.border_color, border_width=1)
        self.insights_container.pack(fill="both", expand=True)

        self.insights_header = ctk.CTkLabel(self.insights_container, text="📊 Insights & Wellness Overview", font=("Inter", 14, "bold"), text_color=self.text_primary)
        self.insights_header.pack(anchor="w", padx=20, pady=(15, 2))

        self.insights_sub = ctk.CTkLabel(self.insights_container, text="Click a category to filter history", font=("Inter", 11), text_color=self.text_muted)
        self.insights_sub.pack(anchor="w", padx=20, pady=(0, 5))

        self.insights_scroll = ctk.CTkScrollableFrame(self.insights_container, fg_color="transparent")
        self.insights_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        ctk.CTkLabel(self.insights_scroll, text="Awaiting profile selection...", text_color=self.text_muted).pack(pady=50, fill="x")

        self.analyzer_instance = analyzer.BrowserHistoryAnalyzer()

        # -------- RIGHT COLUMN: DATA TABS --------
        self.right_tab_container = ctk.CTkFrame(self.dashboard_split_frame, fg_color="transparent")
        self.right_tab_container.pack(side="right", fill="both", expand=True)
        self.right_tab_container.grid_columnconfigure(0, weight=1)
        self.right_tab_container.grid_rowconfigure(0, weight=1)

        self.data_tabs = ctk.CTkTabview(self.right_tab_container, corner_radius=12, fg_color=self.card_color,
                                        segmented_button_selected_color=self.primary_color,
                                        segmented_button_unselected_color=self.bg_color,
                                        segmented_button_selected_hover_color=self.primary_color,
                                        text_color=self.text_primary)
        self.data_tabs.grid(row=0, column=0, sticky="nsew")

        self.data_tabs.add("History Engine")
        self.data_tabs.add("Download Vault")
        self.data_tabs.add("Extension Modules")
        self.data_tabs.add("System & Cache")

        # History Tab
        self.history_frame = self.data_tabs.tab("History Engine")
        self.history_frame.grid_columnconfigure(0, weight=1)
        self.history_frame.grid_rowconfigure(1, weight=1)

        self.history_filter_bar = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        self.history_filter_bar.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 0))

        self.filter_label = ctk.CTkLabel(self.history_filter_bar, text="Filter:", font=("Inter", 12, "bold"), text_color=self.text_muted)
        self.filter_label.pack(side="left", padx=(0, 8))

        self.show_all_btn = ctk.CTkButton(self.history_filter_bar, text="📋 Show All", width=90, height=28,
                                           fg_color=self.primary_color, hover_color="#2563eb",
                                           font=("Inter", 11, "bold"), corner_radius=6,
                                           command=self.clear_category_filter)
        self.show_all_btn.pack(side="left", padx=(0, 5))

        self.active_filter_label = ctk.CTkLabel(self.history_filter_bar, text="", font=("Inter", 12, "bold"), text_color=self.warning_color)
        self.active_filter_label.pack(side="left", padx=(10, 0))

        self.history_text = ctk.CTkTextbox(self.history_frame, font=("Inter", 13), fg_color=self.bg_color, text_color=self.text_primary, corner_radius=8, border_color=self.border_color, border_width=1)
        self.history_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)

        self.history_actions = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        self.history_actions.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))

        self.history_range = ctk.CTkOptionMenu(self.history_actions, values=["Last Hour", "Last 24 Hours", "All Time"], fg_color=self.bg_color, button_color=self.border_color, text_color=self.text_primary)
        self.history_range.pack(side="left", padx=(0, 15))

        self.wipe_history_btn = ctk.CTkButton(self.history_actions, text="Wipe Engine History", command=self.on_clear_history, fg_color=self.danger_color, hover_color="#b91c1c", font=("Inter", 13, "bold"), height=35)
        self.wipe_history_btn.pack(side="left")

        # Downloads Tab
        self.downloads_frame = self.data_tabs.tab("Download Vault")
        self.downloads_frame.grid_columnconfigure(0, weight=1)
        self.downloads_frame.grid_rowconfigure(0, weight=1)
        self.downloads_scroll = ctk.CTkScrollableFrame(self.downloads_frame, fg_color=self.bg_color, corner_radius=8, border_color=self.border_color, border_width=1)
        self.downloads_scroll.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        # Extensions Tab
        self.ext_frame = self.data_tabs.tab("Extension Modules")
        self.ext_frame.grid_columnconfigure(0, weight=1)
        self.ext_frame.grid_rowconfigure(0, weight=1)
        self.ext_text = ctk.CTkTextbox(self.ext_frame, font=("Inter", 13), fg_color=self.bg_color, text_color=self.text_primary, corner_radius=8, border_color=self.border_color, border_width=1)
        self.ext_text.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        # System Tab
        self.sys_frame = self.data_tabs.tab("System & Cache")
        self.sys_frame.grid_columnconfigure(0, weight=1)
        self.sys_info_panel = ctk.CTkFrame(self.sys_frame, fg_color=self.bg_color, corner_radius=8, border_color=self.border_color, border_width=1)
        self.sys_info_panel.pack(fill="x", padx=20, pady=20)
        self.sys_info_label = ctk.CTkLabel(self.sys_info_panel, text="No profile selected.", font=("Inter", 15), justify="left", text_color=self.text_primary)
        self.sys_info_label.pack(padx=30, pady=30, anchor="w")
        self.wipe_cache_btn = ctk.CTkButton(self.sys_frame, text="Purge Cache Files", command=self.on_clear_cache, fg_color=self.warning_color, hover_color="#d97706", font=("Inter", 13, "bold"), height=45)
        self.wipe_cache_btn.pack(fill="x", padx=20, pady=(0, 20))

        # Bottom Status Bar
        self.status_bar = ctk.CTkFrame(self, height=40, corner_radius=0, fg_color=self.card_color, border_width=1, border_color=self.border_color)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_bar.grid_columnconfigure(1, weight=1)
        self.status_msg = ctk.CTkLabel(self.status_bar, text="Ready", font=("Inter", 12), text_color=self.text_muted)
        self.status_msg.grid(row=0, column=0, padx=30, sticky="w")
        self.clock_lbl = ctk.CTkLabel(self.status_bar, text="", font=("Inter", 12, "bold"), text_color=self.text_primary)
        self.clock_lbl.grid(row=0, column=1, padx=30, sticky="e")

        self.data = {}
        self.update_clock()
        self.after(500, self.start_scan)

    # ======================== BASIC METHODS ========================

    def change_appearance(self, mode):
        ctk.set_appearance_mode(mode)

    def update_clock(self):
        self.clock_lbl.configure(text=datetime.now().strftime("%I:%M:%S %p  |  %Y-%m-%d"))
        self.after(1000, self.update_clock)

    def set_status(self, msg, is_error=False):
        self.status_msg.configure(text=msg, text_color=self.danger_color if is_error else self.text_muted)
        if is_error: logger.error(msg)
        else: logger.info(msg)

    def start_scan(self):
        self.set_status("Executing Global Environment Scan...")
        self.global_scan_btn.configure(state="disabled", text="Scanning Engine...")
        threading.Thread(target=self.scan_logic, daemon=True).start()

    def scan_logic(self):
        try:
            self.data = browser_extractor.get_all_browsers_data()
            self.after(0, self.on_scan_complete)
        except Exception as e:
            self.after(0, lambda: self.set_status(f"Scan Failure: {e}", True))
            self.after(0, lambda: self.global_scan_btn.configure(state="normal", text="Global Security Scan"))

    def on_scan_complete(self):
        self.set_status("Scan Complete. Security Profiles Loaded.")
        self.global_scan_btn.configure(state="normal", text="Global Security Scan")
        self.build_sidebar_profiles()
        if self.data:
            if not self.current_browser or self.current_browser not in self.data:
                first_browser = list(self.data.keys())[0]
                self.select_profile(first_browser)
            else:
                self.select_profile(self.current_browser)

    def build_sidebar_profiles(self):
        for widget in self.profile_list_frame.winfo_children():
            widget.destroy()
        self.profile_buttons.clear()
        if not self.data:
            ctk.CTkLabel(self.profile_list_frame, text="No profiles detected.", text_color=self.text_muted).pack(pady=20)
            return
        for browser_id in self.data.keys():
            btn = ctk.CTkButton(self.profile_list_frame, text=browser_id, anchor="w", fg_color="transparent",
                                text_color=self.text_primary, hover_color=self.card_color, corner_radius=8, font=("Inter", 13),
                                height=38, command=lambda b=browser_id: self.select_profile(b))
            btn.pack(fill="x", pady=4, padx=5)
            self.profile_buttons[browser_id] = btn

    def select_profile(self, browser_id):
        if self.current_browser and self.current_browser in self.profile_buttons:
            self.profile_buttons[self.current_browser].configure(fg_color="transparent", text_color=self.text_primary)
        self.current_browser = browser_id
        self.active_category_filter = None
        if browser_id in self.profile_buttons:
            self.profile_buttons[browser_id].configure(fg_color=self.primary_color, text_color="#ffffff")
        self.update_dashboard()

    # ======================== CATEGORY FILTER LOGIC ========================

    def apply_category_filter(self, category_name):
        if not self.current_analysis:
            return
        self.active_category_filter = category_name
        self.data_tabs.set("History Engine")
        if category_name == "Other / Uncategorized":
            entries = self.current_analysis.get("uncategorized", {}).get("entries", [])
        else:
            entries = self.current_analysis.get("categories", {}).get(category_name, {}).get("entries", [])
        self.active_filter_label.configure(text=f"Showing: {category_name} ({len(entries)} entries)")
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        if entries:
            for h in entries:
                self.history_text.insert("end", f"[{h.get('time', 'N/A')}] {h.get('title', 'No Title')}\n")
                self.history_text.insert("end", f"URL: {h.get('url', 'N/A')}\n\n")
        else:
            self.history_text.insert("end", f"No entries found for category: {category_name}")
        self.history_text.configure(state="disabled")
        self._highlight_active_category(category_name)

    def clear_category_filter(self):
        self.active_category_filter = None
        self.active_filter_label.configure(text="")
        if not self.current_browser or self.current_browser not in self.data:
            return
        bdata = self.data[self.current_browser]
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        if bdata.get("status") == "Active" and bdata["history"]:
            for h in bdata["history"]:
                self.history_text.insert("end", f"[{h['time']}] {h['title']}\nURL: {h['url']}\n\n")
        else:
            self.history_text.insert("end", "Audit unavailable: Profile locked by OS or empty.")
        self.history_text.configure(state="disabled")
        self._highlight_active_category(None)

    def _highlight_active_category(self, active_cat_name):
        for widget in self.insights_scroll.winfo_children():
            if hasattr(widget, '_cat_name'):
                if active_cat_name and widget._cat_name == active_cat_name:
                    widget.configure(fg_color="#1e3a5f", border_color=self.primary_color, border_width=2)
                else:
                    widget.configure(fg_color="transparent", border_color="transparent", border_width=0)

    # ======================== WELLNESS INTERVENTION PANEL ========================

    def build_wellness_panel(self, wellness_resources, critical_matches):
        for widget in self.wellness_panel.winfo_children():
            widget.destroy()
        self.wellness_panel.pack_forget()
        if not wellness_resources:
            return
        self.wellness_panel.pack(fill="x", pady=(0, 15), before=self.insights_container)
        for resource in wellness_resources:
            card = ctk.CTkFrame(self.wellness_panel, fg_color="#1a0505", corner_radius=12, border_width=2,
                                border_color=resource.get("color", self.danger_color))
            card.pack(fill="x", pady=(0, 10))

            title_frame = ctk.CTkFrame(card, fg_color=resource.get("color", self.danger_color), corner_radius=8, height=40)
            title_frame.pack(fill="x", padx=8, pady=(8, 0))
            title_frame.pack_propagate(False)
            ctk.CTkLabel(title_frame, text=resource.get("title", "Alert"), font=("Inter", 14, "bold"), text_color="#ffffff").pack(side="left", padx=15, pady=8)

            severity_text = "CRITICAL" if resource["color"] in ("#ef4444", "#dc2626") else "ATTENTION"
            severity_bg = "#991b1b" if severity_text == "CRITICAL" else "#78350f"
            ctk.CTkLabel(title_frame, text=f" {severity_text} ", font=("Inter", 10, "bold"), text_color="#ffffff", fg_color=severity_bg, corner_radius=4).pack(side="right", padx=15, pady=8)

            ctk.CTkLabel(card, text=resource.get("message", ""), font=("Inter", 12), text_color="#e2e8f0", wraplength=350, justify="left").pack(anchor="w", padx=20, pady=(12, 8))

            ctk.CTkFrame(card, fg_color=self.border_color, height=1).pack(fill="x", padx=15, pady=5)

            ctk.CTkLabel(card, text="HELPLINE NUMBERS", font=("Inter", 11, "bold"), text_color=self.text_muted).pack(anchor="w", padx=20, pady=(5, 5))

            for hotline in resource.get("hotlines", []):
                hf = ctk.CTkFrame(card, fg_color="#0f172a", corner_radius=8)
                hf.pack(fill="x", padx=15, pady=2)
                type_icon = "call" if hotline.get("type") == "call" else "text"
                ctk.CTkLabel(hf, text=f"[{type_icon}]  {hotline['name']}", font=("Inter", 12), text_color="#cbd5e1").pack(side="left", padx=12, pady=8)
                ctk.CTkLabel(hf, text=hotline["number"], font=("Inter", 13, "bold"), text_color=self.success_color).pack(side="right", padx=12, pady=8)

            web_resources = resource.get("web_resources", [])
            if web_resources:
                bf = ctk.CTkFrame(card, fg_color="transparent")
                bf.pack(fill="x", padx=15, pady=(8, 12))
                ctk.CTkButton(bf, text="Get Help Now", fg_color=resource.get("color", self.danger_color),
                              hover_color="#7f1d1d" if resource["color"] in ("#ef4444", "#dc2626") else "#92400e",
                              font=("Inter", 13, "bold"), height=38, corner_radius=8,
                              command=lambda url=web_resources[0]: webbrowser.open(url)).pack(side="left", padx=(0, 10))
                ctk.CTkButton(bf, text="Dismiss", fg_color="transparent", border_color=self.border_color, border_width=1,
                              hover_color=self.card_color, text_color=self.text_muted, font=("Inter", 12), height=38, corner_radius=8,
                              command=lambda: self.wellness_panel.pack_forget()).pack(side="left")

        if critical_matches:
            ff = ctk.CTkFrame(self.wellness_panel, fg_color="#1e1b4b", corner_radius=8, border_color="#4338ca", border_width=1)
            ff.pack(fill="x", pady=(0, 5))
            ctk.CTkLabel(ff, text=f"{len(critical_matches)} flagged entries detected in browsing history", font=("Inter", 11, "bold"), text_color="#a5b4fc").pack(padx=15, pady=8)

    # ====== WELLNESS SCORE GAUGE ======

    def build_wellness_score_section(self, analysis):
        """Build the wellness score gauge + streak + positive reinforcement."""
        score = analysis.get("wellness_score", 100)
        grade = analysis.get("wellness_grade", "A+")
        color = analysis.get("wellness_color", self.success_color)
        label = analysis.get("wellness_label", "Excellent")
        streak = analysis.get("streak_days", 0)
        is_healthy = analysis.get("is_healthy", True)

        # Score card frame
        score_frame = ctk.CTkFrame(self.insights_scroll, fg_color="#0f172a", corner_radius=10, border_width=1, border_color=color)
        score_frame.pack(fill="x", pady=(0, 12))

        # Title row
        title_row = ctk.CTkFrame(score_frame, fg_color="transparent")
        title_row.pack(fill="x", padx=15, pady=(12, 5))
        ctk.CTkLabel(title_row, text="Digital Wellness Score", font=("Inter", 13, "bold"), text_color=self.text_primary).pack(side="left")

        # Grade badge
        ctk.CTkLabel(title_row, text=f" {grade} ", font=("Inter", 14, "bold"), text_color="#ffffff", fg_color=color, corner_radius=6).pack(side="right")

        # Score bar
        bar_container = ctk.CTkFrame(score_frame, fg_color="transparent")
        bar_container.pack(fill="x", padx=15, pady=(0, 5))

        score_bar = ctk.CTkProgressBar(bar_container, progress_color=color, fg_color="#1e293b", height=14, corner_radius=7)
        score_bar.pack(fill="x", side="left", expand=True, padx=(0, 10))
        score_bar.set(score / 100.0)

        ctk.CTkLabel(bar_container, text=f"{score}/100", font=("Inter", 14, "bold"), text_color=color).pack(side="right")

        # Label
        ctk.CTkLabel(score_frame, text=label, font=("Inter", 12), text_color=color).pack(anchor="w", padx=15, pady=(0, 5))

        # Positive Reinforcement / Streak
        if is_healthy:
            positive_frame = ctk.CTkFrame(score_frame, fg_color="#052e16", corner_radius=8)
            positive_frame.pack(fill="x", padx=12, pady=(0, 10))

            badge_text = "Healthy Browsing Pattern Detected"
            ctk.CTkLabel(positive_frame, text=badge_text, font=("Inter", 12, "bold"), text_color="#4ade80").pack(anchor="w", padx=12, pady=(8, 2))

            if streak > 0:
                streak_emoji = ""
                if streak >= 30:
                    streak_emoji = " (Legendary!)"
                elif streak >= 14:
                    streak_emoji = " (Amazing!)"
                elif streak >= 7:
                    streak_emoji = " (On Fire!)"
                elif streak >= 3:
                    streak_emoji = " (Great Start!)"

                ctk.CTkLabel(positive_frame, text=f"{streak} day{'s' if streak != 1 else ''} healthy browsing streak{streak_emoji}", font=("Inter", 11), text_color="#86efac").pack(anchor="w", padx=12, pady=(0, 8))
            else:
                ctk.CTkLabel(positive_frame, text="Keep it up! Your streak starts today.", font=("Inter", 11), text_color="#86efac").pack(anchor="w", padx=12, pady=(0, 8))
        else:
            concern_frame = ctk.CTkFrame(score_frame, fg_color="#2d0a0a", corner_radius=8)
            concern_frame.pack(fill="x", padx=12, pady=(0, 10))
            ctk.CTkLabel(concern_frame, text="Concerning patterns detected. Support resources available above.", font=("Inter", 12), text_color="#fca5a5").pack(anchor="w", padx=12, pady=8)

    # ====== TIME-OF-DAY HEATMAP ======

    def build_time_heatmap(self, heatmap_data, late_night_concern):
        """Build a time-of-day activity heatmap in the insights panel."""
        heatmap_frame = ctk.CTkFrame(self.insights_scroll, fg_color="#0f172a", corner_radius=10, border_width=1, border_color=self.border_color)
        heatmap_frame.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(heatmap_frame, text="Browsing Time Heatmap", font=("Inter", 13, "bold"), text_color=self.text_primary).pack(anchor="w", padx=15, pady=(12, 8))

        max_count = max(heatmap_data.values()) if heatmap_data.values() else 1
        if max_count == 0:
            max_count = 1

        for slot_name, count in heatmap_data.items():
            row = ctk.CTkFrame(heatmap_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)

            # Determine color intensity based on count
            ratio = count / max_count
            if "Late Night" in slot_name and late_night_concern:
                bar_color = "#ef4444"  # Red for concerning late-night
            elif ratio > 0.7:
                bar_color = "#f59e0b"  # Amber for heavy usage
            elif ratio > 0.3:
                bar_color = "#3b82f6"  # Blue for moderate
            else:
                bar_color = "#334155"  # Gray for low

            ctk.CTkLabel(row, text=slot_name, font=("Inter", 11), text_color=self.text_muted, width=180, anchor="w").pack(side="left")

            bar = ctk.CTkProgressBar(row, progress_color=bar_color, fg_color="#1e293b", height=10, corner_radius=5, width=120)
            bar.pack(side="left", padx=(5, 8), fill="x", expand=True)
            bar.set(max(ratio, 0.02))  # Minimum visible bar

            ctk.CTkLabel(row, text=str(count), font=("Inter", 11, "bold"), text_color=self.text_primary, width=30).pack(side="right")

        if late_night_concern:
            warn = ctk.CTkFrame(heatmap_frame, fg_color="#2d0a0a", corner_radius=6)
            warn.pack(fill="x", padx=12, pady=(5, 10))
            ctk.CTkLabel(warn, text="Late-night concerning activity detected", font=("Inter", 11, "bold"), text_color="#fca5a5").pack(padx=10, pady=6)
        else:
            # Add bottom padding
            ctk.CTkFrame(heatmap_frame, fg_color="transparent", height=8).pack()

    # ====== TREND ANALYSIS ======

    def build_trend_section(self, trends):
        """Build the trend analysis cards in the insights panel."""
        if not trends:
            return

        trend_frame = ctk.CTkFrame(self.insights_scroll, fg_color="#0f172a", corner_radius=10, border_width=1, border_color=self.border_color)
        trend_frame.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(trend_frame, text="Weekly Trend Analysis", font=("Inter", 13, "bold"), text_color=self.text_primary).pack(anchor="w", padx=15, pady=(12, 8))

        for cat_name, trend_data in trends.items():
            row = ctk.CTkFrame(trend_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)

            # Direction arrow and color
            direction = trend_data["direction"]
            change = abs(trend_data["change_pct"])

            if direction == "up":
                arrow = "^"
                # Determine if "up" is good or bad based on category
                is_negative_cat = cat_name in ("Adult & NSFW", "Uncategorized")
                trend_color = "#ef4444" if is_negative_cat else "#22c55e"
            else:
                arrow = "v"
                is_negative_cat = cat_name in ("Adult & NSFW", "Uncategorized")
                trend_color = "#22c55e" if is_negative_cat else "#f59e0b"

            ctk.CTkLabel(row, text=cat_name, font=("Inter", 11), text_color=self.text_muted, anchor="w").pack(side="left")

            trend_text = f" {arrow} {change:.0f}%  ({trend_data['last_week']} -> {trend_data['this_week']})"
            ctk.CTkLabel(row, text=trend_text, font=("Inter", 12, "bold"), text_color=trend_color).pack(side="right")

        ctk.CTkFrame(trend_frame, fg_color="transparent", height=8).pack()

    # ======================== MAIN DASHBOARD UPDATE ========================

    def update_dashboard(self):
        if not self.current_browser or self.current_browser not in self.data:
            return

        bdata = self.data[self.current_browser]
        status = bdata.get('status', 'Not Found')
        is_active = status == 'Active'

        # Header
        self.status_title.configure(text=self.current_browser)
        status_color = self.success_color if is_active else self.danger_color
        self.status_subtitle.configure(text=f"Environment Status: {status}", text_color=status_color)

        # Metrics
        self.card_history.update_value(str(len(bdata.get('history', []))) if is_active else "Locked")
        self.card_downloads.update_value(str(len(bdata.get('downloads', []))) if is_active else "Locked")
        self.card_extensions.update_value(str(len(bdata.get('extensions', []))) if is_active else "Locked")
        self.card_cache.update_value(bdata.get('cache_size', 'Locked') if is_active else "Locked")

        # History Box
        self.active_filter_label.configure(text="")
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        if is_active and bdata['history']:
            for h in bdata['history']:
                self.history_text.insert("end", f"[{h['time']}] {h['title']}\nURL: {h['url']}\n\n")
        else:
            self.history_text.insert("end", "Audit unavailable: Profile locked by OS or empty.")
        self.history_text.configure(state="disabled")

        # Extensions Box
        self.ext_text.configure(state="normal")
        self.ext_text.delete("1.0", "end")
        if is_active and bdata['extensions']:
            for ext in bdata['extensions']:
                self.ext_text.insert("end", f"> {ext}\n")
        else:
            self.ext_text.insert("end", "Audit unavailable: Profile locked by OS or empty.")
        self.ext_text.configure(state="disabled")

        # =============== INSIGHTS PANEL ===============
        for widget in self.insights_scroll.winfo_children():
            widget.destroy()
        for widget in self.wellness_panel.winfo_children():
            widget.destroy()
        self.wellness_panel.pack_forget()

        if is_active and bdata['history']:
            analysis_results = self.analyzer_instance.analyze_history(bdata['history'])
            self.current_analysis = analysis_results

            # 1. Wellness Intervention (if needed)
            if analysis_results["needs_intervention"]:
                self.build_wellness_panel(
                    analysis_results.get("wellness_resources", []),
                    analysis_results.get("critical_matches", [])
                )

            # 2. Wellness Score Gauge + Positive Reinforcement
            self.build_wellness_score_section(analysis_results)

            # 3. Category Bars (clickable)
            # Section header
            cat_header = ctk.CTkFrame(self.insights_scroll, fg_color="transparent")
            cat_header.pack(fill="x", pady=(0, 5))
            ctk.CTkLabel(cat_header, text="Category Breakdown", font=("Inter", 13, "bold"), text_color=self.text_primary).pack(anchor="w")

            has_data = False
            for cat_name, info in analysis_results["categories"].items():
                if info["count"] > 0:
                    self.create_insight_bar(cat_name, info["percentage"], info["color"], info["icon"], info["count"])
                    has_data = True
            uncat = analysis_results["uncategorized"]
            if uncat["count"] > 0:
                self.create_insight_bar("Other / Uncategorized", uncat["percentage"], uncat["color"], uncat["icon"], uncat["count"])
                has_data = True
            if not has_data:
                ctk.CTkLabel(self.insights_scroll, text="No scannable history found.", text_color=self.text_muted).pack(pady=10)

            # 4. Time Heatmap
            self.build_time_heatmap(analysis_results.get("time_heatmap", {}), analysis_results.get("late_night_concern", False))

            # 5. Trend Analysis
            self.build_trend_section(analysis_results.get("trends", {}))

        else:
            self.current_analysis = None
            ctk.CTkLabel(self.insights_scroll, text="Audit unavailable:\nProfile locked or empty.", text_color=self.text_muted).pack(pady=20, fill="x")

        # Downloads
        for widget in self.downloads_scroll.winfo_children():
            widget.destroy()
        if is_active and bdata['downloads']:
            for d in bdata['downloads']:
                self.create_download_row(d)
        else:
            ctk.CTkLabel(self.downloads_scroll, text="Audit unavailable: Profile locked by OS or empty.", text_color=self.text_muted).pack(pady=30)

        # System
        info = f"Engine Type:\t\t{bdata.get('browser_type', 'Unknown').capitalize()}\n"
        info += f"Entity Path:\t\t{bdata.get('base_path', 'Unknown')}\n\n"
        info += f"Lock State:\t\t{status}\n"
        if is_active:
            info += f"Total Cache Files:\t{bdata.get('cache_files', 0)}\n"
            info += f"Total Cache Volume:\t{bdata.get('cache_size', '0 MB')}"
        self.sys_info_label.configure(text=info)

        state = "normal" if is_active else "disabled"
        self.wipe_history_btn.configure(state=state)
        self.wipe_cache_btn.configure(state=state)

    def create_insight_bar(self, category_title, percentage, color, icon, count):
        bar_frame = ctk.CTkFrame(self.insights_scroll, fg_color="transparent", corner_radius=8, cursor="hand2")
        bar_frame.pack(fill="x", pady=(0, 6))
        bar_frame._cat_name = category_title
        bar_frame.bind("<Button-1>", lambda e, cat=category_title: self.apply_category_filter(cat))

        header = ctk.CTkFrame(bar_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 3))
        header.bind("<Button-1>", lambda e, cat=category_title: self.apply_category_filter(cat))

        lbl = ctk.CTkLabel(header, text=f"{icon}  {category_title}", font=("Inter", 12, "bold"), text_color=self.text_primary, cursor="hand2")
        lbl.pack(side="left")
        lbl.bind("<Button-1>", lambda e, cat=category_title: self.apply_category_filter(cat))

        stats = ctk.CTkLabel(header, text=f"{percentage:.1f}% ({count})", font=("Inter", 11), text_color=self.text_muted, cursor="hand2")
        stats.pack(side="right")
        stats.bind("<Button-1>", lambda e, cat=category_title: self.apply_category_filter(cat))

        prog = ctk.CTkProgressBar(bar_frame, progress_color=color, fg_color=self.bg_color, height=7, corner_radius=4)
        prog.pack(fill="x")
        prog.set(percentage / 100.0)
        prog.bind("<Button-1>", lambda e, cat=category_title: self.apply_category_filter(cat))

    def create_download_row(self, item):
        row = ctk.CTkFrame(self.downloads_scroll, fg_color=self.card_color, corner_radius=8, border_color=self.border_color, border_width=1)
        row.pack(fill="x", pady=6, padx=5)
        path = item.get('path', 'Unknown')
        name = os.path.basename(path) if path != "Unknown" else "Unknown File"
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=20, pady=15)
        ctk.CTkLabel(info, text=name, font=("Inter", 14, "bold"), text_color=self.text_primary, anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=f"{item.get('size', 'N/A')}  |  {item.get('time', 'N/A')}", font=("Inter", 11), text_color=self.success_color, anchor="w").pack(fill="x", pady=(2,0))
        ctk.CTkLabel(info, text=f"Path: {path}", font=("Inter", 11), text_color=self.text_muted, anchor="w").pack(fill="x", pady=(5,0))
        if path != "Unknown":
            ctk.CTkButton(row, text="Inspect Asset", width=140, height=36, fg_color=self.bg_color, border_color=self.border_color, border_width=1,
                          hover_color=self.border_color, text_color=self.text_primary, command=lambda p=path: self.open_folder(p)).pack(side="right", padx=20)

    def open_folder(self, path):
        if not path or path == "Unknown": return
        if os.path.exists(path):
            try: subprocess.run(['explorer.exe', '/select,', os.path.normpath(path)])
            except: pass
        else:
            d = os.path.dirname(path)
            if os.path.exists(d): os.startfile(d)
            else: messagebox.showerror("System Error", "Asset permanently moved or destroyed by host OS.")

    def on_clear_history(self):
        if not self.current_browser or self.current_browser not in self.data: return
        bdata = self.data[self.current_browser]
        trange = self.history_range.get()

        # ---- PRE-WIPE SUMMARY ----
        history_count = len(bdata.get('history', []))
        downloads_count = len(bdata.get('downloads', []))

        if history_count == 0 and downloads_count == 0:
            messagebox.showinfo("Nothing to Purge", f"No history or download data found for {self.current_browser}.")
            return

        summary = (
            f"DATA TO BE PERMANENTLY DELETED:\n"
            f"{'='*40}\n\n"
            f"Browser:       {self.current_browser}\n"
            f"Time Range:    {trange}\n\n"
            f"  History Entries:    {history_count}\n"
            f"  Download Records:  {downloads_count}\n\n"
            f"{'='*40}\n"
            f"This action CANNOT be reversed.\n"
            f"Proceed with destructive purge?"
        )

        if not messagebox.askyesno("Confirm Data Purge", summary):
            return

        # ---- PERFORM WIPE ----
        self.set_status(f"Purging {trange} history for {self.current_browser}...")
        success, msg, report = browser_extractor.clear_browser_history(
            self.current_browser, bdata['base_path'], bdata['browser_type'], trange
        )

        if not success:
            self.set_status("Secure purge failed.", True)
            messagebox.showerror("Purge Failed", msg)
            return

        # ---- VERIFICATION RE-SCAN ----
        self.set_status("Verifying purge completion...")
        try:
            verified_data = browser_extractor.get_browser_data(
                self.current_browser, bdata['base_path'], bdata['browser_type']
            )
            remaining_history = len(verified_data.get('history', []))
            remaining_downloads = len(verified_data.get('downloads', []))
        except Exception:
            remaining_history = -1
            remaining_downloads = -1

        # Determine verification status
        if trange == "All Time":
            verified = (remaining_history == 0 and remaining_downloads == 0)
        else:
            verified = (remaining_history < history_count)

        # ---- DELETION REPORT ----
        status_icon = "VERIFIED" if verified else "PARTIAL"
        deletion_report = (
            f"DELETION REPORT\n"
            f"{'='*40}\n\n"
            f"Status: {status_icon}\n"
            f"Browser: {self.current_browser}\n"
            f"Range: {trange}\n\n"
            f"REMOVED:\n"
            f"  URLs Deleted:           {report.get('urls_deleted', 0)}\n"
            f"  Visit Records Deleted:  {report.get('visits_deleted', 0)}\n"
            f"  Downloads Deleted:      {report.get('downloads_deleted', 0)}\n"
            f"  Search Terms Deleted:   {report.get('search_terms_deleted', 0)}\n\n"
            f"VERIFICATION:\n"
            f"  History Before:  {history_count}\n"
            f"  History After:   {remaining_history if remaining_history >= 0 else 'Could not verify'}\n"
            f"  Downloads Before: {downloads_count}\n"
            f"  Downloads After:  {remaining_downloads if remaining_downloads >= 0 else 'Could not verify'}\n\n"
            f"{'='*40}\n"
        )

        if verified:
            deletion_report += "All targeted data has been permanently destroyed."
        else:
            deletion_report += "Some data may remain. Try closing the browser and wiping again."

        self.set_status(f"Purge complete: {report.get('urls_deleted', 0)} URLs + {report.get('visits_deleted', 0)} visits removed.")
        messagebox.showinfo("Deletion Report", deletion_report)

        # Refresh the UI
        self.start_scan()

    def on_clear_cache(self):
        if not self.current_browser or self.current_browser not in self.data: return
        bdata = self.data[self.current_browser]

        # ---- PRE-WIPE SUMMARY ----
        cache_size = bdata.get('cache_size', '0 MB')
        cache_files = bdata.get('cache_files', 0)

        if cache_files == 0:
            messagebox.showinfo("Nothing to Purge", f"No cache files found for {self.current_browser}.")
            return

        summary = (
            f"CACHE DATA TO BE PERMANENTLY DELETED:\n"
            f"{'='*40}\n\n"
            f"Browser:       {self.current_browser}\n\n"
            f"  Cache Size:    {cache_size}\n"
            f"  Cache Files:   {cache_files}\n\n"
            f"{'='*40}\n"
            f"This action CANNOT be reversed.\n"
            f"Proceed with cache purge?"
        )

        if not messagebox.askyesno("Confirm Cache Purge", summary):
            return

        # ---- PERFORM WIPE ----
        self.set_status(f"Purging cache for {self.current_browser}...")
        success, msg = browser_extractor.clear_browser_cache(
            self.current_browser, bdata['base_path'], bdata['browser_type']
        )

        if not success:
            self.set_status("Cache purge failed.", True)
            messagebox.showerror("Purge Failed", msg)
            return

        # ---- VERIFICATION RE-SCAN ----
        self.set_status("Verifying cache purge...")
        try:
            cache_dir = os.path.join(bdata['base_path'], 'Cache')
            new_size, new_count = browser_extractor.get_cache_info(cache_dir)
        except Exception:
            new_size = "Unknown"
            new_count = -1

        verified = (new_count == 0) if new_count >= 0 else False

        # ---- DELETION REPORT ----
        status_icon = "VERIFIED" if verified else "PARTIAL"
        deletion_report = (
            f"CACHE DELETION REPORT\n"
            f"{'='*40}\n\n"
            f"Status: {status_icon}\n"
            f"Browser: {self.current_browser}\n\n"
            f"REMOVED:\n"
            f"  Cache Size Freed:    {cache_size}\n"
            f"  Cache Files Deleted: {cache_files}\n\n"
            f"VERIFICATION:\n"
            f"  Files Before:  {cache_files}\n"
            f"  Files After:   {new_count if new_count >= 0 else 'Could not verify'}\n"
            f"  Size Before:   {cache_size}\n"
            f"  Size After:    {new_size}\n\n"
            f"{'='*40}\n"
        )

        if verified:
            deletion_report += "All cache data has been permanently destroyed."
        else:
            deletion_report += "Some cache may remain. Try closing the browser and purging again."

        self.set_status(f"Cache purge complete: {cache_size} freed.")
        messagebox.showinfo("Cache Deletion Report", deletion_report)

        # Refresh the UI
        self.start_scan()


def main():
    app = BrowserExtractorGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
