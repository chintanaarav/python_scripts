import xmlrpc.client

class ServerConnection:
     
     def connection(self):

       # Odoo credentials and URL
       url = "https://cocreateaarav-itgnew-itgdev-15781887.dev.odoo.com/"  # Odoo instance URL/IP address
       db = "cocreateaarav-itgnew-itgdev-15781887"  # Odoo database name
       username = "john@yopmail.com"  # Instance username
       password = "123456"  # Instance password


       #getting server version
       common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
       #authentication
       uid = common.authenticate(db, username, password, {})

       return uid,url,db,password