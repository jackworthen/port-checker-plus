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
import webbrowser
import csv
import xml.etree.ElementTree as ET
import random  # Added for port randomization
import ipaddress  # Added for CIDR support
from concurrent.futures import ThreadPoolExecutor, as_completed
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

def get_max_threads_limit():
    """Calculate reasonable max threads based on system resources"""
    try:
        # Get system file descriptor limit
        try:
            import resource
            soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
            # Use 20% of available file descriptors for more aggressive scanning
            fd_based_limit = min(soft_limit // 5, 3000)
            print(f"Debug: File descriptor limit: {soft_limit}, calculated fd_based_limit: {fd_based_limit}")
        except (ImportError, AttributeError):
            # Fallback for systems without resource module (Windows)
            fd_based_limit = 2000
            print(f"Debug: No resource module, using fd_based_limit: {fd_based_limit}")
        
        # CPU-based limit (much more generous for I/O bound tasks)
        try:
            cpu_count = os.cpu_count() or 4  # Fallback to 4 if cpu_count() returns None
            cpu_based_limit = max(cpu_count * 20, 1000)  # Much more generous scaling, minimum 1000
            print(f"Debug: CPU count: {cpu_count}, calculated cpu_based_limit: {cpu_based_limit}")
        except:
            cpu_based_limit = 1000  # Higher fallback
            print(f"Debug: CPU count failed, using cpu_based_limit: {cpu_based_limit}")
        
        # Platform-specific adjustments (much less conservative)
        if platform.system() == "Windows":
            # Windows can handle more with modern versions
            platform_limit = 2000
        else:
            platform_limit = 3000
        print(f"Debug: Platform: {platform.system()}, platform_limit: {platform_limit}")
        
        # Return the most generous limit, but at least 1000, max 5000
        calculated_limit = max(fd_based_limit, cpu_based_limit, platform_limit)  # Use MAX instead of MIN
        final_limit = max(1000, min(calculated_limit, 5000))  # Minimum 1000 threads always
        print(f"Debug: Final calculated limit: {final_limit}")
        return final_limit
    except Exception as e:
        print(f"Warning: Could not calculate optimal thread limit ({e}), using default.")
        return 2000  # Much higher fallback

def get_recommended_threads():
    """Get a recommended thread count for most users"""
    max_limit = get_max_threads_limit()
    # Recommend 25% of max limit, but at least 20 and at most 150
    recommended = max_limit // 4
    return max(20, min(recommended, 150))

def get_safe_max_threads():
    """Get a safe maximum that most systems can handle without issues"""
    return min(get_max_threads_limit(), 1000)  # Increased from 200 to 1000

CONFIG_PATH = str(get_config_path())

# Note: get_recommended_threads() will be called after functions are defined
def get_default_config():
    return {
        "timeout": 0.3,
        "export_results": False,
        "export_directory": os.getcwd(),
        "export_format": "TXT",
        "default_host": "",
        "default_ports": "",
        "retry_count": 2,
        "scan_protocol": "TCP",
        "show_open_only": False,
        "randomize_ports": False,  # Added for port randomization
        "variable_delay_scan": False,  # Added for variable delay scanning
        "max_cidr_hosts": 254,  # Added limit for CIDR scanning
        "max_concurrent_threads": get_recommended_threads()  # Dynamic default based on system
    }

# Get default config dynamically
default_config = None  # Will be set in load_config()

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
    global default_config
    if default_config is None:
        default_config = get_default_config()
        
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                # Ensure new keys exist
                if "export_format" not in config:
                    config["export_format"] = "TXT"
                if "randomize_ports" not in config:
                    config["randomize_ports"] = False
                if "variable_delay_scan" not in config:
                    config["variable_delay_scan"] = False
                if "max_cidr_hosts" not in config:
                    config["max_cidr_hosts"] = 254
                if "max_concurrent_threads" not in config:
                    config["max_concurrent_threads"] = get_recommended_threads()
                return config
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

def is_cidr_notation(host_input):
    """Check if the input is in CIDR notation"""
    try:
        ipaddress.ip_network(host_input, strict=False)
        return True
    except ValueError:
        return False

def parse_cidr_hosts(host_input, config):
    """Parse CIDR notation and return list of host IPs"""
    try:
        network = ipaddress.ip_network(host_input, strict=False)
        hosts = []
        max_hosts = config.get("max_cidr_hosts", 254)
        
        # For networks larger than max_hosts, warn user
        if network.num_addresses > max_hosts + 2:  # +2 for network and broadcast
            response = messagebox.askyesno(
                "Large Network Range", 
                f"The network {host_input} contains {network.num_addresses} addresses.\n"
                f"This will scan {min(network.num_addresses, max_hosts)} hosts.\n"
                f"This may take a significant amount of time.\n\n"
                f"Do you want to continue?",
                icon="warning"
            )
            if not response:
                return None
        
        # Get host addresses (excluding network and broadcast for /31 and smaller)
        host_count = 0
        for ip in network.hosts():
            if host_count >= max_hosts:
                break
            hosts.append(str(ip))
            host_count += 1
        
        # If no hosts() (like /31 or /32), use all addresses
        if not hosts:
            for ip in network:
                if host_count >= max_hosts:
                    break
                hosts.append(str(ip))
                host_count += 1
                
        return hosts
    except ValueError as e:
        messagebox.showerror("CIDR Error", f"Invalid CIDR notation: {e}")
        return None

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

def update_advanced_options_indicator():
    """Update the advanced options indicator label"""
    if hasattr(root, 'advanced_label'):
        config = load_config()
        randomize_enabled = config.get("randomize_ports", False)
        delay_enabled = config.get("variable_delay_scan", False)
        
        if randomize_enabled or delay_enabled:
            root.advanced_label.config(
                text=" Advanced Options Enabled ",
                bg="#e74c3c",  # Red background
                fg="white"
            )
            # Show the label by packing it
            root.advanced_label.pack(side="left", padx=(0, 15))
        else:
            # Hide the label by removing it from pack
            root.advanced_label.pack_forget()

def open_documentation():
    """Open the documentation URL in the default browser"""
    try:
        webbrowser.open("https://github.com/jackworthen/port-checker-plus")
    except Exception as e:
        messagebox.showerror("Error", f"Could not open documentation:\n{e}")

def get_export_file_path(config):
    """Get the export file path with appropriate extension"""
    export_format = config.get("export_format", "TXT").upper()
    extensions = {
        "TXT": "portcheck_log.txt",
        "CSV": "portcheck_log.csv", 
        "JSON": "portcheck_log.json",
        "XML": "portcheck_log.xml"
    }
    filename = extensions.get(export_format, "portcheck_log.txt")
    return os.path.join(config["export_directory"], filename)

def export_results_to_file(scan_data, scan_results, config):
    """Export scan results in the specified format"""
    if not config.get("export_results", False):
        return
        
    export_format = config.get("export_format", "TXT").upper()
    export_file_path = get_export_file_path(config)
    
    try:
        os.makedirs(os.path.dirname(export_file_path), exist_ok=True)
        
        if export_format == "TXT":
            export_to_txt(export_file_path, scan_data, scan_results)
        elif export_format == "CSV":
            export_to_csv(export_file_path, scan_data, scan_results)
        elif export_format == "JSON":
            export_to_json(export_file_path, scan_data, scan_results)
        elif export_format == "XML":
            export_to_xml(export_file_path, scan_data, scan_results)
            
    except Exception as e:
        messagebox.showerror("Export Error", f"Could not export results:\n{e}")

def export_to_txt(file_path, scan_data, scan_results):
    """Export results to TXT format (updated for CIDR support)"""
    with open(file_path, "a") as f:
        f.write("\n" + "=" * 50 + "\n")
        f.write(f"Scan Results: {scan_data['timestamp']}\n")
        f.write(f"Target: {scan_data['host_input']}\n")
        if scan_data.get('is_cidr', False):
            f.write(f"Network Range: {len(scan_data.get('scanned_hosts', []))} hosts\n")
        else:
            f.write(f"Resolved IP: {scan_data.get('resolved_ip', 'N/A')}\n")
        f.write(f"Ports: {scan_data['port_input']}\n")
        f.write(f"Protocol: {scan_data['protocol']}\n")
        f.write("=" * 50 + "\n\n")
        
        # Group results by host
        if scan_data.get('is_cidr', False):
            host_results = {}
            for result in scan_results:
                host = result['host']
                if host not in host_results:
                    host_results[host] = []
                host_results[host].append(result)
            
            for host, results in host_results.items():
                f.write(f"\nHost: {host}\n")
                f.write("-" * 30 + "\n")
                for result in results:
                    status_text = f"{result['protocol']} Port {result['port']} is {result['status']}"
                    if result['service'] and result['service'] != 'Unknown':
                        status_text += f" (Service: {result['service']})"
                    if result['response_time'] > 0:
                        status_text += f" - {result['response_time']}ms"
                    f.write(status_text + "\n")
        else:
            for result in scan_results:
                status_text = f"{result['protocol']} Port {result['port']} is {result['status']}"
                if result['service'] and result['service'] != 'Unknown':
                    status_text += f" (Service: {result['service']})"
                if result['response_time'] > 0:
                    status_text += f" - {result['response_time']}ms"
                f.write(status_text + "\n")

def export_to_csv(file_path, scan_data, scan_results):
    """Export results to CSV format (updated for CIDR support)"""
    file_exists = os.path.exists(file_path)
    
    with open(file_path, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header if file is new
        if not file_exists:
            writer.writerow(["Timestamp", "Target", "Host", "Port", "Protocol", "Status", "Service", "Response Time (ms)"])
        
        # Write scan results
        for result in scan_results:
            writer.writerow([
                scan_data['timestamp'],
                scan_data['host_input'],
                result['host'],
                result['port'],
                result['protocol'],
                result['status'],
                result['service'],
                result['response_time'] if result['response_time'] > 0 else ""
            ])

def export_to_json(file_path, scan_data, scan_results):
    """Export results to JSON format (updated for CIDR support)"""
    # Load existing data if file exists
    scan_history = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding='utf-8') as f:
                scan_history = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            scan_history = []
    
    # Create new scan entry
    scan_entry = {
        "scan_info": scan_data,
        "results": scan_results,
        "summary": {
            "total_ports": len(scan_results),
            "total_hosts": len(set(r['host'] for r in scan_results)) if scan_data.get('is_cidr', False) else 1,
            "open_ports": len([r for r in scan_results if r['status'] == 'OPEN']),
            "closed_ports": len([r for r in scan_results if r['status'] == 'CLOSED']),
            "filtered_ports": len([r for r in scan_results if 'FILTERED' in r['status']]),
            "error_ports": len([r for r in scan_results if r['status'] == 'ERROR'])
        }
    }
    
    scan_history.append(scan_entry)
    
    # Write updated data
    with open(file_path, "w", encoding='utf-8') as f:
        json.dump(scan_history, f, indent=2, ensure_ascii=False)

def export_to_xml(file_path, scan_data, scan_results):
    """Export results to XML format (updated for CIDR support)"""
    # Load existing XML or create new root
    if os.path.exists(file_path):
        try:
            tree = ET.parse(file_path)
            root_elem = tree.getroot()
        except ET.ParseError:
            root_elem = ET.Element("port_scan_history")
    else:
        root_elem = ET.Element("port_scan_history")
    
    # Create scan element
    scan_elem = ET.SubElement(root_elem, "scan")
    scan_elem.set("timestamp", scan_data['timestamp'])
    
    # Add scan info
    info_elem = ET.SubElement(scan_elem, "scan_info")
    ET.SubElement(info_elem, "target").text = scan_data['host_input']
    if scan_data.get('is_cidr', False):
        ET.SubElement(info_elem, "scan_type").text = "CIDR"
        ET.SubElement(info_elem, "hosts_scanned").text = str(len(scan_data.get('scanned_hosts', [])))
    else:
        ET.SubElement(info_elem, "scan_type").text = "Single Host"
        ET.SubElement(info_elem, "resolved_ip").text = scan_data.get('resolved_ip', 'N/A')
    ET.SubElement(info_elem, "ports").text = scan_data['port_input']
    ET.SubElement(info_elem, "protocol").text = scan_data['protocol']
    
    # Add results grouped by host if CIDR
    results_elem = ET.SubElement(scan_elem, "results")
    if scan_data.get('is_cidr', False):
        # Group by host
        host_results = {}
        for result in scan_results:
            host = result['host']
            if host not in host_results:
                host_results[host] = []
            host_results[host].append(result)
        
        for host, results in host_results.items():
            host_elem = ET.SubElement(results_elem, "host")
            host_elem.set("ip", host)
            
            for result in results:
                port_elem = ET.SubElement(host_elem, "port")
                port_elem.set("number", str(result['port']))
                port_elem.set("protocol", result['protocol'])
                port_elem.set("status", result['status'])
                
                if result['service']:
                    port_elem.set("service", result['service'])
                if result['response_time'] > 0:
                    port_elem.set("response_time", f"{result['response_time']}ms")
    else:
        for result in scan_results:
            port_elem = ET.SubElement(results_elem, "port")
            port_elem.set("host", result['host'])
            port_elem.set("number", str(result['port']))
            port_elem.set("protocol", result['protocol'])
            port_elem.set("status", result['status'])
            
            if result['service']:
                port_elem.set("service", result['service'])
            if result['response_time'] > 0:
                port_elem.set("response_time", f"{result['response_time']}ms")
    
    # Add summary
    summary_elem = ET.SubElement(scan_elem, "summary")
    summary_elem.set("total_ports", str(len(scan_results)))
    summary_elem.set("total_hosts", str(len(set(r['host'] for r in scan_results)) if scan_data.get('is_cidr', False) else 1))
    summary_elem.set("open_ports", str(len([r for r in scan_results if r['status'] == 'OPEN'])))
    summary_elem.set("closed_ports", str(len([r for r in scan_results if r['status'] == 'CLOSED'])))
    summary_elem.set("filtered_ports", str(len([r for r in scan_results if 'FILTERED' in r['status']])))
    summary_elem.set("error_ports", str(len([r for r in scan_results if r['status'] == 'ERROR'])))
    
    # Write XML
    tree = ET.ElementTree(root_elem)
    ET.indent(tree, space="  ", level=0)  # Pretty print
    tree.write(file_path, encoding='utf-8', xml_declaration=True)

def open_settings_window(root, config):
    # Reload config to get latest saved settings
    config = load_config()
    
    settings_win = tk.Toplevel(root)
    settings_win.title("Settings - Port Checker Plus")
    settings_win.geometry("520x750")  # Increased height for new options
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
    tk.Label(defaults_section, text="Default Host/Network:", font=("Segoe UI", 10), 
             bg="#ffffff", fg="#2c3e50").pack(anchor="w", pady=(5, 2))
    tk.Label(defaults_section, text="Examples: 192.168.1.1 or 192.168.1.0/24", 
             font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d").pack(anchor="w")
    host_entry = tk.Entry(defaults_section, font=("Segoe UI", 10), width=50)
    host_entry.insert(0, config.get("default_host", ""))
    host_entry.pack(fill="x", pady=(5, 15))

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

    # Max concurrent threads with dynamic limit
    threads_frame = tk.Frame(scan_section, bg="#ffffff")
    threads_frame.pack(fill="x", pady=(0, 2))
    tk.Label(threads_frame, text="Max Concurrent Threads:", font=("Segoe UI", 10), 
             bg="#ffffff", fg="#2c3e50").pack(side="left")
    
    # Get system-specific max threads limit - allow high performance values
    max_system_threads = get_max_threads_limit()
    safe_max_threads = get_safe_max_threads()
    
    # Always allow at least 2000 threads regardless of system calculation
    spinbox_max = max(max_system_threads, 2000)
    
    threads_spin = tk.Spinbox(threads_frame, from_=1, to=spinbox_max, width=8, font=("Segoe UI", 10))
    threads_spin.delete(0, tk.END)
    threads_spin.insert(0, str(config.get("max_concurrent_threads", get_recommended_threads())))
    threads_spin.pack(side="right")

    # Add comprehensive info label for thread limits (moved closer to the spinbox)
    threads_info_frame = tk.Frame(scan_section, bg="#ffffff")
    threads_info_frame.pack(fill="x", pady=(0, 5))
    
    # Multi-line guidance with color coding
    recommended_text = f"Recommended: {get_recommended_threads()} | Safe Max: {safe_max_threads} | Manual Max: {spinbox_max}"
    threads_info = tk.Label(threads_info_frame, 
                           text=recommended_text,
                           font=("Segoe UI", 8), bg="#ffffff", fg="#7f8c8d")
    threads_info.pack(anchor="w")
    
    # Warning for high thread counts
    threads_warning_frame = tk.Frame(scan_section, bg="#ffffff")
    threads_warning_frame.pack(fill="x", pady=(0, 12))
    threads_warning = tk.Label(threads_warning_frame, 
                              text=f"⚠️ Values >1000 may consume significant system resources.",
                              font=("Segoe UI", 8, "italic"), bg="#ffffff", fg="#e67e22", wraplength=450)
    threads_warning.pack(anchor="w")

    # Max CIDR hosts
    cidr_frame = tk.Frame(scan_section, bg="#ffffff")
    cidr_frame.pack(fill="x", pady=(0, 0))
    tk.Label(cidr_frame, text="Max Hosts per CIDR Scan:", font=("Segoe UI", 10), 
             bg="#ffffff", fg="#2c3e50").pack(side="left")
    cidr_spin = tk.Spinbox(cidr_frame, from_=10, to=1024, width=8, font=("Segoe UI", 10))
    cidr_spin.delete(0, tk.END)
    cidr_spin.insert(0, str(config.get("max_cidr_hosts", 254)))
    cidr_spin.pack(side="right")

    # CIDR description
    cidr_desc = tk.Label(scan_section, 
                        text="Limit scanned hosts when using CIDR notation to prevent excessive scanning.", 
                        font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d", 
                        wraplength=450, justify="left")
    cidr_desc.pack(anchor="w", pady=(5, 0))

    # Display Options Section
    display_section = tk.LabelFrame(general_frame, text="Display Options", 
                                   font=("Segoe UI", 10, "bold"), bg="#ffffff", 
                                   fg="#34495e", padx=15, pady=10)
    display_section.pack(fill="x", padx=15, pady=10)

    show_open_only_var = tk.BooleanVar(value=config.get("show_open_only", False))
    show_open_check = tk.Checkbutton(display_section, 
                                    text="Only Show OPEN Ports", 
                                    variable=show_open_only_var,
                                    bg="#ffffff", font=("Segoe UI", 10), 
                                    fg="#2c3e50", activebackground="#ffffff")
    show_open_check.pack(anchor="w", pady=5)

    # ===== ADVANCED TAB =====
    advanced_frame = tk.Frame(notebook, bg="#ffffff")
    notebook.add(advanced_frame, text="Advanced")

    # Stealth Options Section
    stealth_section = tk.LabelFrame(advanced_frame, text="Stealth Options", 
                                   font=("Segoe UI", 10, "bold"), bg="#ffffff", 
                                   fg="#34495e", padx=15, pady=10)
    stealth_section.pack(fill="x", padx=15, pady=(15, 10))

    # Port randomization option
    randomize_ports_var = tk.BooleanVar(value=config.get("randomize_ports", False))
    randomize_check = tk.Checkbutton(stealth_section, 
                                    text="Randomize Ports", 
                                    variable=randomize_ports_var,
                                    bg="#ffffff", font=("Segoe UI", 10), 
                                    fg="#2c3e50", activebackground="#ffffff")
    randomize_check.pack(anchor="w", pady=(5, 0))

    # Description for randomization
    randomize_desc = tk.Label(stealth_section, 
                             text="Randomizes the order in which ports are scanned.", 
                             font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d", 
                             wraplength=450, justify="left")
    randomize_desc.pack(anchor="w", pady=(2, 15))

    # Variable delay scan option
    variable_delay_var = tk.BooleanVar(value=config.get("variable_delay_scan", False))
    variable_delay_check = tk.Checkbutton(stealth_section, 
                                         text="Variable Delay Scan", 
                                         variable=variable_delay_var,
                                         bg="#ffffff", font=("Segoe UI", 10), 
                                         fg="#2c3e50", activebackground="#ffffff")
    variable_delay_check.pack(anchor="w", pady=(5, 0))

    # Description for variable delay
    delay_desc = tk.Label(stealth_section, 
                         text="Adds random delays (300-700ms) between port scans to avoid rate limiting.", 
                         font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d", 
                         wraplength=450, justify="left")
    delay_desc.pack(anchor="w", pady=(2, 15))

    # Warning note
    warning_label = tk.Label(stealth_section, 
                            text="⚠️ Use advanced features responsibly and only on networks you own or have permission to test.", 
                            font=("Segoe UI", 9, "italic"), bg="#ffffff", fg="#e67e22", 
                            wraplength=450, justify="left")
    warning_label.pack(anchor="w", pady=(5, 0))

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
                                 text="Enable Logging", 
                                 variable=export_var,
                                 bg="#ffffff", font=("Segoe UI", 10), 
                                 fg="#2c3e50", activebackground="#ffffff")
    export_check.pack(anchor="w", pady=(5, 15))

    # Export format selection
    format_frame = tk.Frame(export_section, bg="#ffffff")
    format_frame.pack(fill="x", pady=(0, 15))
    
    tk.Label(format_frame, text="Export Format:", font=("Segoe UI", 10), 
             bg="#ffffff", fg="#2c3e50").pack(side="left")
    format_var = tk.StringVar(value=config.get("export_format", "TXT"))
    format_options = ["TXT", "CSV", "JSON", "XML"]
    format_combo = ttk.Combobox(format_frame, textvariable=format_var, 
                               values=format_options, state="readonly", width=10,
                               font=("Segoe UI", 10))
    format_combo.pack(side="right")

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

    # Export file info
    def update_info_label():
        selected_format = format_var.get().lower()
        filename = f"portcheck_log.{selected_format}"
        info_label.config(text=f"Log will be saved to '{filename}' in the selected directory")

    info_label = tk.Label(export_section, 
                         text="",
                         font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d")
    info_label.pack(anchor="w", pady=(5, 0))
    
    # Bind format change to update info label
    format_combo.bind("<<ComboboxSelected>>", lambda e: update_info_label())
    update_info_label()  # Set initial text

    # ===== CLEAR LOGS SECTION =====
    clear_logs_section = tk.LabelFrame(export_frame, text="Log Management", 
                                      font=("Segoe UI", 10, "bold"), bg="#ffffff", 
                                      fg="#34495e", padx=15, pady=10)
    # Don't pack initially - will be controlled by toggle_export_inputs
    
    clear_logs_frame = tk.Frame(clear_logs_section, bg="#ffffff")
    clear_logs_frame.pack(fill="x", pady=5)
    
    def clear_logs():
        """Delete all existing log files from directory."""
        export_dir = dir_entry.get().strip()
        if not export_dir or not os.path.exists(export_dir):
            messagebox.showwarning("Clear Logs", "Please select a valid export directory first.")
            return
        
        # Define all possible log files
        log_files = [
            "portcheck_log.txt",
            "portcheck_log.csv", 
            "portcheck_log.json",
            "portcheck_log.xml"
        ]
        
        # Find existing log files
        existing_files = []
        for filename in log_files:
            file_path = os.path.join(export_dir, filename)
            if os.path.exists(file_path):
                existing_files.append((filename, file_path))
        
        if not existing_files:
            messagebox.showinfo("Clear Logs", "No log files found in the specified directory.")
            return
        
        # Confirm deletion
        file_list = "\n".join([f"• {filename}" for filename, _ in existing_files])
        confirm_message = f"Are you sure you want to delete the following log files?\n\n{file_list}\n\nThis action cannot be undone."
        
        if not messagebox.askyesno("Confirm Delete", confirm_message, icon="warning"):
            return
        
        # Delete files
        deleted_files = []
        failed_files = []
        
        for filename, file_path in existing_files:
            try:
                os.remove(file_path)
                deleted_files.append(filename)
            except Exception as e:
                failed_files.append((filename, str(e)))
        
        # Show results
        if deleted_files and not failed_files:
            messagebox.showinfo("Clear Logs", 
                              f"Successfully deleted {len(deleted_files)} log file(s):\n" + 
                              "\n".join([f"• {f}" for f in deleted_files]))
        elif deleted_files and failed_files:
            success_msg = "Deleted:\n" + "\n".join([f"• {f}" for f in deleted_files])
            error_msg = "Failed to delete:\n" + "\n".join([f"• {f}: {e}" for f, e in failed_files])
            messagebox.showwarning("Clear Logs - Partial Success", 
                                 f"{success_msg}\n\n{error_msg}")
        else:
            error_msg = "Failed to delete:\n" + "\n".join([f"• {f}: {e}" for f, e in failed_files])
            messagebox.showerror("Clear Logs - Error", f"Could not delete any files:\n\n{error_msg}")
    
    clear_logs_btn = tk.Button(clear_logs_frame, text="Clear Logs", font=("Segoe UI", 10),
                              command=clear_logs, bg="#e74c3c", fg="white", 
                              activebackground="#c0392b", relief="flat", padx=20, pady=6)
    clear_logs_btn.pack(side="left")
    
    clear_logs_info = tk.Label(clear_logs_frame, 
                              text="Delete all existing log files from directory.",
                              font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d")
    clear_logs_info.pack(side="left", padx=(15, 0))

    def toggle_export_inputs():
        state = tk.NORMAL if export_var.get() else tk.DISABLED
        dir_entry.config(state=state)
        browse_btn.config(state=state)
        format_combo.config(state="readonly" if export_var.get() else tk.DISABLED)
        clear_logs_btn.config(state=state)
        dir_label.config(fg="#2c3e50" if export_var.get() else "#bdc3c7")
        clear_logs_info.config(fg="#7f8c8d" if export_var.get() else "#bdc3c7")
        info_label.config(fg="#7f8c8d" if export_var.get() else "#bdc3c7")
        
        # Toggle the entire clear logs section visibility
        if export_var.get():
            clear_logs_section.pack(fill="x", padx=15, pady=10)
        else:
            clear_logs_section.pack_forget()

    export_check.config(command=toggle_export_inputs)
    toggle_export_inputs()

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

            # Validate max CIDR hosts
            max_cidr_hosts = int(cidr_spin.get())
            if max_cidr_hosts < 1:
                messagebox.showerror("Invalid Input", "Max CIDR hosts must be at least 1.")
                return

            # Validate max concurrent threads with dynamic limit and warnings
            max_threads = int(threads_spin.get())
            max_system_threads = get_max_threads_limit()
            spinbox_max = max(max_system_threads, 2000)  # Manual override limit
            
            if max_threads < 1 or max_threads > spinbox_max:
                messagebox.showerror("Invalid Input", 
                                   f"Max concurrent threads must be between 1 and {spinbox_max}.\n\n"
                                   f"System calculated limit: {max_system_threads}\n"
                                   f"Manual override limit: {spinbox_max}")
                return
            
            # Warn for very high thread counts but allow them (now 1000+ instead of 200+)
            if max_threads > 1000:
                warning_message = (
                    f"You've set {max_threads} threads, which is above the recommended limit of 1000.\n\n"
                    f"Very high thread counts can:\n"
                    f"• Consume significant system memory (1-8MB per thread)\n"
                    f"• Trigger rate limiting on target networks\n"
                    f"• Overwhelm target systems\n"
                    f"• Be detected as aggressive scanning\n\n"
                    f"This setting is intended for:\n"
                    f"• Internal network scanning\n"
                    f"• High-performance systems\n"
                    f"• Controlled environments\n"
                    f"• Advanced users with specific requirements\n\n"
                    f"Continue with {max_threads} threads?"
                )
                
                if not messagebox.askyesno("Very High Thread Count Warning", warning_message, icon="warning"):
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
            config["export_format"] = format_var.get()
            config["show_open_only"] = show_open_only_var.get()
            config["default_host"] = host_entry.get().strip()
            config["retry_count"] = int(retry_spin.get())
            config["default_ports"] = port_input
            config["scan_protocol"] = protocol_var.get()
            config["randomize_ports"] = randomize_ports_var.get()
            config["variable_delay_scan"] = variable_delay_var.get()
            config["max_cidr_hosts"] = max_cidr_hosts
            config["max_concurrent_threads"] = max_threads
            
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
                
                # Update the advanced options indicator
                update_advanced_options_indicator()

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
stop_scan_event = threading.Event()

def get_port_category(port):
    """All ports use the same category now - simplified"""
    return "normal"

def scan_port_with_export(host, port, results_tree, config, scan_results):
    try:
        # Check if scan should be stopped before starting
        if stop_scan_event.is_set():
            return False  # Return False to indicate scan was stopped before execution
            
        # Add variable delay if enabled (but check stop event during delay)
        if config.get("variable_delay_scan", False):
            base_delay = 0.2  # Base delay of 200ms
            jitter = random.uniform(0.1, 0.5)  # Random jitter between 100-500ms
            delay_time = base_delay + jitter
            
            # Break delay into smaller chunks to be more responsive to stop
            chunks = 10
            chunk_delay = delay_time / chunks
            for _ in range(chunks):
                if stop_scan_event.is_set():
                    return False
                time.sleep(chunk_delay)
        
        # Final check before actual scan
        if stop_scan_event.is_set():
            return False
            
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

        # Check if scan was stopped during execution
        if stop_scan_event.is_set():
            return False

        # Create result data
        result_data = {
            'host': host,  # Include host in result data
            'port': port,
            'protocol': 'TCP',
            'status': status,
            'service': service,
            'response_time': response_time if status == "OPEN" else 0,
            'category': get_port_category(port)
        }

        if config.get("show_open_only", False) and status != "OPEN":
            return True  # Return True to indicate scan completed successfully

        # Store result for later insertion into tree and export
        with file_lock:
            scan_results.append(result_data)
        
        return True  # Return True to indicate scan completed successfully

    except Exception as e:
        # Don't add error data if scan was stopped
        if stop_scan_event.is_set():
            return False
            
        error_data = {
            'host': host,
            'port': port,
            'protocol': 'TCP',
            'status': 'ERROR',
            'service': str(e),
            'response_time': 0,
            'category': 'error'
        }
        with file_lock:
            scan_results.append(error_data)
        
        return True  # Return True even for errors, as the scan was attempted

def scan_udp_port(host, port, results_tree, config, scan_results):
    try:
        # Check if scan should be stopped before starting
        if stop_scan_event.is_set():
            return False
            
        # Add variable delay if enabled (but check stop event during delay)
        if config.get("variable_delay_scan", False):
            base_delay = 0.2  # Base delay of 200ms
            jitter = random.uniform(0.1, 0.5)  # Random jitter between 100-500ms
            delay_time = base_delay + jitter
            
            # Break delay into smaller chunks to be more responsive to stop
            chunks = 10
            chunk_delay = delay_time / chunks
            for _ in range(chunks):
                if stop_scan_event.is_set():
                    return False
                time.sleep(chunk_delay)
        
        # Final check before actual scan
        if stop_scan_event.is_set():
            return False
            
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
        
        # Check if scan was stopped during execution
        if stop_scan_event.is_set():
            return False
        
        result_data = {
            'host': host,  # Include host in result data
            'port': port,
            'protocol': 'UDP',
            'status': status,
            'service': 'Unknown',
            'response_time': response_time if "OPEN" in status else 0,
            'category': get_port_category(port)
        }

        if config.get("show_open_only", False) and "OPEN" not in status:
            return True

        with file_lock:
            scan_results.append(result_data)
        
        return True

    except Exception as e:
        # Don't add error data if scan was stopped
        if stop_scan_event.is_set():
            return False
            
        if not config.get("show_open_only", False):
            error_data = {
                'host': host,
                'port': port,
                'protocol': 'UDP',
                'status': 'ERROR',
                'service': str(e),
                'response_time': 0,
                'category': 'error'
            }
            with file_lock:
                scan_results.append(error_data)
        
        return True

def update_results_tree(results_tree, scan_results):
    """Update the results tree with scan data and apply color coding"""
    for result in scan_results:
        values = (
            result['host'],
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

def check_ports_threaded_with_export(hosts, ports, results_tree, clear_button, config, scan_data):
    clear_button.config(state=tk.NORMAL)

    # Reload config to get the latest settings (in case user just changed them)
    current_config = load_config()
    
    protocol = root.protocol_var.get().upper()
    
    # Randomize port order if enabled
    if current_config.get("randomize_ports", False):
        ports = ports.copy()  # Create a copy to avoid modifying the original list
        random.shuffle(ports)
    
    # Calculate total expected scans
    total_scans = 0
    if protocol in ("TCP", "TCP/UDP"):
        total_scans += len(hosts) * len(ports)
    if protocol in ("UDP", "TCP/UDP"):
        total_scans += len(hosts) * len(ports)

    counter = {"count": 0, "completed": 0}
    counter_lock = threading.Lock()
    scan_results = []

    def on_port_done():
        with counter_lock:
            counter["count"] += 1
            # Update progress bar and status
            progress = (counter["count"] / total_scans) * 100
            root.progress_var.set(progress)
            
            if stop_scan_event.is_set():
                root.status_label.config(text=f"Scan stopped - {counter['count']} of {total_scans} scans completed")
            else:
                root.status_label.config(text=f"{counter['count']} of {total_scans} scans completed")
            
            if counter["count"] == total_scans or stop_scan_event.is_set():
                counter["completed"] = 1
                # Update the results tree when scanning is complete
                results_tree.after(0, lambda: update_results_tree(results_tree, scan_results))
                
                # Export results after scanning is complete (only if not stopped)
                if current_config.get("export_results", False) and not stop_scan_event.is_set():
                    try:
                        export_results_to_file(scan_data, scan_results, current_config)
                    except Exception as e:
                        messagebox.showerror("Export Error", f"Could not export results:\n{e}")
                
                # Update status label and button state on main thread
                def update_completion_ui():
                    host_count = len(hosts)
                    port_count = len(ports)
                    if stop_scan_event.is_set():
                        root.status_label.config(text=f"Scan stopped - {len(scan_results)} results collected")
                        # Update stop button to show "Stopped" briefly before hiding
                        root.stop_button.config(text="Stopped")
                        # Hide stop button after 2 seconds and reset its state
                        root.after(2000, lambda: (
                            root.stop_button.pack_forget(),
                            root.stop_button.config(state=tk.NORMAL, text="Stop Scan")
                        ))
                    else:
                        root.status_label.config(text=f"Scan complete - {host_count} host(s), {port_count} port(s) checked")
                        # For completed scans, hide stop button immediately
                        root.stop_button.pack_forget()
                        root.stop_button.config(state=tk.NORMAL, text="Stop Scan")
                    
                    # Always re-enable check button
                    root.check_button.config(state=tk.NORMAL)
                
                # Schedule UI update on main thread
                root.after(0, update_completion_ui)
                
                # Reset progress bar after completion
                root.after(3000, lambda: (root.progress_var.set(0), root.status_label.config(text="Ready")))

    def run_tcp_scan(h, p):
        if stop_scan_event.is_set():
            return False
        scan_completed = scan_port_with_export(h, p, results_tree, current_config, scan_results)
        if scan_completed:
            on_port_done()
        return scan_completed

    def run_udp_scan(h, p):
        if stop_scan_event.is_set():
            return False
        scan_completed = scan_udp_port(h, p, results_tree, current_config, scan_results)
        if scan_completed:
            on_port_done()
        return scan_completed

    # Create list of all scan tasks
    scan_tasks = []
    for host in hosts:
        for port in ports:
            if protocol in ("TCP", "TCP/UDP"):
                scan_tasks.append(('tcp', host, port))
            if protocol in ("UDP", "TCP/UDP"):
                scan_tasks.append(('udp', host, port))

    # Use ThreadPoolExecutor with limited workers for better control
    # Active threads: min(config_value, total_tasks) - only this many threads run concurrently
    # Queued tasks: Only 20 tasks queued at a time (batch processing)
    max_workers = min(current_config.get("max_concurrent_threads", get_recommended_threads()), len(scan_tasks))
    
    def trigger_stop_completion():
        """Helper function to trigger completion UI when scan is stopped"""
        def force_completion_ui():
            root.status_label.config(text=f"Scan stopped - {len(scan_results)} results collected")
            root.stop_button.config(text="Stopped")
            root.after(1000, lambda: (
                root.stop_button.pack_forget(),
                root.stop_button.config(state=tk.NORMAL, text="Stop Scan")
            ))
            root.check_button.config(state=tk.NORMAL)
            results_tree.after(0, lambda: update_results_tree(results_tree, scan_results))
        
        root.after(0, force_completion_ui)

    def run_scan_batch():
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks in optimized batches for better stop responsiveness
            # Scale batch size with thread count for high-performance scanning
            if max_workers <= 50:
                batch_size = max(20, max_workers * 2)  # Conservative for lower thread counts
            elif max_workers <= 200:
                batch_size = max_workers + 50  # Moderate scaling
            else:
                batch_size = max_workers + 100  # Aggressive batching for high thread counts
            
            task_index = 0
            future_to_task = {}
            
            while task_index < len(scan_tasks) and not stop_scan_event.is_set():
                # Submit a batch of tasks
                batch_end = min(task_index + batch_size, len(scan_tasks))
                
                for i in range(task_index, batch_end):
                    if stop_scan_event.is_set():
                        trigger_stop_completion()
                        return
                    
                    task_type, host, port = scan_tasks[i]
                    if task_type == 'tcp':
                        future = executor.submit(run_tcp_scan, host, port)
                    else:
                        future = executor.submit(run_udp_scan, host, port)
                    future_to_task[future] = (task_type, host, port)
                
                task_index = batch_end
                
                # Process completed tasks from this batch
                completed_in_batch = 0
                for future in as_completed(future_to_task.copy()):
                    if stop_scan_event.is_set():
                        # Cancel all remaining futures
                        for f in future_to_task:
                            if not f.done():
                                f.cancel()
                        trigger_stop_completion()
                        return
                    
                    try:
                        result = future.result()
                        completed_in_batch += 1
                        future_to_task.pop(future, None)  # Remove completed task
                    except Exception as e:
                        print(f"Scan task failed: {e}")
                        completed_in_batch += 1
                        future_to_task.pop(future, None)
                
                # Small delay between batches to allow stop checking
                if not stop_scan_event.is_set():
                    time.sleep(0.1)
            
            # Check if we exited due to stop event
            if stop_scan_event.is_set():
                trigger_stop_completion()
                return
            
            # Wait for any remaining tasks to complete
            if future_to_task and not stop_scan_event.is_set():
                for future in as_completed(future_to_task):
                    if stop_scan_event.is_set():
                        for f in future_to_task:
                            if not f.done():
                                f.cancel()
                        trigger_stop_completion()
                        break
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Scan task failed: {e}")

    # Run the batch in a separate thread
    threading.Thread(target=run_scan_batch, daemon=True).start()

def on_check_ports_with_export():
    config = load_config()
    host_input = root.host_entry.get().strip()
    port_input = root.ports_entry.get().strip()

    if not host_input or not port_input:
        messagebox.showwarning("Input Error", "Please enter both host/network and port(s).")
        return

    # Clear results tree
    clear_results_tree()
    
    # Reset stop event for new scan
    stop_scan_event.clear()
    
    # Check if input is CIDR notation
    if is_cidr_notation(host_input):
        # Handle CIDR scanning
        hosts = parse_cidr_hosts(host_input, config)
        if hosts is None:
            return  # User cancelled or error occurred
        
        if not hosts:
            messagebox.showwarning("CIDR Error", "No valid hosts found in CIDR range.")
            return
        
        # For CIDR, we don't resolve individual IPs since they're already IPs
        is_cidr = True
        resolved_ip = None
    else:
        # Handle single host scanning
        resolved_ip = resolve_hostname_and_print(host_input, root.results_tree, config)
        if not resolved_ip:
            return
        hosts = [resolved_ip]
        is_cidr = False

    try:
        ports = parse_ports(port_input)
        if not ports:
            messagebox.showwarning("Input Error", "No valid ports found in input.")
            return
            
        root.clear_button.config(state=tk.DISABLED)
        
        # Disable check button and show stop button
        root.check_button.config(state=tk.DISABLED)
        root.stop_button.config(state=tk.NORMAL, text="Stop Scan")  # Ensure stop button is ready
        root.stop_button.pack(side="left", padx=(0, 10), after=root.check_button)
        
        # Initialize progress bar and show scanning status
        root.progress_var.set(0)
        if is_cidr:
            scan_status = f"Scanning {host_input} ({len(hosts)} hosts) - {len(ports)} ports"
        else:
            scan_status = f"Scanning {host_input} ({resolved_ip}) - {len(ports)} ports"
        
        # Add thread count to status for user feedback
        max_threads = config.get("max_concurrent_threads", get_recommended_threads())
        scan_status += f" ({max_threads} threads)"
            
        if config.get("randomize_ports", False):
            scan_status += " (randomized)"
        if config.get("variable_delay_scan", False):
            scan_status += " (delayed)"
        root.status_label.config(text=scan_status)
        
        # Prepare scan data for export
        scan_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'host_input': host_input,
            'resolved_ip': resolved_ip,
            'port_input': port_input,
            'protocol': root.protocol_var.get(),
            'is_cidr': is_cidr,
            'scanned_hosts': hosts if is_cidr else [resolved_ip]
        }
        
        threading.Thread(
            target=check_ports_threaded_with_export,
            args=(hosts, ports, root.results_tree, root.clear_button, config, scan_data),
            daemon=True
        ).start()
        root.clear_button.config(state=tk.NORMAL)
    except Exception as e:
        # Reset UI state on error
        root.check_button.config(state=tk.NORMAL)
        root.stop_button.pack_forget()
        messagebox.showerror("Error", str(e))

def on_stop_scan():
    """Stop the current scan"""
    stop_scan_event.set()
    
    # Immediately update UI to show stopping
    root.status_label.config(text="Stopping scan...")
    root.stop_button.config(state=tk.DISABLED, text="Stopping...")
    
    # Re-enable check button immediately so user can start new scan
    root.check_button.config(state=tk.NORMAL)
    
    # Force completion UI update after a short delay
    def force_completion():
        if stop_scan_event.is_set():  # Only if still in stopped state
            root.status_label.config(text="Scan stopped")
            root.stop_button.config(text="Stopped")
            # Hide stop button after 1 second and reset its state
            root.after(1000, lambda: (
                root.stop_button.pack_forget(),
                root.stop_button.config(state=tk.NORMAL, text="Stop Scan")
            ))
    
    root.after(500, force_completion)

def clear_results_tree():
    """Clear the results tree"""
    for item in root.results_tree.get_children():
        root.results_tree.delete(item)
    root.clear_button.config(state=tk.DISABLED)
    # Reset progress bar and status when clearing
    root.progress_var.set(0)
    root.status_label.config(text="Ready")
    # Reset UI state
    root.check_button.config(state=tk.NORMAL)
    root.stop_button.pack_forget()
    root.stop_button.config(state=tk.NORMAL, text="Stop Scan")  # Reset stop button state
    stop_scan_event.clear()

def sort_treeview(tree, col, reverse):
    """Sort treeview by column"""
    data = [(tree.set(child, col), child) for child in tree.get_children('')]
    
    # Handle numeric sorting for port and response time columns
    if col in ['Port', 'Response Time']:
        try:
            data.sort(key=lambda x: int(x[0].replace('ms', '').replace('-', '0')), reverse=reverse)
        except ValueError:
            data.sort(reverse=reverse)
    elif col == 'Host':
        # Sort IP addresses properly
        try:
            data.sort(key=lambda x: ipaddress.ip_address(x[0]), reverse=reverse)
        except ValueError:
            data.sort(reverse=reverse)
    else:
        data.sort(reverse=reverse)
    
    for index, (val, child) in enumerate(data):
        tree.move(child, '', index)
    
    # Update column heading to show sort direction
    for column in ['Host', 'Port', 'Protocol', 'Status', 'Service', 'Response Time']:
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
        if not values or len(values) < 6:
            continue
            
        host, port, protocol, status, service, response_time = values
        
        # Text search filter
        show_item = True
        if search_term:
            searchable_text = f"{host} {port} {protocol} {status} {service}".lower()
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
    root.geometry("1100x640")  # Increased width for additional column

    menubar = Menu(root)
    file_menu = Menu(menubar, tearoff=0)
    file_menu.add_command(label="⏻ Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=file_menu)

    edit_menu = Menu(menubar, tearoff=0)
    edit_menu.add_command(label="🔧 Settings", command=lambda: open_settings_window(root, config))
    menubar.add_cascade(label="Edit", menu=edit_menu)

    help_menu = Menu(menubar, tearoff=0)
    help_menu.add_command(label="📖 Documentation", command=open_documentation)
    menubar.add_cascade(label="Help", menu=help_menu)

    root.config(menu=menubar)

    # Input section
    input_frame = tk.Frame(root, bg="#f8f8f8")
    input_frame.pack(padx=12, pady=(15, 10), fill="x")

    # Host input
    host_frame = tk.Frame(input_frame, bg="#f8f8f8")
    host_frame.pack(fill="x", pady=(0, 5))
    tk.Label(host_frame, text="Host/Network:", bg="#f8f8f8", font=("Segoe UI", 10)).pack(side="left")
    root.host_entry = tk.Entry(host_frame, width=40, font=("Segoe UI", 10))
    root.host_entry.pack(side="left", padx=(8, 0), fill="x", expand=True)
    root.host_entry.insert(0, config.get("default_host", ""))
    
    # Add example label for CIDR
    cidr_example = tk.Label(host_frame, text="(e.g., 192.168.1.1 or 192.168.1.0/24)", 
                           bg="#f8f8f8", font=("Segoe UI", 8), fg="#7f8c8d")
    cidr_example.pack(side="right", padx=(10, 0))

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
    root.check_button = tk.Button(button_frame, text="Check Ports", font=("Segoe UI", 10), 
                            command=on_check_ports_with_export, bg="#3498db", fg="white",
                            activebackground="#2980b9", relief="flat", padx=20, pady=5)
    root.check_button.pack(side="left", padx=(0, 10))
    
    # Stop button (initially hidden)
    root.stop_button = tk.Button(button_frame, text="Stop Scan", font=("Segoe UI", 10), 
                                command=on_stop_scan, bg="#e74c3c", fg="white",
                                activebackground="#c0392b", relief="flat", padx=20, pady=5)
    # Don't pack initially - will be shown when scanning starts
    
    root.clear_button = tk.Button(button_frame, text="Clear Results", font=("Segoe UI", 10), 
                                 command=clear_results_tree, state=tk.DISABLED, bg="#95a5a6", 
                                 fg="white", activebackground="#7f8c8d", relief="flat", padx=20, pady=5)
    root.clear_button.pack(side="left", padx=(0, 15))
    
    # Advanced options indicator label
    root.advanced_label = tk.Label(button_frame, text="", font=("Segoe UI", 9, "bold"), 
                                  relief="solid", padx=10, pady=3, borderwidth=1)
    # Don't pack initially - will be shown/hidden by update_advanced_options_indicator()
    
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

    # Create Treeview with columns (added Host column)
    columns = ('Host', 'Port', 'Protocol', 'Status', 'Service', 'Response Time')
    root.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)

    # Define column properties
    root.results_tree.column('Host', width=120, anchor='center')
    root.results_tree.column('Port', width=80, anchor='center')
    root.results_tree.column('Protocol', width=80, anchor='center')
    root.results_tree.column('Status', width=120, anchor='center')
    root.results_tree.column('Service', width=150, anchor='center')
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

    # Initialize the profile indicator and advanced options indicator
    update_profile_indicator()
    update_advanced_options_indicator()

    root.mainloop()

if __name__ == "__main__":
    run_gui()