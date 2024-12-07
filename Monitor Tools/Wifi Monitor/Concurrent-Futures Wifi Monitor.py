import os
import platform
import subprocess
import socket
import threading
import time
import logging
import concurrent.futures
from typing import Dict, List, Optional

class OptimizedWiFiMonitor:
    def __init__(self, log_file='wifi_monitoring.log'):
        """
        Inisialisasi sistem monitoring jaringan Wi-Fi dengan optimasi
        
        Args:
            log_file (str): Path file log untuk pencatatan aktivitas
        """
        self.os_type = platform.system()
        self.logger = self._setup_logger(log_file)

    def _setup_logger(self, log_file):
        """
        Konfigurasi logger
        """
        logging.basicConfig(
            filename=log_file, 
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        return logging.getLogger(__name__)

    def identify_network(self):
        """
        Identifikasi jaringan Wi-Fi yang sedang digunakan
        """
        try:
            # Dapatkan gateway dan IP lokal
            gateways = self._get_network_gateways()
            return {
                'gateway': gateways[0] if gateways else 'Tidak Terdeteksi',
                'local_ip': self._get_local_ip(),
                'network_prefix': self._get_network_prefix()
            }
        except Exception as e:
            self.logger.error(f"Kesalahan identifikasi jaringan: {e}")
            return None

    def _get_local_ip(self):
        """
        Dapatkan alamat IP lokal
        """
        try:
            # Metode alternatif untuk mendapatkan IP lokal
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return '127.0.0.1'

    def _get_network_prefix(self):
        """
        Dapatkan prefix jaringan
        """
        local_ip = self._get_local_ip()
        return '.'.join(local_ip.split('.')[:3])

    def _get_network_gateways(self):
        """
        Dapatkan gateway jaringan
        """
        try:
            if self.os_type == 'Windows':
                # Perintah untuk Windows
                result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                gateways = []
                for line in result.stdout.split('\n'):
                    if 'Default Gateway' in line:
                        gateway = line.split(':')[1].strip()
                        if gateway != '0.0.0.0' and gateway:
                            gateways.append(gateway)
                return gateways
            elif self.os_type in ['Linux', 'Darwin']:
                # Perintah untuk Linux/MacOS
                result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
                gateways = []
                for line in result.stdout.split('\n'):
                    if 'default via' in line:
                        gateway = line.split('via')[1].split()[0]
                        gateways.append(gateway)
                return gateways
        except Exception as e:
            self.logger.error(f"Kesalahan mendapatkan gateway: {e}")
            return []

    def scan_network_fast(self, timeout=1, max_threads=100):
        """
        Pindai jaringan dengan metode konkurensi untuk kecepatan
        
        Args:
            timeout (int): Waktu timeout untuk setiap ping
            max_threads (int): Jumlah maksimal thread konkurensi
        
        Returns:
            List perangkat yang aktif di jaringan
        """
        network_prefix = self._get_network_prefix()
        active_devices = []

        def ping_ip(ip):
            """
            Fungsi internal untuk melakukan ping
            """
            try:
                # Gunakan ping dengan timeout pendek
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', str(timeout), ip], 
                    capture_output=True, 
                    text=True,
                    timeout=timeout
                )
                
                # Jika ping berhasil, coba resolusi hostname
                if result.returncode == 0:
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                    except:
                        hostname = ip
                    
                    return {
                        'ip': ip,
                        'hostname': hostname,
                        'status': 'Active'
                    }
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass
            return None

        # Gunakan ThreadPoolExecutor untuk ping konkurensi
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            # Buat daftar IP untuk dipindai
            ips_to_scan = [f"{network_prefix}.{i}" for i in range(1, 255)]
            
            # Jalankan ping untuk semua IP secara konkurensi
            futures = [executor.submit(ping_ip, ip) for ip in ips_to_scan]
            
            # Kumpulkan hasil
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    active_devices.append(result)

        return active_devices

    def get_network_info(self):
        """
        Dapatkan informasi komprehensif jaringan
        """
        network = self.identify_network()
        devices = self.scan_network_fast()
        
        return {
            'network': network,
            'active_devices': devices,
            'device_count': len(devices)
        }

    def continuous_monitoring(self, interval=300):
        """
        Monitoring berkelanjutan
        """
        def monitor_task():
            while True:
                try:
                    # Dapatkan informasi jaringan
                    network_info = self.get_network_info()
                    
                    # Cetak informasi
                    print("\n--- Monitoring Jaringan ---")
                    print(f"Jaringan: {network_info['network']}")
                    print(f"Perangkat Aktif: {network_info['device_count']}")
                    print("Daftar Perangkat:")
                    for device in network_info['active_devices']:
                        print(f"  - IP: {device['ip']}, Hostname: {device['hostname']}")
                    
                    # Log informasi
                    self.logger.info(f"Monitoring Jaringan: {network_info}")
                    
                    # Jeda sebelum monitor selanjutnya
                    time.sleep(interval)
                
                except Exception as e:
                    self.logger.error(f"Kesalahan monitoring: {e}")
                    break

        # Jalankan monitoring di thread terpisah
        monitoring_thread = threading.Thread(target=monitor_task)
        monitoring_thread.daemon = True
        monitoring_thread.start()

def main():
    # Inisialisasi monitor
    wifi_monitor = OptimizedWiFiMonitor()
    
    # Mulai monitoring
    wifi_monitor.continuous_monitoring(interval=300)  # Setiap 5 menit
    
    # Pertahankan program berjalan
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Monitoring dihentikan.")

if __name__ == "__main__":
    main()

# Proses Kompleks dan lama serta beresiko mengalami Frezee