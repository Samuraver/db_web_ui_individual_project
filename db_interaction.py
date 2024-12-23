import mysql.connector
import pandas as pd

def connect(username, password):
    try:
        conn = mysql.connector.connect(
            user = username,
            password = password,
            host = "127.0.0.1",
            database = "mydb"
        )
        return conn
    except mysql.connector.Error as err:
        return str(err)

def get_grants(conn):
    cur = conn.cursor()
    cur.execute('show grants;')
    return cur.fetchall()[0][0].replace(',', '').split(' ')

def get_tables(conn, db):
    cur = conn.cursor()
    cur.execute(f'use {db};')
    cur.execute('show tables;')
    return [item[0] for item in cur.fetchall()]

def get_table_data(conn, table, db, filter=''):
    return pd.read_sql(f'select * from {db}.{table} {filter};', conn)

def insert_rows(conn, table, db, headers, values):
    cur = conn.cursor()
    cur.execute(f'use {db};')
    cur.execute(f'insert into {table} ({headers}) values {values};')
    conn.commit()

def update_table(conn, table, db, values):
    cur = conn.cursor()
    cur.execute(f'use {db};')
    q_set = ''
    for field in list(values.keys()):
        if values[field] != '' and field!='condition':
            if values[field].isnumeric():
                q_set += f'{field}={values[field]},'
            else:
                q_set += f'{field}="{values[field]}",'
    q_set=q_set[:-1]
    cur.execute(f'update {table} set {q_set} where {values["condition"]};')
    conn.commit()

def delete_from_table(conn, table, db, condition):
    cur = conn.cursor()
    cur.execute(f'use {db};')
    cur.execute(f'delete from {table} where {condition};')
    conn.commit()
