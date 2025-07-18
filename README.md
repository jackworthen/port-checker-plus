# 🚀 Port Checker Plus

**🔍 A powerful, user-friendly network port scanner with advanced stealth capabilities**

*Scan single hosts or entire networks with professional-grade evasion techniques!*

[📖 Documentation](#-features) • [🚀 Quick Start](#-quick-start) • [⚙️ Configuration](#️-configuration) • [🤝 Contributing](#-contributing)

---

## ✨ Features

### 🎯 **Core Scanning Capabilities**
- 🖥️ **Single Host Scanning** - Scan individual IP addresses or hostnames
- 🌐 **CIDR Network Scanning** - Scan entire network ranges (e.g., `192.168.1.0/24`)
- 🔄 **Multi-Protocol Support** - TCP, UDP, or both simultaneously
- ⚡ **High-Performance Threading** - Intelligent system-aware threading (20-2000+ threads)
- 🧠 **Smart Resource Management** - Automatic optimization based on system capabilities

### 🏓 **Network Connectivity Testing**
- 🏓 **Integrated Ping Tool** - Test host connectivity before scanning
- 🎛️ **Configurable Ping Settings** - Customizable packet count (1-100) and timeout (1-30s)
- 📊 **Real-time Ping Results** - Live output display with color-coded status
- 🔄 **Seamless Workflow Integration** - One-click host transfer to port scanner
- 🖥️ **Cross-Platform Support** - Native ping commands on Windows, Linux, and macOS
- 🛑 **Interactive Control** - Start, stop, and clear ping operations
- 📝 **Professional Output** - Clean, organized results without terminal windows

### 🥷 **Advanced Stealth Features**
- 🧩 **Fragmented Packet Scanning** - Split packets across IP fragments to evade basic firewalls and IDS
- 🎲 **Port Randomization** - Randomize scan order for stealth operations
- ⏱️ **Variable Delays** - Add random delays between scans to avoid detection
- 🚨 **Advanced Mode Indicator** - Red window border and title when stealth features are active

### 🎨 **Modern User Interface**
- 📊 **Real-time Progress Tracking** - Live progress bar and status updates
- 🔍 **Advanced Search & Filtering** - Find specific results instantly
- 🎨 **Color-coded Results** - Visual distinction between open, closed, and filtered ports
- 📋 **Sortable Columns** - Click any column header to sort results
- 🛑 **Responsive Stop Button** - Cancel large scans instantly
- 🚨 **Visual Stealth Indicators** - Clear indication when advanced features are active

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
- 📝 **Multiple Formats** - Export results to TXT, CSV or JSON
- 📈 **Detailed Reports** - Timestamps, response times, service detection, scan methods
- 🗂️ **Automatic Logging** - Optional automatic result logging
- 🧹 **Log Management** - Built-in log cleanup tool.

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
- **For Fragmented Scanning:** Administrative/root privileges

### 💾 Installation

1. **Clone the repository:**
```bash
git clone https://github.com/jackworthen/port-checker-plus.git
cd port-checker-plus
```

2. **Run the application:**
```bash
# Standard mode
python portCheckerPlus.py

# For fragmented scanning (requires admin privileges)
# Windows:
# Right-click "Command Prompt" → "Run as administrator"
python portCheckerPlus.py

# Linux/macOS:
sudo python portCheckerPlus.py
```

### 🎯 Basic Usage

1. **Test Connectivity First:**
   - Go to **Tools → 🏓 Ping**
   - Enter hostname or IP: `google.com` or `192.168.1.1`
   - Set packet count and timeout
   - Click **Start Ping** to test connectivity
   - Click **Set Host** to copy to port scanner and close ping tool

2. **Single Host Scan:**
   - Enter hostname or IP: `google.com` or `192.168.1.1`
   - Enter ports: `80,443,22` or `1-1000`
   - Click **Check Ports**

3. **Network Range Scan:**
   - Enter CIDR notation: `192.168.1.0/24`
   - Select port profile or enter custom ports
   - Click **Check Ports**

4. **High-Performance Scanning:**
   - Go to **Edit → Settings → General**
   - Increase **Max Concurrent Threads** (e.g., 500-1000)
   - Perfect for internal networks and large port ranges

5. **Stealth Scanning:**
   - Go to **Edit → Settings → Advanced**
   - Enable **Fragmented Packet Scanning** (requires admin privileges)
   - Enable **Port Randomization** and **Variable Delays**
   - Window will show red border and "ADVANCED MODE" in title

6. **Stop Large Scans:**
   - Click **Stop Scan** button
   - Results collected so far will be displayed

### 🏓 **Ping Tool Workflow**
1. **Open Ping Tool:** **Tools → 🏓 Ping**
2. **Configure Settings:**
   - Enter target host/IP
   - Set packet count (1-100)
   - Set timeout (1-30 seconds)
3. **Test Connectivity:** Click **Start Ping**
4. **Monitor Results:** View real-time ping output
5. **Transfer to Scanner:** Click **Set Host** to copy host and return to main window
6. **Proceed with Scanning:** Host is now ready for port scanning

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
- 🧩 **Fragmented Packet Scanning** - **NEW!** Split packets into IP fragments to evade basic firewalls and IDS
  - ✅ **System Check** - Automatic detection of raw socket availability
  - 🔑 **Privilege Requirement** - Requires administrative privileges
  - 🛡️ **Firewall Evasion** - Bypasses simple packet filters that don't reassemble fragments
- 🎲 **Port Randomization** - Randomize scan order
- ⏱️ **Variable Delays** - Add 300-700ms random delays
- 🚨 **Visual Indicators** - Red window border appears when any advanced feature is enabled
- 🚩 **Service Banner Grabbing** - Provides detailed service version information

#### 📊 **Logging Tab**
- 📝 **Export Formats** - TXT, CSV, JSON, XML
- 📁 **Export Directory** - Choose save location
- 🧹 **Log Management** - **UPDATED!** Always-available log cleanup (no longer hidden when logging is disabled)

#### 📊 **Export Tab**
- 📝 **Export Formats** - TXT, CSV, JSON
- 📁 **Export Directory** - Choose save location

### 🛠️ **Tools Menu**
Access additional utilities via **Tools**:

#### 🏓 **Ping Tool**
- 🎯 **Host/IP Input** - Enter target for connectivity testing
- 🔢 **Packet Count** - Configure number of ping packets (1-100)
- ⏱️ **Timeout Setting** - Set per-packet timeout (1-30 seconds)
- 📊 **Real-time Results** - Live ping output with color coding:
  - ⚫ **Normal Output** - Standard ping responses
  - 🔴 **Error Messages** - Connection failures and timeouts
  - 🔵 **Status Updates** - Operation start/stop notifications
- 🎛️ **Control Buttons:**
  - ▶️ **Start Ping** - Begin connectivity test
  - ⏹️ **Stop Ping** - Interrupt ongoing operation
  - 🧹 **Clear Results** - Clean output display
  - 🔄 **Set Host** - Copy host to main scanner and close ping tool
- 🖥️ **Cross-Platform** - Uses native system ping commands
- 🎨 **Clean Interface** - No terminal windows on any platform

---

## ⚡ Performance Guide

### 🎯 **Choosing Thread Count**

| Scenario | Recommended Threads | Notes |
|----------|-------------------|-------|
| 🏠 **Home Network** | 20-50 | Conservative, good for WiFi |
| 🏢 **Corporate Network** | 100-300 | Balance speed and stealth |
| 🔥 **Internal Auditing** | 500-1000 | Maximum speed, no rate limiting |
| 🚄 **Extreme Performance** | 1000+ | High-end systems, controlled environments |

### 🥷 **Stealth vs Performance Trade-offs**

| Feature | Performance Impact | Stealth Benefit | Best Use Case |
|---------|------------------|-----------------|---------------|
| 🧩 **Fragmented Scanning** | Minimal | High firewall evasion | Bypassing basic packet filters |
| 🎲 **Port Randomization** | None | Medium pattern disruption | Avoiding sequential scan detection |
| ⏱️ **Variable Delays** | High (slower) | High rate limit avoidance | External/remote scanning |

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
- 🧩 **For stealth:** Enable fragmented scanning with administrative privileges
- 🏓 **Before scanning:** Use ping tool to verify target accessibility

---

## 🔒 Ethical Usage & Legal Compliance

> ⚠️ **Critical:** This tool includes advanced evasion techniques that must only be used ethically and legally.

### ✅ **Appropriate Use Cases:**
- 🏢 Testing your own networks and systems
- 🔍 Security audits with proper written authorization
- 📚 Educational and learning purposes in controlled environments
- 🛠️ Network troubleshooting and administration
- 🚄 High-performance internal network scanning
- 🛡️ **Penetration testing with explicit client permission**
- 🏓 **Network connectivity testing and diagnostics**

### ❌ **Prohibited Activities:**
- 🚫 Scanning networks without explicit written permission
- 🚫 Unauthorized penetration testing or security assessments
- 🚫 Malicious network reconnaissance or intelligence gathering
- 🚫 Using advanced evasion techniques against systems you don't own
- 🚫 Any illegal or unethical activities

### 🧩 **Fragmented Scanning Considerations:**
- 🔑 **Administrative Privileges Required** - Raw socket access needs elevated permissions
- 🛡️ **Firewall Evasion** - Specifically designed to bypass basic security controls
- 📝 **Documentation Required** - Always document usage for legitimate security testing
- 🏢 **Internal Use Recommended** - Most effective for controlled environment testing

**⚖️ Legal Disclaimer:** Users are solely responsible for compliance with local, state, federal, and international laws. Advanced evasion features should only be used on networks you own or have explicit written authorization to test.

---

## 🛠️ Technical Details

### 🏗️ **Architecture**
- **Language:** Python 3.7+
- **GUI Framework:** Tkinter
- **Threading:** ThreadPoolExecutor with intelligent resource management
- **Performance:** System-aware thread optimization and batch processing
- **Network:** Socket-based scanning with timeout controls
- **Advanced Features:** Raw socket implementation for packet fragmentation
- **Connectivity Testing:** Cross-platform subprocess ping implementation

### 🏓 **Integrated Ping Tool**
- 🖥️ **Cross-Platform Implementation** - Native system ping commands
- 🔇 **Silent Background Execution** - No terminal windows on Windows
- 📊 **Real-time Output Processing** - Live parsing and display of ping results
- 🎨 **Color-coded Results** - Visual distinction between success, errors, and status
- 🛑 **Responsive Cancellation** - Immediate stop capability with proper cleanup
- 🔄 **Seamless Integration** - One-click host transfer to port scanner
- 🛡️ **Error Handling** - Graceful handling of network failures and invalid hosts

### 🧩 **Fragmented Packet Scanning Engine**
- 🔌 **Raw Socket Implementation** - Low-level packet crafting and transmission
- 📦 **IP Fragment Construction** - Splits TCP/UDP headers across multiple IP fragments
- 🎯 **Automatic Fallback** - Gracefully falls back to standard scanning when fragmented fails
- 🖥️ **Cross-Platform Support** - Windows and Unix-like systems (with admin privileges)
- 🔍 **Response Analysis** - Intelligent interpretation of fragmented responses
- ⚡ **Performance Integration** - Full integration with threading and progress systems

### ⚡ **Threading Engine**
- 🧠 **Intelligent Limits** - Automatically calculates optimal thread count based on:
  - 🖥️ CPU core count (20x scaling for I/O-bound tasks)
  - 📁 File descriptor limits (20% utilization for safety)
  - 🖱️ Platform optimization (Windows vs Unix handling)
- 🎛️ **Manual Override** - Allows up to 2000+ threads for extreme performance
- 📊 **Batch Processing** - Scales batch size with thread count for efficiency
- 🛑 **Responsive Cancellation** - Immediate stop capability even with high thread counts

### 🚨 **Advanced Mode Indicators**
- 🔴 **Visual Window Border** - Red frame appears when any advanced feature is enabled
- 📝 **Dynamic Window Title** - Shows "ADVANCED MODE" with active features list
- 🏷️ **Result Tagging** - Scan results include method tags (Standard vs Fragmented)

### 📦 **Dependencies**
- `tkinter` - GUI framework (included with Python)
- `socket` - Network communication and raw socket access
- `threading` - Concurrent execution
- `json` - Configuration management
- `csv`, `xml` - Export formats
- `ipaddress` - CIDR network parsing
- `concurrent.futures` - Advanced thread management
- `struct` - Binary data handling for packet construction
- `subprocess` - Cross-platform ping implementation

### 🔧 **Configuration Storage**
- **Windows:** `%APPDATA%\PortCheckerPlus\config.json`
- **macOS:** `~/Library/Application Support/PortCheckerPlus/config.json`
- **Linux:** `~/.config/PortCheckerPlus/config.json`

### 🔑 **Privilege Requirements**
- **Standard Scanning:** No special privileges required
- **Ping Tool:** No special privileges required
- **Fragmented Scanning:** Administrative/root privileges for raw socket access
- **Automatic Detection:** System capability checking with helpful error messages

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

### 💬 **Get Help**
- 📖 [Documentation](https://github.com/jackworthen/port-checker-plus/wiki)
- 🐛 [Issue Tracker](https://github.com/jackworthen/port-checker-plus/issues)
- 💡 [Feature Requests](https://github.com/jackworthen/port-checker-plus/discussions)

### 🔧 **Troubleshooting**
- **Fragmented scanning not available?** Ensure you're running with administrative privileges
- **Performance issues?** Check thread count recommendations for your system
- **Advanced mode not showing?** Verify advanced features are enabled in settings
- **Ping tool not working?** Verify network connectivity and target host accessibility
- **Terminal windows appearing?** Ensure you're using the compiled .exe version on Windows

---

**🌟 Star this repo if you found it helpful! 🌟**

*Developed by Jack Worthen [@jackworthen](https://github.com/jackworthen)*
