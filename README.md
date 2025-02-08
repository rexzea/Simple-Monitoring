# 🌐 Network and Local Device Monitoring System

## 📋 Project Summary
This Network Monitoring System is a Python-based tool designed to provide monitoring of network infrastructure, device health, and WiFi connectivity. By utilizing these monitoring techniques, it offers real-time analysis and reporting of network-related metrics.

## ✨ Main Features

### 🖥️ System Monitoring
- System resource tracking (CPU, Memory, Disk)
- Platform-specific system information retrieval
- Performance logging and analysis

### 🌐 Network Intelligence
- Network interface scanning
- IP address and hostname resolution
- Connection status and network topology mapping
- WiFi network detection and analysis

### 🔒 Security & Logging
- Robust logging mechanism
- Security-based network scanning
- Concurrent processing for efficient monitoring
- SQLite database integration for persistent data storage

## 🛠️ Technologies Used
- **Language**: Python 3.8+
- **Main Libraries**:
  - `psutil`: System and process utilities
  - `platform`: System information retrieval
  - `socket`: Network communication
  - `threading`: Concurrent operations
  - `sqlite3`: Database management
  - `requests`: HTTP networking

   **MUST BE INSTALLED!**

## 🚀 Prerequisites
- Python 3.8 or higher
- Required Python libraries (see `External Tools`)
- Administrative/root access recommended

## 🔧 Installation Clone
```bash
https://github.com/rexzea/Simple-Monitoring.git
```

## 📊 External Tools
```python
import psutil
import platform
import socket
import time
import logging
import datetime
import socket
import json
import threading
import time
import sqlite3
import re
import os
import subprocess
import concurrent.futures
import uuid
import requests
import ipaddress
```

## 🔧 Preview
```bash
--- Network Monitoring ---
Network: {'ssid': 'Not shown', 'platform': 'Windows'}
Connected Devices: 0
Download Speed: 18.81 Mbps
Upload Speed: 9.4 Mbps
Signal Strength: 84%
Local IP: not shown
Subnet: not shown
Device List: not shown
Monitoring stopped.
```
![m1](assets/m1.png)
![m2](assets/m2.png)

## 🔍 How It Works
This project uses concurrent programming techniques to:
- Monitor system performance in real-time
- Collect network data from various sources
- Analyze network connectivity and performance
- Store and report findings in an easy-to-read format

## 🛡️ Security
- Secure logging implementation
- Network threat detection
- Sensitive data protection
- Access monitoring

## 🤝 Contributing
Feel free to contribute and submit Pull Requests!

## 📄 License
MIT

## 🏆 Acknowledgments
cr: Rexzea

---
**Disclaimer**: Use responsibly and ensure compliance with local network policies and applicable regulations.
