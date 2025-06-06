# 🚀 Port Checker Plus

**🔍 A powerful, user-friendly network port scanner with a modern GUI**

*Scan single hosts or entire networks with style!*

[📖 Documentation](#-features) • [🚀 Quick Start](#-quick-start) • [⚙️ Configuration](#️-configuration) • [🤝 Contributing](#-contributing)

---

## ✨ Features

### 🎯 **Core Scanning Capabilities**
- 🖥️ **Single Host Scanning** - Scan individual IP addresses or hostnames
- 🌐 **CIDR Network Scanning** - Scan entire network ranges (e.g., `192.168.1.0/24`)
- 🔄 **Multi-Protocol Support** - TCP, UDP, or both simultaneously
- ⚡ **Concurrent Threading** - Configurable thread count (1-100) for optimal performance
- 🎲 **Port Randomization** - Randomize scan order for stealth operations
- ⏱️ **Variable Delays** - Add random delays between scans to avoid detection

### 🎨 **Modern User Interface**
- 📊 **Real-time Progress Tracking** - Live progress bar and status updates
- 🔍 **Advanced Search & Filtering** - Find specific results instantly
- 🎨 **Color-coded Results** - Visual distinction between open, closed, and filtered ports
- 📋 **Sortable Columns** - Click any column header to sort results
- 🛑 **Responsive Stop Button** - Cancel large scans instantly

### 🎯 **Smart Port Profiles**
Choose from pre-configured port sets for common scenarios:

| Profile | Ports | Use Case |
|---------|-------|----------|
| 🌐 **Web Servers** | 80, 443, 8080, 8443... | Web application testing |
| 📧 **Mail Servers** | 25, 110, 143, 993, 995... | Email server discovery |
| 📁 **File Transfer** | 21, 22, 69, 873... | FTP/SSH services |
| 🗄️ **Database** | 3306, 5432, 27017... | Database server scanning |
| 🎮 **Gaming** | 27015, 25565, 19132... | Game server discovery |
| 🔒 **Security Scan** | 21, 22, 23, 80, 443... | Security assessment |

### 📊 **Export & Logging**
- 📝 **Multiple Formats** - Export to TXT, CSV, JSON, or XML
- 📈 **Detailed Reports** - Timestamps, response times, service detection
- 🗂️ **Automatic Logging** - Optional automatic result logging
- 🧹 **Log Management** - Built-in log cleanup tools

### ⚙️ **Advanced Configuration**
- ⏱️ **Timeout Control** - Configurable connection timeouts (0.1-10.0s)
- 🔄 **DNS Retry Logic** - Automatic hostname resolution retries
- 🌐 **CIDR Limits** - Safety limits for large network scans
- 🎛️ **Thread Control** - Fine-tune concurrent scanning threads
- 👁️ **Filter Options** - Show only open ports option

---

## 🚀 Quick Start

### 📋 Prerequisites
- Python 3.7 or higher
- tkinter (usually included with Python)

### 💾 Installation

1. **Clone the repository:**
```bash
git clone https://github.com/jackworthen/port-checker-plus.git
cd port-checker-plus
```

2. **Run the application:**
```bash
python portCheckerPlus.py
```

### 🎯 Basic Usage

1. **Single Host Scan:**
   - Enter hostname or IP: `google.com` or `192.168.1.1`
   - Enter ports: `80,443,22` or `1-1000`
   - Click **Check Ports**

2. **Network Range Scan:**
   - Enter CIDR notation: `192.168.1.0/24`
   - Select port profile or enter custom ports
   - Click **Check Ports**

3. **Stop Large Scans:**
   - Click **Stop Scan** button
   - Results collected so far will be displayed

---

## ⚙️ Configuration

### 🎛️ Settings Panel
Access via **Edit → Settings** to customize:

#### 📊 **Defaults Tab**
- 🎯 **Port Profiles** - Quick selection of common port sets
- 🌐 **Default Host/Network** - Pre-fill scan targets
- 🎮 **Default Ports** - Your go-to port ranges

#### 🔧 **General Tab**
- 🔌 **Protocol Selection** - TCP, UDP, or both
- ⏱️ **Connection Timeout** - Fine-tune scan speed vs accuracy
- 🔄 **DNS Retry Count** - Handle unreliable DNS
- 🧵 **Max Concurrent Threads** - Balance speed and resources
- 🌐 **Max Hosts per CIDR** - Safety limit for large networks
- 👁️ **Display Options** - Show only open ports

#### 🕵️ **Advanced Tab**
- 🎲 **Port Randomization** - Randomize scan order
- ⏱️ **Variable Delays** - Add 300-700ms random delays
- ⚠️ **Responsible Use Warning** - Ethical guidelines

#### 📊 **Logging Tab**
- 📝 **Export Formats** - TXT, CSV, JSON, XML
- 📁 **Export Directory** - Choose save location
- 🧹 **Log Management** - Clear old log files

---

## 🔒 Ethical Usage

> ⚠️ **Important:** This tool is designed for legitimate network administration and security testing purposes only.

### ✅ **Appropriate Use Cases:**
- 🏢 Testing your own networks and systems
- 🔍 Security audits with proper authorization
- 📚 Educational and learning purposes
- 🛠️ Network troubleshooting and administration

### ❌ **Prohibited Activities:**
- 🚫 Scanning networks without permission
- 🚫 Unauthorized penetration testing
- 🚫 Malicious network reconnaissance
- 🚫 Any illegal or unethical activities

**Always ensure you have explicit permission before scanning any network that you don't own.**

---

## 🛠️ Technical Details

### 🏗️ **Architecture**
- **Language:** Python 3.7+
- **GUI Framework:** Tkinter
- **Threading:** ThreadPoolExecutor with configurable workers
- **Network:** Socket-based scanning with timeout controls

### 📦 **Dependencies**
- `tkinter` - GUI framework (included with Python)
- `socket` - Network communication
- `threading` - Concurrent execution
- `json` - Configuration management
- `csv`, `xml` - Export formats

### 🔧 **Configuration Storage**
- **Windows:** `%APPDATA%\PortCheckerPlus\config.json`
- **macOS:** `~/Library/Application Support/PortCheckerPlus/config.json`
- **Linux:** `~/.config/PortCheckerPlus/config.json`

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### 🐛 **Bug Reports**
- Use the [Issues](https://github.com/jackworthen/port-checker-plus/issues) tab
- Include your OS, Python version, and steps to reproduce

### 🔧 **Pull Requests**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with clear commit messages
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

### 💬 **Get Help**
- 📖 [Documentation](https://github.com/jackworthen/port-checker-plus/wiki)
- 🐛 [Issue Tracker](https://github.com/jackworthen/port-checker-plus/issues)
- 💡 [Feature Requests](https://github.com/jackworthen/port-checker-plus/discussions)

---

**🌟 Star this repo if you found it helpful! 🌟**

*Developed by Jack Worthen [@jackworthen](https://github.com/jackworthen)*
