from flask import Flask, render_template, request, redirect, json
import mysql.connector
from mysql.connector import Error
from cheroot import wsgi
from configparser import ConfigParser

#configs
config = ConfigParser()
config.read('conf')
#----------------service-----------------------
host = config.get('service', 'host')
port = config.get('service', 'port')
url = config.get('service', 'url')
#-----------------DataBase---------------------
dbhost = config.get('database', 'host')
dbport = config.get('database', 'port')
dbuser = config.get('database', 'user')
dbpassword = config.get('database', 'pass')
dbname = config.get('database', 'name')
#----------------logging-----------------------
logEnable = config.get('logging', 'logEnable')
pathLog = config.get('logging', 'fileLog')
#----------------params------------------------

app = Flask(__name__)
d = wsgi.WSGIPathInfoDispatcher({'/': app.wsgi_app})
server = wsgi.Server((host, int(port)), d)

@app.route('/termos', methods=["POST","GET"])
def method():
    if request.method == 'GET': return render_template("index.html")
    if request.method == 'POST':
       header = str(request.headers).splitlines()
       data = request.form.to_dict()
       log(str(data))
       data['headers'] = str(header)
       resp = storagedata(data)
       if resp != 1: return resp
       return redirect("https://userintegrity-ui.latallynis.gemalto.com/", code=200)


def storagedata(data):
    values = [data['name'], data['email'], data['cpf'], data['headers']]
    fields = ['subscribe_name', 'subscribes_email', 'subscribes_cpf', 'subscribes_headers']
    args = {'table': 'terms_subscribes', 'fields': fields, 'values': values}
    resp = sqlfunction('insert', args)
    if resp[1] == 0:
        print('deu erro: '+resp[0])
        if 'subscribes_cpf_UNIQUE' in resp[0]:
            return 'Esse CPF já foi cadastrado. Clique <a href=%s>aqui</a> e tente novamente.' %(url)
        if 'subscribes_email_UNIQUE' in resp[0]:
            return 'Esse email já foi cadastrado. Clique <a href=%s>aqui</a> e tente novamente.' %(url)
    return 1


def sqlfunction(dmltype,args):
    con = connectDB()
    if con == 0: return 0
    if dmltype == 'insert':
        table = args['table']
        fields = str(args['fields']).replace('[', '(').replace(']', ')').replace("'", "")
        values = str(args['values']).replace('[', '(').replace(']', ')')
        strSQL = 'insert into %s %s values %s;' % (table, fields, values)
    if dmltype == 'update':
        strSQL=''
    if dmltype == 'delete':
        strSQL=''
    if dmltype == 'select':
        strSQL=''
    cursor = con.cursor()
    try:
        rec = cursor.execute(strSQL)
        con.commit()
    except Error as e:
        return [str(e),0]

    return [rec, 1]



def connectDB():
    try:
        con = mysql.connector.connect(host=dbhost, port=dbport, database=dbname, user=dbuser, password=dbpassword)
        if con.is_connected():
            db_Info = con.get_server_info()
            log("Connected to MySQL Server version " + str(db_Info))
            cursor = con.cursor()
            cursor.execute("select database();")
            record = cursor.fetchone()
            log("You're connected to database: " + str(record[0]))
            cursor.close()
    except Error as e:
        log(e)
        return 0;
    return con


def log(msg):
    if logEnable == '1':
        with open(pathLog, "a+") as myfile:
            myfile.write(msg+'\n')


if __name__ == '__main__':
    app.static_url_path = ''
    app.static_folder = 'templates/static'
    if hasattr(server, 'signal_handler'):
        server.signal_handler.subscribe()
    try:
        server.start()

    except KeyboardInterrupt:
        server.stop()