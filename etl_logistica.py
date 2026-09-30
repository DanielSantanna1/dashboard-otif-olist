from sqlalchemy import create_engine
import pandas as pd

engine = create_engine(
    "mssql+pyodbc://localhost\\SQLEXPRESS/Olist?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)

df_orders = pd.read_sql("SELECT * FROM olist_orders_dataset", engine)
df_items = pd.read_sql("SELECT * FROM olist_order_items_dataset", engine)

# Filtra só entregues
df_entregues = df_orders[df_orders['order_status'] == 'delivered'].copy()

df_entregues['dias_atraso'] = (
    df_entregues['order_delivered_customer_date'] - df_entregues['order_estimated_delivery_date']
).dt.days
df_entregues['status_entrega'] = df_entregues['dias_atraso'].apply(
    lambda x: 'Atrasado' if x > 0 else 'No Prazo'
)
df_entregues['tempo_entrega_dias'] = (
    df_entregues['order_delivered_customer_date'] - df_entregues['order_purchase_timestamp']
).dt.days

# Agrega frete e valor por pedido (um pedido pode ter vários itens)
df_frete = df_items.groupby('order_id').agg(
    valor_frete_total=('freight_value', 'sum'),
    valor_produtos_total=('price', 'sum'),
    qtd_itens=('order_item_id', 'count'),
    seller_id=('seller_id', 'first')  # pega o vendedor principal do pedido
).reset_index()

# Junta tudo
df_fato = df_entregues.merge(df_frete, on='order_id', how='left')

print(df_fato[['order_id', 'dias_atraso', 'status_entrega', 'valor_frete_total', 'seller_id']].head(10))
print(f"\nTotal de linhas na fato: {len(df_fato)}")
print(f"Colunas: {df_fato.columns.tolist()}")
print(df_frete['valor_frete_total'].describe())

# Seleciona só as colunas finais que vão pra tabela fato
df_fato_final = df_fato[[
    'order_id', 'customer_id', 'seller_id',
    'order_purchase_timestamp', 'order_delivered_customer_date', 
    'order_estimated_delivery_date', 'dias_atraso', 'status_entrega',
    'tempo_entrega_dias', 'valor_frete_total', 'valor_produtos_total', 'qtd_itens'
]].copy()

# Grava no SQL Server (cria a tabela se não existir, substitui se já existir)
df_fato_final.to_sql('fato_entregas', engine, if_exists='replace', index=False)

print("Tabela fato_entregas gravada com sucesso!")
print(f"Total de linhas gravadas: {len(df_fato_final)}")

df_sellers = pd.read_sql("SELECT * FROM olist_sellers_dataset", engine)
df_sellers.to_sql('dim_vendedores', engine, if_exists='replace', index=False)
print(f"dim_vendedores gravada: {len(df_sellers)} linhas")

df_customers = pd.read_sql("SELECT * FROM olist_customers_dataset", engine)
df_customers.to_sql('dim_clientes', engine, if_exists='replace', index=False)
print(f"dim_clientes gravada: {len(df_customers)} linhas")

# Gera um calendário cobrindo o período das datas de pedido
data_min = df_orders['order_purchase_timestamp'].min()
data_max = df_orders['order_estimated_delivery_date'].max()

datas = pd.date_range(start=data_min, end=data_max, freq='D')

df_tempo = pd.DataFrame({'data': datas})
df_tempo['ano'] = df_tempo['data'].dt.year 
df_tempo['mes'] = df_tempo['data'].dt.month
df_tempo['nome_mes'] = df_tempo['data'].dt.month_name()
df_tempo['dia'] = df_tempo['data'].dt.day
df_tempo['dia_semana'] = df_tempo['data'].dt.day_name()
df_tempo['trimestre'] = df_tempo['data'].dt.quarter

df_tempo.to_sql('dim_tempo', engine, if_exists='replace', index=False)
print(f"dim_tempo gravada: {len(df_tempo)} linhas")
print(f"Período: {data_min.date()} até {data_max.date()}")