import pandas as pd
from sqlalchemy import create_engine

# Создайте соединение с вашей базой данных PostgreSQL
engine = create_engine('postgresql://postgres:12345@localhost:5433/postgres')

# Загрузите данные из CSV
contracts = pd.read_excel('C:\\Users\\mi\\Documents\\Diplom_Ali4i4\\Buying Hub Update feb 2025 (1).xlsx')
tenders = pd.read_excel("C:\\Users\\mi\\Documents\\Diplom_Ali4i4\\DB tenders final.xlsx")
procurement = pd.read_excel('C:\\Users\\mi\\Documents\\Diplom_Ali4i4\\Responsible buyers per HACAT 2024.xlsx')

# Загрузите данные в PostgreSQL
contracts.to_sql('contracts', engine, if_exists='replace', index=False)
tenders.to_sql('tenders', engine, if_exists='replace', index=False)
procurement.to_sql('procurement', engine, if_exists='replace', index=False)