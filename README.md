# 🚀 Port Checker Plus

**🔍 A modern, feature-rich network port scanner with a beautiful GUI**

*Scan ports like a pro with style and substance!* ✨

---

## 🎯 What is Port Checker Plus?

Port Checker Plus is a **powerful yet user-friendly** network port scanner built with Python and Tkinter. Whether you're a network administrator, security professional, or curious developer, this tool makes port scanning accessible and efficient with its intuitive graphical interface.

### 🌟 Why Choose Port Checker Plus?

- 🎨 **Beautiful Modern UI** - Clean, professional interface that's actually enjoyable to use
- ⚡ **Blazing Fast** - Multi-threaded scanning for optimal performance
- 📊 **Multiple Export Formats** - Save results in TXT, CSV, JSON, or XML
- 🎛️ **Smart Profiles** - Pre-configured port lists for common services
- 🔧 **Highly Customizable** - Extensive settings for power users
- 🛡️ **Cross-Platform** - Works on Windows, macOS, and Linux

---

## ✨ Features That Make You Go "Wow!"

### 🔍 **Scanning Capabilities**
- **TCP & UDP Support** - Scan both protocols individually or together
- **Smart Port Parsing** - Supports ranges (1-100), lists (80,443,22), and combinations
- **Response Time Tracking** - Monitor connection speeds in real-time
- **DNS Resolution** - Automatic hostname to IP resolution with retry logic

### 🎯 **Pre-Built Profiles**
Choose from 14+ expertly crafted port profiles:

| 🌐 **Web Servers** | 📧 **Mail Servers** | 🗄️ **Databases** | 🎮 **Gaming** |
|-------------------|-------------------|-----------------|---------------|
| 🔐 **Security Scan** | 🎵 **Streaming/Media** | 🔗 **P2P/Torrent** | 💻 **Development** |
| 🏢 **Remote Access** | 📁 **File Transfer** | 🌐 **Network Services** | 🔒 **VPN Services** |

### 📊 **Export & Logging**
- **TXT Format** - Clean, readable text logs
- **CSV Format** - Perfect for spreadsheet analysis
- **JSON Format** - Structured data with scan summaries
- **XML Format** - Rich metadata and hierarchical data
- **Log Management** - Easy cleanup tools for managing old logs

### ⚙️ **Advanced Settings**
- 🕐 **Timeout Control** - Fine-tune connection timeouts (0.1-10s)
- 🔄 **DNS Retry Logic** - Configure retry attempts for reliability
- 👁️ **Display Filters** - Show only open ports to reduce noise
- 🎨 **Smart Color Coding** - Visual status indicators for quick scanning

---

## 🚀 Quick Start

### 📋 Prerequisites

```bash
# Python 3.7 or higher
python --version

# Required packages (included in standard library)
✅ tkinter
✅ socket
✅ threading
✅ json
✅ xml
✅ csv
```

### 💾 Installation

```bash
# Clone the awesome repo
git clone https://github.com/jackworthen/port-checker-plus.git

# Navigate to the project
cd port-checker-plus

# Launch the application
python portCheckerPlus.py
```

### 🎉 First Scan

1. **Enter a target** - `google.com`, `192.168.1.1`, or any hostname/IP
2. **Choose ports** - Try `80,443` for web servers or `1-1000` for a range
3. **Select protocol** - TCP, UDP, or both
4. **Hit "Check Ports"** - Watch the magic happen! ✨

---

## 🎭 Usage Examples

### 🌐 **Web Server Health Check**
```
Host: mywebsite.com
Ports: 80,443,8080,8443
Protocol: TCP
```

### 🔍 **Network Discovery**
```
Host: 192.168.1.1
Ports: 1-1000
Protocol: TCP
```

### 🛡️ **Security Audit**
```
Host: target-server.com
Ports: 21,22,23,25,53,80,110,443,993,995
Protocol: TCP
```

### 🎮 **Gaming Server Check**
```
Host: gameserver.example.com
Ports: 27015,7777,25565,19132
Protocol: TCP/UDP
```

---

## 🎨 Configuration Magic

### 🏗️ **Smart Profiles**

Port Checker Plus comes with **14 built-in profiles** designed by network professionals:

- 🌐 **Web Servers** - HTTP/HTTPS and common web ports
- 📧 **Mail Servers** - SMTP, POP3, IMAP, and secure variants  
- 🗄️ **Database** - MySQL, PostgreSQL, MongoDB, Redis, and more
- 🔐 **Security Scan** - Common vulnerable services
- 🎮 **Gaming** - Popular game server ports
- 💻 **Development** - Local development server ports

### ⚙️ **Advanced Settings**

Access the settings via **Edit → Settings** to customize:

| Setting | Description | Range |
|---------|-------------|-------|
| 🕐 **Timeout** | Connection timeout | 0.1 - 10.0 seconds |
| 🔄 **DNS Retries** | Resolution retry count | 0 - 5 attempts |
| 👁️ **Show Open Only** | Filter closed ports | Toggle |
| 📊 **Export Format** | Log file format | TXT/CSV/JSON/XML |

---

## 📊 Export Formats Explained

### 📝 **TXT Format**
Perfect for quick reading and sharing:
```
==============================
Scan Results: 2025-06-04 15:30:22
Host: example.com
Resolved IP: 93.184.216.34
==============================
TCP Port 80 is OPEN (Service: http) - 45.2ms
TCP Port 443 is OPEN (Service: https) - 52.1ms
```

### 📈 **CSV Format**
Ideal for analysis in Excel or Google Sheets:
```csv
Timestamp,Host,Resolved IP,Port,Protocol,Status,Service,Response Time (ms)
2025-06-04 15:30:22,example.com,93.184.216.34,80,TCP,OPEN,http,45.2
```

### 🔧 **JSON Format**
Structured data with rich metadata:
```json
{
  "scan_info": {
    "timestamp": "2025-06-04 15:30:22",
    "host": "example.com",
    "resolved_ip": "93.184.216.34"
  },
  "summary": {
    "total_ports": 100,
    "open_ports": 2,
    "closed_ports": 98
  }
}
```

### 🏗️ **XML Format**
Hierarchical data perfect for integrations:
```xml
<port_scan_history>
  <scan timestamp="2025-06-04 15:30:22">
    <scan_info>
      <host>example.com</host>
      <resolved_ip>93.184.216.34</resolved_ip>
    </scan_info>
  </scan>
</port_scan_history>
```

---

## 🛠️ Development & Contributing

### 🏗️ **Project Structure**
```
port-checker-plus/
├── 📄 portCheckerPlus.py    # Main application
├── 🖼️ psp_icon2.ico         # Application icon
├── 📋 README.md             # This awesome readme
└── 📜 LICENSE               # MIT License
```

### 🤝 **Contributing**

We welcome contributions! Here's how you can help:

1. 🍴 **Fork** the repository
2. 🌿 **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. 💾 **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. 📤 **Push** to the branch (`git push origin feature/AmazingFeature`)
5. 🎯 **Open** a Pull Request

### 💡 **Ideas for Contributors**

- 🌈 **Dark Mode Theme** - Add dark/light theme toggle
- 🔄 **Scheduled Scans** - Add cron-like scheduling
- 📊 **Historical Charts** - Visualize scan trends over time
- 🔌 **Plugin System** - Allow custom scan modules
- 🌐 **IPv6 Support** - Full dual-stack scanning
- 📱 **REST API** - Headless operation mode

---

## 🐛 Troubleshooting

### ❓ **Common Issues**

**🚫 Permission Denied Errors**
```bash
# On Linux/macOS, you might need elevated privileges for certain scans
sudo python portCheckerPlus.py
```

**🔥 Firewall Blocking Scans**
- Ensure your firewall allows outbound connections
- Some corporate networks may block port scanning tools

**⚡ Slow Scanning Performance**
- Reduce timeout values for faster scans
- Use smaller port ranges for quicker results
- Consider your network bandwidth and target server load

### 🆘 **Getting Help**

- 📋 **Issues**: Open an issue on GitHub
- 💬 **Discussions**: Start a discussion for feature requests
- 📧 **Contact**: Reach out to [@jackworthen](https://github.com/jackworthen)

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### 🎊 **What this means:**
- ✅ **Commercial use** - Use it in your business
- ✅ **Modification** - Customize to your heart's content
- ✅ **Distribution** - Share with friends and colleagues
- ✅ **Private use** - Perfect for personal projects

---

## 🙏 Acknowledgments

- 🐍 **Python Community** - For the amazing standard library
- 🖼️ **Tkinter Team** - For the GUI framework that keeps on giving
- 🌐 **Network Admins** - For inspiring the port profiles
- 🔒 **Security Professionals** - For valuable feedback and testing

---

### 🌟 **Star this repo if you find it useful!** ⭐

*Developed by [jackworthen](https://github.com/jackworthen)**

*Happy Port Scanning!* 🚀

