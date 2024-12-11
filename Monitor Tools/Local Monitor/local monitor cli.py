import psutil
import platform
import socket
import time
import logging
from datetime import datetime

def get_size(bytes, suffix="B"):

    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def get_gpu_info():

    try:
        # Metode 1: Coba import GPUtil
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                return f"GPU: {gpus[0].name}, Utilization: {gpus[0].load * 100:.2f}%"
        except ImportError:
            pass

        # Metode 2: memakai WMI for Windows
        try:
            import _wmi
            c = _wmi.WMI()
            gpu_info = c.Win32_VideoController()[0]
            return f"GPU: {gpu_info.Name}, Memory: {get_size(gpu_info.AdapterRAM)}"
        except ImportError:
            pass

        # Metode 3: menggunakn subproces for informasi GPU
        try:
            import subprocess
            
            # untuk Windows
            if platform.system() == "Windows":
                try:
                    output = subprocess.check_output(["wmic", "path", "win32_VideoController", "get", "name"], universal_newlines=True)
                    return f"GPU: {output.strip().split('\\n')[1]}"
                except:
                    pass
            
            # untuk Linux
            elif platform.system() == "Linux":
                try:
                    output = subprocess.check_output(["lspci", "-vnn", "|", "grep", "VGA"], universal_newlines=True)
                    return f"GPU: {output.strip()}"
                except:
                    pass
        except:
            pass

        return "GPU: Informasi tidak tersedia"

    except Exception as e:
        return f"Error mendapatkan info GPU: {e}"

def monitor_system():
    """
    Memantau penggunaan sumber daya sistem
    """
    print("=" * 50)
    print("🖥️  SISTEM MONITORING".center(50))
    print("=" * 50)

    while True:
        try:
            # info sistem utama
            print("\n📊 OVERVIEW SISTEM:")
            uname = platform.uname()
            print(f"🖥️  Sistem: {uname.system} {uname.release}")
            print(f"🖲️  Hostname: {uname.node}")
            print(f"🔧  Versi: {uname.version}")
            
            # CPU
            print("\n💻 PENGGUNAAN CPU:")
            print(f"🔥 Total Penggunaan: {psutil.cpu_percent()}%")
            print("🌡️ Penggunaan per Core:")
            for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
                print(f"   Core {i+1}: {percentage}%")
            
            # memory (RAM)
            memory = psutil.virtual_memory()
            print("\n🧠 PENGGUNAAN MEMORY:")
            print(f"💾 Total: {get_size(memory.total)}")
            print(f"🔋 Tersedia: {get_size(memory.available)}")
            print(f"🔥 Digunakan: {get_size(memory.used)} ({memory.percent}%)")
            
            # disk
            disk = psutil.disk_usage('/')
            print("\n💽 PENGGUNAAN DISK:")
            print(f"💾 Total: {get_size(disk.total)}")
            print(f"🔥 Terpakai: {get_size(disk.used)} ({disk.percent}%)")
            print(f"🆓 Tersedia: {get_size(disk.free)}")
            
            # jaringan
            net_io = psutil.net_io_counters()
            print("\n🌐 STATISTIK JARINGAN:")
            print(f"📤 Data Terkirim: {get_size(net_io.bytes_sent)}")
            print(f"📥 Data Diterima: {get_size(net_io.bytes_recv)}")
            
            # IP
            try:
                local_ip = socket.gethostbyname(socket.gethostname())
                print(f"\n🌍 IP Lokal: {local_ip}")
            except Exception as ip_err:
                print(f"\n❌ Gagal mendapatkan IP: {ip_err}")
            
          
            print(f"\n🎮 {get_gpu_info()}")
            
            # waktu
            print(f"\n🕒 Waktu Pemantauan: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            print("\n" + "=" * 50)
            print("Tekan Ctrl+C untuk keluar".center(50))
            print("=" * 50)
            
            time.sleep(5)  # jeda 5 detik
            
        except KeyboardInterrupt:
            print("\n✋ Pemantauan dihentikan oleh pengguna.")
            break
        except Exception as e:
            print(f"❌ Terjadi kesalahan: {e}")
            time.sleep(5)

def main():
    try:
        monitor_system()
    except Exception as e:
        print(f"Kesalahan utama: {e}")

if __name__ == "__main__":
    main()
