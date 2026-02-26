import os
import sys
import shutil
import customtkinter as ctk
from PIL import Image
import threading
import time
import subprocess

# Use the same resource path logic
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SetupWizard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Adharsh Browser Auditor - Setup Wizard")
        self.geometry("600x400")
        self.resizable(False, False)
        
        # Design Tokens
        self.primary_color = "#3b82f6"
        self.bg_color = "#0f172a"
        self.card_color = "#1e293b"
        
        ctk.set_appearance_mode("Dark")
        
        # Set icon
        icon_path = resource_path("app_logo.ico")
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except: pass

        # Main Container
        self.main_frame = ctk.CTkFrame(self, fg_color=self.bg_color, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True)

        self.show_welcome()

    def show_welcome(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Logo
        logo_path = resource_path("app_logo.png")
        if os.path.exists(logo_path):
            logo_image = ctk.CTkImage(Image.open(logo_path), size=(100, 100))
            self.logo_label = ctk.CTkLabel(self.main_frame, image=logo_image, text="")
            self.logo_label.pack(pady=(40, 10))

        self.title_label = ctk.CTkLabel(self.main_frame, text="Welcome to Adharsh Browser Auditor", 
                                        font=("Inter", 20, "bold"))
        self.title_label.pack(pady=10)

        self.desc_label = ctk.CTkLabel(self.main_frame, text="This wizard will install the Auditor on your computer\nand create a desktop shortcut for one-click access.", 
                                       font=("Inter", 12), text_color="gray")
        self.desc_label.pack(pady=10)

        self.install_btn = ctk.CTkButton(self.main_frame, text="Install Now", fg_color=self.primary_color, 
                                          hover_color="#2563eb", command=self.start_install)
        self.install_btn.pack(pady=30)

    def start_install(self):
        self.install_btn.configure(state="disabled", text="Installing...")
        threading.Thread(target=self.run_installation_logic, daemon=True).start()

    def run_installation_logic(self):
        try:
            # 1. Define Paths
            appdata_dir = os.path.join(os.environ['LOCALAPPDATA'], "AdharshBrowserAuditor")
            if not os.path.exists(appdata_dir):
                os.makedirs(appdata_dir)

            exe_name = "Adharsh_Browser_Auditor.exe"
            src_exe = resource_path(exe_name)
            dest_exe = os.path.join(appdata_dir, exe_name)

            # 2. Copy App
            if os.path.exists(src_exe):
                shutil.copy2(src_exe, dest_exe)

            # 3. Create Shortcut via PowerShell (Zero Dependency)
            desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            shortcut_path = os.path.join(desktop, "Adharsh Browser Auditor.lnk")
            
            ps_script = f"""
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
            $Shortcut.TargetPath = '{dest_exe}'
            $Shortcut.WorkingDirectory = '{appdata_dir}'
            $Shortcut.IconLocation = '{dest_exe}'
            $Shortcut.Save()
            """
            
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True)

            time.sleep(1.5)
            self.after(0, self.show_finished)

        except Exception as e:
            self.after(0, lambda: self.show_error(str(e)))

    def show_finished(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self.success_label = ctk.CTkLabel(self.main_frame, text="Installation Successful!", 
                                          font=("Inter", 24, "bold"), text_color="#22c55e")
        self.success_label.pack(pady=(80, 20))

        self.info_label = ctk.CTkLabel(self.main_frame, text="A shortcut has been created on your Desktop.\nYou can now use Adharsh Browser Auditor with one click!", 
                                       font=("Inter", 14))
        self.info_label.pack(pady=10)

        self.finish_btn = ctk.CTkButton(self.main_frame, text="Launch & Finish", fg_color=self.primary_color, 
                                         command=self.launch_app)
        self.finish_btn.pack(pady=40)

    def launch_app(self):
        appdata_dir = os.path.join(os.environ['LOCALAPPDATA'], "AdharshBrowserAuditor")
        dest_exe = os.path.join(appdata_dir, "Adharsh_Browser_Auditor.exe")
        os.startfile(dest_exe)
        self.destroy()

    def show_error(self, err):
        ctk.CTkLabel(self.main_frame, text=f"Error: {err}", text_color="red").pack()

if __name__ == "__main__":
    app = SetupWizard()
    app.mainloop()
