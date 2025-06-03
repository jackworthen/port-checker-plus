# 🚀 Port Checker Plus

**🔍 A powerful, user-friendly network port scanner with a beautiful GUI**

*Scan ports like a pro, visualize results like an artist* ✨

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Contributing](#-contributing)

---

## 🎯 What is Port Checker Plus?

Port Checker Plus is a modern, feature-rich network port scanner built with Python and Tkinter. Whether you're a network administrator, security professional, or curious developer, this tool makes port scanning intuitive and visually appealing!

## ✨ Features

### 🚄 **Lightning Fast Scanning**
- **Multi-threaded scanning** for blazing speed
- **TCP & UDP protocol support** 
- **Customizable timeouts** and retry counts
- **Real-time progress tracking** with visual progress bars

### 🎨 **Beautiful & Intuitive Interface**
- **Modern GUI design** with clean, professional look
- **Color-coded results** (🟢 Open, ⚫ Closed, 🔴 Error, 🟣 Filtered)
- **Sortable result tables** - click any column header to sort
- **Search & filter functionality** to find what you need instantly

### 🔧 **Smart Port Profiles**
Choose from pre-configured port sets for common scenarios:

| Profile | Ports | Use Case |
|---------|-------|----------|
| 🌐 **Web Servers** | 80, 443, 8080, 8443, 8000... | Web development & hosting |
| 📧 **Mail Servers** | 25, 110, 143, 993, 995... | Email server management |
| 🗄️ **Databases** | 3306, 5432, 1433, 27017... | Database administration |
| 🎮 **Gaming** | 27015, 7777, 25565... | Game server management |
| 🔒 **Security Scan** | 21, 22, 23, 25, 53, 80... | Security assessment |
| 🔌 **Remote Access** | 22, 23, 3389, 5900... | Remote administration |
| 📁 **File Transfer** | 21, 22, 69, 873, 2049... | File sharing services |
| 🌐 **Network Services** | 53, 67, 123, 161, 514... | Network infrastructure |
| 🏴‍☠️ **P2P/Torrent** | 6881-6889, 51413... | P2P applications |
| 🎬 **Streaming/Media** | 554, 1935, 8554... | Media streaming |
| 🔐 **VPN Services** | 1194, 500, 4500, 1723... | VPN management |
| 💻 **Development** | 3000, 4000, 5000, 8000... | Development servers |

### 📊 **Advanced Features**
- **Hostname resolution** with DNS retry logic
- **Service detection** - automatically identifies running services
- **Response time measurement** for performance analysis
- **Export results to files** for documentation and reporting
- **Cross-platform compatibility** (Windows, macOS, Linux)
- **Persistent configuration** - remembers your preferences

## 🚀 Installation

### Option 1: Download Executable (Easiest)
1. Go to the [Releases](https://github.com/jackworthen/port-checker-plus/releases) page
2. Download the latest executable for your operating system
3. Run and enjoy! 🎉

### Option 2: Run from Source
```bash
# Clone the repository
git clone https://github.com/jackworthen/port-checker-plus.git
cd port-checker-plus

# Install required dependencies
pip install -r requirements.txt

# Run the application
python portCheckerPlus.py
```

### Requirements
- Python 3.6 or higher
- tkinter (usually included with Python)
- Standard library modules (socket, threading, json, etc.)

## 📖 Usage

### Quick Start Guide

1. **🏠 Enter Target Host**
   - IP address (e.g., `192.168.1.1`)
   - Domain name (e.g., `google.com`)
   - Localhost (e.g., `127.0.0.1`)

2. **🔌 Specify Ports**
   - Single port: `80`
   - Multiple ports: `80,443,22`
   - Port ranges: `1-100,8080`
   - Mixed: `22,80-90,443,8000-8080`

3. **⚙️ Choose Protocol**
   - TCP (most common)
   - UDP 
   - TCP/UDP (scans both)

4. **🚀 Click "Check Ports"** and watch the magic happen!

### Advanced Configuration

Access the settings menu (Edit → Settings) to customize:

- **⏱️ Timeout settings** for faster or more thorough scans
- **🔄 DNS retry count** for unreliable networks  
- **📁 Export directory** for saving scan results
- **🎯 Default values** for host and ports
- **👁️ Display options** (show only open ports)

### Pro Tips 💡

- **Use port profiles** for quick scans of common services
- **Filter results** using the search box to find specific ports
- **Sort columns** by clicking headers for better analysis
- **Enable logging** to keep records of your scans
- **Use port ranges** for efficient scanning (e.g., `1-1000`)


## 🛠️ Building from Source

To create your own executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --windowed --icon=psp_icon2.ico portCheckerPlus.py

# Find your executable in the 'dist' folder
```

## 🤝 Contributing

We love contributions! Here's how you can help make Port Checker Plus even better:

### 🐛 Found a Bug?
- Open an [issue](https://github.com/jackworthen/port-checker-plus/issues) with details
- Include steps to reproduce the problem
- Mention your operating system and Python version

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⭐ Show Your Support

If you find Port Checker Plus helpful, please:
- ⭐ Star this repository
- 🍴 Fork it for your own projects  
- 📢 Share it with friends and colleagues
- 🐛 Report bugs and suggest improvements

