import psycopg2
from config import *
from CTkMessagebox import CTkMessagebox



class Data_Base():


    def request_data(request):
        # Подключаемся к БД
        try:
            conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
            )
            # Создаем курсор
            cur = conn.cursor()
            
            # Выполняем запрос для получения данных из базы данных
            cur.execute(request)
            
            # Получаем все строки результата запроса
            
            rows = cur.fetchall()

            # Закрываем курсор и соединение с базой данных
            cur.close()
            conn.close()
            return rows
        

        except Exception as _ex:
            print(_ex)



    def change_data(request):
    

        try:
            conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
            )
          
            cur = conn.cursor()
            
        
            cur.execute(request)
            conn.commit()
 
            cur.close()
            conn.close()
            
        
        except Exception as _ex:
            print('DB Error:', _ex)
        