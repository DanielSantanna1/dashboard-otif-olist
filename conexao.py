from sqlalchemy import create_engine
import pandas as pd

# Ajusta conforme sua instância (você usa localhost\SQLEXPRESS)
engine = create_engine(
    "mssql+pyodbc://localhost\\SQLEXPRESS/Olist?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)

# Testa lendo uma tabela pequena
df_teste = pd.read_sql("SELECT TOP 5 * FROM olist_sellers_dataset", engine)
print(df_teste)