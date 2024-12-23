# import the Flask class from the flask module
from flask import Flask, render_template, redirect, url_for, request
import db_interaction
import pandas as pd
from numbers import Number

db_conn = ""
username = ""
grants = []
tables = []
cur_table = ""
db_name = "mydb"
grant_op_mapping = {
    'SELECT':'Получить данные из таблицы',
    'INSERT':'Добавить записи в таблицу',
    'UPDATE':'Обновить записи в таблице',
    'DELETE':'Удалить записи из таблицы',
    'CREATE':'Создать таблицу',
    'DROP':'Удалить таблицу',
    'ALTER':'Изменить таблицу'
}


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    global db_conn
    global username
    global grants
    global tables
    global cur_table
    if type(db_conn) == str:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'exit' in request.form.to_dict().keys():
            db_conn.close()
            db_conn = ""
            username = ""
            grants = []
            tables = []
            return redirect(url_for('login'))
        else:
            cur_table = list(request.form.to_dict().keys())[0]
            return redirect(url_for('table_inspection'))
    if len(grants) == 0:
        grants_unfiltered = set(db_interaction.get_grants(db_conn))
        for el in grants_unfiltered:
            if el in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']:
                grants.append(el)
    tables = db_interaction.get_tables(db_conn, db_name)
    html_tables = ''
    for table in tables:
        html_tables += f"""
                <form method="post">
                    <input type="submit" value="{table}" name="{table}" style = "background-color: teal; color: white"/>
                </form>
        """
    return render_template('home.html',
                           user=username,
                           grants=', '.join(grants),
                           table_list=html_tables)

# Route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        global db_conn
        global username
        db_conn = db_interaction.connect(request.form['username'], request.form['password'])
        if type(db_conn) == str:
            error = "Неверно указано имя пользователя или пароль"
        else:
            username = request.form['username']
            return redirect(url_for('home'))
    return render_template('login.html', error=error)

@app.route('/table_inspection', methods=['GET', 'POST'])
def table_inspection():
    q_filter = ""
    if cur_table == "":
        return redirect(url_for('home'))
    if request.method == 'POST':
        if 'filter' in request.form.to_dict().keys() and len(request.form['filter'])>0:
            q_filter = f"where {request.form['filter']}"
        elif 'INSERT' in request.form.to_dict().keys() and 'INSERT' in grants:
            return redirect(url_for('insert'))
        elif 'UPDATE' in request.form.to_dict().keys() and 'UPDATE' in grants:
            return redirect(url_for('update'))
        elif 'DELETE' in request.form.to_dict().keys() and 'DELETE' in grants:
            return redirect(url_for('delete'))
        elif 'return' in request.form.to_dict().keys():
            return redirect(url_for('home'))
    data = db_interaction.get_table_data(db_conn, cur_table, db_name, q_filter)
    headers = data.columns
    data = data.values.tolist()
    op_buttons = ""
    for grant in list(grant_op_mapping.keys()):
        if grant not in ['SELECT', 'CREATE', 'ALTER', 'DROP']:
            if grant in grants:
                op_buttons += f"""
                        <form method="post">
                            <input type="submit" value="{grant_op_mapping[grant]}" name="{grant}" style = "background-color: teal; color: white"/>
                        </form>
                """
            else:
                op_buttons += f"""
                        <form method="post">
                            <input type="submit" value="{grant_op_mapping[grant]}" name="{grant}" style = "background-color: gray; color: white"/>
                        </form>
                """
    return render_template('table_inspection.html',
                           table=cur_table,
                           headers=headers,
                           data=data,
                           ops=op_buttons)


@app.route('/table_inspection/insert', methods=['GET', 'POST'])
def insert():
    if request.method == 'POST':
        f = request.files['file']
        f.save(f.filename)
        upload = pd.read_excel(f.filename)
        headers = ', '.join(upload.columns)
        upload = upload.values.tolist()
        values = ''
        for tab_row in upload:
            row = "("
            for value in tab_row:
                if isinstance(value, Number):
                    row += str(value)
                else:
                    row += f"'{value}'"
                row += ','
            row = row[:-1]
            row += "),"
            values += row
        values = values[:-1]
        db_interaction.insert_rows(db_conn,cur_table,db_name,headers,values)
        return redirect(url_for('table_inspection'))
    return render_template("insert.html",
                           table=cur_table)

@app.route('/table_inspection/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        db_interaction.update_table(db_conn,cur_table,db_name,request.form)
        return redirect(url_for('table_inspection'))
    data = db_interaction.get_table_data(db_conn, cur_table, db_name)
    headers = data.columns
    forms = ''
    forms += '<form method="post">'
    for field in headers:
        forms += field
        forms += ': <input type="text" name="'+field+'">'
        forms += '<br>'
    forms += '<br>'
    forms += 'Условие для замены: <input type="text" name="condition">'
    forms += '<input type = "submit" value="Внести изменения">'
    forms += '</form>'
    return render_template('update.html',
                           table=cur_table,
                           field_forms=forms)

@app.route('/table_inspection/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        db_interaction.delete_from_table(db_conn,cur_table,db_name,request.form['condition'])
        return redirect(url_for('table_inspection'))
    return render_template('delete.html',
                           table=cur_table)

# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True)
