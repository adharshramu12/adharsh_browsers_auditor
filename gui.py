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

VERSION = "v1.0.0-enterprise"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class BrowserExtractorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"Adharsh Browser Auditor {VERSION}")
        self.geometry("1200x800")
        
        # Set window icon
        icon_path = resource_path("app_logo.ico")
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except: pass

        # Premium Design Tokens
        self.primary_color = "#3b82f6"  # Professional blue
        self.danger_color = "#ef4444"   # Soft red
        self.sidebar_color = "#1e293b"  # Slate 800
        self.bg_color = "#0f172a"       # Slate 900
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar frame
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=self.sidebar_color)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        # Sidebar Logo
        logo_path = resource_path("app_logo.png")
        if os.path.exists(logo_path):
            try:
                logo_image = ctk.CTkImage(light_image=Image.open(logo_path),
                                          dark_image=Image.open(logo_path),
                                          size=(80, 80))
                self.logo_img_label = ctk.CTkLabel(self.sidebar_frame, image=logo_image, text="")
                self.logo_img_label.grid(row=0, column=0, padx=20, pady=(30, 0))
            except Exception as e:
                logger.error(f"Failed to load sidebar logo: {e}")

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="AUDITOR", font=ctk.CTkFont(family="Inter", size=24, weight="bold"), text_color=self.primary_color)
        self.logo_label.grid(row=1, column=0, padx=20, pady=(10, 20))

        self.browser_var = ctk.StringVar(value="")
        
        # Profile Scrollable Frame
        self.profile_frame = ctk.CTkScrollableFrame(self.sidebar_frame, label_text="DETECTED PROFILES", 
                                                    fg_color="transparent", label_font=("Inter", 11, "bold"),
                                                    label_text_color=self.primary_color)
        self.profile_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(1, weight=1)

        # Creator Info (Moved to bottom of sidebar)
        self.creator_label = ctk.CTkLabel(self.sidebar_frame, text="Developed by Adharsh Kumar Bachu", 
                                          font=ctk.CTkFont(family="Inter", size=10, slant="italic"), text_color="gray")
        self.creator_label.grid(row=7, column=0, padx=20, pady=(10, 0))

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=9, column=0, padx=20, pady=(10, 20))
        self.appearance_mode_optionemenu.set("Dark")

        # Main content area
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=self.bg_color)
        self.main_frame.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Header with Refresh button
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Browser Performance Insights", font=ctk.CTkFont(family="Inter", size=26, weight="bold"))
        self.title_label.pack(side="left")
        
        self.refresh_btn = ctk.CTkButton(self.header_frame, text="Global Scan", command=self.start_scan, 
                                         fg_color=self.primary_color, hover_color="#2563eb", width=160, height=40, font=("Inter", 13, "bold"))
        self.refresh_btn.pack(side="right")

        # Tabview for data
        self.tabview = ctk.CTkTabview(self.main_frame, corner_radius=10)
        self.tabview.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.tabview.add("History")
        self.tabview.add("Downloads")
        self.tabview.add("Extensions")
        self.tabview.add("System Info")

        # History view
        self.history_textbox = ctk.CTkTextbox(self.tabview.tab("History"), font=("Inter", 12))
        self.history_textbox.pack(fill="both", expand=True, padx=10, pady=(10, 5))
        
        self.history_mgmt_frame = ctk.CTkFrame(self.tabview.tab("History"), fg_color="transparent")
        self.history_mgmt_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.history_range_var = ctk.StringVar(value="All Time")
        self.history_range_menu = ctk.CTkOptionMenu(self.history_mgmt_frame, 
                                                   values=["Last Hour", "Last 24 Hours", "All Time"],
                                                   variable=self.history_range_var, width=150)
        self.history_range_menu.pack(side="left", padx=5)

        self.clear_history_btn = ctk.CTkButton(self.history_mgmt_frame, text="Wipe Selected History", 
                                                command=self.on_clear_history, fg_color=self.danger_color, hover_color="#dc2626", height=40, font=("Inter", 12, "bold"))
        self.clear_history_btn.pack(side="left", fill="x", expand=True, padx=5)

        # Status Bar
        self.status_bar = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color=self.sidebar_color)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.status_bar, text=f"Ready | {VERSION}", font=("Inter", 11), text_color="gray")
        self.status_label.pack(side="left", padx=20)
        
        self.time_label = ctk.CTkLabel(self.status_bar, text="", font=("Inter", 11), text_color="gray")
        self.time_label.pack(side="right", padx=20)
        self.update_clock()

        # Downloads view
        self.downloads_tab = self.tabview.tab("Downloads")
        
        self.downloads_scroll = ctk.CTkScrollableFrame(self.downloads_tab, fg_color="transparent")
        self.downloads_scroll.pack(fill="both", expand=True, padx=10, pady=(10, 5))
        
        self.downloads_mgmt_frame = ctk.CTkFrame(self.downloads_tab, fg_color="transparent")
        self.downloads_mgmt_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.clear_downloads_btn = ctk.CTkButton(self.downloads_mgmt_frame, text="Clear Download History", 
                                                 command=self.on_clear_history, fg_color="#e67e22", hover_color="#d35400", height=40)
        self.clear_downloads_btn.pack(fill="x", expand=True)

        # Extensions view
        self.extensions_textbox = ctk.CTkTextbox(self.tabview.tab("Extensions"), font=("Inter", 12))
        self.extensions_textbox.pack(fill="both", expand=True, padx=10, pady=10)

        # System Info view
        self.info_label = ctk.CTkLabel(self.tabview.tab("System Info"), text="Select a browser to see info", font=ctk.CTkFont(size=14))
        self.info_label.pack(pady=(40, 20))

        self.cache_mgmt_frame = ctk.CTkFrame(self.tabview.tab("System Info"), fg_color="transparent")
        self.cache_mgmt_frame.pack(pady=10, fill="x", padx=100)
        
        self.clear_cache_btn = ctk.CTkButton(self.cache_mgmt_frame, text="Clear Browser Cache", 
                                              command=self.on_clear_cache, fg_color="#f39c12", hover_color="#d35400", height=40)
        self.clear_cache_btn.pack(fill="x", expand=True)

        self.data = {}
        self.start_scan()

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def update_clock(self):
        self.time_label.configure(text=datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self.update_clock)

    def set_status(self, msg, level="info"):
        self.status_label.configure(text=msg)
        if level == "error":
            logger.error(msg)
        else:
            logger.info(msg)

    def start_scan(self):
        self.set_status("Initializing Global Scan...")
        self.refresh_btn.configure(state="disabled", text="Scanning...")
        threading.Thread(target=self.scan_logic, daemon=True).start()

    def scan_logic(self):
        try:
            self.data = browser_extractor.get_all_browsers_data()
            self.after(0, self.on_scan_complete)
        except Exception as e:
            self.set_status(f"Scan failed: {e}", "error")
            self.after(0, lambda: messagebox.showerror("Auditor Error", f"Failed to scan: {e}"))
            self.after(0, lambda: self.refresh_btn.configure(state="normal", text="Global Scan"))

    def on_scan_complete(self):
        self.set_status("Global Scan Complete")
        self.refresh_btn.configure(state="normal", text="Global Scan")
        self.update_sidebar()
        if self.data and not self.browser_var.get():
            first_browser = list(self.data.keys())[0]
            self.browser_var.set(first_browser)
        self.update_view()

    def update_sidebar(self):
        # Clear existing buttons
        for child in self.profile_frame.winfo_children():
            child.destroy()
        
        if not self.data:
            return

        for browser_id in self.data.keys():
            btn = ctk.CTkRadioButton(self.profile_frame, text=browser_id, variable=self.browser_var, 
                                     value=browser_id, command=self.update_view, font=("Inter", 12))
            btn.pack(pady=5, padx=10, anchor="w")

    def update_view(self):
        browser = self.browser_var.get()
        if browser not in self.data:
            return

        browser_data = self.data[browser]
        status = browser_data.get('status', 'Not Found')
        
        self.title_label.configure(text=f"{browser} Insights ({status})")

        # Update History
        self.history_textbox.configure(state="normal")
        self.history_textbox.delete("1.0", "end")
        if status == 'Active' and browser_data['history']:
            for item in browser_data['history']:
                self.history_textbox.insert("end", f"[{item['time']}] {item['title']}\nURL: {item['url']}\n\n")
        else:
            self.history_textbox.insert("end", "No history found or browser is locked.")
        self.history_textbox.configure(state="disabled")

        # Update Downloads
        for widget in self.downloads_scroll.winfo_children():
            widget.destroy()
            
        if status == 'Active' and browser_data['downloads']:
            for item in browser_data['downloads']:
                self.add_download_item(item)
        else:
            ctk.CTkLabel(self.downloads_scroll, text="No downloads found or browser is locked.").pack(pady=20)

        # Update Extensions
        self.extensions_textbox.configure(state="normal")
        self.extensions_textbox.delete("1.0", "end")
        if status == 'Active' and browser_data['extensions']:
            for ext in browser_data['extensions']:
                self.extensions_textbox.insert("end", f"- {ext}\n")
        else:
            self.extensions_textbox.insert("end", "No extensions found.")
        self.extensions_textbox.configure(state="disabled")

        # Update Info
        info_text = f"Status: {status}\n"
        if status == 'Active':
            info_text += f"Cache Size: {browser_data.get('cache_size', 'N/A')}\n"
            info_text += f"Cache Files: {browser_data.get('cache_files', 'N/A')}"
            self.clear_history_btn.configure(state="normal")
            self.clear_cache_btn.configure(state="normal")
        else:
            self.clear_history_btn.configure(state="disabled")
            self.clear_cache_btn.configure(state="disabled")
        self.info_label.configure(text=info_text)

    def on_clear_history(self):
        browser_name = self.browser_var.get()
        if browser_name not in self.data: 
            return
        
        data = self.data[browser_name]
        time_range = self.history_range_var.get()
        logger.info(f"User requested wipe of {time_range} history for {browser_name}")
        
        if messagebox.askyesno("Auditor Confirmation", f"Are you sure you want to permanently WIPE {time_range} history for {browser_name}?"):
            success, message = browser_extractor.clear_browser_history(
                browser_name, data['base_path'], data['browser_type'], time_range
            )
            if success:
                self.set_status(f"History wipe successful for {browser_name}")
                messagebox.showinfo("Success", message)
                self.start_scan()
            else:
                self.set_status(f"History wipe failed for {browser_name}", "error")
                messagebox.showwarning("Failed", message)

    def on_clear_cache(self):
        browser_name = self.browser_var.get()
        if browser_name not in self.data: 
            return
        
        data = self.data[browser_name]
        logger.info(f"User requested cache clearing for {browser_name}")
        
        if messagebox.askyesno("Auditor Confirmation", f"Are you sure you want to clear the cache for {browser_name}?"):
            success, message = browser_extractor.clear_browser_cache(
                browser_name, data['base_path'], data['browser_type']
            )
            if success:
                self.set_status(f"Cache cleared for {browser_name}")
                messagebox.showinfo("Success", message)
                self.start_scan()
            else:
                self.set_status(f"Cache clear failed for {browser_name}", "error")
                messagebox.showwarning("Failed", message)

    def add_download_item(self, item):
        item_frame = ctk.CTkFrame(self.downloads_scroll, fg_color="#2b2b2b", corner_radius=8)
        item_frame.pack(fill="x", padx=5, pady=5)
        
        path = item.get('path', 'Unknown')
        filename = os.path.basename(path) if path != "Unknown" else "Unknown File"
        
        info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(info_frame, text=filename, font=("Inter", 13, "bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(info_frame, text=f"Path: {path}", font=("Inter", 11), anchor="w", text_color="gray").pack(fill="x")
        ctk.CTkLabel(info_frame, text=f"Size: {item.get('size', 'N/A')} | Time: {item.get('time', 'N/A')}", 
                     font=("Inter", 10), anchor="w", text_color="gray").pack(fill="x")
        
        if path != "Unknown":
            open_btn = ctk.CTkButton(item_frame, text="Open Folder", width=100, height=32,
                                     command=lambda p=path: self.open_file_location(p))
            open_btn.pack(side="right", padx=10)

    def open_file_location(self, path):
        if not path or path == "Unknown":
            messagebox.showwarning("Warning", "Path not available.")
            return
            
        if os.path.exists(path):
            try:
                subprocess.run(['explorer.exe', '/select,', os.path.normpath(path)])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {e}")
        else:
            dir_path = os.path.dirname(path)
            if os.path.exists(dir_path):
                os.startfile(dir_path)
            else:
                messagebox.showerror("Error", "File or folder no longer exists.")

def main():
    app = BrowserExtractorGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
