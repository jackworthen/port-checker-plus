import socket
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog, Menu
import json
import os
from datetime import datetime
import platform
from pathlib import Path
import time

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
    "retry_count": 2,
    "scan_protocol": "TCP",
    "show_open_only": False
}

# Define common port profiles
PORT_PROFILES = {
    "Custom": {"ports": "", "protocol": "TCP"},
    "Web Servers": {"ports": "80,443,8080,8443,8000,8008,9000,9080", "protocol": "TCP"},
    "Mail Servers": {"ports": "25,110,143,993,995,587,465,2525", "protocol": "TCP"},
    "File Transfer": {"ports": "21,22,69,873,989,990,2049", "protocol": "TCP"},
    "Database": {"ports": "1433,1521,3306,5432,27017,6379,11211,1521", "protocol": "TCP"},
    "Network Services": {"ports": "53,67,68,123,161,162,514,520", "protocol": "UDP"},
    "Remote Access": {"ports": "22,23,3389,5900,5901,5902,5800", "protocol": "TCP"},
    "Gaming": {"ports": "27015,7777,25565,19132,28015,27017,28016", "protocol": "TCP/UDP"},
    "Top 100 Common": {"ports": "7,9,13,21-23,25-26,37,53,79-81,88,106,110-111,113,119,135,139,143-144,179,199,389,427,443-445,993-995,1723,3306,3389,5632,5900,6000-6001,8000,8008,8080-8081,8443,8888,9100", "protocol": "TCP"},
    "Security Scan": {"ports": "21,22,23,25,53,80,110,111,135,139,143,443,993,995,1723,3306,3389,5900,8080", "protocol": "TCP"},
    "P2P/Torrent": {"ports": "6881-6889,51413,25401,6346,4662", "protocol": "TCP/UDP"},
    "Streaming/Media": {"ports": "554,1935,8554,8080,1755,7070", "protocol": "TCP"},
    "VPN Services": {"ports": "1194,500,4500,1723,1701", "protocol": "UDP"},
    "Development": {"ports": "3000,3001,4000,5000,8000,8080,9000,5173,3001", "protocol": "TCP"}
}

# Port categorization removed - all open ports will be green

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

def get_matching_profile(config):
    """Determine which profile matches current config"""
    current_ports = config.get("default_ports", "")
    current_protocol = config.get("scan_protocol", "TCP")
    
    # Check if current config matches any predefined profile
    for profile_name, profile_data in PORT_PROFILES.items():
        if profile_name == "Custom":
            continue
        if (profile_data["ports"] == current_ports and 
            profile_data["protocol"] == current_protocol):
            return profile_name
    
    # If no match found, return Custom
    return "Custom"

def get_profile_color(profile_name):
    """Return color scheme for different profile types"""
    color_map = {
        "Custom": {"bg": "#e74c3c", "fg": "white"},
        "Web Servers": {"bg": "#3498db", "fg": "white"},
        "Mail Servers": {"bg": "#2ecc71", "fg": "white"},
        "File Transfer": {"bg": "#f39c12", "fg": "white"},
        "Database": {"bg": "#9b59b6", "fg": "white"},
        "Network Services": {"bg": "#1abc9c", "fg": "white"},
        "Remote Access": {"bg": "#e67e22", "fg": "white"},
        "Gaming": {"bg": "#e91e63", "fg": "white"},
        "Top 100 Common": {"bg": "#34495e", "fg": "white"},
        "Security Scan": {"bg": "#8e44ad", "fg": "white"},
        "P2P/Torrent": {"bg": "#16a085", "fg": "white"},
        "Streaming/Media": {"bg": "#d35400", "fg": "white"},
        "VPN Services": {"bg": "#27ae60", "fg": "white"},
        "Development": {"bg": "#2980b9", "fg": "white"}
    }
    return color_map.get(profile_name, {"bg": "#95a5a6", "fg": "white"})

def update_profile_indicator():
    """Update the profile indicator label"""
    if hasattr(root, 'profile_label'):
        config = load_config()
        current_profile = get_matching_profile(config)
        colors = get_profile_color(current_profile)
        
        root.profile_label.config(
            text=f" {current_profile} ",
            bg=colors["bg"],
            fg=colors["fg"]
        )

def open_settings_window(root, config):
    settings_win = tk.Toplevel(root)
    settings_win.title("Settings - Port Checker Plus")
    settings_win.geometry("520x560")
    settings_win.configure(bg="#ffffff")
    settings_win.transient(root)
    settings_win.grab_set()
    settings_win.resizable(False, False)
    set_window_icon(settings_win)

    # Create main container with padding
    main_frame = tk.Frame(settings_win, bg="#ffffff")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Title
    title_label = tk.Label(main_frame, text="Settings", 
                          font=("Segoe UI", 14, "bold"), bg="#ffffff", fg="#2c3e50")
    title_label.pack(anchor="w", pady=(0, 20))

    # Create notebook for tabbed interface
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill="both", expand=True, pady=(0, 20))

    # ===== DEFAULTS TAB =====
    defaults_frame = tk.Frame(notebook, bg="#ffffff")
    notebook.add(defaults_frame, text="Defaults")

    # Port Profiles Section
    profiles_section = tk.LabelFrame(defaults_frame, text="Port Profiles", 
                                    font=("Segoe UI", 10, "bold"), bg="#ffffff", 
                                    fg="#34495e", padx=15, pady=10)
    profiles_section.pack(fill="x", padx=15, pady=(15, 10))

    # Profile selection
    profile_frame = tk.Frame(profiles_section, bg="#ffffff")
    profile_frame.pack(fill="x", pady=(5, 15))
    
    tk.Label(profile_frame, text="Select Profile:", font=("Segoe UI", 10), 
             bg="#ffffff", fg="#2c3e50").pack(anchor="w", pady=(0, 5))
    
    # Set the profile variable to the matching profile
    initial_profile = get_matching_profile(config)
    profile_var = tk.StringVar(value=initial_profile)
    profile_options = list(PORT_PROFILES.keys())
    profile_combo = ttk.Combobox(profile_frame, textvariable=profile_var, 
                                values=profile_options, state="readonly", 
                                font=("Segoe UI", 10), width=25)
    profile_combo.pack(anchor="w")

    # Profile description
    profile_desc = tk.Label(profiles_section, text="Select a predfined port range based on common services.", 
                           font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d", wraplength=450, justify="left")
    profile_desc.pack(anchor="w", pady=(5, 0))

    # Default Values Section
    defaults_section = tk.LabelFrame(defaults_frame, text="Default Values", 
                                    font=("Segoe UI", 10, "bold"), bg="#ffffff", 
                                    fg="#34495e", padx=15, pady=10)
    defaults_section.pack(fill="x", padx=15, pady=10)

    # Default host
    tk.Label(defaults_section, text="Default Host:", font=("Segoe UI", 10), 
             bg="#ffffff", fg="#2c3e50").pack(anchor="w", pady=(5, 2))
    host_entry = tk.Entry(defaults_section, font=("Segoe UI", 10), width=50)
    host_entry.insert(0, config.get("default_host", ""))
    host_entry.pack(fill="x", pady=(0, 15))

    # Default ports
    tk.Label(defaults_section, text="Default Ports:", font=("Segoe UI", 10), 
             bg="#ffffff", fg="#2c3e50").pack(anchor="w", pady=(0, 2))
    tk.Label(defaults_section, text="Examples: 80,443,22 or 1-100,8080", 
             font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d").pack(anchor="w")
    ports_entry = tk.Entry(defaults_section, font=("Segoe UI", 10), width=50)
    ports_entry.insert(0, config.get("default_ports", ""))
    ports_entry.pack(fill="x", pady=(5, 0))

    # ===== GENERAL TAB =====
    general_frame = tk.Frame(notebook, bg="#ffffff")
    notebook.add(general_frame, text="General")

    # Scanning Options Section
    scan_section = tk.LabelFrame(general_frame, text="Scanning Options", 
                                font=("Segoe UI", 10, "bold"), bg="#ffffff", 
                                fg="#34495e", padx=15, pady=10)
    scan_section.pack(fill="x", padx=15, pady=(15, 10))

    # Protocol selection
    protocol_frame = tk.Frame(scan_section, bg="#ffffff")
    protocol_frame.pack(fill="x", pady=(0, 12))
    tk.Label(protocol_frame, text="Scan Protocol:", font=("Segoe UI", 10), 
             bg="#ffffff", fg="#2c3e50").pack(side="left")
    protocol_options = ["TCP", "UDP", "TCP/UDP"]
    protocol_var = tk.StringVar(value=config.get("scan_protocol", "TCP"))
    protocol_menu = ttk.Combobox(protocol_frame, textvariable=protocol_var, 
                                values=protocol_options, state="readonly", width=12,
                                font=("Segoe UI", 10))
    protocol_menu.pack(side="right")

    # Store custom values - initialize with current config if we're starting in Custom mode
    if initial_profile == "Custom":
        custom_values = {
            "ports": config.get("default_ports", ""),
            "protocol": config.get("scan_protocol", "TCP")
        }
    else:
        custom_values = {
            "ports": "",
            "protocol": "TCP"
        }
    
    # Track if we're currently in custom mode to save user input
    current_mode = {"is_custom": initial_profile == "Custom"}
    
    # Profile selection callback
    def on_profile_change(event=None):
        selected_profile = profile_var.get()
        if selected_profile in PORT_PROFILES:
            profile_data = PORT_PROFILES[selected_profile]
            
            # If we're switching FROM custom mode, save the current custom values
            if current_mode["is_custom"] and selected_profile != "Custom":
                custom_values["ports"] = ports_entry.get().strip()
                custom_values["protocol"] = protocol_var.get()
            
            if selected_profile == "Custom":
                # Set to saved custom values
                ports_entry.delete(0, tk.END)
                ports_entry.insert(0, custom_values["ports"])
                protocol_var.set(custom_values["protocol"])
                current_mode["is_custom"] = True
            else:
                # Update ports entry and protocol with profile data
                ports_entry.delete(0, tk.END)
                ports_entry.insert(0, profile_data["ports"])
                protocol_var.set(profile_data["protocol"])
                current_mode["is_custom"] = False

    profile_combo.bind("<<ComboboxSelected>>", on_profile_change)

    # Timeout setting
    timeout_frame = tk.Frame(scan_section, bg="#ffffff")
    timeout_frame.pack(fill="x", pady=(0, 12))
    tk.Label(timeout_frame, text="Connection Timeout (seconds):", font=("Segoe UI", 10), 
             bg="#ffffff", fg="#2c3e50").pack(side="left")
    timeout_spin = tk.Spinbox(timeout_frame, width=8, from_=0.1, to=10.0, 
                             increment=0.1, format="%.1f", font=("Segoe UI", 10))
    timeout_spin.delete(0, tk.END)
    timeout_spin.insert(0, str(config.get("timeout", 0.3)))
    timeout_spin.pack(side="right")

    # DNS retry count
    retry_frame = tk.Frame(scan_section, bg="#ffffff")
    retry_frame.pack(fill="x", pady=(0, 12))
    tk.Label(retry_frame, text="DNS Retry Count:", font=("Segoe UI", 10), 
             bg="#ffffff", fg="#2c3e50").pack(side="left")
    retry_spin = tk.Spinbox(retry_frame, from_=0, to=5, width=8, font=("Segoe UI", 10))
    retry_spin.delete(0, tk.END)
    retry_spin.insert(0, str(config.get("retry_count", 2)))
    retry_spin.pack(side="right")

    # Display Options Section
    display_section = tk.LabelFrame(general_frame, text="Display Options", 
                                   font=("Segoe UI", 10, "bold"), bg="#ffffff", 
                                   fg="#34495e", padx=15, pady=10)
    display_section.pack(fill="x", padx=15, pady=10)

    show_open_only_var = tk.BooleanVar(value=config.get("show_open_only", False))
    show_open_check = tk.Checkbutton(display_section, 
                                    text="Only show OPEN ports", 
                                    variable=show_open_only_var,
                                    bg="#ffffff", font=("Segoe UI", 10), 
                                    fg="#2c3e50", activebackground="#ffffff")
    show_open_check.pack(anchor="w", pady=5)

    # ===== EXPORT TAB =====
    export_frame = tk.Frame(notebook, bg="#ffffff")
    notebook.add(export_frame, text="Logging")

    # Export Options Section
    export_section = tk.LabelFrame(export_frame, text="Export Options", 
                                  font=("Segoe UI", 10, "bold"), bg="#ffffff", 
                                  fg="#34495e", padx=15, pady=10)
    export_section.pack(fill="x", padx=15, pady=(15, 10))

    export_var = tk.BooleanVar(value=config.get("export_results", False))
    export_check = tk.Checkbutton(export_section, 
                                 text="Enable logging", 
                                 variable=export_var,
                                 bg="#ffffff", font=("Segoe UI", 10), 
                                 fg="#2c3e50", activebackground="#ffffff")
    export_check.pack(anchor="w", pady=(5, 15))

    # Export directory
    dir_label = tk.Label(export_section, text="Export Directory:", 
                        font=("Segoe UI", 10), bg="#ffffff", fg="#2c3e50")
    dir_label.pack(anchor="w", pady=(0, 5))

    dir_frame = tk.Frame(export_section, bg="#ffffff")
    dir_frame.pack(fill="x", pady=(0, 10))
    
    dir_entry = tk.Entry(dir_frame, font=("Segoe UI", 10))
    dir_entry.insert(0, config.get("export_directory", os.getcwd()))
    dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
    
    browse_btn = tk.Button(dir_frame, text="Browse...", font=("Segoe UI", 9),
                          bg="#3498db", fg="white", activebackground="#2980b9",
                          relief="flat", padx=15)
    browse_btn.pack(side="right")

    def browse_directory():
        selected = filedialog.askdirectory(parent=settings_win)
        if selected:
            dir_entry.delete(0, tk.END)
            dir_entry.insert(0, selected)
        settings_win.lift()
        settings_win.focus_force()

    browse_btn.config(command=browse_directory)

    def toggle_export_inputs():
        state = tk.NORMAL if export_var.get() else tk.DISABLED
        dir_entry.config(state=state)
        browse_btn.config(state=state)
        dir_label.config(fg="#2c3e50" if export_var.get() else "#bdc3c7")

    export_check.config(command=toggle_export_inputs)
    toggle_export_inputs()

    # Export file info
    info_label = tk.Label(export_section, 
                         text="Log will be saved to 'portcheck_log.txt' in the selected directory",
                         font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d")
    info_label.pack(anchor="w", pady=(5, 0))

    # ===== BUTTONS FRAME =====
    button_frame = tk.Frame(main_frame, bg="#ffffff")
    button_frame.pack(fill="x", pady=(10, 0))

    # Separator line
    separator = tk.Frame(button_frame, height=1, bg="#e0e0e0")
    separator.pack(fill="x", pady=(0, 15))

    # Button container
    btn_container = tk.Frame(button_frame, bg="#ffffff")
    btn_container.pack(anchor="e")

    def on_cancel():
        settings_win.destroy()

    def on_save():
        try:
            # Validate timeout
            timeout_val = float(timeout_spin.get())
            if timeout_val <= 0:
                messagebox.showerror("Invalid Input", "Timeout must be greater than 0.")
                return

            # Validate default ports if provided
            port_input = ports_entry.get().strip()
            if port_input:
                parsed_ports = parse_ports(port_input)
                invalid_ports = [p for p in parsed_ports if p > 65535]
                if invalid_ports:
                    messagebox.showerror("Invalid Ports", 
                                       f"The following ports are invalid: {invalid_ports}\n\n"
                                       f"Valid port range: 0-65535")
                    return

            # Validate export directory if export is enabled
            if export_var.get():
                export_path = dir_entry.get().strip()
                if not export_path:
                    messagebox.showerror("Export Error", "Please select a directory for export.")
                    return
                if not os.path.exists(export_path):
                    try:
                        os.makedirs(export_path, exist_ok=True)
                    except Exception as e:
                        messagebox.showerror("Export Error", 
                                           f"Cannot create export directory:\n{e}")
                        return

            # Save configuration
            config["timeout"] = timeout_val
            config["export_results"] = export_var.get()
            config["show_open_only"] = show_open_only_var.get()
            config["default_host"] = host_entry.get().strip()
            config["retry_count"] = int(retry_spin.get())
            config["default_ports"] = port_input
            config["scan_protocol"] = protocol_var.get()
            
            if export_var.get():
                config["export_directory"] = dir_entry.get().strip()

            save_config(config)
            
            # Update main window if it exists
            if root and hasattr(root, "host_entry") and hasattr(root, "ports_entry"):
                root.host_entry.delete(0, tk.END)
                root.host_entry.insert(0, config["default_host"])
                root.ports_entry.delete(0, tk.END)
                root.ports_entry.insert(0, config["default_ports"])
                root.protocol_var.set(config["scan_protocol"])
                
                # Update the profile indicator
                update_profile_indicator()

            messagebox.showinfo("Settings Saved", "Your settings have been saved successfully.")
            settings_win.destroy()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", "Please check your input values.")

    # Style buttons
    cancel_btn = tk.Button(btn_container, text="Cancel", font=("Segoe UI", 10),
                          command=on_cancel, bg="#95a5a6", fg="white", 
                          activebackground="#7f8c8d", relief="flat", padx=20, pady=8)
    cancel_btn.pack(side="right", padx=(10, 0))

    save_btn = tk.Button(btn_container, text="Save Settings", font=("Segoe UI", 10, "bold"),
                        command=on_save, bg="#27ae60", fg="white", 
                        activebackground="#229954", relief="flat", padx=20, pady=8)
    save_btn.pack(side="right")

    # Center the window
    settings_win.update_idletasks()
    x = (settings_win.winfo_screenwidth() // 2) - (settings_win.winfo_width() // 2)
    y = (settings_win.winfo_screenheight() // 2) - (settings_win.winfo_height() // 2)
    settings_win.geometry(f"+{x}+{y}")

def resolve_hostname_and_print(host, results_tree, config):
    retries = config.get("retry_count", 2)
    for attempt in range(retries + 1):
        try:
            resolved_ip = socket.gethostbyname(host)
            return resolved_ip
        except socket.gaierror as e:
            if attempt == retries:
                messagebox.showerror("DNS Error", f"Could not resolve host: {host} - {e}")
                return None
            time.sleep(0.5)

file_lock = threading.Lock()

def get_export_file_path(config):
    return os.path.join(config["export_directory"], "portcheck_log.txt")

def get_port_category(port):
    """All ports use the same category now - simplified"""
    return "normal"

def scan_port_with_export(host, port, results_tree, config, export_file_path, scan_results):
    try:
        start_time = time.time()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(config.get("timeout", 0.3))
            result = sock.connect_ex((host, port))
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 1)  # Convert to ms
            
            status = "OPEN" if result == 0 else "CLOSED"

        try:
            service = socket.getservbyport(port)
        except:
            service = 'Unknown'

        # Create result data
        result_data = {
            'port': port,
            'protocol': 'TCP',
            'status': status,
            'service': service,
            'response_time': response_time if status == "OPEN" else 0,
            'category': get_port_category(port)
        }

        if config.get("show_open_only", False) and status != "OPEN":
            return

        # Store result for later insertion into tree
        scan_results.append(result_data)

        message = f"TCP Port {port} is {status} (Service: {service})\n"
        if config.get("export_results", False):
            os.makedirs(os.path.dirname(export_file_path), exist_ok=True)
            with file_lock:
                with open(config.get("_current_export_file", export_file_path), "a") as f:
                    f.write(message)

    except Exception as e:
        error_data = {
            'port': port,
            'protocol': 'TCP',
            'status': 'ERROR',
            'service': str(e),
            'response_time': 0,
            'category': 'error'
        }
        scan_results.append(error_data)
        
        error_msg = f"Error on TCP port {port}: {e}\n"
        if config.get("export_results", False):
            os.makedirs(os.path.dirname(export_file_path), exist_ok=True)
            with file_lock:
                with open(config.get("_current_export_file", export_file_path), "a") as f:
                    f.write(error_msg)

def scan_udp_port(host, port, results_tree, config, export_file_path, scan_results):
    try:
        start_time = time.time()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(config.get("timeout", 0.3))
            sock.sendto(b"", (host, port))
            try:
                data, _ = sock.recvfrom(1024)
                status = "OPEN"
                end_time = time.time()
                response_time = round((end_time - start_time) * 1000, 1)
            except socket.timeout:
                status = "OPEN|FILTERED"
                end_time = time.time()
                response_time = round((end_time - start_time) * 1000, 1)
        
        result_data = {
            'port': port,
            'protocol': 'UDP',
            'status': status,
            'service': 'Unknown',
            'response_time': response_time if "OPEN" in status else 0,
            'category': get_port_category(port)
        }

        if config.get("show_open_only", False) and "OPEN" not in status:
            return

        scan_results.append(result_data)

        message = f"UDP Port {port} is {status}\n"
        if config.get("export_results", False):
            os.makedirs(os.path.dirname(export_file_path), exist_ok=True)
            with file_lock:
                with open(config.get("_current_export_file", export_file_path), "a") as f:
                    f.write(message)

    except Exception as e:
        if not config.get("show_open_only", False):
            error_data = {
                'port': port,
                'protocol': 'UDP',
                'status': 'ERROR',
                'service': str(e),
                'response_time': 0,
                'category': 'error'
            }
            scan_results.append(error_data)
            
            error_msg = f"Error on UDP port {port}: {e}\n"
            if config.get("export_results", False):
                os.makedirs(os.path.dirname(export_file_path), exist_ok=True)
                with file_lock:
                    with open(config.get("_current_export_file", export_file_path), "a") as f:
                        f.write(error_msg)

def update_results_tree(results_tree, scan_results):
    """Update the results tree with scan data and apply color coding"""
    for result in scan_results:
        values = (
            result['port'],
            result['protocol'],
            result['status'],
            result['service'],
            f"{result['response_time']}ms" if result['response_time'] > 0 else "-"
        )
        
        # Insert item with appropriate tag for color coding
        tag = ""
        if result['status'] == 'OPEN':
            tag = "open"
        elif result['status'] == 'CLOSED':
            tag = "closed"
        elif result['status'] == 'ERROR':
            tag = "error"
        else:
            tag = "filtered"
            
        results_tree.insert("", "end", values=values, tags=(tag,))

def check_ports_threaded_with_export(host, ports, results_tree, clear_button, config):
    clear_button.config(state=tk.NORMAL)
    export_file_path = get_export_file_path(config) if config.get("export_results") else None

    protocol = root.protocol_var.get().upper()
    
    # Calculate total expected scans
    total_scans = 0
    if protocol in ("TCP", "TCP/UDP"):
        total_scans += len(ports)
    if protocol in ("UDP", "TCP/UDP"):
        total_scans += len(ports)

    counter = {"count": 0}
    counter_lock = threading.Lock()
    scan_results = []
    results_lock = threading.Lock()

    def on_port_done():
        with counter_lock:
            counter["count"] += 1
            # Update progress bar and status
            progress = (counter["count"] / total_scans) * 100
            root.progress_var.set(progress)
            root.status_label.config(text=f"{counter['count']} of {total_scans} ports scanned")
            
            if counter["count"] == total_scans:
                # Update the results tree when scanning is complete
                results_tree.after(0, lambda: update_results_tree(results_tree, scan_results))
                # Update status label with completion message
                root.status_label.config(text=f"Scan complete - {len(ports)} ports checked")
                # Reset progress bar after completion
                root.after(3000, lambda: (root.progress_var.set(0), root.status_label.config(text="Ready")))

    def run_tcp_scan(p):
        try:
            scan_port_with_export(host, p, results_tree, config, export_file_path, scan_results)
        finally:
            on_port_done()

    def run_udp_scan(p):
        try:
            scan_udp_port(host, p, results_tree, config, export_file_path, scan_results)
        finally:
            on_port_done()

    for port in ports:
        if protocol in ("TCP", "TCP/UDP"):
            threading.Thread(target=run_tcp_scan, args=(port,), daemon=True).start()
        if protocol in ("UDP", "TCP/UDP"):
            threading.Thread(target=run_udp_scan, args=(port,), daemon=True).start()

def on_check_ports_with_export():
    config = load_config()
    host = root.host_entry.get().strip()
    port_input = root.ports_entry.get().strip()

    if not host or not port_input:
        messagebox.showwarning("Input Error", "Please enter both host and port(s).")
        return

    # Clear results tree
    clear_results_tree()
    
    resolved_ip = resolve_hostname_and_print(host, root.results_tree, config)
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
        if not ports:
            messagebox.showwarning("Input Error", "No valid ports found in input.")
            return
            
        root.clear_button.config(state=tk.DISABLED)
        
        # Initialize progress bar and show scanning status
        root.progress_var.set(0)
        root.status_label.config(text=f"Scanning {host} ({resolved_ip}) - {len(ports)} ports...")
        
        threading.Thread(
            target=check_ports_threaded_with_export,
            args=(host, ports, root.results_tree, root.clear_button, config),
            daemon=True
        ).start()
        root.clear_button.config(state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def clear_results_tree():
    """Clear the results tree"""
    for item in root.results_tree.get_children():
        root.results_tree.delete(item)
    root.clear_button.config(state=tk.DISABLED)
    # Reset progress bar and status when clearing
    root.progress_var.set(0)
    root.status_label.config(text="Ready")

def sort_treeview(tree, col, reverse):
    """Sort treeview by column"""
    data = [(tree.set(child, col), child) for child in tree.get_children('')]
    
    # Handle numeric sorting for port and response time columns
    if col in ['Port', 'Response Time']:
        try:
            data.sort(key=lambda x: int(x[0].replace('ms', '').replace('-', '0')), reverse=reverse)
        except ValueError:
            data.sort(reverse=reverse)
    else:
        data.sort(reverse=reverse)
    
    for index, (val, child) in enumerate(data):
        tree.move(child, '', index)
    
    # Update column heading to show sort direction
    for column in ['Port', 'Protocol', 'Status', 'Service', 'Response Time']:
        if column == col:
            tree.heading(column, text=f"{column} {'↓' if reverse else '↑'}")
        else:
            tree.heading(column, text=column)

def toggle_sort(col):
    """Toggle sort direction for a column"""
    # Initialize sort states if not exist
    if not hasattr(root, 'sort_states'):
        root.sort_states = {}
    
    # Toggle the sort state for this column (default to True so first click = False = ascending)
    current_reverse = root.sort_states.get(col, True)
    new_reverse = not current_reverse
    root.sort_states[col] = new_reverse
    
    # Sort with the new direction
    sort_treeview(root.results_tree, col, new_reverse)

def filter_results():
    """Filter results based on search criteria"""
    search_term = root.search_var.get().lower()
    
    visible_items = []
    hidden_items = []
    
    # Categorize items based on search criteria
    for item in root.results_tree.get_children():
        values = root.results_tree.item(item)['values']
        if not values or len(values) < 5:
            continue
            
        port, protocol, status, service, response_time = values
        
        # Text search filter
        show_item = True
        if search_term:
            searchable_text = f"{port} {protocol} {status} {service}".lower()
            if search_term not in searchable_text:
                show_item = False
        
        # Determine original tag based on status
        if status == 'OPEN':
            original_tag = "open"
        elif status == 'CLOSED':
            original_tag = "closed"
        elif status == 'ERROR':
            original_tag = "error"
        else:
            original_tag = "filtered"
        
        if show_item:
            visible_items.append((item, original_tag))
        else:
            hidden_items.append((item, "hidden"))
    
    # Reorder items: visible items first, then hidden items
    for index, (item, tag) in enumerate(visible_items + hidden_items):
        root.results_tree.move(item, '', index)
        root.results_tree.item(item, tags=(tag,))

def set_window_icon(window):
    """Set the window icon, handling PyInstaller bundling"""
    try:
        icon_path = resource_path("psp_icon2.ico")
        if os.path.exists(icon_path):
            window.iconbitmap(icon_path)
        else:
            # Try alternative paths
            alternative_paths = [
                "psp_icon2.ico",
                os.path.join(os.path.dirname(__file__), "psp_icon2.ico"),
                os.path.join(os.getcwd(), "psp_icon2.ico")
            ]
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    window.iconbitmap(alt_path)
                    break
    except Exception as e:
        # If icon loading fails, continue without icon
        print(f"Could not load icon: {e}")

def run_gui():
    global root
    config = load_config()
    root = tk.Tk()
    set_window_icon(root)
    root.title("Port Checker Plus")
    root.configure(bg="#f8f8f8")
    root.geometry("800x700")  # Increased size for better table display

    menubar = Menu(root)
    file_menu = Menu(menubar, tearoff=0)
    file_menu.add_command(label="⏻ Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=file_menu)

    edit_menu = Menu(menubar, tearoff=0)
    edit_menu.add_command(label="🔧 Settings", command=lambda: open_settings_window(root, config))
    menubar.add_cascade(label="Edit", menu=edit_menu)
    root.config(menu=menubar)

    # Input section
    input_frame = tk.Frame(root, bg="#f8f8f8")
    input_frame.pack(padx=12, pady=(15, 10), fill="x")

    # Host input
    host_frame = tk.Frame(input_frame, bg="#f8f8f8")
    host_frame.pack(fill="x", pady=(0, 5))
    tk.Label(host_frame, text="Host:", bg="#f8f8f8", font=("Segoe UI", 10)).pack(side="left")
    root.host_entry = tk.Entry(host_frame, width=40, font=("Segoe UI", 10))
    root.host_entry.pack(side="left", padx=(8, 0), fill="x", expand=True)
    root.host_entry.insert(0, config.get("default_host", ""))

    # Ports and protocol input
    port_protocol_frame = tk.Frame(input_frame, bg="#f8f8f8")
    port_protocol_frame.pack(fill="x", pady=5)

    # Ports
    tk.Label(port_protocol_frame, text="Ports:", bg="#f8f8f8", font=("Segoe UI", 10)).pack(side="left")
    root.ports_entry = tk.Entry(port_protocol_frame, width=30, font=("Segoe UI", 10))
    root.ports_entry.pack(side="left", padx=(8, 20), fill="x", expand=True)
    root.ports_entry.insert(0, config.get("default_ports", ""))

    # Protocol
    tk.Label(port_protocol_frame, text="Protocol:", bg="#f8f8f8", font=("Segoe UI", 10)).pack(side="left")
    root.protocol_var = tk.StringVar(value=config.get("scan_protocol", "TCP"))
    protocol_options = ["TCP", "UDP", "TCP/UDP"]
    root.protocol_menu = ttk.Combobox(port_protocol_frame, textvariable=root.protocol_var, 
                                     values=protocol_options, state="readonly", width=10)
    root.protocol_menu.pack(side="left", padx=(8, 0))

    # Buttons
    button_frame = tk.Frame(input_frame, bg="#f8f8f8")
    button_frame.pack(fill="x", pady=(10, 0))
    check_button = tk.Button(button_frame, text="Check Ports", font=("Segoe UI", 10), 
                            command=on_check_ports_with_export, bg="#3498db", fg="white",
                            activebackground="#2980b9", relief="flat", padx=20, pady=5)
    check_button.pack(side="left", padx=(0, 10))
    root.clear_button = tk.Button(button_frame, text="Clear Results", font=("Segoe UI", 10), 
                                 command=clear_results_tree, state=tk.DISABLED, bg="#95a5a6", 
                                 fg="white", activebackground="#7f8c8d", relief="flat", padx=20, pady=5)
    root.clear_button.pack(side="left", padx=(0, 15))
    
    # Profile indicator label (positioned to the far right)
    root.profile_label = tk.Label(button_frame, text="", font=("Segoe UI", 10, "bold"), 
                                 relief="solid", padx=12, pady=5, borderwidth=1)
    root.profile_label.pack(side="right")

    # Filter section
    filter_frame = tk.LabelFrame(root, text="Search Results", bg="#f8f8f8", font=("Segoe UI", 10, "bold"))
    filter_frame.pack(padx=12, pady=(0, 10), fill="x")

    filter_content = tk.Frame(filter_frame, bg="#f8f8f8")
    filter_content.pack(padx=10, pady=5, fill="x")

    # Search box
    tk.Label(filter_content, text="Search:", bg="#f8f8f8", font=("Segoe UI", 10)).pack(side="left")
    root.search_var = tk.StringVar()
    search_entry = tk.Entry(filter_content, textvariable=root.search_var, font=("Segoe UI", 10), width=30)
    search_entry.pack(side="left", padx=(5, 0))
    search_entry.bind('<KeyRelease>', lambda e: filter_results())

    # Results tree view
    results_frame = tk.Frame(root, bg="#f8f8f8")
    results_frame.pack(padx=12, pady=(0, 10), fill="both", expand=True)

    # Create Treeview with columns
    columns = ('Port', 'Protocol', 'Status', 'Service', 'Response Time')
    root.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)

    # Define column properties
    root.results_tree.column('Port', width=80, anchor='center')
    root.results_tree.column('Protocol', width=80, anchor='center')
    root.results_tree.column('Status', width=120, anchor='center')
    root.results_tree.column('Service', width=150, anchor='w')
    root.results_tree.column('Response Time', width=100, anchor='center')

    # Configure column headings with sorting
    for col in columns:
        root.results_tree.heading(col, text=col, 
                                 command=lambda c=col: toggle_sort(c))

    # Add scrollbars using grid layout
    root.results_tree.grid(row=0, column=0, sticky="nsew")
    
    v_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=root.results_tree.yview)
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    root.results_tree.configure(yscrollcommand=v_scrollbar.set)
    
    h_scrollbar = ttk.Scrollbar(results_frame, orient="horizontal", command=root.results_tree.xview)
    h_scrollbar.grid(row=1, column=0, sticky="ew")
    root.results_tree.configure(xscrollcommand=h_scrollbar.set)

    # Configure grid weights
    results_frame.grid_rowconfigure(0, weight=1)
    results_frame.grid_columnconfigure(0, weight=1)

    # Configure tags for color coding
    root.results_tree.tag_configure("open", foreground="#27ae60", font=("Segoe UI", 10, "bold"))
    root.results_tree.tag_configure("closed", foreground="#7f8c8d")
    root.results_tree.tag_configure("filtered", foreground="#9b59b6")
    root.results_tree.tag_configure("error", foreground="#e74c3c", font=("Segoe UI", 10, "italic"))
    root.results_tree.tag_configure("hidden", foreground="#ffffff")

    # Progress bar and status frame
    progress_frame = tk.Frame(root, bg="#f8f8f8")
    progress_frame.pack(padx=12, pady=(0, 10), fill="x")
    
    # Status label
    root.status_label = tk.Label(progress_frame, text="Ready", bg="#f8f8f8", font=("Segoe UI", 9))
    root.status_label.pack(side="left")
    
    # Progress bar
    root.progress_var = tk.DoubleVar()
    root.progress_bar = ttk.Progressbar(progress_frame, variable=root.progress_var, maximum=100, length=200)
    root.progress_bar.pack(side="right", padx=(10, 0))

    # Initialize the profile indicator
    update_profile_indicator()

    root.mainloop()

if __name__ == "__main__":
    run_gui()