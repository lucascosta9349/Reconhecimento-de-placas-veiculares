import mysql.connector

# Conectar ao banco de dados (ou criar um novo)
conn = mysql.connector.connect(  
    host = 'localhost',
    user = 'root',
    password = '',
    database = 'OCR'
)
    
cursor = conn.cursor()

# Criar uma tabela para placas
cursor.execute("SELECT placa FROM Placas")
resultados = cursor.fetchall()
for row in resultados:
    print("Placa:", row[0])


# Confirmar as mudanças e fechar a conexão
conn.commit()
cursor.close()
conn.close()

