import psycopg2

connection = psycopg2.connect(
    user='project_2',
    password='fnubar',
    host='140.117.68.66',
    port='5432',
    dbname='project_2'  # PostgreSQL 的資料庫名稱
)
cursor = connection.cursor()

