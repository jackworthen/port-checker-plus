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
- ⚡ **High-Performance Threading** - Intelligent system-aware threading (20-2000+ threads)
- 🧠 **Smart Resource Management** - Automatic optimization based on system capabilities
- 🎲 **Port Randomization** - Randomize scan order for stealth operations
- ⏱️ **Variable Delays** - Add random delays between scans to avoid detection

### 🎨 **Modern User Interface**
- 📊 **Real-time Progress Tracking** - Live progress bar and status updates
- 🔍 **Advanced Search & Filtering** - Find specific results instantly
- 🎨 **Color-coded Results** - Visual distinction between open, closed, and filtered ports
- 📋 **Sortable Columns** - Click any column header to sort results
- 🛑 **Responsive Stop Button** - Cancel large scans instantly

### ⚡ **Enhanced Performance**
- 🚀 **Intelligent Threading** - System calculates optimal thread limits automatically
- 🎛️ **Tiered Performance Options:**
  - 📱 **Recommended (20-150)** - Optimal for most users
  - 🔥 **Safe Max (up to 1000)** - High-performance scanning without warnings
  - 🚄 **Manual Override (up to 2000+)** - Maximum speed for power users
- 🖥️ **System-Aware Scaling** - Adapts to your hardware (CPU cores, file descriptors)
- 📊 **Optimized Batch Processing** - Scales efficiently with thread count

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
- 🧵 **Intelligent Thread Control** - System-optimized concurrent scanning
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

3. **High-Performance Scanning:**
   - Go to **Edit → Settings → General**
   - Increase **Max Concurrent Threads** (e.g., 500-1000)
   - Perfect for internal networks and large port ranges

4. **Stop Large Scans:**
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
- 🧵 **Max Concurrent Threads** - **NEW!** Intelligent system-aware threading:
  - 📱 **Recommended Range** - Automatically calculated for your system
  - 🔥 **Safe Maximum** - Up to 1000 threads without warnings
  - 🚄 **Manual Override** - Up to 2000+ threads for extreme performance
  - 🧠 **System Optimization** - Based on CPU cores and file descriptors
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

## ⚡ Performance Guide

### 🎯 **Choosing Thread Count**

| Scenario | Recommended Threads | Notes |
|----------|-------------------|-------|
| 🏠 **Home Network** | 20-50 | Conservative, good for WiFi |
| 🏢 **Corporate Network** | 100-300 | Balance speed and stealth |
| 🔥 **Internal Auditing** | 500-1000 | Maximum speed, no rate limiting |
| 🚄 **Extreme Performance** | 1000+ | High-end systems, controlled environments |

### 📊 **System Requirements by Thread Count**

| Thread Count | RAM Usage | File Descriptors | Best For |
|-------------|-----------|------------------|----------|
| 20-100 | ~20-100MB | ~50-200 | Most users |
| 100-500 | ~100-500MB | ~200-1000 | Power users |
| 500-1000 | ~500MB-1GB | ~1000-2000 | Performance systems |
| 1000+ | ~1GB+ | ~2000+ | Extreme use cases |

### 🛠️ **Optimization Tips**
- 🖥️ **For older systems:** Stick to recommended range (20-150 threads)
- 🚀 **For modern systems:** 500-1000 threads work great for internal networks
- 🌐 **For external scanning:** Use lower counts (50-200) to avoid rate limiting
- ⚡ **For maximum speed:** Disable variable delays and use port randomization

---

## 🔒 Ethical Usage

> ⚠️ **Important:** This tool is designed for legitimate network administration and security testing purposes only.

### ✅ **Appropriate Use Cases:**
- 🏢 Testing your own networks and systems
- 🔍 Security audits with proper authorization
- 📚 Educational and learning purposes
- 🛠️ Network troubleshooting and administration
- 🚄 High-performance internal network scanning

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
- **Threading:** ThreadPoolExecutor with intelligent resource management
- **Performance:** System-aware thread optimization and batch processing
- **Network:** Socket-based scanning with timeout controls

### ⚡ **Threading Engine**
- 🧠 **Intelligent Limits** - Automatically calculates optimal thread count based on:
  - 🖥️ CPU core count (20x scaling for I/O-bound tasks)
  - 📁 File descriptor limits (20% utilization for safety)
  - 🖱️ Platform optimization (Windows vs Unix handling)
- 🎛️ **Manual Override** - Allows up to 2000+ threads for extreme performance
- 📊 **Batch Processing** - Scales batch size with thread count for efficiency
- 🛑 **Responsive Cancellation** - Immediate stop capability even with high thread counts

### 📦 **Dependencies**
- `tkinter` - GUI framework (included with Python)
- `socket` - Network communication
- `threading` - Concurrent execution
- `json` - Configuration management
- `csv`, `xml` - Export formats
- `ipaddress` - CIDR network parsing
- `concurrent.futures` - Advanced thread management

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
4. Test thoroughly (especially with different thread counts)
5. Submit a pull request

### 💡 **Feature Ideas**
- 🚀 Additional performance optimizations
- 🎨 UI/UX improvements
- 📊 New export formats
- 🔒 Enhanced security features

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
