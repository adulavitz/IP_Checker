import tkinter as tk
from tkinter import messagebox, PhotoImage
import requests
import threading
import time
import winsound
import subprocess
import json
import os
import sys
from datetime import datetime
from aslookup import get_as_data
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
from win10toast import ToastNotifier
import tkinter as tk
import ctypes
from ctypes import wintypes

import tkinter as tk
from tkinter import PhotoImage
import time

def show_splash():
    splash_root = tk.Toplevel()
    splash_root.overrideredirect(True)
    splash_root.attributes("-topmost", True)

    splash_img = PhotoImage(file=resource_path("splash.png"))
    resized_img = splash_img.subsample(3)  # ~35%

    img_width = resized_img.width()
    img_height = resized_img.height()
    screen_width = splash_root.winfo_screenwidth()
    screen_height = splash_root.winfo_screenheight()
    pos_x = int((screen_width - img_width) / 2)
    pos_y = int((screen_height - img_height) / 2)

    splash_root.geometry(f"{img_width}x{img_height}+{pos_x}+{pos_y}")

    canvas = tk.Canvas(splash_root, width=img_width, height=img_height, highlightthickness=0)
    canvas.pack()
    canvas.create_image(0, 0, anchor="nw", image=resized_img)

    splash_root.after(3500, splash_root.destroy)
    splash_root.update()

    root.wait_window(splash_root)

last_real_isp = None
# === Config ===
APP_VERSION = "1.0.4"
CONFIG_FILE = "ipchecker_config.json"

# === Globals ===
sound_enabled = True
last_asn = None
is_minimized = False
dark_mode = False
tray_icon = None
toast = ToastNotifier()

status_light = None
conn_icon_label = None
wired_icon_img = None
wireless_icon_img = None

import os
from datetime import datetime

# Other imports...

import sys
import os

def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller uses this during --onefile runtime
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") if self.widget.bbox("insert") else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tip, text=self.text() if callable(self.text) else self.text, bg="lightyellow", fg="black",
                         relief="solid", borderwidth=1, font=("Segoe UI", 8))
        label.pack(ipadx=4, ipady=2)

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

def resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.abspath(filename)


import ctypes

def load_settings():
    try:
        with open(resource_path(CONFIG_FILE), "r") as f:
            return json.load(f)
    except:
        return {"dark_mode": False}

def save_settings(settings):
    with open(resource_path(CONFIG_FILE), "w") as f:
        json.dump(settings, f)

def get_external_ip():
    try:
        return requests.get("https://api64.ipify.org?format=json", timeout=5).json()["ip"]
    except:
        return "Unavailable"

def get_isp_info(ip):
    try:
        as_info = get_as_data(ip)
        if not as_info: return "Unknown", "Unknown ISP"
        if isinstance(as_info, list): as_info = as_info[0]
        return as_info.asn, f"{as_info.asn} - {as_info.isp}"
    except:
        return "Lookup Failed", "Lookup Failed"

def get_network_name():
    try:
        result = subprocess.check_output("netsh wlan show interfaces", shell=True).decode()
        for line in result.splitlines():
            if "SSID" in line and "BSSID" not in line:
                return line.split(":", 1)[1].strip()
    except:
        return "Unavailable"

def get_connection_type():
    try:
        result = subprocess.check_output("netsh interface show interface", shell=True).decode()
        for line in result.splitlines():
            if "Connected" in line:
                if "Wi-Fi" in line or "Wireless" in line:
                    return "wireless"
                elif "Ethernet" in line:
                    return "wired"
        return "disconnected"
    except:
        return "unknown"

def update_status_light(connected=True):
    color = "#33cc33" if connected else "#cc3333"
    status_canvas.itemconfig(status_light, fill=color)

def update_connection_icon():
    conn_type = get_connection_type()
    if conn_type == "wired":
        conn_icon_label.config(image=wired_icon_img)
        conn_icon_label.image = wired_icon_img
    elif conn_type == "wireless":
        conn_icon_label.config(image=wireless_icon_img)
        conn_icon_label.image = wireless_icon_img
    else:
        conn_icon_label.config(image=None)

def show_toast(message):
    try:
        toast.show_toast("IP Checker", message, duration=5, threaded=True)
    except:
        pass

import winsound

def play_alert(filename):
    if sound_enabled and filename:
        try:
            winsound.PlaySound(resource_path(filename), winsound.SND_FILENAME | winsound.SND_ASYNC)
        except RuntimeError as e:
            # Log the error or pass
            print(f"Sound playback failed: {e}")

def log_event(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp}  {message}\n"

    # Update GUI
    log_box.insert(tk.END, entry)
    log_box.see(tk.END)

    # Write to monthly log file
    log_path = get_log_path()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)

def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode
    toggle_btn.config(relief="sunken" if dark_mode else "raised", text="🌙 Dark Mode ON" if dark_mode else "☀️ Dark Mode OFF")
    bg = "#1e1e1e" if dark_mode else "SystemButtonFace"
    fg = "#ffffff" if dark_mode else "black"
    data_fg = "#7cd4ff" if dark_mode else "black"
    box_bg = "#2b2b2b" if dark_mode else "white"
    box_fg = "#ffff66" if dark_mode else "black"

    for widget in [root, main_frame, log_box]:
        widget.configure(bg=bg)
    for label in [ssid_label, ip_label, isp_label, toggle_btn, tray_button, about_button]:
        label.configure(bg=bg, fg=fg)
    for data in [ssid_data, ip_data, isp_data]:
        data.configure(fg=data_fg, bg=bg)
    log_box.configure(bg=box_bg, fg=box_fg, insertbackground=box_fg)
    status_canvas.configure(bg=bg)
    conn_icon_label.configure(bg=bg)
    # Refresh satellite label color if active
    connection_type_label.config(
        fg="#ffff66" if dark_mode and connection_type_label.cget("text") else "black",
        bg=main_frame.cget("bg")
    )


def update_loop():
    global last_asn, is_minimized, last_real_isp
    while True:
        ip = get_external_ip()
        asn, isp_text = get_isp_info(ip) if ip != "Unavailable" else ("Unknown", "No connection")
        connected = ip != "Unavailable"

        if asn != last_asn:
            ip_data.config(text=ip)
            isp_data.config(text=isp_text)

            ssid = get_network_name()
            ssid_data.config(text=ssid)

            isp_lower = isp_text.lower()
            connection_type = ""

            if "propelcloud" in isp_lower:
                if last_real_isp is None:
                    connection_type = "Undetermined Connection"
                elif "space" in last_real_isp.lower():
                    connection_type = "Satellite Connection"
                else:
                    connection_type = "Cellular Connection"
            else:
                last_real_isp = isp_text  # Store the most recent non-propelCLOUD ISP

            # Update connection type label
            bg_color = main_frame.cget("bg")
            fg_color = "#ffff66" if dark_mode and connection_type else "black"

            connection_type_label.config(
                text=connection_type,
                fg=fg_color,
                bg=bg_color
            )
            update_status_light(connected)
            update_connection_icon()
            log_event(f"{ip} | {isp_text}")

            if last_asn is None and connected:
                play_alert("connect.wav")
            elif not connected:
                play_alert("disconnect.wav")
            else:
                play_alert("change.wav")
                show_toast(f"Connection changed: {isp_text}")

            if is_minimized:
                show_window()

            last_asn = asn

        time.sleep(30)

def save_state():
    settings = {
        "dark_mode": dark_mode,
        "position": root.geometry()
    }
    save_settings(settings)

def create_icon():
    icon_img = Image.new("RGB", (64, 64), (50, 160, 255))
    d = ImageDraw.Draw(icon_img)
    d.ellipse((20, 20, 44, 44), fill=(255, 255, 255))
    return icon_img

def minimize_to_tray():
    global is_minimized, tray_icon
    if messagebox.askokcancel("Minimize to Tray", "The app will continue running in the system tray."):
        is_minimized = True
        root.withdraw()
        if not tray_icon:
            tray_icon = Icon("IP Checker", icon=create_icon(), title="IP Checker", menu=Menu(
                MenuItem("Restore", show_window),
                MenuItem("Quit", exit_app)
            ))
            threading.Thread(target=tray_icon.run, daemon=True).start()

def show_window(icon=None, item=None):
    global is_minimized
    is_minimized = False
    root.deiconify()
    root.after(100, position_window)

def exit_app(icon=None, item=None):
    save_state()
    if tray_icon:
        tray_icon.visible = False
        tray_icon.stop()
    root.quit()  # Clean exit of the Tkinter mainloop
    os._exit(0)  # Force process shutdown


def show_about():
    messagebox.showinfo("About IP Checker", f"IP Checker\nVersion: {APP_VERSION}\n© 2024 Andrew Dulavitz\nEmail: adulavitz@hotmail.com")

def position_window():
    root.update_idletasks()
    w, sw = root.winfo_width(), root.winfo_screenwidth()
    x, y = sw - w - 6, 6
    root.geometry(f"+{x}+{y}")



root = tk.Tk()
root.withdraw()
root.geometry("+10000+10000")  # Move offscreen immediately

show_splash()  # No assignment here

root.deiconify()
root.title("IP Checker")
root.geometry("460x300")       # Move to correct position
root.protocol("WM_DELETE_WINDOW", minimize_to_tray)


icon_path = resource_path("IP_Checker.png")
if os.path.exists(icon_path):
    try:
        app_icon = tk.PhotoImage(file=icon_path)
        root.iconphoto(False, app_icon)
    except Exception as e:
        print("Failed to set icon:", e)

main_frame = tk.Frame(root)
main_frame.pack(padx=10, pady=10, fill="both", expand=True)

# Load icons
wired_icon_img = PhotoImage(file=resource_path("wired.png"))
wireless_icon_img = PhotoImage(file=resource_path("wireless.png"))

def get_log_path():
    now = datetime.now()
    filename = f"{now.strftime('%y-%m')}_IP_Checker_Log.txt"
    log_dir = os.path.join(os.getcwd(), "Logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, filename)

# Then follow with:
# - log_event()
# - get_external_ip()
# - get_network_name()
# etc.

from tkinter import filedialog
import webbrowser

def view_logs():
    log_path = filedialog.askopenfilename(
        initialdir=os.path.join(os.getcwd(), "Logs"),
        title="Select a log file",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if log_path:
        webbrowser.open(log_path)

view_logs_button = tk.Button(
    main_frame,
    text="View Logs",
    font=("Segoe UI", 9),
    width=18,
    command=view_logs)
view_logs_button.grid(row=5, column=1, sticky="w", pady=(8, 0), padx=(4, 0))
def update_connection_icon():
    conn_type = get_connection_type()
    if conn_type == "wired":
        conn_icon_label.config(image=wired_icon_img)
        conn_icon_label.image = wired_icon_img
        conn_icon_label.tooltip_text = "Wired Connection"
    elif conn_type == "wireless":
        conn_icon_label.config(image=wireless_icon_img)
        conn_icon_label.image = wireless_icon_img
        conn_icon_label.tooltip_text = "Wireless Connection"
    else:
        conn_icon_label.config(image=None)
        conn_icon_label.tooltip_text = ""

status_canvas = tk.Canvas(root, width=16, height=16, highlightthickness=0, bg="SystemButtonFace")
status_canvas.place(relx=1.0, x=-20, y=10, anchor="ne")
status_light = status_canvas.create_oval(2, 2, 14, 14, fill="#cc3333")

# Connection icon - bottom right, separated from layout
conn_icon_label = tk.Label(main_frame, image=None, bg="SystemButtonFace")
conn_icon_label.grid(row=5, column=4, sticky="e", padx=4, pady=(8, 0))

# Tooltip attachment
ToolTip(conn_icon_label, lambda: getattr(conn_icon_label, "tooltip_text", ""))

# Suggested 5-column layout
main_frame.columnconfigure(0, weight=0)  # Label column
main_frame.columnconfigure(1, weight=1)  # Data (start)
main_frame.columnconfigure(2, weight=1)
main_frame.columnconfigure(3, weight=1)  # Data (end of span)
main_frame.columnconfigure(4, weight=0)  # Spacer or future use

# Info Labels using column span for data
ssid_label = tk.Label(main_frame, text="Network ID:", font=("Segoe UI", 9), anchor="w")
ssid_label.grid(row=0, column=0, sticky="w", padx=5)
ssid_data = tk.Label(main_frame, text=get_network_name(), font=("Segoe UI", 9), anchor="w")
ssid_data.grid(row=0, column=1, columnspan=3, sticky="w")

ip_label = tk.Label(main_frame, text="External IP:", font=("Segoe UI", 9), anchor="w")
ip_label.grid(row=1, column=0, sticky="w", padx=5)
ip_data = tk.Label(main_frame, text="...", font=("Segoe UI", 9), anchor="w")
ip_data.grid(row=1, column=1, columnspan=3, sticky="w")

isp_label = tk.Label(main_frame, text="ISP:", font=("Segoe UI", 9), anchor="w")
isp_label.grid(row=2, column=0, sticky="w", padx=5)
isp_data = tk.Label(main_frame, text="...", font=("Segoe UI", 9), anchor="w")
isp_data.grid(row=2, column=1, columnspan=3, sticky="w")

# Log Box spans full width
log_box = tk.Text(main_frame, height=9, font=("Consolas", 9), wrap="none")
log_box.grid(row=3, column=0, columnspan=5, pady=(10, 0))
log_box.insert(tk.END, "Log started...\n")

connection_type_label = tk.Label(main_frame, font=("Segoe UI", 10, "bold"), anchor="w", text="")
connection_type_label.grid(row=4, column=1, columnspan=3, sticky="w", padx=40, pady=(6, 0))

#about_button = tk.Button(main_frame, text="About", command=show_about)
#about_button.grid(row=5, column=0, sticky="w", columnspan=2, pady=(6, 0))

# Dark mode toggle button
toggle_btn = tk.Button(main_frame, text="☀️ Dark Mode OFF", font=("Segoe UI", 9), width=18, relief="raised", command=toggle_dark_mode)
toggle_btn.grid(row=4, column=0, sticky="w", pady=(10, 0), padx=4)

# About button - aligned with toggle
about_button = tk.Button(main_frame, text="About", font=("Segoe UI", 9), command=show_about)
about_button.grid(row=4, column=4, sticky="e", pady=(10, 0), padx=4)

# Tray button - stacked under toggle
tray_button = tk.Button(main_frame, text="Minimize to Tray", font=("Segoe UI", 9), width=18, command=minimize_to_tray)
tray_button.grid(row=5, column=0, sticky="w", pady=(8, 0), padx=4)

# Connection icon - bottom right, separated from layout
conn_icon_label = tk.Label(main_frame, image=None, bg="SystemButtonFace")
conn_icon_label.grid(row=5, column=4, sticky="e", padx=4, pady=(8, 0))
ToolTip(conn_icon_label, lambda: getattr(conn_icon_label, "tooltip_text", ""))

# === Load settings and initialize ===
prefs = load_settings()
dark_mode = prefs.get("dark_mode", False)
if dark_mode:
    toggle_dark_mode()

if "position" in prefs:
    root.geometry(prefs["position"])
else:
    root.after(100, position_window)

# Start update thread and launch app
threading.Thread(target=update_loop, daemon=True).start()
root.mainloop()