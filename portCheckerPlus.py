import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, Menu
import json
import os
from datetime import datetime
import platform
from pathlib import Path

import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS  # Set by PyInstaller
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_config_path():
    if platform.system() == "Windows":
        base = Path(os.getenv("APPDATA", os.getcwd()))
    elif platform.system() == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    config_dir = base / "PortCheckerPlus"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"

CONFIG_PATH = str(get_config_path())
default_config = {
    "timeout": 0.3,
    "export_results": False,
    "export_directory": os.getcwd(),
    "default_host": "",
    "default_ports": "",
    "retry_count": 2
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    # Write default config if file doesn't exist or is invalid
    with open(CONFIG_PATH, "w") as f:
        json.dump(default_config, f, indent=4)
    return default_config.copy()

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

def parse_ports(port_input):
    ports = []
    seen = set()
    parts = port_input.split(",")
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                for p in range(start, end + 1):
                    if p not in seen:
                        seen.add(p)
                        ports.append(p)
            except ValueError:
                continue
        else:
            try:
                p = int(part)
                if p not in seen:
                    seen.add(p)
                    ports.append(p)
            except ValueError:
                continue
    return ports

def open_settings_window(root, config):
    settings_win = tk.Toplevel(root)
    settings_win.title("Settings")
    settings_win.geometry("450x400")
    settings_win.configure(bg="#f0f0f0")
    settings_win.transient(root)
    settings_win.grab_set()

    def label(master, text):
        return tk.Label(master, text=text, bg="#f0f0f0", font=("Segoe UI", 10))

    show_open_only_var = tk.BooleanVar(value=config.get("show_open_only", False))
    show_open_only_check = tk.Checkbutton(settings_win, text="Only Show Open Ports", variable=show_open_only_var,
                                          bg="#f0f0f0", font=("Segoe UI", 10))
    show_open_only_check.pack(anchor="w", padx=12)

    export_var = tk.BooleanVar(value=config.get("export_results", False))
    export_check = tk.Checkbutton(settings_win, text="Export Results", variable=export_var,
                                   bg="#f0f0f0", font=("Segoe UI", 10))
    export_check.pack(anchor="w", padx=12)

    label(settings_win, "Export Directory:").pack(anchor="w", padx=12, pady=(12, 0))
    dir_frame = tk.Frame(settings_win, bg="#f0f0f0")
    dir_frame.pack(fill="x", padx=12)
    dir_entry = tk.Entry(dir_frame, font=("Segoe UI", 10))
    dir_entry.insert(0, config.get("export_directory", os.getcwd()))
    dir_entry.pack(side="left", fill="x", expand=True)
    browse_btn = tk.Button(dir_frame, text="Browse", font=("Segoe UI", 9))

    def browse_directory():
        selected = filedialog.askdirectory(parent=settings_win)
        if selected:
            dir_entry.delete(0, tk.END)
            dir_entry.insert(0, selected)
        settings_win.lift()
        settings_win.focus_force()

    browse_btn.config(command=browse_directory)
    browse_btn.pack(side="left", padx=5)

    def toggle_export_inputs():
        state = tk.NORMAL if export_var.get() else tk.DISABLED
        dir_entry.config(state=state)
        browse_btn.config(state=state)

    export_check.config(command=toggle_export_inputs)
    toggle_export_inputs()

    label(settings_win, "Custom Timeout (seconds):").pack(anchor="w", padx=12, pady=(12, 0))
    timeout_frame = tk.Frame(settings_win, bg="#f0f0f0")
    timeout_frame.pack(fill="x", padx=12)
    timeout_spin = tk.Spinbox(timeout_frame, width=5, from_=0.1, to=10.0, increment=0.1, format="%.1f", font=("Segoe UI", 9))
    timeout_spin.delete(0, tk.END)
    timeout_spin.insert(0, str(config.get("timeout", 0.3)))
    timeout_spin.pack(side="left")
    
    label(settings_win, "DNS Retry Count:").pack(anchor="w", padx=12, pady=(12, 0))
    retry_spin = tk.Spinbox(settings_win, from_=0, to=5, width=5, font=("Segoe UI", 9))
    retry_spin.delete(0, tk.END)
    retry_spin.insert(0, str(config.get("retry_count", 2)))
    retry_spin.pack(anchor="w", padx=12)
    label(settings_win, "Default Host:").pack(anchor="w", padx=12, pady=(12, 0))
    host_entry = tk.Entry(settings_win, font=("Segoe UI", 10))
    host_entry.insert(0, config.get("default_host", ""))
    host_entry.pack(fill="x", padx=12)

    label(settings_win, "Default Ports:").pack(anchor="w", padx=12, pady=(12, 0))
    ports_entry = tk.Entry(settings_win, font=("Segoe UI", 10))
    ports_entry.insert(0, config.get("default_ports", ""))
    ports_entry.pack(fill="x", padx=12)

    def on_save():
        try:
            config["timeout"] = float(timeout_spin.get())
            config["export_results"] = export_var.get()
            config["show_open_only"] = show_open_only_var.get()
            config["default_host"] = host_entry.get().strip()
            config["retry_count"] = int(retry_spin.get())
            config["default_ports"] = ports_entry.get().strip()

            # Validate default ports
            port_input = config["default_ports"]
            parsed_ports = parse_ports(port_input)
            invalid_ports = [p for p in parsed_ports if p > 65535]
            if invalid_ports:
                messagebox.showerror("Error", f"The following ports are invalid: {invalid_ports}\n\nValid port range: 0-65535")
                return

            if export_var.get():
                export_path = dir_entry.get().strip()
                if not export_path:
                    messagebox.showerror("Error", "Please select a directory for export.")
                    return
                config["export_directory"] = export_path

            save_config(config)
            if root and hasattr(root, "host_entry") and hasattr(root, "ports_entry"):
                root.host_entry.delete(0, tk.END)
                root.host_entry.insert(0, config["default_host"])
                root.ports_entry.delete(0, tk.END)
                root.ports_entry.insert(0, config["default_ports"])

            settings_win.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Timeout must be a number.")

    save_cancel_frame = tk.Frame(settings_win, bg="#f0f0f0")
    save_cancel_frame.pack(pady=15)

    def on_cancel():
        settings_win.destroy()

    save_btn = tk.Button(save_cancel_frame, text="Save", font=("Segoe UI", 10), command=on_save)
    save_btn.pack(side="left", padx=(0, 10))

    cancel_btn = tk.Button(save_cancel_frame, text="Cancel", font=("Segoe UI", 10), command=on_cancel)
    cancel_btn.pack(side="left")



def resolve_hostname_and_print(host, output_widget, config):
    retries = config.get("retry_count", 2)
    for attempt in range(retries + 1):
        try:
            output_widget.insert(tk.END, f"Resolving hostname: {host}\n")
            resolved_ip = socket.gethostbyname(host)
            output_widget.insert(tk.END, f"Resolved IP: {resolved_ip}\n")
            output_widget.insert(tk.END, f"Attempt: {attempt + 1}\n\n")
            return resolved_ip
        except socket.gaierror as e:
            if attempt == retries:
                messagebox.showerror("DNS Error", f"Could not resolve host: {host}{e}")
                return None
                time.sleep(0.5)

file_lock = threading.Lock()

def get_export_file_path(config):
    return os.path.join(config["export_directory"], "psp_log.txt")

def scan_port_with_export(host, port, output_widget, config, export_file_path):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(config.get("timeout", 0.3))
            result = sock.connect_ex((host, port))
            status = "OPEN" if result == 0 else "CLOSED"
            message = f"Port {port} is {status}\n"

            if config.get("show_open_only", False) and status != "OPEN":
                return
            output_widget.after(0, lambda: output_widget.insert(
                tk.END, message, "open" if status == "OPEN" else None))

            if config.get("export_results", False):
                os.makedirs(os.path.dirname(export_file_path), exist_ok=True)
                with file_lock:
                    with open(config.get("_current_export_file", export_file_path), "a") as f:
                        f.write(message)
    except Exception as e:
        error_msg = f"Error on port {port}: {e}\n"
        output_widget.after(0, lambda: output_widget.insert(tk.END, error_msg))
        if config.get("export_results", False):
            os.makedirs(os.path.dirname(export_file_path), exist_ok=True)
            with file_lock:
                with open(config.get("_current_export_file", export_file_path), "a") as f:
                    f.write(error_msg)

def check_ports_threaded_with_export(host, ports, output_widget, clear_button, config):
    clear_button.config(state=tk.NORMAL)
    export_file_path = get_export_file_path(config) if config.get("export_results") else None

    remaining = len(ports)
    counter = {"count": 0}
    counter_lock = threading.Lock()

    def on_port_done():
        with counter_lock:
            counter["count"] += 1
            if counter["count"] == remaining:
                output_widget.after(0, lambda: output_widget.insert(tk.END, f"\nScan complete.\nNumber of ports checked:{remaining}"))

    for port in ports:
        threading.Thread(
            target=lambda p=port: (
                scan_port_with_export(host, p, output_widget, config, export_file_path),
                on_port_done()
            ),
            daemon=True
        ).start()

def parse_ports(port_input):
    ports = []
    seen = set()
    parts = port_input.split(",")
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                for p in range(start, end + 1):
                    if p not in seen:
                        seen.add(p)
                        ports.append(p)
            except ValueError:
                continue
        else:
            try:
                p = int(part)
                if p not in seen:
                    seen.add(p)
                    ports.append(p)
            except ValueError:
                continue
    return ports

def on_check_ports_with_export():
    config = load_config()
    host = root.host_entry.get().strip()
    port_input = root.ports_entry.get().strip()

    if not host or not port_input:
        messagebox.showwarning("Input Error", "Please enter both host and port(s).")
        return

    root.output_text.delete("1.0", tk.END)
    resolved_ip = resolve_hostname_and_print(host, root.output_text, config)
    if resolved_ip and config.get("export_results"):
        export_file_path = get_export_file_path(config)
        try:
            with open(export_file_path, "a") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write("\n" + "=" * 5 + ("Scan Results: {}".format(timestamp) + "=" * 5 + "\n"))
                f.write("Host: {}\n".format(host))
                f.write("Resolved IP: {}\n".format(resolved_ip))
                f.write("Ports: {}\n\n".format(port_input))
        except Exception as e:
            messagebox.showerror("File Error", "Could not write export file: {}".format(e))
    if not resolved_ip:
        return

    try:
        ports = parse_ports(port_input)
        root.clear_button.config(state=tk.DISABLED)
        threading.Thread(
            target=check_ports_threaded_with_export,
            args=(host, ports, root.output_text, root.clear_button, config),
            daemon=True
        ).start()
        root.clear_button.config(state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror("Error", str(e))
def on_clear_output():

    root.output_text.delete("1.0", tk.END)
    root.clear_button.config(state=tk.DISABLED)

def run_gui():
    global root
    config = load_config()
    root = tk.Tk()
    icon_path = resource_path("psp_icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(default=icon_path)
    root.title("Port Checker Plus")
    root.configure(bg="#f8f8f8")
    root.geometry("600x450")

    menubar = Menu(root)
    file_menu = Menu(menubar, tearoff=0)
    file_menu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=file_menu)

    view_menu = Menu(menubar, tearoff=0)
    view_menu.add_command(label="Settings", command=lambda: open_settings_window(root, config))
    menubar.add_cascade(label="View", menu=view_menu)
    root.config(menu=menubar)

    host_frame = tk.Frame(root, bg="#f8f8f8")
    host_frame.pack(padx=12, pady=(15, 5), fill="x")
    tk.Label(host_frame, text="Host:", bg="#f8f8f8", font=("Segoe UI", 10)).pack(side="left")
    root.host_entry = tk.Entry(host_frame, width=40, font=("Segoe UI", 10))
    root.host_entry.pack(side="left", padx=(8, 0), fill="x", expand=True)
    root.host_entry.insert(0, config.get("default_host", ""))

    port_frame = tk.Frame(root, bg="#f8f8f8")
    port_frame.pack(padx=12, pady=5, fill="x")
    tk.Label(port_frame, text="Ports:", bg="#f8f8f8", font=("Segoe UI", 10)).pack(side="left")
    root.ports_entry = tk.Entry(port_frame, width=40, font=("Segoe UI", 10))
    root.ports_entry.pack(side="left", padx=(8, 0), fill="x", expand=True)
    root.ports_entry.insert(0, config.get("default_ports", ""))

    button_frame = tk.Frame(root, bg="#f8f8f8")
    button_frame.pack(padx=12, pady=(5, 10), fill="x")
    check_button = tk.Button(button_frame, text="Check Ports", font=("Segoe UI", 10), command=on_check_ports_with_export)
    check_button.pack(side="left", padx=(0, 5))
    root.clear_button = tk.Button(button_frame, text="Clear Results", font=("Segoe UI", 10), command=on_clear_output, state=tk.DISABLED)
    root.clear_button.pack(side="left")

    root.output_text = scrolledtext.ScrolledText(root, font=("Courier", 10), width=70, height=20, wrap="none")
    root.output_text.pack(padx=12, pady=10, fill="both", expand=True)
    root.output_text.tag_config('open', foreground='green')

    root.mainloop()

if __name__ == "__main__":
    run_gui()