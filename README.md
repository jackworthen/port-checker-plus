# Port Checker Plus

A professional, feature-rich port scanning tool with a modern graphical user interface built in Python. Port Checker Plus provides an intuitive way to scan TCP and UDP ports on remote hosts with advanced configuration options and export capabilities.

## 🌟 Features

### Core Functionality
- **Multi-Protocol Support**: Scan TCP, UDP, or both protocols simultaneously
- **Flexible Port Specification**: Support for individual ports, ranges, and comma-separated lists
- **Real-Time Results**: Live scanning progress with visual progress bar
- **DNS Resolution**: Automatic hostname resolution with configurable retry attempts
- **Service Detection**: Identifies services running on open ports

### Advanced Options
- **Customizable Timeouts**: Adjustable connection timeout settings (0.1-10.0 seconds)
- **Filtered Results**: Option to show only open ports for cleaner output
- **Export Functionality**: Automatic export of scan results to text files
- **Default Configurations**: Save frequently used hosts and port ranges
- **Cross-Platform**: Works on Windows, macOS, and Linux

### Professional UI
- **Tabbed Settings Interface**: Organized settings across General, Defaults, and Export tabs
- **Progress Tracking**: Real-time scan progress with status updates
- **Syntax Highlighting**: Color-coded results (green for open ports)
- **Responsive Design**: Clean, modern interface with proper spacing and typography

## 🚀 Installation

### Prerequisites
- Python 3.6 or higher
- tkinter (usually included with Python)

### Option 1: Run from Source
1. Clone the repository:
   ```bash
   git clone https://github.com/jackworthen/port-checker-plus.git
   cd port-checker-plus
   ```

2. Run the application:
   ```bash
   python portCheckerPlus.py
   ```

## 📖 Usage

### Basic Port Scanning
1. Enter the target host (IP address or hostname)
2. Specify ports using any of these formats:
   - Single port: `80`
   - Multiple ports: `80,443,22`
   - Port range: `1-100`
   - Combined: `80,443,1000-2000`
3. Select the protocol (TCP, UDP, or TCP/UDP)
4. Click "Check Ports" to start scanning

### Port Specification Examples
```
22,80,443           # SSH, HTTP, HTTPS
1-1000              # Ports 1 through 1000
21,22,23,80-90      # FTP, SSH, Telnet, and range 80-90
3389,5900,22        # RDP, VNC, SSH
```

### Settings Configuration

#### General Tab
- **Scan Protocol**: Choose between TCP, UDP, or TCP/UDP scanning
- **Connection Timeout**: Set timeout for connection attempts (0.1-10.0 seconds)
- **DNS Retry Count**: Configure hostname resolution retry attempts (0-5)
- **Display Options**: Toggle to show only open ports in results

#### Defaults Tab
- **Default Host**: Set a default hostname or IP address
- **Default Ports**: Set default port ranges for quick scanning

#### Export Tab
- **Enable Export**: Automatically save scan results to files
- **Export Directory**: Choose where to save result files
- **File Format**: Results saved as `psp_log.txt` with timestamps

## 🔧 Configuration

Configuration is automatically saved in platform-appropriate locations:
- **Windows**: `%APPDATA%/PortCheckerPlus/config.json`
- **macOS**: `~/Library/Application Support/PortCheckerPlus/config.json`
- **Linux**: `~/.config/PortCheckerPlus/config.json`

### Default Configuration
```json
{
    "timeout": 0.3,
    "export_results": false,
    "export_directory": "current_directory",
    "default_host": "",
    "default_ports": "",
    "retry_count": 2,
    "scan_protocol": "TCP",
    "show_open_only": false
}
```

## 📊 Output Format

### Console Output
```
Resolving hostname: example.com
Resolved IP: 93.184.216.34
Attempt: 1

TCP Port 22 is CLOSED (Service: ssh)
TCP Port 80 is OPEN (Service: http)
TCP Port 443 is OPEN (Service: https)

Scan complete.
Number of ports checked: 3
```

### Export File Format
```
===== Scan Results: 2025-05-27 14:30:15 =====
Host: example.com
Resolved IP: 93.184.216.34
Ports: 22,80,443

TCP Port 22 is CLOSED (Service: ssh)
TCP Port 80 is OPEN (Service: http)
TCP Port 443 is OPEN (Service: https)
```

## 🛠️ Building from Source

### Creating Standalone Executable
Use PyInstaller to create a standalone executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable (with icon if available)
pyinstaller --onefile --windowed --icon=psp_icon2.ico portCheckerPlus.py

# The executable will be in the dist/ directory
```

### Dependencies
- **tkinter**: GUI framework (included with Python)
- **socket**: Network operations (built-in)
- **threading**: Multi-threaded scanning (built-in)
- **json**: Configuration management (built-in)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
6. Push to the branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

## 📋 Roadmap

- [ ] IPv6 support
- [ ] Custom port scan profiles
- [ ] Network range scanning (CIDR notation)
- [ ] XML/JSON export formats
- [ ] Scan scheduling and automation
- [ ] Performance optimization for large port ranges
- [ ] Plugin system for custom protocols

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python's tkinter for cross-platform GUI compatibility
- Inspired by traditional network scanning tools like nmap
- Icons and design influenced by modern application interfaces

## 📞 Support

If you encounter any problems or have suggestions:
- Open an [issue](https://github.com/jackworthen/port-checker-plus/issues)

---

**Port Checker Plus** - Professional port scanning made simple and accessible.
