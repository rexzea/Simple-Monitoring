import psutil
import socket
import json
import platform
import logging
import threading
import time
from datetime import datetime
import sqlite3
import re
import os

class NetworkConnectionMonitor:
    def __init__(self, log_path='network_monitor.log', db_path='network_connections.db'):

        # mengkonfigurasi logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('NetworkMonitor')
        
        # database tracking
        self.db_path = db_path
        self._init_database()
        
        # daftar port
        self.suspicious_ports = {
            21: 'FTP',
            22: 'SSH',
            23: 'Telnet',
            445: 'SMB',
            3389: 'Remote Desktop',
            5900: 'VNC',
            8080: 'HTTP Proxy',
            # kamu bisa menambahkan port
        }
        
        # proses untuk efisiensi
        self.process_cache = {}
    
    def _init_database(self):
        """membuat database untuk menyimpan log koneksi"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                #tabel koneksi
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS network_connections (
                        timestamp DATETIME,
                        local_address TEXT,
                        local_port INTEGER,
                        remote_address TEXT,
                        remote_port INTEGER,
                        status TEXT,
                        process_name TEXT,
                        pid INTEGER,
                        is_suspicious INTEGER
                    )
                ''')
                
                # tabel alert
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        timestamp DATETIME,
                        alert_type TEXT,
                        description TEXT
                    )
                ''')
                
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
    
    def _get_process_name(self, pid):

        if pid in self.process_cache:
            return self.process_cache[pid]
        
        try:
            process = psutil.Process(pid)
            name = process.name()
            self.process_cache[pid] = name
            return name
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "Unknown"
    
    def _is_suspicious_connection(self, connection):

        # anomali atau kejanggalan
        suspicious_conditions = [
            connection.laddr.port in self.suspicious_ports,
            connection.status == 'LISTEN' and connection.laddr.port not in [80, 443, 22],
            connection.raddr and self._is_private_ip(connection.raddr.ip) is False
        ]
        
        return any(suspicious_conditions)
    
    def _is_private_ip(self, ip):

        private_ranges = [ # kamus
            re.compile(r'^10\.'),           # 10.0.0.0 - 10.255.255.255 
            re.compile(r'^172\.(1[6-9]|2\d|3[0-1])\.'),  # 172.16.0.0 - 172.31.255.255
            re.compile(r'^192\.168\.'),     # 192.168.0.0 - 192.168.255.255
            re.compile(r'^127\.')            # Localhost
        ]
        
        return any(pattern.match(ip) for pattern in private_ranges)
    
    def log_connection(self, connection, is_suspicious):

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO network_connections VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    str(connection.laddr.ip),
                    connection.laddr.port,
                    str(connection.raddr.ip) if connection.raddr else 'N/A',
                    connection.raddr.port if connection.raddr else 0,
                    connection.status,
                    self._get_process_name(connection.pid),
                    connection.pid,
                    1 if is_suspicious else 0
                ))
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error logging connection: {e}")
    
    def log_alert(self, alert_type, description):

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO alerts VALUES (?, ?, ?)
                ''', (datetime.now(), alert_type, description))
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Error logging alert: {e}")
    
    def analyze_connections(self):

        try:
            connections = psutil.net_connections()
            suspicious_connections = []
            
            for conn in connections:
                # meng filer koneksi yang aktif
                if conn.status in ['ESTABLISHED', 'LISTEN', 'TIME_WAIT']:
                    is_suspicious = self._is_suspicious_connection(conn)
                    
                    # log ke semua koneksi
                    self.log_connection(conn, is_suspicious)
                    
                    # mengumpulkan koneksi mencurigakan
                    if is_suspicious:
                        suspicious_connections.append({
                            'local': f"{conn.laddr.ip}:{conn.laddr.port}",
                            'remote': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else 'N/A',
                            'status': conn.status,
                            'process': self._get_process_name(conn.pid)
                        })
            
            # membuat alert untuk koneksi yang aneh dan mencurigakan
            if suspicious_connections:
                alert_msg = json.dumps(suspicious_connections, indent=2)
                self.log_alert('SUSPICIOUS_CONNECTION', alert_msg)
                self.logger.warning(f"Terdeteksi {len(suspicious_connections)} koneksi mencurigakan!")
                
                # Tampilkan detail di console
                print("\n🚨 PERINGATAN: Koneksi Mencurigakan Terdeteksi 🚨")
                for conn in suspicious_connections:
                    print(f"🔴 Proses: {conn['process']}")
                    print(f"   Lokal: {conn['local']}")
                    print(f"   Remote: {conn['remote']}")
                    print(f"   Status: {conn['status']}\n")
            
            return suspicious_connections
        
        except Exception as e:
            self.logger.error(f"Maaf, ada kesalahan dalam analisis koneksi: {e}")
            return []
    
    def get_connection_summary(self):

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # total koneksi
                cursor.execute("SELECT COUNT(*) FROM network_connections")
                total_connections = cursor.fetchone()[0]
                
                # koneksi aneh
                cursor.execute("SELECT COUNT(*) FROM network_connections WHERE is_suspicious = 1")
                suspicious_count = cursor.fetchone()[0]
                
                # top koneksi
                cursor.execute("""
                    SELECT process_name, COUNT(*) as connection_count 
                    FROM network_connections 
                    GROUP BY process_name 
                    ORDER BY connection_count DESC 
                    LIMIT 5
                """)
                top_processes = cursor.fetchall()
                
                return {
                    'total_connections': total_connections,
                    'suspicious_connections': suspicious_count,
                    'top_processes': top_processes
                }
        except sqlite3.Error as e:
            self.logger.error(f"Maaf, ada kesalahan dalam ringkasan koneksi: {e}")
            return {}
    
    def continuous_monitor(self, interval=30):

        try:
            while True:
                print("\n📡 Memindai Koneksi yang sedang Aktif...")
                suspicious_conns = self.analyze_connections()
                
                summary = self.get_connection_summary()
                print("\n📊 Ringkasan Koneksi:")
                print(f"🔹 Total Koneksi: {summary.get('total_connections', 0)}")
                print(f"🚨 Koneksi Mencurigakan: {summary.get('suspicious_connections', 0)}")
                
                print("\n🏆 Top Proses Terkoneksi:")
                for process, count in summary.get('top_processes', []):
                    print(f"   {process}: {count} koneksi")
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n✋ Monitoring dihentikan.")
        except Exception as e:
            self.logger.error(f" Maaf ada kesalahan dalam monitoring: {e}")

def main():
    print("🌐 Network Connection Monitor 🌐")
    print("--------------------------------")
    
    # izin kalau administrator
    try:
        monitor = NetworkConnectionMonitor()
        monitor.continuous_monitor()
    
    except PermissionError:
        print("❌ Error: Aplikasi memerlukan izin administrator!")
        print("Jalankan script sebagai administrator/root.")
    except Exception as e:
        print(f"❌ Kesalahan: {e}")

if __name__ == "__main__":
    main()
