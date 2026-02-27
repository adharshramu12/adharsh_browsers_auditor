import customtkinter as ctk
import browser_extractor
import os
import sys
import subprocess
import threading
import logging
from tkinter import messagebox
from datetime import datetime
from PIL import Image

# Configure logging for the GUI
logger = logging.getLogger("AdharshBrowserAuditorGUI")

VERSION = "v2.0.0-enterprise"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class MetricsCard(ctk.CTkFrame):
    def __init__(self, master, title, value, icon, color, **kwargs):
        super().__init__(master, fg_color="#1e293b", corner_radius=12, border_width=1, border_color="#334155", **kwargs)
        
        self.grid_columnconfigure(1, weight=1)
        
        # Icon (Simulated with emoji for now, can be replaced with images)
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
        
        # Set window icon
        icon_path = resource_path("app_logo.ico")
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except: pass

        # Premium Enterprise Design Tokens
        self.primary_color = "#3b82f6"  # Blue 500
        self.success_color = "#10b981"  # Emerald 500
        self.warning_color = "#f59e0b"  # Amber 500
        self.danger_color = "#ef4444"   # Red 500
        self.sidebar_color = "#0f172a"  # Slate 900
        self.bg_color = "#020617"       # Slate 950
        self.card_color = "#1e293b"     # Slate 800
        self.border_color = "#334155"   # Slate 700
        self.text_primary = "#f8fafc"   # Slate 50
        self.text_muted = "#94a3b8"     # Slate 400
        
        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=self.bg_color)

        # Main Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---------------- SIDEBAR ----------------
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=self.sidebar_color, border_width=0, border_color=self.border_color)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1) # Push everything below nav to bottom

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

        # Profiles Header
        self.profiles_label = ctk.CTkLabel(self.sidebar_frame, text="DETECTED PROFILES", font=("Inter", 10, "bold"), text_color=self.text_muted)
        self.profiles_label.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="w")

        # Profile List (Scrollable)
        self.profile_list_frame = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent", corner_radius=0)
        self.profile_list_frame.grid(row=2, column=0, sticky="nsew", padx=10)

        self.profile_buttons = {}
        self.current_browser = None

        # Bottom Sidebar (Settings / Info)
        self.bottom_sidebar = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.bottom_sidebar.grid(row=3, column=0, sticky="ew", padx=20, pady=20)
        
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

        self.card_cache = MetricsCard(self.metrics_row, "Cache Size", "-", "🗄️", self.danger_color)
        self.card_cache.grid(row=0, column=3, sticky="ew", padx=(5, 0))

        # Main Data Area (Tabview)
        # Using a specialized style to make the tabview look like an enterprise panel
        self.data_tabs = ctk.CTkTabview(self.main_content, corner_radius=12, fg_color=self.card_color, 
                                        segmented_button_selected_color=self.primary_color, 
                                        segmented_button_unselected_color=self.bg_color,
                                        segmented_button_selected_hover_color=self.primary_color,
                                        text_color=self.text_primary)
        self.data_tabs.grid(row=2, column=0, sticky="nsew")
        
        self.data_tabs.add("History Engine")
        self.data_tabs.add("Download Vault")
        self.data_tabs.add("Extension Modules")
        self.data_tabs.add("System & Cache")

        # History Tab
        self.history_frame = self.data_tabs.tab("History Engine")
        self.history_frame.grid_columnconfigure(0, weight=1)
        self.history_frame.grid_rowconfigure(0, weight=1)
        
        self.history_text = ctk.CTkTextbox(self.history_frame, font=("Inter", 13), fg_color=self.bg_color, text_color=self.text_primary, corner_radius=8, border_color=self.border_color, border_width=1)
        self.history_text.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        self.history_actions = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        self.history_actions.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        
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
        
        # Start scanning slightly after window load for visual effect
        self.after(500, self.start_scan)

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
        
        if self.data and not self.current_browser:
            first_browser = list(self.data.keys())[0]
            self.select_profile(first_browser)

    def build_sidebar_profiles(self):
        # Clear old
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
        # Reset previous active button
        if self.current_browser and self.current_browser in self.profile_buttons:
            self.profile_buttons[self.current_browser].configure(fg_color="transparent", text_color=self.text_primary)
        
        self.current_browser = browser_id
        
        # Highlight new active button
        if browser_id in self.profile_buttons:
            self.profile_buttons[browser_id].configure(fg_color=self.primary_color, text_color="#ffffff")

        self.update_dashboard()

    def update_dashboard(self):
        if not self.current_browser or self.current_browser not in self.data:
            return

        bdata = self.data[self.current_browser]
        status = bdata.get('status', 'Not Found')
        is_active = status == 'Active'

        # Update Header
        self.status_title.configure(text=self.current_browser)
        status_color = self.success_color if is_active else self.danger_color
        self.status_subtitle.configure(text=f"Environment Status: {status}", text_color=status_color)

        # Update Metrics
        self.card_history.update_value(str(len(bdata.get('history', []))) if is_active else "Locked")
        self.card_downloads.update_value(str(len(bdata.get('downloads', []))) if is_active else "Locked")
        self.card_extensions.update_value(str(len(bdata.get('extensions', []))) if is_active else "Locked")
        self.card_cache.update_value(bdata.get('cache_size', 'Locked') if is_active else "Locked")

        # Update History Box
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        if is_active and bdata['history']:
            for h in bdata['history']:
                self.history_text.insert("end", f"[{h['time']}] {h['title']}\nURL: {h['url']}\n\n")
        else:
            self.history_text.insert("end", "Audit unavailable: Profile locked by OS or empty.")
        self.history_text.configure(state="disabled")

        # Update Extensions Box
        self.ext_text.configure(state="normal")
        self.ext_text.delete("1.0", "end")
        if is_active and bdata['extensions']:
            for ext in bdata['extensions']:
                self.ext_text.insert("end", f"▶ {ext}\n")
        else:
            self.ext_text.insert("end", "Audit unavailable: Profile locked by OS or empty.")
        self.ext_text.configure(state="disabled")

        # Update Downloads
        for widget in self.downloads_scroll.winfo_children():
            widget.destroy()
            
        if is_active and bdata['downloads']:
            for d in bdata['downloads']:
                self.create_download_row(d)
        else:
            ctk.CTkLabel(self.downloads_scroll, text="Audit unavailable: Profile locked by OS or empty.", text_color=self.text_muted).pack(pady=30)

        # Update System Box
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
            btn = ctk.CTkButton(row, text="Inspect Asset", width=140, height=36, fg_color=self.bg_color, border_color=self.border_color, border_width=1, hover_color=self.border_color, text_color=self.text_primary, command=lambda p=path: self.open_folder(p))
            btn.pack(side="right", padx=20)

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
        
        if messagebox.askyesno("Enterprise Override", f"WARNING: You are about to permanently purge the '{trange}' history subset for {self.current_browser}. This action cannot be reversed.\n\nProceed with destructive purge?"):
            success, msg = browser_extractor.clear_browser_history(self.current_browser, bdata['base_path'], bdata['browser_type'], trange)
            if success:
                self.set_status(f"Purge successful: {trange} erased.")
                messagebox.showinfo("Success", msg)
                self.start_scan()
            else:
                self.set_status("Secure purge failed.", True)
                messagebox.showerror("Failure", msg)

    def on_clear_cache(self):
        if not self.current_browser or self.current_browser not in self.data: return
        bdata = self.data[self.current_browser]
        
        if messagebox.askyesno("Enterprise Override", f"WARNING: You are about to mass purge core cache fragment files for {self.current_browser}.\n\nProceed with destructive purge?"):
            success, msg = browser_extractor.clear_browser_cache(self.current_browser, bdata['base_path'], bdata['browser_type'])
            if success:
                self.set_status("Cache purge completed successfully.")
                messagebox.showinfo("Success", msg)
                self.start_scan()
            else:
                self.set_status("Cache purge failed.", True)
                messagebox.showerror("Failure", msg)

def main():
    app = BrowserExtractorGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
