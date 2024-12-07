import os
import platform
import subprocess
import psutil
import socket
import requests
import threading
import time
import logging
import uuid
from typing import Dict, List, Optional

class WiFiMonitor:
    def __init__(self, log_file='wifi_monitoring.log'):
        """
        Inisialisasi sistem monitoring jaringan Wi-Fi
        
        Args:
            log_file (str): Path file log untuk pencatatan aktivitas
        """
        self.os_type = platform.system()
        self.current_network = None
        
        # Konfigurasi logging
        logging.basicConfig(
            filename=log_file, 
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def identify_current_network(self) -> Optional[Dict[str, str]]:
        """
        Identifikasi jaringan Wi-Fi yang sedang digunakan
        
        Returns:
            Dict dengan informasi jaringan atau None
        """
        try:
            if self.os_type == 'Windows':
                result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                                        capture_output=True, 
                                        text=True)
                for line in result.stdout.split('\n'):
                    if 'SSID' in line and 'Signal' not in line:
                        ssid = line.split(':')[1].strip()
                        return {
                            'ssid': ssid,
                            'platform': 'Windows'
                        }
            
            elif self.os_type == 'Linux':
                result = subprocess.run(['iwconfig'], 
                                        capture_output=True, 
                                        text=True)
                for line in result.stdout.split('\n'):
                    if 'ESSID' in line:
                        ssid = line.split('ESSID:')[1].strip('"')
                        return {
                            'ssid': ssid,
                            'platform': 'Linux'
                        }
            
            elif self.os_type == 'Darwin':  # MacOS
                result = subprocess.run(['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'], 
                                        capture_output=True, 
                                        text=True)
                for line in result.stdout.split('\n'):
                    if ' SSID' in line:
                        ssid = line.split(':')[1].strip()
                        return {
                            'ssid': ssid,
                            'platform': 'MacOS'
                        }
        
        except Exception as e:
            self.logger.error(f"Kesalahan identifikasi jaringan: {e}")
        
        return None

    def get_local_devices(self) -> List[Dict[str, str]]:
        """
        Dapatkan daftar perangkat di jaringan lokal
        
        Returns:
            Daftar perangkat dalam jaringan
        """
        try:
            # Dapatkan alamat IP lokal
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # Ambil prefix subnet (misal dari 192.168.1.100 menjadi 192.168.1)
            ip_prefix = '.'.join(local_ip.split('.')[:3])
            
            devices = []
            
            # Coba ping sejumlah alamat IP dalam subnet
            for i in range(1, 255):
                test_ip = f"{ip_prefix}.{i}"
                try:
                    # Gunakan subprocess untuk ping
                    result = subprocess.run(['ping', '-c', '1', '-W', '1', test_ip], 
                                            capture_output=True, 
                                            text=True)
                    
                    if result.returncode == 0:
                        try:
                            # Coba resolusi nama host
                            hostname = socket.gethostbyaddr(test_ip)[0]
                        except:
                            hostname = 'Unknown'
                        
                        # Dapatkan MAC address menggunakan ARP (untuk Windows)
                        if self.os_type == 'Windows':
                            try:
                                arp_result = subprocess.run(['arp', '-a', test_ip], 
                                                            capture_output=True, 
                                                            text=True)
                                mac = [line.split()[1] for line in arp_result.stdout.split('\n') if test_ip in line][0]
                            except:
                                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])
                        else:
                            mac = 'Unknown'
                        
                        devices.append({
                            'ip': test_ip,
                            'hostname': hostname,
                            'mac': mac
                        })
                except Exception as e:
                    # Abaikan kesalahan ping
                    pass
            
            return devices
        
        except Exception as e:
            self.logger.error(f"Kesalahan mendapatkan perangkat: {e}")
            return []

    def get_network_speed(self) -> Dict[str, float]:
        """
        Dapatkan kecepatan download dan upload
        Catatan: Memerlukan koneksi internet
        
        Returns:
            Dict dengan kecepatan dalam Mbps
        """
        try:
            # Gunakan API eksternal untuk tes kecepatan
            speed_test = requests.get('https://api.ipify.org/speed', timeout=10)
            
            # Ukur waktu respons sebagai proksi kecepatan
            download_speed = 1 / speed_test.elapsed.total_seconds() * 8
            
            return {
                'download_speed': round(download_speed, 2),
                'upload_speed': round(download_speed / 2, 2)
            }
        except Exception as e:
            self.logger.error(f"Kesalahan tes kecepatan: {e}")
            return {'download_speed': 0, 'upload_speed': 0}

    def get_signal_strength(self) -> Optional[int]:
        """
        Dapatkan kekuatan sinyal jaringan Wi-Fi
        
        Returns:
            Kekuatan sinyal dalam persen
        """
        try:
            if self.os_type == 'Windows':
                result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                                        capture_output=True, 
                                        text=True)
                for line in result.stdout.split('\n'):
                    if 'Signal' in line:
                        return int(line.split(':')[1].strip().replace('%', ''))
        
        except Exception as e:
            self.logger.error(f"Kesalahan mendapatkan kekuatan sinyal: {e}")
        
        return None

    def continuous_monitoring(self, interval=300):
        """
        Monitoring berkelanjutan dengan interval tertentu
        
        Args:
            interval (int): Interval pemantauan dalam detik
        """
        def monitor_task():
            while True:
                try:
                    # Kumpulkan informasi jaringan
                    network_info = self.identify_current_network()
                    devices = self.get_local_devices()
                    speed_info = self.get_network_speed()
                    signal_strength = self.get_signal_strength()

                    # Log informasi
                    self.logger.info(f"Jaringan: {network_info}")
                    self.logger.info(f"Perangkat Terhubung: {len(devices)}")
                    self.logger.info(f"Kecepatan: {speed_info}")
                    self.logger.info(f"Kekuatan Sinyal: {signal_strength}%")

                    # Cetak informasi
                    print("\n--- Monitoring Jaringan ---")
                    print(f"Jaringan: {network_info}")
                    print(f"Perangkat Terhubung: {len(devices)}")
                    print(f"Kecepatan Download: {speed_info['download_speed']} Mbps")
                    print(f"Kecepatan Upload: {speed_info['upload_speed']} Mbps")
                    print(f"Kekuatan Sinyal: {signal_strength}%")
                    print("Daftar Perangkat:")
                    for device in devices:
                        print(f"  - IP: {device['ip']}, Hostname: {device['hostname']}, MAC: {device['mac']}")

                    time.sleep(interval)
                
                except Exception as e:
                    self.logger.error(f"Kesalahan monitoring: {e}")
                    break

        # Jalankan monitoring di thread terpisah
        monitoring_thread = threading.Thread(target=monitor_task)
        monitoring_thread.daemon = True
        monitoring_thread.start()

def main():
    wifi_monitor = WiFiMonitor()
    
    # Mulai monitoring berkelanjutan
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