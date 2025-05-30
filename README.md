# Port Checker Plus

A modern, feature-rich network port scanning tool with an intuitive GUI built in Python. Port Checker Plus provides comprehensive port scanning capabilities with advanced results visualization, real-time filtering, and detailed reporting.

## 🚀 Features

### Core Scanning
- **Multi-Protocol Support**: TCP, UDP, and combined TCP/UDP scanning
- **Flexible Port Input**: Single ports, ranges (1-100), or comma-separated lists (80,443,22)
- **DNS Resolution**: Automatic hostname resolution with configurable retry attempts
- **Response Time Measurement**: Real-time connection speed measurement in milliseconds
- **Threaded Scanning**: Fast, concurrent port scanning for improved performance

### Enhanced User Interface
- **Sortable Results Table**: Click column headers to sort by port, protocol, status, service, or response time
- **Real-Time Search**: Instantly filter results by port number, service, or status
- **Color-Coded Results**: 
  - 🟢 **Open Ports** - Green and bold
  - ⚫ **Closed Ports** - Gray text
  - 🟣 **Filtered Ports** - Purple text (UDP)
  - ❌ **Errors** - Red italic text
- **Progress Tracking**: Real-time progress bar and status updates
- **Professional Layout**: Clean, modern interface with proper spacing and organization

### Advanced Configuration
- **Customizable Timeouts**: Adjust connection timeout from 0.1 to 10 seconds
- **Default Values**: Set default hosts and port ranges for quick scanning
- **Show Open Only**: Option to display only open ports for cleaner results
- **Protocol Selection**: Choose between TCP, UDP, or both protocols

### Export & Reporting
- **Automatic Export**: Optional automatic saving of scan results
- **Timestamped Logs**: Each scan includes timestamp and target information
- **Configurable Location**: Choose custom directory for export files
- **Cross-Platform Paths**: Intelligent config file placement per operating system

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- tkinter (usually included with Python)

### Clone Repository
```bash
git clone https://github.com/jackworthen/portCheckerPlus.git
cd portCheckerPlus
```

### Run Application
```bash
python portCheckerPlus.py
```

## 🎯 Usage

### Basic Scanning
1. **Enter Target Host**: IP address or hostname (e.g., `google.com`, `192.168.1.1`)
2. **Specify Ports**: Enter ports in any of these formats:
   - Single port: `80`
   - Port range: `1-1000`
   - Multiple ports: `80,443,22,21`
   - Combined: `1-100,443,8080`
3. **Select Protocol**: Choose TCP, UDP, or TCP/UDP
4. **Click "Check Ports"** to start scanning

### Advanced Features

#### Search and Filter
- Use the **Search** box to filter results in real-time
- Search works across port numbers, protocols, status, and service names
- Results update automatically as you type

#### Sorting Results
- Click any column header to sort results
- **Port** and **Response Time** columns sort numerically
- **Protocol**, **Status**, and **Service** columns sort alphabetically
- Click again to reverse sort order (indicated by ↑↓ arrows)

#### Configuration
Access advanced settings via **Edit → Settings**:

**General Tab:**
- Scan protocol selection
- Connection timeout adjustment
- DNS retry count
- Display options (show open ports only)

**Defaults Tab:**
- Set default host and port values
- Quick setup for repeated scans

**Export Tab:**
- Enable/disable automatic result export
- Choose export directory
- Results saved to `psp_log.txt`

## 📊 Sample Results

```
Port    Protocol    Status    Service      Response Time
22      TCP         OPEN      ssh          15.2ms
80      TCP         OPEN      http         8.7ms
443     TCP         OPEN      https        12.1ms
8080    TCP         CLOSED    http-proxy   -
```

## ⚙️ Configuration Files

Configuration is automatically stored in platform-appropriate locations:
- **Windows**: `%APPDATA%\PortCheckerPlus\config.json`
- **macOS**: `~/Library/Application Support/PortCheckerPlus/config.json`
- **Linux**: `~/.config/PortCheckerPlus/config.json`

## 🛠️ Building Executable

To create a standalone executable using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=psp_icon2.ico portCheckerPlus.py
```

## 🎨 Customization

### Adding Custom Icons
Place your icon file as `psp_icon2.ico` in the same directory as the script for custom window icons.

### Modifying Colors
Edit the color configuration in the `run_gui()` function:
```python
root.results_tree.tag_configure("open", foreground="#27ae60")  # Green for open ports
root.results_tree.tag_configure("closed", foreground="#7f8c8d")  # Gray for closed ports
```

## 🐛 Troubleshooting

### Common Issues

**DNS Resolution Fails**
- Check network connectivity
- Verify hostname spelling
- Increase DNS retry count in settings

**Slow Scanning**
- Reduce timeout value for faster scans
- Use smaller port ranges
- Check network latency to target

**Export Issues**
- Verify export directory exists and is writable
- Check disk space availability
- Ensure proper file permissions

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Jack Worthen**
- GitHub: [@jackworthen](https://github.com/jackworthen)

## 🙏 Acknowledgments

- Built with Python's tkinter for cross-platform GUI
- Socket programming for network connectivity testing
- Threading implementation for performance optimization

---

⭐ Star this repository if you found it helpful!
