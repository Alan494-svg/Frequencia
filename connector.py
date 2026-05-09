import mysql.connector
from mysql.connector import Error

def criar_conexao():
    try:
        conexao = mysql.connector.connect(
            host='localhost',
            port=3306,  
            user='root',
            password='rootpassword',
            database='mydatabase'
        )
        if conexao.is_connected():
            print('Conexão MySQL realizada com sucesso!')
            return conexao
    except Error as e:
        print(f'Erro ao conectar: {e}')
        return None

if __name__ == '__main__':
    conexao = criar_conexao()
    if conexao:
        conexao.close()