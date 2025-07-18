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
import struct
import re  # Added for banner parsing
import subprocess  # Added for ping functionality

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
        "manual_export_format": "CSV",  # Added for manual export
        "manual_export_directory": os.getcwd(),  # Added for manual export
        "default_host": "",
        "default_ports": "",
        "retry_count": 2,
        "scan_protocol": "TCP",
        "show_open_only": False,
        "randomize_ports": False,  # Added for port randomization
        "variable_delay_scan": False,  # Added for variable delay scanning
        "max_cidr_hosts": 254,  # Added limit for CIDR scanning
        "max_concurrent_threads": get_recommended_threads(),  # Dynamic default based on system
        "fragmented_packets": False,  # Added for fragmented packet scanning
        "banner_grabbing": False  # Added for service banner grabbing
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

# Service Banner Grabbing Implementation
class ServiceBannerGrabber:
    """
    Implements service banner grabbing for various protocols
    """
    
    def __init__(self):
        # Common service probes for different ports
        self.service_probes = {
            21: b"",  # FTP - just connect
            22: b"",  # SSH - just connect
            23: b"",  # Telnet - just connect
            25: b"EHLO test\r\n",  # SMTP
            53: b"",  # DNS - UDP typically
            80: b"GET / HTTP/1.1\r\nHost: test\r\nUser-Agent: PortChecker\r\nConnection: close\r\n\r\n",  # HTTP
            110: b"",  # POP3 - just connect
            143: b"",  # IMAP - just connect
            443: b"GET / HTTP/1.1\r\nHost: test\r\nUser-Agent: PortChecker\r\nConnection: close\r\n\r\n",  # HTTPS
            993: b"",  # IMAPS - just connect
            995: b"",  # POP3S - just connect
            3306: b"",  # MySQL - just connect
            5432: b"",  # PostgreSQL - just connect
            6379: b"",  # Redis - just connect
        }
    
    def grab_banner(self, host, port, timeout=2.0):
        """
        Attempt to grab service banner from a specific host:port
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((host, port))
                
                # Send probe if we have one for this port
                probe = self.service_probes.get(port, b"")
                if probe:
                    sock.send(probe)
                    time.sleep(0.1)  # Brief delay for response
                
                # Try to receive banner
                banner = sock.recv(1024)
                if banner:
                    try:
                        decoded_banner = banner.decode('utf-8', errors='ignore').strip()
                        return self.parse_banner(decoded_banner, port)
                    except:
                        return "Binary response"
                else:
                    return "No banner"
                    
        except socket.timeout:
            return "Timeout"
        except ConnectionRefusedError:
            return "Connection refused"
        except Exception as e:
            return f"Error: {str(e)[:50]}"
    
    def parse_banner(self, banner, port):
        """
        Parse and clean banner information
        """
        if not banner:
            return "No banner"
        
        # Limit banner length for display
        if len(banner) > 100:
            banner = banner[:97] + "..."
        
        # Remove control characters and clean up
        banner = ''.join(char for char in banner if char.isprintable() or char.isspace())
        banner = ' '.join(banner.split())  # Normalize whitespace
        
        # Extract useful information based on port
        if port in [80, 443, 8080, 8443]:
            # HTTP responses
            if "HTTP/" in banner:
                # Extract server information
                server_match = re.search(r'Server:\s*([^\r\n]+)', banner, re.IGNORECASE)
                if server_match:
                    return f"HTTP - {server_match.group(1).strip()}"
                else:
                    return "HTTP Server"
            return banner
        elif port == 21:
            # FTP
            if "FTP" in banner.upper():
                return banner
            return f"FTP - {banner}"
        elif port == 22:
            # SSH
            if "SSH" in banner.upper():
                return banner
            return f"SSH - {banner}"
        elif port == 25:
            # SMTP
            if any(word in banner.upper() for word in ["SMTP", "MAIL", "ESMTP"]):
                return banner
            return f"SMTP - {banner}"
        else:
            return banner

# Global instances
banner_grabber = ServiceBannerGrabber()

# Fragmented Packet Scanner Implementation
class FragmentedPacketScanner:
    """
    Implements fragmented packet scanning for stealth port scanning.
    Requires administrative privileges for raw socket access.
    """
    
    def __init__(self):
        self.available = False
        self.error_message = ""
        self._check_availability()
    
    def _check_availability(self):
        """Check if fragmented scanning is available on this system"""
        try:
            # Test raw socket creation
            if platform.system() == "Windows":
                # Windows requires special handling
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
                test_sock.close()
            else:
                # Unix-like systems
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
                test_sock.close()
            self.available = True
        except PermissionError:
            self.error_message = "Administrative privileges required for fragmented scanning"
        except OSError as e:
            self.error_message = f"Raw sockets not available: {e}"
        except Exception as e:
            self.error_message = f"Fragmented scanning not supported: {e}"
    
    def _calculate_checksum(self, data):
        """Calculate Internet checksum for packet data"""
        # Ensure even number of bytes
        if len(data) % 2:
            data += b'\x00'
        
        checksum = 0
        for i in range(0, len(data), 2):
            checksum += (data[i] << 8) + data[i + 1]
        
        # Add carry
        checksum = (checksum >> 16) + (checksum & 0xFFFF)
        checksum += (checksum >> 16)
        
        # One's complement
        return (~checksum) & 0xFFFF
    
    def _create_ip_header(self, src_ip, dest_ip, protocol, packet_id, flags, frag_offset, total_length):
        """Create IP header with fragmentation support"""
        # IP Header fields
        version = 4
        ihl = 5  # Internet Header Length (5 * 4 = 20 bytes)
        tos = 0  # Type of Service
        ttl = 64  # Time to Live
        checksum = 0  # Will be calculated later
        
        # Pack flags and fragment offset (3 bits + 13 bits = 16 bits)
        flags_and_frag = (flags << 13) | frag_offset
        
        # Pack IP header (without checksum)
        ip_header = struct.pack(
            '!BBHHHBBH4s4s',
            (version << 4) + ihl,  # Version + IHL
            tos,
            total_length,
            packet_id,
            flags_and_frag,
            ttl,
            protocol,
            checksum,
            socket.inet_aton(src_ip),
            socket.inet_aton(dest_ip)
        )
        
        # Calculate and insert checksum
        checksum = self._calculate_checksum(ip_header)
        ip_header = struct.pack(
            '!BBHHHBBH4s4s',
            (version << 4) + ihl,
            tos,
            total_length,
            packet_id,
            flags_and_frag,
            ttl,
            protocol,
            checksum,
            socket.inet_aton(src_ip),
            socket.inet_aton(dest_ip)
        )
        
        return ip_header
    
    def _create_tcp_header(self, src_port, dest_port, seq=0, ack=0, flags=0x02):
        """Create TCP header with SYN flag (default)"""
        # TCP Header fields
        offset_reserved = (5 << 4) + 0  # Data offset (5 * 4 = 20 bytes) + reserved
        window = socket.htons(5840)  # Window size
        checksum = 0  # Will be calculated with pseudo header
        urgent_ptr = 0
        
        tcp_header = struct.pack(
            '!HHLLBBHHH',
            src_port,
            dest_port,
            seq,
            ack,
            offset_reserved,
            flags,
            window,
            checksum,
            urgent_ptr
        )
        
        return tcp_header
    
    def _create_udp_header(self, src_port, dest_port, data=b''):
        """Create UDP header"""
        length = 8 + len(data)  # UDP header is 8 bytes + data
        checksum = 0  # Simplified - not calculating UDP checksum
        
        udp_header = struct.pack(
            '!HHHH',
            src_port,
            dest_port,
            length,
            checksum
        )
        
        return udp_header + data
    
    def _get_local_ip(self, target_ip):
        """Get local IP address for the route to target"""
        try:
            # Create a socket to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect((target_ip, 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"  # Fallback
    
    def scan_tcp_fragmented(self, target_ip, target_port, timeout=1.0):
        """
        Perform fragmented TCP SYN scan.
        Splits TCP header across multiple IP fragments.
        """
        if not self.available:
            return None, self.error_message
        
        try:
            src_ip = self._get_local_ip(target_ip)
            src_port = random.randint(32768, 65535)
            packet_id = random.randint(1, 65535)
            
            # Create TCP header
            tcp_header = self._create_tcp_header(src_port, target_port)
            
            # Fragment the TCP header
            # Fragment 1: First 8 bytes of TCP header (src_port, dest_port, seq_num first 4 bytes)
            fragment1_data = tcp_header[:8]
            # Fragment 2: Remaining TCP header (contains the SYN flag)
            fragment2_data = tcp_header[8:]
            
            # Create raw socket
            if platform.system() == "Windows":
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            
            sock.settimeout(timeout)
            
            # Fragment 1: More Fragments flag set (0x1), offset 0
            frag1_total_len = 20 + len(fragment1_data)  # IP header + data
            ip_header1 = self._create_ip_header(src_ip, target_ip, socket.IPPROTO_TCP, 
                                              packet_id, 0x1, 0, frag1_total_len)
            packet1 = ip_header1 + fragment1_data
            
            # Fragment 2: No more fragments (0x0), offset 1 (8 bytes)
            frag2_total_len = 20 + len(fragment2_data)  # IP header + data
            ip_header2 = self._create_ip_header(src_ip, target_ip, socket.IPPROTO_TCP, 
                                              packet_id, 0x0, 1, frag2_total_len)
            packet2 = ip_header2 + fragment2_data
            
            start_time = time.time()
            
            # Send fragments with small delay
            sock.sendto(packet1, (target_ip, 0))
            time.sleep(0.001)  # 1ms delay between fragments
            sock.sendto(packet2, (target_ip, 0))
            
            # Try to receive response (simplified - just check if we get anything back)
            try:
                sock.settimeout(timeout)
                data, addr = sock.recvfrom(1024)
                end_time = time.time()
                response_time = round((end_time - start_time) * 1000, 1)
                
                # Basic response analysis
                if len(data) >= 20:  # At least IP header
                    # Extract IP header
                    ip_header = data[:20]
                    protocol = struct.unpack('!B', ip_header[9:10])[0]
                    
                    if protocol == socket.IPPROTO_TCP and len(data) >= 40:
                        # Extract TCP header
                        tcp_header = data[20:40]
                        flags = struct.unpack('!B', tcp_header[13:14])[0]
                        
                        if flags & 0x12:  # SYN+ACK
                            sock.close()
                            return "OPEN", response_time
                        elif flags & 0x04:  # RST
                            sock.close()
                            return "CLOSED", response_time
                
                sock.close()
                return "OPEN|FILTERED", response_time
                
            except socket.timeout:
                sock.close()
                end_time = time.time()
                response_time = round((end_time - start_time) * 1000, 1)
                return "FILTERED", response_time
            
        except Exception as e:
            return "ERROR", str(e)
    
    def scan_udp_fragmented(self, target_ip, target_port, timeout=1.0):
        """
        Perform fragmented UDP scan.
        Splits UDP header and data across fragments.
        """
        if not self.available:
            return None, self.error_message
        
        try:
            src_ip = self._get_local_ip(target_ip)
            src_port = random.randint(32768, 65535)
            packet_id = random.randint(1, 65535)
            
            # Create UDP packet with some test data
            test_data = b"FRAGMENTED_UDP_SCAN"
            udp_packet = self._create_udp_header(src_port, target_port, test_data)
            
            # Fragment the UDP packet
            # Fragment 1: UDP header (8 bytes)
            fragment1_data = udp_packet[:8]
            # Fragment 2: UDP data
            fragment2_data = udp_packet[8:]
            
            # Create raw socket
            if platform.system() == "Windows":
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            
            sock.settimeout(timeout)
            
            # Fragment 1: More Fragments flag set (0x1), offset 0
            frag1_total_len = 20 + len(fragment1_data)  # IP header + data
            ip_header1 = self._create_ip_header(src_ip, target_ip, socket.IPPROTO_UDP, 
                                              packet_id, 0x1, 0, frag1_total_len)
            packet1 = ip_header1 + fragment1_data
            
            # Fragment 2: No more fragments (0x0), offset 1 (8 bytes)
            frag2_total_len = 20 + len(fragment2_data)  # IP header + data
            ip_header2 = self._create_ip_header(src_ip, target_ip, socket.IPPROTO_UDP, 
                                              packet_id, 0x0, 1, frag2_total_len)
            packet2 = ip_header2 + fragment2_data
            
            start_time = time.time()
            
            # Send fragments
            sock.sendto(packet1, (target_ip, 0))
            time.sleep(0.001)  # 1ms delay between fragments
            sock.sendto(packet2, (target_ip, 0))
            
            # Try to receive response
            try:
                sock.settimeout(timeout)
                data, addr = sock.recvfrom(1024)
                end_time = time.time()
                response_time = round((end_time - start_time) * 1000, 1)
                
                sock.close()
                return "OPEN", response_time
                
            except socket.timeout:
                sock.close()
                end_time = time.time()
                response_time = round((end_time - start_time) * 1000, 1)
                return "OPEN|FILTERED", response_time
            
        except Exception as e:
            return "ERROR", str(e)

# Global fragmented scanner instance
fragmented_scanner = FragmentedPacketScanner()

# Enhanced Ping Tool Implementation
class PingTool:
    """
    Cross-platform ping implementation using subprocess
    """
    
    def __init__(self):
        self.current_process = None
        self.stop_event = threading.Event()
        self.ping_count = 0
        self.continuous_mode = False
    
    def ping(self, host, count=4, timeout=3, continuous=False, callback=None):
        """
        Ping a host and return results via callback
        """
        self.stop_event.clear()
        self.ping_count = 0
        self.continuous_mode = continuous
        
        # Determine ping command based on operating system
        if platform.system().lower() == "windows":
            if continuous:
                cmd = ["ping", "-t", "-w", str(timeout * 1000), host]
            else:
                cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
        else:
            if continuous:
                cmd = ["ping", "-W", str(timeout), host]
            else:
                cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
        
        try:
            # Configure subprocess to hide window on Windows
            popen_kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'text': True,
                'bufsize': 1,
                'universal_newlines': True
            }
            
            # Hide console window on Windows
            if platform.system().lower() == "windows":
                popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            
            # Start the ping process
            self.current_process = subprocess.Popen(cmd, **popen_kwargs)
            
            # Read output line by line
            while True:
                if self.stop_event.is_set():
                    break
                
                try:
                    # Use poll to check if process is still running
                    if self.current_process.poll() is not None:
                        # Process has terminated
                        break
                    
                    # Read line with timeout
                    line = self.current_process.stdout.readline()
                    if not line:
                        # End of output
                        break
                    
                    line = line.strip()
                    if line:
                        # Parse ping results for response time
                        response_time = self._parse_ping_line(line)
                        
                        if callback:
                            # Schedule callback on main thread to avoid UI crashes
                            callback(line + "\n", "output", response_time)
                        
                        self.ping_count += 1
                        
                        # In non-continuous mode, check if we've reached the count
                        if not continuous and self.ping_count >= count:
                            break
                
                except Exception as e:
                    print(f"Error reading ping output: {e}")
                    break
            
            # Clean up process
            if self.current_process:
                try:
                    self.current_process.terminate()
                    self.current_process.wait(timeout=2)
                except:
                    try:
                        self.current_process.kill()
                    except:
                        pass
            
            # Final callback
            if callback and not self.stop_event.is_set():
                callback("Ping completed successfully\n", "info", None)
                    
        except FileNotFoundError:
            if callback:
                callback("Error: ping command not found\n", "error", None)
        except Exception as e:
            if callback:
                callback(f"Error: {str(e)}\n", "error", None)
        finally:
            self.current_process = None
    
    def _parse_ping_line(self, line):
        """Parse ping output line to extract response time"""
        try:
            # Common patterns for response time extraction
            patterns = [
                r'time[<=](\d+(?:\.\d+)?)ms',  # Windows/Linux format
                r'time=(\d+(?:\.\d+)?)ms',     # Alternative format
                r'time:\s*(\d+(?:\.\d+)?)ms',  # Another format
                r'(\d+(?:\.\d+)?)ms',          # Simple ms extraction
            ]
            
            line_lower = line.lower()
            for pattern in patterns:
                match = re.search(pattern, line_lower)
                if match:
                    response_time = float(match.group(1))
                    return response_time
            
            # Check for timeout or unreachable
            if any(keyword in line_lower for keyword in ['timeout', 'unreachable', 'no reply', 'request timed out']):
                return None
                
        except Exception as e:
            print(f"Error parsing ping line: {e}")
        
        return None
    
    def stop_ping(self):
        """Stop the current ping operation"""
        self.stop_event.set()
        if self.current_process:
            try:
                self.current_process.terminate()
                # Give it a moment to terminate gracefully
                try:
                    self.current_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    self.current_process.kill()
                    self.current_process.wait(timeout=1)
            except Exception as e:
                print(f"Error stopping ping process: {e}")
                try:
                    self.current_process.kill()
                except:
                    pass

# Global ping tool instance
ping_tool = PingTool()

def open_ping_window(root):
    """Open the ping tool window"""
    ping_win = tk.Toplevel(root)
    ping_win.title("Ping - Port Checker Plus")
    ping_win.geometry("500x575")  # Reduced height since no graph
    ping_win.configure(bg="#ffffff")
    ping_win.transient(root)
    ping_win.grab_set()
    ping_win.resizable(True, True)
    set_window_icon(ping_win)
    
    # Configure window grid weights
    ping_win.grid_rowconfigure(2, weight=1)  # Results area gets most space
    ping_win.grid_columnconfigure(0, weight=1)
    
    # Add window close handler to stop ping when window is closed
    def on_window_close():
        """Handle window closing - stop ping and destroy window"""
        try:
            ping_tool.stop_ping()
            # Give a moment for cleanup
            time.sleep(0.1)
        except:
            pass
        finally:
            ping_win.destroy()
    
    ping_win.protocol("WM_DELETE_WINDOW", on_window_close)
    
    # Title and input frame
    input_frame = tk.Frame(ping_win, bg="#ffffff")
    input_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
    input_frame.grid_columnconfigure(1, weight=1)
    
    # Ping Tool Section
    ping_section = tk.LabelFrame(input_frame, text="Configure", 
                                font=("Segoe UI", 10, "bold"), bg="#ffffff", 
                                fg="#34495e", padx=15, pady=10)
    ping_section.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 15))
    ping_section.grid_columnconfigure(1, weight=1)
    
    # Host input
    host_frame = tk.Frame(ping_section, bg="#ffffff")
    host_frame.grid(row=0, column=0, columnspan=2, sticky="w", pady=5)

    tk.Label(host_frame, text="Host/IP:", font=("Segoe UI", 10), 
         bg="#ffffff", fg="#2c3e50").pack(side="left")
    host_entry = tk.Entry(host_frame, font=("Segoe UI", 10), width=20)
    host_entry.pack(side="left", padx=(2, 0))
    
    # Pre-populate with host from main window, stripping CIDR notation if present
    try:
        if hasattr(root, 'host_entry') and root.host_entry:
            main_host = root.host_entry.get()
            
            if main_host:
                main_host = main_host.strip()
                
                # Check for CIDR notation (both / and \ separators) and remove it
                if '/' in main_host:
                    ping_host = main_host.split('/')[0].strip()
                elif '\\' in main_host:
                    ping_host = main_host.split('\\')[0].strip()
                else:
                    ping_host = main_host
                
                # Clear the entry and insert the processed host
                host_entry.delete(0, tk.END)
                host_entry.insert(0, ping_host)
    except Exception as e:
        pass  # Silently handle any errors during pre-population
    
    # Count input and continuous checkbox
    count_frame = tk.Frame(ping_section, bg="#ffffff")
    count_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
    
    tk.Label(count_frame, text="Count:", font=("Segoe UI", 10), 
             bg="#ffffff", fg="#2c3e50").pack(side="left")
    count_var = tk.StringVar(value="4")
    count_spin = tk.Spinbox(count_frame, from_=1, to=100, width=10, 
                           textvariable=count_var, font=("Segoe UI", 10))
    count_spin.pack(side="left", padx=(10, 15))
    
    # Continuous ping checkbox
    continuous_var = tk.BooleanVar()
    continuous_check = tk.Checkbutton(count_frame, text="Until stopped", 
                                     variable=continuous_var, bg="#ffffff", 
                                     font=("Segoe UI", 10), fg="#2c3e50",
                                     activebackground="#ffffff")
    continuous_check.pack(side="left")
    
    def on_continuous_toggle():
        """Handle continuous checkbox toggle"""
        if continuous_var.get():
            count_spin.config(state="disabled")
        else:
            count_spin.config(state="normal")
    
    continuous_check.config(command=on_continuous_toggle)
    
    # Timeout input
    tk.Label(ping_section, text="Timeout (sec):", font=("Segoe UI", 10), 
             bg="#ffffff", fg="#2c3e50").grid(row=2, column=0, sticky="w", pady=5)
    timeout_var = tk.StringVar(value="5")
    timeout_spin = tk.Spinbox(ping_section, from_=1, to=30, width=10, 
                             textvariable=timeout_var, font=("Segoe UI", 10))
    timeout_spin.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=5)
    
    # Buttons frame
    button_frame = tk.Frame(input_frame, bg="#ffffff")
    button_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(15, 0))
    
    # Ping button
    ping_button = tk.Button(button_frame, text="Start", font=("Segoe UI", 10),
                           bg="#27ae60", fg="white", activebackground="#229954", 
                           relief="flat", padx=20, pady=8)
    ping_button.pack(side="left", padx=(0, 10))
    
    # Stop button
    stop_button = tk.Button(button_frame, text="Stop", font=("Segoe UI", 10),
                           bg="#e74c3c", fg="white", activebackground="#c0392b", 
                           relief="flat", padx=20, pady=8, state=tk.DISABLED)
    stop_button.pack(side="left", padx=(0, 10))
    
    # Clear button
    clear_button = tk.Button(button_frame, text="Clear Results", font=("Segoe UI", 10),
                            bg="#95a5a6", fg="white", activebackground="#7f8c8d", 
                            relief="flat", padx=20, pady=8, state=tk.DISABLED)
    clear_button.pack(side="left")
    
    # Set Host button (positioned to the right)
    def set_host_to_main():
        """Copy the host from ping tool to main window's host entry"""
        try:
            host_text = host_entry.get().strip()
            if host_text and hasattr(root, 'host_entry'):
                root.host_entry.delete(0, tk.END)
                root.host_entry.insert(0, host_text)
                if ping_win.winfo_exists():
                    ping_win.destroy()  # Close the ping window after setting host
            elif not host_text:
                messagebox.showwarning("No Host", "Please enter a host/IP address first.")
            else:
                messagebox.showerror("Error", "Main window not accessible.")
        except tk.TclError:
            # Widget has been destroyed, ignore
            pass
    
    set_host_button = tk.Button(button_frame, text="Set Host", font=("Segoe UI", 10),
                               bg="#3498db", fg="white", activebackground="#2980b9", 
                               relief="flat", padx=20, pady=8, command=set_host_to_main)
    set_host_button.pack(side="right")
    
    # Results frame
    results_frame = tk.Frame(ping_win, bg="#ffffff")
    results_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
    results_frame.grid_rowconfigure(1, weight=1)
    results_frame.grid_columnconfigure(0, weight=1)
    
    # Results label
    results_label = tk.Label(results_frame, text="Results:", 
                            font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#2c3e50")
    results_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
    
    # Results text widget with scrollbar
    text_frame = tk.Frame(results_frame, bg="#ffffff")
    text_frame.grid(row=1, column=0, sticky="nsew")
    text_frame.grid_rowconfigure(0, weight=1)
    text_frame.grid_columnconfigure(0, weight=1)
    
    results_text = tk.Text(text_frame, font=("Consolas", 9), bg="#f8f9fa", 
                          fg="#2c3e50", wrap=tk.WORD, state=tk.DISABLED, height=18)
    results_text.grid(row=0, column=0, sticky="nsew")
    
    # Scrollbar for text widget
    text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=results_text.yview)
    text_scrollbar.grid(row=0, column=1, sticky="ns")
    results_text.configure(yscrollcommand=text_scrollbar.set)
    
    # Configure text tags for colored output
    results_text.tag_configure("output", foreground="#2c3e50")
    results_text.tag_configure("error", foreground="#e74c3c", font=("Consolas", 9, "bold"))
    results_text.tag_configure("info", foreground="#3498db", font=("Consolas", 9, "italic"))
    results_text.tag_configure("success", foreground="#27ae60")
    
    # Statistics frame (moved below results)
    stats_frame = tk.Frame(ping_win, bg="#ffffff")
    stats_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
    
    stats_label = tk.Label(stats_frame, text="", 
                          font=("Segoe UI", 9), bg="#ffffff", fg="#3498db", justify="left")
    stats_label.pack(anchor="w")
    
    # Status label
    status_frame = tk.Frame(ping_win, bg="#ffffff")
    status_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10))
    
    status_label = tk.Label(status_frame, text="Ready", font=("Segoe UI", 9), 
                           bg="#ffffff", fg="#7f8c8d")
    status_label.pack(side="left")
    
    # Statistics tracking
    ping_stats = {
        'sent': 0,
        'received': 0,
        'lost': 0,
        'min_time': float('inf'),
        'max_time': 0,
        'total_time': 0,
        'avg_time': 0
    }
    
    def update_statistics(response_time):
        """Update ping statistics"""
        ping_stats['sent'] += 1
        
        if response_time is not None:
            ping_stats['received'] += 1
            ping_stats['min_time'] = min(ping_stats['min_time'], response_time)
            ping_stats['max_time'] = max(ping_stats['max_time'], response_time)
            ping_stats['total_time'] += response_time
            ping_stats['avg_time'] = ping_stats['total_time'] / ping_stats['received']
        else:
            ping_stats['lost'] += 1
        
        # Calculate packet loss percentage
        loss_percent = (ping_stats['lost'] / ping_stats['sent']) * 100 if ping_stats['sent'] > 0 else 0
        
        # Update statistics display with two lines
        if ping_stats['received'] > 0:
            line1 = f"Sent: {ping_stats['sent']}, Received: {ping_stats['received']}, Lost: {ping_stats['lost']} ({loss_percent:.1f}% loss)"
            line2 = f"Min: {ping_stats['min_time']:.1f}ms, Max: {ping_stats['max_time']:.1f}ms, Avg: {ping_stats['avg_time']:.1f}ms"
            stats_text = f"{line1}\n{line2}"
        else:
            stats_text = f"Sent: {ping_stats['sent']}, Received: 0, Lost: {ping_stats['lost']} (100% loss)"
        
        stats_label.config(text=stats_text)
    
    def append_result(text, tag="output", response_time=None):
        """Append text to results with specified tag"""
        try:
            # Check if the widget still exists before trying to modify it
            if results_text.winfo_exists():
                results_text.config(state=tk.NORMAL)
                results_text.insert(tk.END, text, tag)
                results_text.see(tk.END)
                results_text.config(state=tk.DISABLED)
                # Enable clear button when results are added
                if clear_button.winfo_exists():
                    clear_button.config(state=tk.NORMAL)
                # Update the window to show new text immediately
                if ping_win.winfo_exists():
                    ping_win.update_idletasks()
                
                # Update statistics if this is a ping result
                if tag == "output" and ("time" in text.lower() or "timeout" in text.lower() or "unreachable" in text.lower()):
                    update_statistics(response_time)
                    
        except tk.TclError:
            # Widget has been destroyed, ignore the update
            pass
    
    def safe_append_result(text, tag="output", response_time=None):
        """Thread-safe wrapper for append_result"""
        if ping_win.winfo_exists():
            ping_win.after(0, lambda: append_result(text, tag, response_time))
    
    def clear_results():
        """Clear the results text and reset statistics"""
        try:
            if results_text.winfo_exists():
                results_text.config(state=tk.NORMAL)
                results_text.delete(1.0, tk.END)
                results_text.config(state=tk.DISABLED)
                # Disable clear button when results are cleared
                if clear_button.winfo_exists():
                    clear_button.config(state=tk.DISABLED)
                if status_label.winfo_exists():
                    status_label.config(text="Ready")
                
                # Reset statistics
                ping_stats.update({
                    'sent': 0, 'received': 0, 'lost': 0,
                    'min_time': float('inf'), 'max_time': 0,
                    'total_time': 0, 'avg_time': 0
                })
                stats_label.config(text="")
                
        except tk.TclError:
            # Widget has been destroyed, ignore the update
            pass
    
    def start_ping():
        """Start the ping operation"""
        host = host_entry.get().strip()
        if not host:
            messagebox.showwarning("Input Error", "Please enter a host or IP address.")
            return
        
        try:
            count = int(count_var.get()) if not continuous_var.get() else 0
            timeout = int(timeout_var.get())
            continuous = continuous_var.get()
        except ValueError:
            messagebox.showerror("Input Error", "Count and timeout must be valid numbers.")
            return
        
        # Clear previous results and update UI
        clear_results()
        ping_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
        
        if continuous:
            status_label.config(text=f"Pinging {host} continuously...")
            append_result(f"Pinging {host} continuously (press Stop to end)\n", "info")
        else:
            status_label.config(text=f"Pinging {host}...")
            append_result(f"Pinging {host} with {count} packets (timeout: {timeout}s)\n", "info")
        
        append_result("-" * 50 + "\n", "info")
        
        def ping_callback(text, tag, response_time):
            """Callback function for ping results - thread-safe"""
            safe_append_result(text, tag, response_time)
        
        def ping_complete():
            """Called when ping operation completes - thread-safe"""
            def update_ui():
                try:
                    if ping_button.winfo_exists():
                        ping_button.config(state=tk.NORMAL)
                    if stop_button.winfo_exists():
                        stop_button.config(state=tk.DISABLED)
                    if status_label.winfo_exists():
                        status_label.config(text="Ping completed")
                except tk.TclError:
                    # Widget has been destroyed, ignore the update
                    pass
            
            if ping_win.winfo_exists():
                ping_win.after(0, update_ui)
        
        def run_ping():
            """Run ping in separate thread"""
            try:
                ping_tool.ping(host, count, timeout, continuous, ping_callback)
            except Exception as e:
                # Handle any unexpected errors
                safe_append_result(f"Ping error: {str(e)}\n", "error")
            finally:
                # Schedule UI update on main thread
                if ping_win.winfo_exists():
                    ping_win.after(0, ping_complete)
        
        # Start ping in separate thread
        threading.Thread(target=run_ping, daemon=True).start()
    
    def stop_ping():
        """Stop the ping operation"""
        ping_tool.stop_ping()
        
        def update_ui():
            try:
                if ping_button.winfo_exists():
                    ping_button.config(state=tk.NORMAL)
                if stop_button.winfo_exists():
                    stop_button.config(state=tk.DISABLED)
                if status_label.winfo_exists():
                    status_label.config(text="Ping stopped")
            except tk.TclError:
                # Widget has been destroyed, ignore the update
                pass
        
        if ping_win.winfo_exists():
            ping_win.after(0, update_ui)
            safe_append_result("Ping operation stopped by user\n", "error")
    
    # Bind button commands
    ping_button.config(command=start_ping)
    stop_button.config(command=stop_ping)
    clear_button.config(command=clear_results)
    
    # Bind Enter key to start ping
    def on_enter(event):
        if ping_button['state'] == tk.NORMAL:
            start_ping()
    
    host_entry.bind('<Return>', on_enter)
    count_spin.bind('<Return>', on_enter)
    timeout_spin.bind('<Return>', on_enter)
    
    # Focus on host entry
    host_entry.focus_set()
    
    # Center the window
    ping_win.update_idletasks()
    x = (ping_win.winfo_screenwidth() // 2) - (ping_win.winfo_width() // 2)
    y = (ping_win.winfo_screenheight() // 2) - (ping_win.winfo_height() // 2)
    ping_win.geometry(f"+{x}+{y}")

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
                if "manual_export_format" not in config:
                    config["manual_export_format"] = "CSV"
                if "manual_export_directory" not in config:
                    config["manual_export_directory"] = os.getcwd()
                if "randomize_ports" not in config:
                    config["randomize_ports"] = False
                if "variable_delay_scan" not in config:
                    config["variable_delay_scan"] = False
                if "max_cidr_hosts" not in config:
                    config["max_cidr_hosts"] = 254
                if "max_concurrent_threads" not in config:
                    config["max_concurrent_threads"] = get_recommended_threads()
                if "fragmented_packets" not in config:
                    config["fragmented_packets"] = False
                if "banner_grabbing" not in config:
                    config["banner_grabbing"] = False
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
        # FIXED: Use strict=False to handle inputs like 192.168.1.1/27
        network = ipaddress.ip_network(host_input, strict=False)
        hosts = []
        max_hosts = config.get("max_cidr_hosts", 254)
        
        print(f"DEBUG: Parsing CIDR {host_input}")
        print(f"DEBUG: Network object: {network}")
        print(f"DEBUG: Network address: {network.network_address}")
        print(f"DEBUG: Broadcast address: {network.broadcast_address}")
        print(f"DEBUG: Number of addresses: {network.num_addresses}")
        
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
        
        # FIXED: Get host addresses properly
        host_count = 0
        
        # For /31 and /32 networks, network.hosts() returns empty generator
        # For these special cases, we need to use all addresses
        if network.prefixlen >= 31:
            # For /31 and /32, include all addresses
            for ip in network:
                if host_count >= max_hosts:
                    break
                hosts.append(str(ip))
                host_count += 1
                print(f"DEBUG: Added host (special case): {ip}")
        else:
            # For all other networks, use hosts() which excludes network and broadcast
            for ip in network.hosts():
                if host_count >= max_hosts:
                    break
                hosts.append(str(ip))
                host_count += 1
                print(f"DEBUG: Added host: {ip}")
        
        print(f"DEBUG: Total hosts parsed: {len(hosts)}")
        print(f"DEBUG: First 5 hosts: {hosts[:5] if len(hosts) >= 5 else hosts}")
        
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

def get_dynamic_columns(config):
    """Get columns based on enabled features"""
    base_columns = ['Host', 'Port', 'Protocol', 'Status', 'Service']
    
    if config.get("banner_grabbing", False):
        base_columns.append('Banner')
    
    base_columns.append('Response Time')
    return tuple(base_columns)

def update_results_tree_structure():
    """Update the treeview structure when settings change"""
    if not hasattr(root, 'results_tree'):
        return
    
    config = load_config()
    new_columns = get_dynamic_columns(config)
    
    # Get current data before restructuring
    current_data = []
    for item in root.results_tree.get_children():
        values = root.results_tree.item(item)['values']
        tags = root.results_tree.item(item)['tags']
        current_data.append((values, tags))
    
    # Clear the tree before restoring data to prevent duplicates
    for item in root.results_tree.get_children():
        root.results_tree.delete(item)
    
    # Reconfigure the treeview
    root.results_tree['columns'] = new_columns
    
    # Define column properties based on new structure
    column_widths = {
        'Host': 120,
        'Port': 70,
        'Protocol': 70,
        'Status': 100,
        'Service': 120,
        'Banner': 200,
        'Response Time': 100
    }
    
    # Configure columns that are present
    for col in new_columns:
        root.results_tree.column(col, width=column_widths.get(col, 100), 
                                anchor='center' if col != 'Banner' else 'w')
        root.results_tree.heading(col, text=col, 
                                 command=lambda c=col: toggle_sort(c))
    
    # Restore data with proper column mapping
    for values, tags in current_data:
        # Map old values to new column structure
        mapped_values = []
        old_columns = ['Host', 'Port', 'Protocol', 'Status', 'Service', 'Banner', 'Response Time']
        
        for new_col in new_columns:
            if new_col in old_columns:
                old_index = old_columns.index(new_col)
                if old_index < len(values):
                    mapped_values.append(values[old_index])
                else:
                    mapped_values.append('')
            else:
                mapped_values.append('')
        
        root.results_tree.insert("", "end", values=tuple(mapped_values), tags=tags)

def update_advanced_window_appearance():
    """Update the window frame border and header based on advanced settings"""
    if hasattr(root, 'title'):
        config = load_config()
        randomize_enabled = config.get("randomize_ports", False)
        delay_enabled = config.get("variable_delay_scan", False)
        fragmented_enabled = config.get("fragmented_packets", False)
        banner_enabled = config.get("banner_grabbing", False)
        
        if randomize_enabled or delay_enabled or fragmented_enabled or banner_enabled:
            # Build feature list for header display
            features = []
            if randomize_enabled:
                features.append("Randomize Ports")
            if delay_enabled:
                features.append("Variable Delay")
            if fragmented_enabled:
                features.append("Fragmented Packets")
            if banner_enabled:
                features.append("Banner Grabbing")
            
            # Add red border effect
            root.configure(highlightbackground="#e74c3c", highlightthickness=3, highlightcolor="#e74c3c")
            
            # Show red header frame
            if hasattr(root, 'advanced_header_frame'):
                root.advanced_header_frame.pack(fill="x", before=root.input_frame)
                
        else:
            # Reset to normal appearance
            root.configure(highlightbackground="#d0d0d0", highlightthickness=1, highlightcolor="#d0d0d0")
            
            # Hide red header frame
            if hasattr(root, 'advanced_header_frame'):
                root.advanced_header_frame.pack_forget()

def open_log_directory():
    """Open the configured export/log directory in the system's default file manager"""
    try:
        config = load_config()
        export_dir = config.get("export_directory", os.getcwd())
        
        # Check if directory exists
        if not os.path.exists(export_dir):
            response = messagebox.askyesno(
                "Directory Not Found", 
                f"The log directory does not exist:\n{export_dir}\n\n"
                f"Would you like to create it?",
                icon="question"
            )
            if response:
                try:
                    os.makedirs(export_dir, exist_ok=True)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not create directory:\n{e}")
                    return
            else:
                return
        
        # Open directory in system's default file manager
        if platform.system() == "Windows":
            os.startfile(export_dir)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", export_dir])
        else:  # Linux and other Unix-like systems
            subprocess.run(["xdg-open", export_dir])
            
    except Exception as e:
        messagebox.showerror("Error", f"Could not open log directory:\n{e}")

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
    """Export results to TXT format (updated for CIDR support and discovery features)"""
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
        if scan_data.get('fragmented_used', False):
            f.write("Fragmented Scanning: Enabled\n")
        if scan_data.get('banner_grabbing_used', False):
            f.write("Banner Grabbing: Enabled\n")
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
                    if result.get('banner') and result['banner'] not in ['No banner', 'Unknown']:
                        status_text += f" - Banner: {result['banner']}"
                    if result['response_time'] > 0:
                        status_text += f" - {result['response_time']}ms"
                    if result.get('scan_method'):
                        status_text += f" [{result['scan_method']}]"
                    f.write(status_text + "\n")
        else:
            for result in scan_results:
                status_text = f"{result['protocol']} Port {result['port']} is {result['status']}"
                if result['service'] and result['service'] != 'Unknown':
                    status_text += f" (Service: {result['service']})"
                if result.get('banner') and result['banner'] not in ['No banner', 'Unknown']:
                    status_text += f" - Banner: {result['banner']}"
                if result['response_time'] > 0:
                    status_text += f" - {result['response_time']}ms"
                if result.get('scan_method'):
                    status_text += f" [{result['scan_method']}]"
                f.write(status_text + "\n")

def export_to_csv(file_path, scan_data, scan_results):
    """Export results to CSV format (updated for discovery features)"""
    file_exists = os.path.exists(file_path)
    
    with open(file_path, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header if file is new
        if not file_exists:
            writer.writerow(["Timestamp", "Target", "Host", "Port", "Protocol", "Status", "Service", "Banner", "Response Time (ms)", "Scan Method"])
        
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
                result.get('banner', ''),
                result['response_time'] if result['response_time'] > 0 else "",
                result.get('scan_method', 'Standard')
            ])

def export_to_json(file_path, scan_data, scan_results):
    """Export results to JSON format (updated for discovery features)"""
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
            "error_ports": len([r for r in scan_results if r['status'] == 'ERROR']),
            "fragmented_scans": len([r for r in scan_results if r.get('scan_method') == 'Fragmented']),
            "banners_grabbed": len([r for r in scan_results if r.get('banner') and r['banner'] not in ['No banner', 'Unknown']])
        }
    }
    
    scan_history.append(scan_entry)
    
    # Write updated data
    with open(file_path, "w", encoding='utf-8') as f:
        json.dump(scan_history, f, indent=2, ensure_ascii=False)

def export_to_xml(file_path, scan_data, scan_results):
    """Export results to XML format (updated for discovery features)"""
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
    if scan_data.get('fragmented_used', False):
        ET.SubElement(info_elem, "fragmented_scanning").text = "true"
    if scan_data.get('banner_grabbing_used', False):
        ET.SubElement(info_elem, "banner_grabbing").text = "true"
    
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
                if result.get('banner') and result['banner'] not in ['No banner', 'Unknown']:
                    port_elem.set("banner", result['banner'])
                if result['response_time'] > 0:
                    port_elem.set("response_time", f"{result['response_time']}ms")
                if result.get('scan_method'):
                    port_elem.set("scan_method", result['scan_method'])
    else:
        for result in scan_results:
            port_elem = ET.SubElement(results_elem, "port")
            port_elem.set("host", result['host'])
            port_elem.set("number", str(result['port']))
            port_elem.set("protocol", result['protocol'])
            port_elem.set("status", result['status'])
            
            if result['service']:
                port_elem.set("service", result['service'])
            if result.get('banner') and result['banner'] not in ['No banner', 'Unknown']:
                port_elem.set("banner", result['banner'])
            if result['response_time'] > 0:
                port_elem.set("response_time", f"{result['response_time']}ms")
            if result.get('scan_method'):
                port_elem.set("scan_method", result['scan_method'])
    
    # Add summary
    summary_elem = ET.SubElement(scan_elem, "summary")
    summary_elem.set("total_ports", str(len(scan_results)))
    summary_elem.set("total_hosts", str(len(set(r['host'] for r in scan_results)) if scan_data.get('is_cidr', False) else 1))
    summary_elem.set("open_ports", str(len([r for r in scan_results if r['status'] == 'OPEN'])))
    summary_elem.set("closed_ports", str(len([r for r in scan_results if r['status'] == 'CLOSED'])))
    summary_elem.set("filtered_ports", str(len([r for r in scan_results if 'FILTERED' in r['status']])))
    summary_elem.set("error_ports", str(len([r for r in scan_results if r['status'] == 'ERROR'])))
    summary_elem.set("fragmented_scans", str(len([r for r in scan_results if r.get('scan_method') == 'Fragmented'])))
    summary_elem.set("banners_grabbed", str(len([r for r in scan_results if r.get('banner') and r['banner'] not in ['No banner', 'Unknown']])))
    
    # Write XML
    tree = ET.ElementTree(root_elem)
    ET.indent(tree, space="  ", level=0)  # Pretty print
    tree.write(file_path, encoding='utf-8', xml_declaration=True)

def open_settings_window(root, config, initial_tab="Defaults"):
    # Reload config to get latest saved settings
    config = load_config()
    
    settings_win = tk.Toplevel(root)
    settings_win.title("Settings - Port Checker Plus")
    settings_win.geometry("520x640")  
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
                                   fg="#34495e", padx=15, pady=8)
    stealth_section.pack(fill="x", padx=15, pady=(15, 8))

    # Port randomization option
    randomize_ports_var = tk.BooleanVar(value=config.get("randomize_ports", False))
    randomize_check = tk.Checkbutton(stealth_section, 
                                    text="Randomize Ports", 
                                    variable=randomize_ports_var,
                                    bg="#ffffff", font=("Segoe UI", 10), 
                                    fg="#2c3e50", activebackground="#ffffff")
    randomize_check.pack(anchor="w", pady=(3, 0))

    # Description for randomization
    randomize_desc = tk.Label(stealth_section, 
                             text="Randomizes the order in which ports are scanned.", 
                             font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d", 
                             wraplength=450, justify="left")
    randomize_desc.pack(anchor="w", pady=(1, 8))

    # Variable delay scan option
    variable_delay_var = tk.BooleanVar(value=config.get("variable_delay_scan", False))
    variable_delay_check = tk.Checkbutton(stealth_section, 
                                         text="Variable Delay Scan", 
                                         variable=variable_delay_var,
                                         bg="#ffffff", font=("Segoe UI", 10), 
                                         fg="#2c3e50", activebackground="#ffffff")
    variable_delay_check.pack(anchor="w", pady=(3, 0))

    # Description for variable delay
    delay_desc = tk.Label(stealth_section, 
                         text="Adds random delays (300-700ms) between port scans to avoid rate limiting.", 
                         font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d", 
                         wraplength=450, justify="left")
    delay_desc.pack(anchor="w", pady=(1, 8))

    # Fragmented packet scanning option
    fragmented_packets_var = tk.BooleanVar(value=config.get("fragmented_packets", False))
    fragmented_check = tk.Checkbutton(stealth_section, 
                                     text="Fragmented Packet Scanning", 
                                     variable=fragmented_packets_var,
                                     bg="#ffffff", font=("Segoe UI", 10), 
                                     fg="#2c3e50", activebackground="#ffffff")
    fragmented_check.pack(anchor="w", pady=(3, 0))

    # Description for fragmented scanning
    fragmented_desc = tk.Label(stealth_section, 
                              text="Splits packets into fragments to evade basic firewalls and IDS. Requires administrative privileges.", 
                              font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d", 
                              wraplength=450, justify="left")
    fragmented_desc.pack(anchor="w", pady=(1, 5))

    # Fragmented scanning availability status
    if fragmented_scanner.available:
        frag_status = tk.Label(stealth_section, 
                              text="✅ Fragmented scanning is available on this system.", 
                              font=("Segoe UI", 9), bg="#ffffff", fg="#27ae60", 
                              wraplength=450, justify="left")
    else:
        frag_status = tk.Label(stealth_section, 
                              text=f"❌ {fragmented_scanner.error_message}", 
                              font=("Segoe UI", 9), bg="#ffffff", fg="#e74c3c", 
                              wraplength=450, justify="left")
        # Disable checkbox if not available
        fragmented_check.config(state=tk.DISABLED)
        fragmented_packets_var.set(False)
    
    frag_status.pack(anchor="w", pady=(0, 3))

    # Discovery Options Section
    discovery_section = tk.LabelFrame(advanced_frame, text="Discovery Options", 
                                     font=("Segoe UI", 10, "bold"), bg="#ffffff", 
                                     fg="#34495e", padx=15, pady=8)
    discovery_section.pack(fill="x", padx=15, pady=8)

    # Banner grabbing option
    banner_grabbing_var = tk.BooleanVar(value=config.get("banner_grabbing", False))
    banner_check = tk.Checkbutton(discovery_section, 
                                 text="Service Banner Grabbing", 
                                 variable=banner_grabbing_var,
                                 bg="#ffffff", font=("Segoe UI", 10), 
                                 fg="#2c3e50", activebackground="#ffffff")
    banner_check.pack(anchor="w", pady=(3, 0))

    # Description for banner grabbing
    banner_desc = tk.Label(discovery_section, 
                          text="Provides detailed service version information but increases scan time.", 
                          font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d", 
                          wraplength=450, justify="left")
    banner_desc.pack(anchor="w", pady=(1, 8))

    # ===== EXPORT TAB =====
    export_tab_frame = tk.Frame(notebook, bg="#ffffff")
    notebook.add(export_tab_frame, text="Export")

    # Manual Export Settings Section
    manual_export_section = tk.LabelFrame(export_tab_frame, text="Manual Export Settings", 
                                         font=("Segoe UI", 10, "bold"), bg="#ffffff", 
                                         fg="#34495e", padx=15, pady=10)
    manual_export_section.pack(fill="x", padx=15, pady=(15, 10))

    # Export format selection
    manual_format_frame = tk.Frame(manual_export_section, bg="#ffffff")
    manual_format_frame.pack(fill="x", pady=(5, 15))
    
    tk.Label(manual_format_frame, text="Export Format:", font=("Segoe UI", 10), 
             bg="#ffffff", fg="#2c3e50").pack(side="left")
    manual_format_var = tk.StringVar(value=config.get("manual_export_format", "CSV"))
    manual_format_options = ["CSV", "TXT", "JSON"]
    manual_format_combo = ttk.Combobox(manual_format_frame, textvariable=manual_format_var, 
                                      values=manual_format_options, state="readonly", width=10,
                                      font=("Segoe UI", 10))
    manual_format_combo.pack(side="right")

    # Export directory
    manual_dir_label = tk.Label(manual_export_section, text="Default Export Directory:", 
                               font=("Segoe UI", 10), bg="#ffffff", fg="#2c3e50")
    manual_dir_label.pack(anchor="w", pady=(0, 5))

    manual_dir_frame = tk.Frame(manual_export_section, bg="#ffffff")
    manual_dir_frame.pack(fill="x", pady=(0, 10))
    
    manual_dir_entry = tk.Entry(manual_dir_frame, font=("Segoe UI", 10))
    manual_dir_entry.insert(0, config.get("manual_export_directory", os.getcwd()))
    manual_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
    
    manual_browse_btn = tk.Button(manual_dir_frame, text="Browse...", font=("Segoe UI", 9),
                                 bg="#3498db", fg="white", activebackground="#2980b9",
                                 relief="flat", padx=15)
    manual_browse_btn.pack(side="right")

    def browse_manual_directory():
        selected = filedialog.askdirectory(parent=settings_win, 
                                         title="Select Default Export Directory")
        if selected:
            manual_dir_entry.delete(0, tk.END)
            manual_dir_entry.insert(0, selected)
        settings_win.lift()
        settings_win.focus_force()

    manual_browse_btn.config(command=browse_manual_directory)

    # Export description
    export_desc = tk.Label(manual_export_section, 
                          text="Configure default settings for manual export using the Export Results button. "
                               "These settings are separate from automatic logging.", 
                          font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d", 
                          wraplength=450, justify="left")
    export_desc.pack(anchor="w", pady=(5, 0))

    # ===== LOGGING TAB =====
    export_frame = tk.Frame(notebook, bg="#ffffff")
    notebook.add(export_frame, text="Logging")

    # Log Settings Section
    export_section = tk.LabelFrame(export_frame, text="Log Settings", 
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
    clear_logs_section.pack(fill="x", padx=15, pady=10)  # Always visible now
    
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
        # Clear logs button and info are always enabled - removed from toggle
        dir_label.config(fg="#2c3e50" if export_var.get() else "#bdc3c7")
        info_label.config(fg="#7f8c8d" if export_var.get() else "#bdc3c7")

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

            # Special warning for discovery features with high thread counts
            if banner_grabbing_var.get() and max_threads > 50:
                discovery_warning = (
                    f"Warning: You have enabled banner grabbing with {max_threads} threads.\n\n"
                    f"Banner grabbing significantly increases scan time and may overwhelm targets.\n"
                    f"Recommended: Use ≤50 threads when banner grabbing is enabled.\n\n"
                    f"Continue with current settings?"
                )
                
                if not messagebox.askyesno("Banner Grabbing + High Threads Warning", discovery_warning, icon="warning"):
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

            # Validate fragmented scanning if enabled
            if fragmented_packets_var.get() and not fragmented_scanner.available:
                messagebox.showwarning("Fragmented Scanning", 
                                     f"Fragmented scanning is not available:\n{fragmented_scanner.error_message}\n\n"
                                     f"This option will be disabled.")
                fragmented_packets_var.set(False)

            # Save configuration
            config["timeout"] = timeout_val
            config["export_results"] = export_var.get()
            config["export_format"] = format_var.get()
            config["manual_export_format"] = manual_format_var.get()
            config["manual_export_directory"] = manual_dir_entry.get().strip()
            config["show_open_only"] = show_open_only_var.get()
            config["default_host"] = host_entry.get().strip()
            config["retry_count"] = int(retry_spin.get())
            config["default_ports"] = port_input
            config["scan_protocol"] = protocol_var.get()
            config["randomize_ports"] = randomize_ports_var.get()
            config["variable_delay_scan"] = variable_delay_var.get()
            config["fragmented_packets"] = fragmented_packets_var.get()
            config["banner_grabbing"] = banner_grabbing_var.get()
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
                
                # Update the advanced window appearance
                update_advanced_window_appearance()
                
                # Update results tree structure if discovery features changed
                update_results_tree_structure()

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

    # Select the initial tab based on parameter
    tab_mapping = {
        "Defaults": 0,
        "General": 1, 
        "Advanced": 2,
        "Export": 3,
        "Logging": 4
    }
    
    if initial_tab in tab_mapping:
        notebook.select(tab_mapping[initial_tab])

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
        
        # Try fragmented scanning if enabled
        if config.get("fragmented_packets", False) and fragmented_scanner.available:
            try:
                frag_result, frag_response_time = fragmented_scanner.scan_tcp_fragmented(
                    host, port, config.get("timeout", 0.3)
                )
                
                if frag_result and frag_result != "ERROR":
                    # Fragmented scan succeeded
                    try:
                        service = socket.getservbyport(port)
                    except:
                        service = 'Unknown'

                    # Try banner grabbing if enabled and port is open
                    banner = "No banner"
                    if (config.get("banner_grabbing", False) and 
                        frag_result == "OPEN"):
                        try:
                            banner = banner_grabber.grab_banner(host, port, config.get("timeout", 0.3))
                        except Exception as e:
                            banner = f"Banner error: {str(e)[:30]}"

                    result_data = {
                        'host': host,
                        'port': port,
                        'protocol': 'TCP',
                        'status': frag_result,
                        'service': service,
                        'banner': banner,
                        'response_time': frag_response_time if isinstance(frag_response_time, (int, float)) else 0,
                        'category': get_port_category(port),
                        'scan_method': 'Fragmented'
                    }

                    if config.get("show_open_only", False) and "OPEN" not in frag_result:
                        return True

                    with file_lock:
                        scan_results.append(result_data)
                    
                    return True
                # If fragmented scan failed, fall through to normal scanning
            except Exception as e:
                print(f"Fragmented scan failed for {host}:{port} - {e}, falling back to normal scan")
        
        # Normal TCP scanning (original code)
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

        # Try banner grabbing if enabled and port is open
        banner = "No banner"
        if config.get("banner_grabbing", False) and status == "OPEN":
            try:
                banner = banner_grabber.grab_banner(host, port, config.get("timeout", 0.3))
            except Exception as e:
                banner = f"Banner error: {str(e)[:30]}"

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
            'banner': banner,
            'response_time': response_time if status == "OPEN" else 0,
            'category': get_port_category(port),
            'scan_method': 'Standard'
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
            'banner': 'Error',
            'response_time': 0,
            'category': 'error',
            'scan_method': 'Standard'
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
        
        # Try fragmented scanning if enabled
        if config.get("fragmented_packets", False) and fragmented_scanner.available:
            try:
                frag_result, frag_response_time = fragmented_scanner.scan_udp_fragmented(
                    host, port, config.get("timeout", 0.3)
                )
                
                if frag_result and frag_result != "ERROR":
                    # Fragmented scan succeeded
                    result_data = {
                        'host': host,
                        'port': port,
                        'protocol': 'UDP',
                        'status': frag_result,
                        'service': 'Unknown',
                        'banner': 'No banner',  # UDP banner grabbing is more complex
                        'response_time': frag_response_time if isinstance(frag_response_time, (int, float)) else 0,
                        'category': get_port_category(port),
                        'scan_method': 'Fragmented'
                    }

                    if config.get("show_open_only", False) and "OPEN" not in frag_result:
                        return True

                    with file_lock:
                        scan_results.append(result_data)
                    
                    return True
                # If fragmented scan failed, fall through to normal scanning
            except Exception as e:
                print(f"Fragmented UDP scan failed for {host}:{port} - {e}, falling back to normal scan")
            
        # Normal UDP scanning (original code)
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
            'banner': 'No banner',  # UDP banner grabbing is more complex
            'response_time': response_time if "OPEN" in status else 0,
            'category': get_port_category(port),
            'scan_method': 'Standard'
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
                'banner': 'Error',
                'response_time': 0,
                'category': 'error',
                'scan_method': 'Standard'
            }
            with file_lock:
                scan_results.append(error_data)
        
        return True

def update_results_tree(results_tree, scan_results):
    """Update the results tree with scan data and apply color coding"""
    # Clear existing results first to prevent duplicates
    for item in results_tree.get_children():
        results_tree.delete(item)
    
    # Get current config to determine which columns to show
    config = load_config()
    show_banner = config.get("banner_grabbing", False)
    
    # Add all current scan results
    for result in scan_results:
        # Prepare banner text for display (truncate if too long)
        banner_text = result.get('banner', 'No banner')
        if len(banner_text) > 50:
            banner_text = banner_text[:47] + "..."
        
        # Build values list based on enabled features
        values = [
            result['host'],
            result['port'],
            result['protocol'],
            result['status'],
            result['service']
        ]
        
        # Only add banner column if banner grabbing is enabled
        if show_banner:
            values.append(banner_text)
        
        # Always add response time at the end
        values.append(f"{result['response_time']}ms" if result['response_time'] > 0 else "-")
        
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
            
        results_tree.insert("", "end", values=tuple(values), tags=(tag,))
    
    # Enable clear button if there are results to display
    if scan_results and hasattr(root, 'clear_button'):
        root.clear_button.config(state=tk.NORMAL)
    
    # Update export button visibility
    update_export_button_visibility()

def check_ports_threaded_with_export(hosts, ports, results_tree, clear_button, config, scan_data):
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

    counter = {"count": 0, "completed": 0, "ui_updated": False}  # Added ui_updated flag
    counter_lock = threading.Lock()
    scan_results = []

    def update_completion_ui():
        """Update UI when scan completes or is stopped"""
        host_count = len(hosts)
        port_count = len(ports)
        
        if stop_scan_event.is_set():
            # Scan was stopped
            root.status_label.config(text=f"Scan stopped - {len(scan_results)} results collected")
            root.stop_button.config(text="Stopped", state=tk.DISABLED)
        else:
            # Scan completed normally
            root.status_label.config(text=f"Scan complete - {host_count} host(s), {port_count} port(s) checked")
            root.stop_button.pack_forget()  # Hide stop button for completed scans
            root.stop_button.config(state=tk.NORMAL, text="Stop Scan")  # Reset for next scan
        
        # Always re-enable check button and clear button at completion
        root.check_button.config(state=tk.NORMAL)
        clear_button.config(state=tk.NORMAL)  # Enable clear button when scan completes/stops

    def on_port_done():
        with counter_lock:
            counter["count"] += 1
            # Update progress bar and status
            progress = (counter["count"] / total_scans) * 100
            root.progress_var.set(progress)
            root.progress_percentage.config(text=f"{progress:.0f}%")
            
            if stop_scan_event.is_set():
                root.status_label.config(text=f"Scan stopped - {counter['count']} of {total_scans} scans completed")
            else:
                root.status_label.config(text=f"{counter['count']} of {total_scans} scans completed")
            
            if counter["count"] == total_scans or stop_scan_event.is_set():
                counter["completed"] = 1
                
                if not counter["ui_updated"]:
                    counter["ui_updated"] = True
                    results_tree.after(0, lambda: update_results_tree(results_tree, scan_results))
                
                # Export results after scanning is complete (only if not stopped)
                if current_config.get("export_results", False) and not stop_scan_event.is_set():
                    try:
                        export_results_to_file(scan_data, scan_results, current_config)
                    except Exception as e:
                        messagebox.showerror("Export Error", f"Could not export results:\n{e}")
                
                # Schedule UI update on main thread
                root.after(0, update_completion_ui)
                
                # Reset progress bar after completion
                root.after(3000, lambda: (
                    root.progress_var.set(0), 
                    root.progress_percentage.pack_forget(),  # Hide percentage when resetting
                    root.progress_bar.pack_configure(padx=0),  # Reset progress bar padding
                    root.status_label.config(text="Ready")
                ))

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
    max_workers = min(current_config.get("max_concurrent_threads", get_recommended_threads()), len(scan_tasks))
    
    def trigger_stop_completion():
        """Helper function to trigger completion UI when scan is stopped"""
        root.after(0, update_completion_ui)

    def run_scan_batch():
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks in optimized batches for better stop responsiveness
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
            
        # Keep Clear Results button disabled during scan
        root.clear_button.config(state=tk.DISABLED)
        
        # Disable check button and show stop button
        root.check_button.config(state=tk.DISABLED)
        root.stop_button.config(state=tk.NORMAL, text="Stop Scan")  # Ensure stop button is ready
        root.stop_button.pack(side="left", padx=(0, 10), after=root.check_button)
        
        # Initialize progress bar and show scanning status
        root.progress_var.set(0)
        root.progress_percentage.config(text="0%")
        # Repack widgets in correct order: percentage first (left), then progress bar (right)
        root.progress_bar.pack_forget()  # Temporarily unpack progress bar
        root.progress_percentage.pack(side="left")  # Pack percentage first (will be on left)
        root.progress_bar.pack(side="left", padx=(8, 0))  # Pack progress bar after percentage (will be on right)
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
        if config.get("fragmented_packets", False) and fragmented_scanner.available:
            scan_status += " (fragmented)"
        if config.get("banner_grabbing", False):
            scan_status += " (banners)"
        root.status_label.config(text=scan_status)
        
        # Prepare scan data for export
        scan_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'host_input': host_input,
            'resolved_ip': resolved_ip,
            'port_input': port_input,
            'protocol': root.protocol_var.get(),
            'is_cidr': is_cidr,
            'scanned_hosts': hosts if is_cidr else [resolved_ip],
            'fragmented_used': config.get("fragmented_packets", False) and fragmented_scanner.available,
            'banner_grabbing_used': config.get("banner_grabbing", False)
        }
        
        threading.Thread(
            target=check_ports_threaded_with_export,
            args=(hosts, ports, root.results_tree, root.clear_button, config, scan_data),
            daemon=True
        ).start()
    except Exception as e:
        # Reset UI state on error
        root.check_button.config(state=tk.NORMAL)
        root.stop_button.pack_forget()
        root.progress_percentage.pack_forget()  # Hide percentage on error
        root.progress_bar.pack_configure(padx=0)  # Reset progress bar padding
        messagebox.showerror("Error", str(e))

def on_stop_scan():
    """Stop the current scan"""
    stop_scan_event.set()
    
    # Immediately update UI to show stopping
    root.status_label.config(text="Stopping scan...")
    root.stop_button.config(state=tk.DISABLED, text="Stopping...")
    
    # Re-enable check button immediately so user can start new scan
    root.check_button.config(state=tk.NORMAL)

def export_current_results():
    """Export current scan results using manual export settings"""
    if not hasattr(root, 'results_tree') or not root.results_tree.get_children():
        messagebox.showwarning("No Results", "No scan results to export.")
        return
    
    config = load_config()
    
    # Get manual export settings
    export_format = config.get("manual_export_format", "CSV").upper()
    export_dir = config.get("manual_export_directory", os.getcwd())
    
    # Create default filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"port_scan_results_{timestamp}"
    
    # File extension based on format
    extensions = {
        "CSV": ".csv",
        "TXT": ".txt", 
        "JSON": ".json"
    }
    
    extension = extensions.get(export_format, ".csv")
    default_filename += extension
    
    # Ask user for save location
    file_path = filedialog.asksaveasfilename(
        parent=root,
        title="Export Scan Results",
        defaultextension=extension,
        filetypes=[
            (f"{export_format} files", f"*{extension}"),
            ("All files", "*.*")
        ],
        initialdir=export_dir,
        initialfile=default_filename
    )
    
    if not file_path:
        return  # User cancelled
    
    try:
        # Convert treeview data to scan results format
        scan_results = []
        config = load_config()
        show_banner = config.get("banner_grabbing", False)
        
        for item in root.results_tree.get_children():
            values = root.results_tree.item(item)['values']
            
            # Helper function to safely convert response time
            def safe_float_conversion(time_str):
                try:
                    if time_str == '-' or time_str == '' or time_str is None:
                        return 0
                    # Remove 'ms' suffix and convert to float
                    time_str = str(time_str).replace('ms', '').strip()
                    return float(time_str) if time_str else 0
                except (ValueError, TypeError):
                    return 0
            
            # Parse values based on current column structure
            if len(values) >= 6:  # Has all columns including banner
                if show_banner:
                    # Host, Port, Protocol, Status, Service, Banner, Response Time
                    result = {
                        'host': str(values[0]) if len(values) > 0 else 'Unknown',
                        'port': int(values[1]) if len(values) > 1 and str(values[1]).isdigit() else 0,
                        'protocol': str(values[2]) if len(values) > 2 else 'Unknown',
                        'status': str(values[3]) if len(values) > 3 else 'Unknown',
                        'service': str(values[4]) if len(values) > 4 else 'Unknown',
                        'banner': str(values[5]) if len(values) > 5 else 'No banner',
                        'response_time': safe_float_conversion(values[6]) if len(values) > 6 else 0
                    }
                else:
                    # Host, Port, Protocol, Status, Service, Response Time (no banner)
                    result = {
                        'host': str(values[0]) if len(values) > 0 else 'Unknown',
                        'port': int(values[1]) if len(values) > 1 and str(values[1]).isdigit() else 0,
                        'protocol': str(values[2]) if len(values) > 2 else 'Unknown',
                        'status': str(values[3]) if len(values) > 3 else 'Unknown',
                        'service': str(values[4]) if len(values) > 4 else 'Unknown',
                        'banner': 'No banner',
                        'response_time': safe_float_conversion(values[5]) if len(values) > 5 else 0
                    }
            else:
                # Fallback for incomplete data
                result = {
                    'host': str(values[0]) if len(values) > 0 else 'Unknown',
                    'port': int(values[1]) if len(values) > 1 and str(values[1]).isdigit() else 0,
                    'protocol': str(values[2]) if len(values) > 2 else 'Unknown',
                    'status': str(values[3]) if len(values) > 3 else 'Unknown',
                    'service': str(values[4]) if len(values) > 4 else 'Unknown',
                    'banner': 'No banner',
                    'response_time': 0
                }
            
            scan_results.append(result)
        
        # Create scan data for export
        scan_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'host_input': 'Manual Export',
            'port_input': 'N/A',
            'protocol': 'N/A',
            'is_cidr': False,
            'resolved_ip': 'N/A'
        }
        
        # Export based on format
        if export_format == "CSV":
            export_manual_csv(file_path, scan_data, scan_results)
        elif export_format == "TXT":
            export_manual_txt(file_path, scan_data, scan_results)
        elif export_format == "JSON":
            export_manual_json(file_path, scan_data, scan_results)
        
        messagebox.showinfo("Export Complete", f"Results exported successfully to:\n{file_path}")
        
    except Exception as e:
        messagebox.showerror("Export Error", f"Failed to export results:\n{str(e)}")

def export_manual_csv(file_path, scan_data, scan_results):
    """Export results to CSV format for manual export"""
    with open(file_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(["Host", "Port", "Protocol", "Status", "Service", "Banner", "Response Time (ms)"])
        
        # Write results
        for result in scan_results:
            writer.writerow([
                result['host'],
                result['port'],
                result['protocol'],
                result['status'],
                result['service'],
                result.get('banner', 'No banner'),
                result['response_time'] if result['response_time'] > 0 else ""
            ])

def export_manual_txt(file_path, scan_data, scan_results):
    """Export results to TXT format for manual export"""
    with open(file_path, "w", encoding='utf-8') as f:
        f.write("=" * 50 + "\n")
        f.write(f"Port Scan Results Export\n")
        f.write(f"Generated: {scan_data['timestamp']}\n")
        f.write(f"Total Results: {len(scan_results)}\n")
        f.write("=" * 50 + "\n\n")
        
        # Group results by host
        host_results = {}
        for result in scan_results:
            host = result['host']
            if host not in host_results:
                host_results[host] = []
            host_results[host].append(result)
        
        for host, results in host_results.items():
            f.write(f"Host: {host}\n")
            f.write("-" * 30 + "\n")
            for result in results:
                status_text = f"{result['protocol']} Port {result['port']} is {result['status']}"
                if result['service'] and result['service'] != 'Unknown':
                    status_text += f" (Service: {result['service']})"
                if result.get('banner') and result['banner'] not in ['No banner', 'Unknown']:
                    status_text += f" - Banner: {result['banner']}"
                if result['response_time'] > 0:
                    status_text += f" - {result['response_time']}ms"
                f.write(status_text + "\n")
            f.write("\n")

def export_manual_json(file_path, scan_data, scan_results):
    """Export results to JSON format for manual export"""
    export_data = {
        "export_info": {
            "timestamp": scan_data['timestamp'],
            "export_type": "Manual Export",
            "total_results": len(scan_results)
        },
        "results": scan_results,
        "summary": {
            "total_hosts": len(set(r['host'] for r in scan_results)),
            "total_ports": len(scan_results),
            "open_ports": len([r for r in scan_results if r['status'] == 'OPEN']),
            "closed_ports": len([r for r in scan_results if r['status'] == 'CLOSED']),
            "filtered_ports": len([r for r in scan_results if 'FILTERED' in r['status']]),
            "error_ports": len([r for r in scan_results if r['status'] == 'ERROR'])
        }
    }
    
    with open(file_path, "w", encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

def update_export_button_visibility():
    """Update visibility of export button based on scan results"""
    if hasattr(root, 'export_button') and hasattr(root, 'results_tree'):
        if root.results_tree.get_children():
            # Show export button if there are results
            root.export_button.pack(side="left", padx=(0, 15), after=root.clear_button)
            root.export_button.config(state=tk.NORMAL)
        else:
            # Hide export button if no results
            root.export_button.pack_forget()
            root.export_button.config(state=tk.DISABLED)

def clear_results_tree():
    """Clear the results tree"""
    for item in root.results_tree.get_children():
        root.results_tree.delete(item)
    root.clear_button.config(state=tk.DISABLED)
    # Reset progress bar and status when clearing
    root.progress_var.set(0)
    root.progress_percentage.pack_forget()  # Hide percentage when clearing
    root.progress_bar.pack_configure(padx=0)  # Reset progress bar padding
    root.status_label.config(text="Ready")
    # Reset UI state
    root.check_button.config(state=tk.NORMAL)
    root.stop_button.pack_forget()  # Hide stop button when clearing results
    root.stop_button.config(state=tk.NORMAL, text="Stop Scan")  # Reset stop button state
    stop_scan_event.clear()
    
    # Hide export button when clearing results
    update_export_button_visibility()

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
    current_columns = root.results_tree['columns']
    for column in current_columns:
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
    
    # Get current column structure
    current_columns = root.results_tree['columns']
    
    # Categorize items based on search criteria
    for item in root.results_tree.get_children():
        values = root.results_tree.item(item)['values']
        if not values or len(values) < len(current_columns):
            continue
            
        # Create searchable text from all values
        searchable_text = " ".join(str(val) for val in values).lower()
        
        # Text search filter
        show_item = True
        if search_term:
            if search_term not in searchable_text:
                show_item = False
        
        # Determine original tag based on status (which should be the 4th column)
        if len(values) >= 4:
            status = values[3]  # Status is always the 4th column
            if status == 'OPEN':
                original_tag = "open"
            elif status == 'CLOSED':
                original_tag = "closed"
            elif status == 'ERROR':
                original_tag = "error"
            else:
                original_tag = "filtered"
        else:
            original_tag = "normal"
        
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
    root.geometry("1200x660")  # Reduced width since OS Info column is removed

    menubar = Menu(root)
    file_menu = Menu(menubar, tearoff=0)
    file_menu.add_command(label="Open Log Directory", command=open_log_directory, accelerator="(Ctrl)+O)")
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit, accelerator="(Ctrl+Q)")
    menubar.add_cascade(label="File", menu=file_menu)

    edit_menu = Menu(menubar, tearoff=0)
    edit_menu.add_command(label="Settings", command=lambda: open_settings_window(root, config, "Defaults"), accelerator="(Ctrl+S)")
    menubar.add_cascade(label="Edit", menu=edit_menu)

    # Add Tools menu with Ping option
    tools_menu = Menu(menubar, tearoff=0)
    tools_menu.add_command(label="Ping", command=lambda: open_ping_window(root), accelerator="(Ctrl+P)")
    menubar.add_cascade(label="Tools", menu=tools_menu)

    help_menu = Menu(menubar, tearoff=0)
    help_menu.add_command(label="Documentation", command=open_documentation, accelerator="(Ctrl+D)")
    menubar.add_cascade(label="Help", menu=help_menu)

    root.config(menu=menubar)
    
    # Bind keyboard shortcuts
    root.bind('<Control-o>', lambda e: open_log_directory())
    root.bind('<Control-O>', lambda e: open_log_directory())
    root.bind('<Control-q>', lambda e: root.quit())
    root.bind('<Control-Q>', lambda e: root.quit())
    root.bind('<Control-s>', lambda e: open_settings_window(root, config, "Defaults"))
    root.bind('<Control-S>', lambda e: open_settings_window(root, config, "Defaults"))
    root.bind('<Control-p>', lambda e: open_ping_window(root))
    root.bind('<Control-P>', lambda e: open_ping_window(root))
    root.bind('<Control-d>', lambda e: open_documentation())
    root.bind('<Control-D>', lambda e: open_documentation())

    # Advanced mode header frame (initially hidden)
    root.advanced_header_frame = tk.Frame(root, bg="#e74c3c", height=35)
    # Don't pack initially - will be shown when advanced mode is enabled
    
    # Header content
    header_content = tk.Frame(root.advanced_header_frame, bg="#e74c3c")
    header_content.pack(fill="both", expand=True, padx=15, pady=8)
    
    # Warning icon and text
    warning_icon = tk.Label(header_content, text="⚠️", bg="#e74c3c", fg="white", 
                           font=("Segoe UI", 12, "bold"))
    warning_icon.pack(side="left")
    
    warning_text = tk.Label(header_content, text="ADVANCED FEATURES ENABLED", 
                           bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"))
    warning_text.pack(side="left", padx=(8, 0))
    
    # Feature indicator (will be updated dynamically)
    root.feature_indicator = tk.Label(header_content, text="", bg="#e74c3c", fg="white", 
                                     font=("Segoe UI", 9))
    root.feature_indicator.pack(side="left", padx=(15, 0))
    
    # Settings button on the right
    settings_btn = tk.Button(header_content, text="Settings", bg="#c0392b", fg="white",
                            font=("Segoe UI", 9), relief="flat", padx=10, pady=2,
                            activebackground="#a93226",
                            command=lambda: open_settings_window(root, config, "Advanced"))
    settings_btn.pack(side="right")

    # Input section
    root.input_frame = tk.Frame(root, bg="#f8f8f8")
    root.input_frame.pack(padx=12, pady=(15, 10), fill="x")

    # Host input
    host_frame = tk.Frame(root.input_frame, bg="#f8f8f8")
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
    port_protocol_frame = tk.Frame(root.input_frame, bg="#f8f8f8")
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
    button_frame = tk.Frame(root.input_frame, bg="#f8f8f8")
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
    root.clear_button.pack(side="left", padx=(0, 10))
    
    # Export button (initially hidden)
    root.export_button = tk.Button(button_frame, text="Export Results", font=("Segoe UI", 10), 
                                  command=export_current_results, state=tk.DISABLED, bg="#f39c12", 
                                  fg="white", activebackground="#e67e22", relief="flat", padx=20, pady=5)
    # Don't pack initially - will be shown when scan results are available
    
    # Profile indicator label (positioned to the far right)
    root.profile_label = tk.Label(button_frame, text="", font=("Segoe UI", 10, "bold"), 
                                 relief="solid", padx=12, pady=5, borderwidth=1)
    root.profile_label.pack(side="right", padx=(15, 0))

    # Filter section
    root.filter_frame = tk.LabelFrame(root, text="Search Results", bg="#f8f8f8", font=("Segoe UI", 10, "bold"))
    root.filter_frame.pack(padx=12, pady=(0, 10), fill="x")

    filter_content = tk.Frame(root.filter_frame, bg="#f8f8f8")
    filter_content.pack(padx=10, pady=5, fill="x")

    # Search box
    tk.Label(filter_content, text="Search:", bg="#f8f8f8", font=("Segoe UI", 10)).pack(side="left")
    root.search_var = tk.StringVar()
    search_entry = tk.Entry(filter_content, textvariable=root.search_var, font=("Segoe UI", 10), width=30)
    search_entry.pack(side="left", padx=(5, 0))
    search_entry.bind('<KeyRelease>', lambda e: filter_results())

    # Results tree view
    root.results_frame = tk.Frame(root, bg="#f8f8f8")
    root.results_frame.pack(padx=12, pady=(0, 10), fill="both", expand=True)

    # Create Treeview with dynamic columns based on config
    dynamic_columns = get_dynamic_columns(config)
    root.results_tree = ttk.Treeview(root.results_frame, columns=dynamic_columns, show='headings', height=15)

    # Define column properties
    column_widths = {
        'Host': 120,
        'Port': 70,
        'Protocol': 70,
        'Status': 100,
        'Service': 120,
        'Banner': 200,
        'Response Time': 100
    }
    
    # Configure columns that are present
    for col in dynamic_columns:
        root.results_tree.column(col, width=column_widths.get(col, 100), 
                                anchor='center' if col != 'Banner' else 'w')
        root.results_tree.heading(col, text=col, 
                                 command=lambda c=col: toggle_sort(c))

    # Add scrollbars using grid layout
    root.results_tree.grid(row=0, column=0, sticky="nsew")
    
    v_scrollbar = ttk.Scrollbar(root.results_frame, orient="vertical", command=root.results_tree.yview)
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    root.results_tree.configure(yscrollcommand=v_scrollbar.set)
    
    h_scrollbar = ttk.Scrollbar(root.results_frame, orient="horizontal", command=root.results_tree.xview)
    h_scrollbar.grid(row=1, column=0, sticky="ew")
    root.results_tree.configure(xscrollcommand=h_scrollbar.set)

    # Configure grid weights
    root.results_frame.grid_rowconfigure(0, weight=1)
    root.results_frame.grid_columnconfigure(0, weight=1)

    # Configure tags for color coding
    root.results_tree.tag_configure("open", foreground="#27ae60", font=("Segoe UI", 10, "bold"))
    root.results_tree.tag_configure("closed", foreground="#7f8c8d")
    root.results_tree.tag_configure("filtered", foreground="#9b59b6")
    root.results_tree.tag_configure("error", foreground="#e74c3c", font=("Segoe UI", 10, "italic"))
    root.results_tree.tag_configure("hidden", foreground="#ffffff")

    # Progress bar and status frame
    root.progress_frame = tk.Frame(root, bg="#f8f8f8")
    root.progress_frame.pack(padx=12, pady=(0, 10), fill="x")
    
    # Status label
    root.status_label = tk.Label(root.progress_frame, text="Ready", bg="#f8f8f8", font=("Segoe UI", 9))
    root.status_label.pack(side="left")
    
    # Progress bar container (for progress bar + percentage)
    progress_container = tk.Frame(root.progress_frame, bg="#f8f8f8")
    progress_container.pack(side="right", padx=(10, 0))
    
    # Percentage label (initially hidden)
    root.progress_percentage = tk.Label(progress_container, text="0%", bg="#f8f8f8", font=("Segoe UI", 9, "bold"), fg="#2c3e50", width=4)
    # Don't pack initially - will be shown when scan starts
    
    # Progress bar
    root.progress_var = tk.DoubleVar()
    root.progress_bar = ttk.Progressbar(progress_container, variable=root.progress_var, maximum=100, length=200)
    root.progress_bar.pack(side="left")  # Pack initially so it shows when app starts

    # Initialize the profile indicator and advanced window appearance
    update_profile_indicator()
    update_advanced_window_appearance()
    
    # Initialize export button visibility
    update_export_button_visibility()

    root.mainloop()

if __name__ == "__main__":
    run_gui()