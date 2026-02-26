import tkinter as tk
from tkinter import filedialog, messagebox
import shutil
import os

def main():
    root = tk.Tk()
    root.withdraw()  # Hide main window
    root.attributes('-topmost', True) # Keep dialog on top
    
    messagebox.showinfo("Adharsh Browser Auditor", "Please select the photo you just uploaded so we can add it to the website!")

    file_path = filedialog.askopenfilename(
        title="Select your Creator Profile Picture",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp")],
        parent=root
    )

    if file_path:
        dest_path = r"c:\Users\Administrator\Desktop\woww\creator.jpg"
        try:
            shutil.copy2(file_path, dest_path)
            messagebox.showinfo("Success!", "Creator profile picture updated! Refresh the website to see it.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy image: {e}")
    else:
        print("No file selected.")

if __name__ == "__main__":
    main()
