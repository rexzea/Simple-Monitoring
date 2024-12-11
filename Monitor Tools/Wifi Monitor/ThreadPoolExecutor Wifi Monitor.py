import os
import platform
import subprocess
import socket
import uuid
import concurrent.futures
import ipaddress
import threading
import time
import logging
import requests
from typing import Dict, List, Optional

class WiFiMonitor:
    def __init__(self, log_file='wifi_monitoring.log'):

        self.os_type = platform.system()
        self.logger = self._setup_logging(log_file)
        self.local_ip = self._get_local_ip()
        self.subnet = self._get_subnet()

    def _setup_logging(self, log_file):

        logging.basicConfig(
            filename=log_file, 
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        return logging.getLogger(__name__)

    def _get_local_ip(self):

        try:
            # buat soket sementara untuk mencari IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            self.logger.error(f"Gagal mendapatkan IP lokal: {e}")
            return '127.0.0.1'

    def _get_subnet(self):

        try:
            # buat objek IP dengan subnet /24
            network = ipaddress.IPv4Network(f"{self.local_ip}/24", strict=False)
            return network
        except Exception as e:
            self.logger.error(f"Gagal mendapatkan subnet: {e}")
            return None

    def fast_network_scan(self, timeout=1, max_threads=100):

        if not self.subnet:
            return []

        devices = []
        
        # melakukan ping pada satu IP
        def ping_ip(ip):
            try:
                # pakai ping dengan timeout singkat
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', str(timeout), str(ip)],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if result.returncode == 0:
                    try:
                        # ccoba dapatkan hostname
                        hostname = socket.gethostbyaddr(str(ip))[0]
                    except:
                        hostname = 'Unknown'
                    
                    # mencari MAC address
                    mac = self._get_mac_address(str(ip))
                    
                    return {
                        'ip': str(ip),
                        'hostname': hostname,
                        'mac': mac
                    }
            except subprocess.TimeoutExpired:
                pass
            except Exception as e:
                self.logger.error(f"Kesalahan ping {ip}: {e}")
            
            return None

        # pakai ThreadPoolExecutor buat mengconcurrent scanning
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            # Buat daftar IP untuk di-ping
            ip_list = [str(ip) for ip in self.subnet.hosts()]
            
            # jalankan ping secara concurrent
            future_to_ip = {executor.submit(ping_ip, ip): ip for ip in ip_list}
            
            for future in concurrent.futures.as_completed(future_to_ip):
                result = future.result()
                if result:
                    devices.append(result)
        
        return devices

    def _get_mac_address(self, ip):

        try:
            if self.os_type == 'Windows':
                #pakai perintah arp untuk Windows
                arp_result = subprocess.run(['arp', '-a', ip], 
                                            capture_output=True, 
                                            text=True)
                mac_lines = [line for line in arp_result.stdout.split('\n') if ip in line]
                if mac_lines:
                    return mac_lines[0].split()[1]
            elif self.os_type == 'Linux':
                # kalau Linux, memeakai cara yang beda (lupa)
                arp_result = subprocess.run(['ip', 'neigh', 'show'], 
                                            capture_output=True, 
                                            text=True)
                mac_lines = [line for line in arp_result.stdout.split('\n') if ip in line]
                if mac_lines:
                    return mac_lines[0].split()[4]
        except Exception as e:
            self.logger.error(f"Gagal mendapatkan MAC address: {e}")
        
       
        return ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                         for elements in range(0,2*6,2)][::-1])

    def get_network_info(self):

        try:
            # mengidentifikasi jaringan
            network_details = {
                'local_ip': self.local_ip,
                'subnet': str(self.subnet) if self.subnet else 'Unknown',
                'devices': self.fast_network_scan()
            }
            
            return network_details
        except Exception as e:
            self.logger.error(f"Kesalahan mendapatkan info jaringan: {e}")
            return {}

    def continuous_monitoring(self, interval=300):

        
        def monitor_task():
            while True:
                try:
                    # mencari informasi jaringan
                    network_info = self.get_network_info()
                    
                    # mencetak informasi
                    print("\n--- Monitoring Jaringan ---")
                    print(f"IP Lokal: {network_info.get('local_ip', 'Unknown')}")
                    print(f"Subnet: {network_info.get('subnet', 'Unknown')}")
                    print("Perangkat Terdeteksi:")
                    for device in network_info.get('devices', []):
                        print(f"  - IP: {device['ip']}, "
                              f"Hostname: {device['hostname']}, "
                              f"MAC: {device['mac']}")
                    
                    # log informasi
                    self.logger.info(f"Pemindaian Jaringan: {len(network_info.get('devices', []))} perangkat terdeteksi")
                    
                    # tunggu interval
                    time.sleep(interval)
                
                except Exception as e:
                    self.logger.error(f"Kesalahan monitoring: {e}")
                    break

        # menjalankan monitoring di thread terpisah
        monitoring_thread = threading.Thread(target=monitor_task)
        monitoring_thread.daemon = True
        monitoring_thread.start()

def main():
    # nisialisasi monitor jaringan
    wifi_monitor = WiFiMonitor()
    
    # lakukan scan pas awal
    initial_scan = wifi_monitor.get_network_info()
    print("Perangkat Terdeteksi Saat Ini:")
    for device in initial_scan.get('devices', []):
        print(f"  - {device}")
    
    # mullai monitoring berkelanjutan
    wifi_monitor.continuous_monitoring(interval=300)  # Setiap 5 menit

    # mempertahankan program berjalan
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Monitoring dihentikan.")

if __name__ == "__main__":
    main()

# Proses Kompleks dan lama serta beresiko mengalami Frezee
