import customtkinter as ctk
import time
from MyDb import Data_Base
import socket
import json
import threading
from CTkMessagebox import CTkMessagebox

class DataWindow(ctk.CTkToplevel):
    def __init__(self, master, heads, request, details = False, filter_table = False):
        super().__init__(master)
        self.title("Таблица компьютеров")
        self.geometry('700x500')
        self.create_table(heads, request, details = details, filter_table=filter_table)

       
    def create_table(self, heads, request,  tabs = None, details = False, filter_table = False):
        if tabs :
            win = tabs
        else:
            win = self

        if filter_table:
            frame_filter = ctk.CTkFrame(win)
            frame_filter.pack()
            label_filter = ctk.CTkLabel(frame_filter, text='Введите номер кабинета')
            label_filter.pack(side = 'left')
            text_box = ctk.CTkTextbox(frame_filter, height=10, width=100)
            button_accept = ctk.CTkButton(frame_filter, text='Применить', command= lambda: self.filter_tab(heads, text_box))
            text_box.pack(padx=10, pady=10, side = 'left')
            button_accept.pack(padx=10, pady=10, side = 'left')

        # self.frame_vert = ctk.CTkScrollableFrame(win, border_width=3, border_color='white', fg_color='gray', scrollbar_button_color='#36719f')
        # self.frame_vert.pack(padx = 10, pady = 10, fill="both", expand=True)

       

        self.frame = ctk.CTkScrollableFrame(win, border_width=3, border_color='white', fg_color='gray', scrollbar_button_color='#36719f')
        self.frame.pack(padx = 10, pady = 10, fill="both", expand=True)
      
     
       

        request = Data_Base.request_data(request=request)
        rows = len(request)
        cols = len(request[0]) if request else 0
        

     
        for j, header in enumerate(heads):
            label = ctk.CTkLabel(self.frame,text_color='black', text=header.upper(), width=15, font=("Arial", 10, "bold"))
            label.grid(row=0, column=j, padx=5, pady=5)

        for i in range(rows):
    
            for j in range(cols):
                
                label = ctk.CTkLabel(self.frame, text=str(request[i][j]), width=15)
                label.grid(row=i*2+1, column=j, padx=5, pady=5, sticky="nsew")  
                # if j < cols -1:
                #     vert_line_frame = ctk.CTkFrame(frame, width= 3, fg_color='white')
                #     vert_line_frame.grid(row = 1, column = j*2+1, rowspan = rows, sticky = 'ns')
                if i < rows - 1:
                    line_frame = ctk.CTkFrame(self.frame, height=3,fg_color='white')
                    line_frame.grid(row=i*2+2, column=0, columnspan = cols, rowspan=1, sticky = 'ew' )
  
        if details:

            for i, data_row in enumerate(request):  
                pc_id = data_row[0]
                button = ctk.CTkButton(self.frame, border_width=2, border_color='white', hover_color='#1b67a2', fg_color='transparent', text="Детали", width=100, command=lambda id=pc_id: self.show_details(id))
                button.grid(row=i*2+1, column=cols+1, padx=5, pady=5, sticky="nsew")
    
    def filter_tab(self, heads, text_box):
        office_number = text_box.get("0.0", "end").strip()

        if not office_number:
            self.frame.pack_forget()
            request = 'select * from pc'
            self.create_table(heads, request, details=True)

        else:
            
            office_number = int(office_number)
            self.frame.pack_forget()
            request = f"select * from pc where office = {office_number}"
            self.create_table(heads, request, details= True)


        
    def show_details(self, pc_id):
     
        details_window = ctk.CTkToplevel()
        details_window.title(f"Детали компьютера с id: {pc_id}")
        details_window.geometry('800x500')


        tabview = ctk.CTkTabview(details_window)
        tabview.pack(padx=20, pady=20, fill='both', expand=True)

        tab_names = ['cpu', 'disk', 'net', 'ram', 'sys']
        
        for tab_name in tab_names:
        
            request = Data_Base.request_data(request = f"select column_name, data_type from information_schema.columns WHERE table_name = '{tab_name}'")
            heads = []
            for values in request:
                heads.append(values[0])
            tab = tabview.add(tab_name)
            request = f'select * from {tab_name} where pc_id = {pc_id}'
            self.create_table(heads, request,  tabs = tabview.tab(tab_name))


class MainWindow(ctk.CTk):
    def update_db(self, received_disk_dict):
        try:
            pc_id = self.pc_id
     
            for disk_name, disk_info in received_disk_dict.items():
                total = disk_info['size_total']
                used = disk_info['size_used']
                free = disk_info['size_free']
                percent = disk_info['percent']
                print(f'Диск "{disk_name}" имеет данные: {total}, {used}, {free}, {percent}')
                Data_Base.change_data(request=f"""update disk set size_total = '{total}', size_used = '{used}', size_free = '{free}', 
                                      percent = '{percent}' where pc_id = {pc_id} and disk_name = '{disk_name}'""")
        except Exception as ex:
            CTkMessagebox(title='error', message=f'{ex}', icon='cancel')

    def save_info(self, office, received_dict):
      
        try:
            Data_Base.change_data(request=f'insert into pc (office) values({office})')
            id_pc = Data_Base.request_data('select max(id) from pc')
            for items in id_pc:
                id_pc = f'{items[0]}'
            for item in received_dict['info']:
        
                if item == "system_info":
                    for elem in received_dict['info'][item]:
                        if elem == 'system':
                            
                            pc_name = received_dict['info'][item][elem]['comp_name']
                            os_name = received_dict['info'][item][elem]['os_name']
                            version = received_dict['info'][item][elem]['version']
                            machine = received_dict['info'][item][elem]['machine']

                            Data_Base.change_data(request=f'''insert into sys(pc_id, pc_name, os_name, version, machine) 
                                                    values({id_pc}, '{pc_name}', '{os_name}', '{version}', '{machine}')''')
                        if elem == 'processor':

                            cpu_name = received_dict['info'][item][elem]['name']
                            physical = received_dict['info'][item][elem]['physical_core']
                            all_core = received_dict['info'][item][elem]['all_core']
                            freq_max = received_dict['info'][item][elem]['freq_max']

                            Data_Base.change_data(request=f'''insert into cpu(pc_id, cpu_name, physical_core, all_core, freq_max)
                                                        values({id_pc}, '{cpu_name}', {physical}, {all_core}, '{freq_max}')''')
                        
                        if elem == 'ram':

                            max = received_dict['info'][item][elem]['max']
                      

                            Data_Base.change_data(request=f'''insert into ram(pc_id, max) 
                                                    values({id_pc}, '{max}')''')
                if item == "disk_info":
                    for elem in received_dict['info'][item]:

                        disk_name = elem
                        file_sys = received_dict['info'][item][elem]['file_system']
                        size_total = received_dict['info'][item][elem]['size_total']
                        size_used = received_dict['info'][item][elem]['size_used']
                        size_free = received_dict['info'][item][elem]['size_free']
                        perc = received_dict['info'][item][elem]['percent']

                        Data_Base.change_data(request=f'''insert into disk(pc_id, disk_name, file_sys, size_total, size_used, size_free, percent)
                                                values({id_pc}, '{disk_name}', '{file_sys}', '{size_total}', '{size_used}', '{size_free}', '{perc}')''')
                    
                if item == "net_info":
                    for elem in received_dict['info'][item]:

                        net_name = elem
                        mac = received_dict['info'][item][elem]['mac']
                        v4 = received_dict['info'][item][elem]['ipv4']
                        v6 = received_dict['info'][item][elem]['ipv6']

                        Data_Base.change_data(request=f'''insert into net(pc_id, name, mac, ipv4, ipv6)
                                                values({id_pc}, '{net_name}', '{mac}', '{v4}',' {v6}')''')
            
            sys_id = Data_Base.request_data('select max(id) from sys')
            for items in sys_id:
                sys_id = f'{items[0]}'
            cpu_id = Data_Base.request_data('select max(id) from cpu')
            for items in cpu_id:
                cpu_id = f'{items[0]}'
            disk_id = Data_Base.request_data('select max(id) from disk')
            for items in disk_id:
                disk_id = f'{items[0]}'
            net_id = Data_Base.request_data('select max(id) from net')
            for items in net_id:
                net_id = f'{items[0]}'
            ram_id = Data_Base.request_data('select max(id) from ram')
            for items in ram_id:
                ram_id = f'{items[0]}'
            count_disk = Data_Base.request_data(f'select count(disk_name) from disk where pc_id = {id_pc}')
            for items in count_disk:
                count_disk= f'{items[0]}'
            count_net = Data_Base.request_data(f'select count(name) from net where pc_id = {id_pc}')
            for items in count_net:
                count_net= f'{items[0]}'

            Data_Base.change_data(request=f'''update pc set sys_id = {sys_id}, cpu_id = {cpu_id}, ram_id = {ram_id}, 
                            disk_id = {disk_id}, net_id = {net_id}, count_disk = {count_disk}, count_net = {count_net} where id = {id_pc}''')

        except Exception as ex:
            CTkMessagebox(title='Error', message=f'Ошибка: {ex}', icon='cancel')
            print('Ошибка при сохранении:', ex)


    def listen_conn(self):

        self.lock = threading.Lock()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # host = '0.0.0.0'
        host = 'localhost'  
        port = 5555 
        self.server_socket.bind((host, port))
        self.server_socket.listen(2)
        print('слушаем...')
        self.accept_conn()
        

    def accept_conn(self):
        while True:
            client_socket, client_addr = self.server_socket.accept()
            
            with self.lock:
                self.connected_clients[client_socket] = {'last_ping': time.time()}

            print('принимаем...')
            print('connected with: ', client_addr)
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.daemon = True
            client_handler.start()

            check_conn_thread = threading.Thread(target=self.check_conn, args=(client_socket,))
            check_conn_thread.daemon = True
            check_conn_thread.start()


    def check_conn(self, client_socket):

        while True:
            current_time = time.time()
            print(current_time)
            for client_socket in list(self.connected_clients.keys()):
                if current_time - self.connected_clients[client_socket]['last_ping'] > 20:
                    try:
                        print(f"Клиент {self.connected_clients[client_socket]['pc_id']} был отключен")
                        client_socket.close()
                        self.connected_clients.pop(client_socket, None)
                    except KeyError:
                        client_socket.close()
                        self.connected_clients.pop(client_socket, None)
            time.sleep(10)

    def handle_client(self, client_socket):

            self.client_mac = client_socket.recv(1024)
            self.client_mac = self.client_mac.decode('utf-8')
            mac_bd = Data_Base.request_data(f"select mac from net where mac = '{self.client_mac}'")
            self.pc_id = Data_Base.request_data(request=f"select pc_id from net where mac = '{self.client_mac}'")
            for items in self.pc_id:
                self.pc_id = f'{items[0]}'
            if not self.pc_id:
                print('Нет идетнификатора')
            
            else :
                
                self.connected_clients[client_socket]['pc_id'] = self.pc_id
         
            if not mac_bd:
                data = 'save'
                client_socket.sendall(data.encode('utf-8'))
                
                office = client_socket.recv(1024)
                office = office.decode('utf-8')


                try:
                
                    data_len = client_socket.recv(1024)
                    data_len = int(data_len.decode('utf-8'))

                    dict_info = b''

                    while len(dict_info) < data_len:
                        chunk = client_socket.recv(1024)
                        if not chunk:
                            break
                        dict_info += chunk
                        
                    try:
                        received_dict = json.loads(dict_info)
                        print('JSON успешно декодирован')
                        print(received_dict)
                        self.save_info(office, received_dict)
                            
                    except Exception as ex:
                            print(ex)
                except Exception as ex:
                    print('Ошибка:', ex)


            else: 
                print('Есть в базе данных')
                data = 'disk'
                client_socket.sendall(data.encode('utf-8'))

                try:
                  
                    data_len = client_socket.recv(1024)
                    data_len = int(data_len.decode('utf-8'))

                    disk_dict = b''

                    while len(disk_dict) < data_len:
                        chunk = client_socket.recv(1024)
                        if not chunk:
                            break
                        disk_dict += chunk
                        
                    try:
                        received_disk_dict = json.loads(disk_dict)
                        print('JSON успешно декодирован')
                        print(received_disk_dict)
                        self.update_db(received_disk_dict)
                            
                    except Exception as ex:
                            print(ex)
                except Exception as ex:
                    print('Ошибка:', ex)
                
                while True:
                    try:
                        ping = client_socket.recv(1024)
                        if not ping:
                            raise ConnectionResetError
                        if ping.decode('utf-8') == 'ping':
                            print('ping')
                            
                            self.connected_clients[client_socket]['last_ping'] = time.time()
                    except Exception as ex:
                        print(f"Ошибка при получении пинга: {ex}")
                        break

    def __init__(self):
        super().__init__(fg_color ='gray')
        
        self.connected_clients = {}
        
        
        ctk.set_appearance_mode('light')
      
        self.title('Система учета компьютеров')

        self.server_thread = threading.Thread(target=self.listen_conn)
        self.server_thread.daemon = True
        self.server_thread.start()

        self.button_reference = ctk.CTkButton(self, text='?', border_color='white', hover_color='#1b67a2', fg_color='transparent',width=10, command=self.reference)
        self.button_reference.pack(anchor='nw')

        self.button1 = ctk.CTkButton(self, border_width=2, border_color='white', hover_color='#1b67a2', fg_color='transparent', text="Просмотр подключенных\n компьютеров", command=self.open_connected)
        self.button1.pack(padx=20, pady=10)
      
        self.button2 = ctk.CTkButton(self,  border_width=2, border_color='white', hover_color='#1b67a2', fg_color='transparent', text="Просмотр всех компьютеров", command=self.open_pc_window)
        self.button2.pack(padx=20, pady=10)
     
        
    def reference(self):
        CTkMessagebox(title='Справка', topmost=True, sound=True, message='''
        Эта программа является сервером и частью системы учета компьютеров.
        Учет выполняется автоматически при запуске клиентского приложения на компьютере, который необходимо учесть.
        База данных обновляется автоматически.
        Через интерфейс можно просматривать информацию о любом зарегестрированном комптютере, либо просмотреть подключенные компьютеры.
        При закрытии программы будет отключен сервер!
        ''')

    def open_pc_window(self):

        heads = ['id', 'office', 'sys_id', 'cpu_id', 'ram_id', 'disk_id', 'net_id', 'count_disk', 'count_net'] 
        request = 'select * from pc'
        pc_id = Data_Base.request_data(request='select id from pc')
        window = DataWindow(self, heads, request, details= True, filter_table=True)
   
    def open_connected(self):
        try:
            print(self.connected_clients)
            heads = ['id', 'office', 'sys_id', 'cpu_id', 'ram_id', 'disk_id', 'net_id', 'count_disk', 'count_net'] 
            id_list = []
            for socket, client_data in self.connected_clients.items():
                pc_id = client_data['pc_id']
                id_list.append(int(pc_id))
            id_str = ','.join(map(str,id_list))
            request = f'select * from pc where id in ({id_str})'
            window = DataWindow(self, heads, request,  details= True, filter_table=True)
        except Exception as ex:
            CTkMessagebox(title='Ошибка', message=f'Нет подключенных компьютеров', icon='cancel')

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()