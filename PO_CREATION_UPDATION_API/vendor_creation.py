import xmlrpc.client
from serverconncetion import ServerConnection
from error_handling import ErrorHandling

class VendorCreation:
    def create_vendor(order_data,file_name,file_id, error_folder_id):
  
        uid, url, db, password = ServerConnection.connection()  
        vendor_data={}
        #header data             
        try:
               vendor_data['id'] = order_data['partner_id']   #vendor id
               vendor_data['name']=order_data['partner_ref']  #vendor name
               vendor_data['sap_vendor_id']=order_data['partner_id']  #vendor name
        except ValueError as e:
             error_message = f"Error: Invalid value in XML: {str(e)}"
             print(error_message)
             ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models)   

        except TypeError as e: 
             error_message = f"Error while fetching value for vendor creation:{str(e)}"
             print(error_message)
             ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models)         
        try:
           models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
           #creating vendor
           partner_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [vendor_data])
           print("created vendor ->", partner_id)
        except xmlrpc.client.Fault as e:
             error_message = f"Error creating vendor:{str(e)}"
             print(error_message)
             ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models)                                      
        except Exception as e:
             error_message = f"Unexpected error occurred during vendor creation:{str(e)}"
             print(error_message)
             ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models)                         
            
            
        return partner_id  
     