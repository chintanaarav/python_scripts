import xmlrpc.client
from dotenv import load_dotenv
import os

class ServerConnection:
     
     def __init__(self):
        # Load environment variables from the specified file
        load_dotenv('/home/odoo/src/myenv/hashkey.env')     
     
     def connection(self):

       # Odoo credentials and URL
       url = "https://cocreateaarav-itgnew-itgdev-15781887.dev.odoo.com/"  # Odoo instance URL/IP address
       db = "cocreateaarav-itgnew-itgdev-15781887"  # Odoo database name
       username = os.getenv("ODOO_USERNAME")  # Fetching username from .env file
       password = os.getenv("ODOO_PASSWORD")  # Fetching password from .env file


       #getting server version
       common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
       #authentication
       uid = common.authenticate(db, username, password, {})

       return uid,url,db,password