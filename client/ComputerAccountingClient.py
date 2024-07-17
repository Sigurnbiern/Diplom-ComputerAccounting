import psutil
from platform import uname
import json
import socket
import time
import threading


class os_info():
    

    def correct_size(bts):
        size = 1024
        for item in ["", "K", "M", "G", "T", "P"]:
            if bts < size:
                return f"{bts:.2f}{item}iB"
            bts /= size


    def creating_file():
        collect_info_dict = dict()
        if 'info' not in collect_info_dict:
            collect_info_dict['info'] = dict()
            collect_info_dict['info']['system_info'] = dict()
            collect_info_dict['info']['system_info'] = {'system': {'comp_name': uname().node,
                                                                'os_name': f"{uname().system} {uname().release}",
                                                                'version': uname().version,
                                                                'machine': uname().machine},
                                                        'processor': {'name': uname().processor,
                                                                    'physical_core': psutil.cpu_count(logical=False),
                                                                    'all_core': psutil.cpu_count(logical=True),
                                                                    'freq_max': f"{psutil.cpu_freq().max:.2f}Мгц"},
                                                        'ram': {'max': os_info.correct_size(psutil.virtual_memory().total)}}

        for partition in psutil.disk_partitions():
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                continue
            if 'disk_info' not in collect_info_dict['info']:
                collect_info_dict['info']['disk_info'] = dict()
            if f"'device': {partition.device}" not in collect_info_dict['info']['disk_info']:
                collect_info_dict['info']['disk_info'][partition.device] = dict()
                collect_info_dict['info']['disk_info'][partition.device] = {'file_system': partition.fstype,
                                                                            'size_total': os_info.correct_size(
                                                                                partition_usage.total),
                                                                            'size_used': os_info.correct_size(
                                                                                partition_usage.used),
                                                                            'size_free': os_info.correct_size(
                                                                                partition_usage.free),
                                                                            'percent':
                                                                                f'{partition_usage.percent}'}

        for interface_name, interface_address in psutil.net_if_addrs().items():
            if interface_name == 'Loopback Pseudo-Interface 1':
                continue
            else:
                if 'net_info' not in collect_info_dict['info']:
                    collect_info_dict['info']['net_info'] = dict()
                if interface_name not in collect_info_dict['info']['net_info']:
                    collect_info_dict['info']['net_info'][interface_name] = dict()
                    collect_info_dict['info']['net_info'][interface_name] = {
                        'mac': interface_address[0].address.replace("-", ":"),
                        'ipv4': interface_address[1].address,
                        'ipv6': interface_address[2].address}

        return collect_info_dict
    
    def print_info(info_dict):
        print("=== Информация о системе ===")
        for key, value in info_dict['info']['system_info']['system'].items():
            print(f"{key}: {value}")
        
        print("\n=== Информация о процессоре ===")
        for key, value in info_dict['info']['system_info']['processor'].items():
            print(f"{key}: {value}")

        print("\n=== Оперативная память ===")
        for key, value in info_dict['info']['system_info']['ram'].items():
            print(f"{key}: {value}")

        print("\n=== Информация о дисках ===")
        for disk, disk_info in info_dict['info']['disk_info'].items():
            print(f"Диск: {disk}")
            for key, value in disk_info.items():
                print(f"{key}: {value}")

        print("\n=== Информация о сети ===")
        for interface, interface_info in info_dict['info']['net_info'].items():
            print(f"Интерфейс: {interface}")
            for key, value in interface_info.items():
                print(f"{key}: {value}")
    


    def __init__(self):
        try:
            
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # host = str(input('введите ip: ')) 
            host = 'localhost'
            port = 5555
            self.s.connect((host, port))

            info_dict = os_info.creating_file()
            os_info.print_info(info_dict)
            
            try:
                mac_client = info_dict['info']['net_info']['Ethernet']['mac']
                print(mac_client)
                self.s.send(mac_client.encode('utf-8'))
            except Exception as ex:
                print('Данных не существует')
            
            command = self.s.recv(1024)
            command = command.decode('utf-8')
            if 'save' in command:
                try:
                    office = str(input('Введите номер аудитории: '))
                    self.s.send(office.encode('utf-8'))
                    json_data = json.dumps(info_dict, ensure_ascii=False)

                    data_len = len(json_data)
                    self.s.send(str(data_len).encode('utf-8'))
                    
                    bytes_sent = 0
                    while bytes_sent < data_len:
                        bytes_to_send = min(1024, data_len - bytes_sent)
                        self.s.send(json_data[bytes_sent:bytes_sent + bytes_to_send].encode('utf-8'))
                        bytes_sent += bytes_to_send
                   
                except Exception as ex:
                    data = 'проблема создания и отправки json'
                    self.s.send(data.encode('unf-8'))
                    self.s.close
            if 'disk' in command:
                disk_info = info_dict['info']['disk_info']
                print('данные о дисках:', disk_info)
                json_data = json.dumps(disk_info, ensure_ascii=False)

                data_length = len(json_data)
                self.s.send(str(data_length).encode('utf-8'))
                
                bytes_sent = 0
                while bytes_sent < data_length:
                    bytes_to_send = min(1024, data_length - bytes_sent)
                    self.s.send(json_data[bytes_sent:bytes_sent + bytes_to_send].encode('utf-8'))
                    bytes_sent += bytes_to_send

        except Exception as ex:
            print(f"Ошибка: {ex}")

        finally:
            time.sleep(10)
            threading.Thread(target=self.ping).start()
        
    def ping(self):
        
        try:
            while True:
                self.s.send(b'ping')
                print('pinging')
                time.sleep(10)
        except Exception as ex:
            print(f"Ошибка при отправке пинга: {ex}")
            

    def cleanup(self):
        if self.s:
            try:
                self.s.shutdown(socket.SHUT_RDWR)
            except Exception as e:
                print(f"Ошибка при завершении соединения: {e}")
            self.s.close()
            print("Соединение закрыто.")
os_info()