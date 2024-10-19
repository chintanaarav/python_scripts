import xmlrpc.client
from serverconncetion import ServerConnection
from error_handling import ErrorHandling



class ProductCreation:
    def create_product_with_no(product_lines,file_name,file_id, error_folder_id):
        uid, url, db, password = ServerConnection.connection()
        product_data={}
        #header data             
        try: 
             #with material no              
            product_data['id'] = product_lines[2]['product_id']   #product id
            product_data['name']=product_lines[2]['name']  #product name             
            product_data['default_code']=product_lines[2]['product_id']  #internal refrence
            print(product_data)
             #creating product            
            try:
               models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))           
               product_ids = models.execute_kw(db, uid, password, 'product.product', 'create', [product_data])
               print("created product ->", product_ids)           
            except (Exception,xmlrpc.client.Fault) as e:                    
                error_message = f"Unexpected error occurred during product creation:{str(e)}"
                print(error_message)                     
                ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models)                                       
        except ValueError as e:                    
            error_message = f"Error: Invalid value in XML for product:{str(e)}"
            print(error_message)
            ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models)        
        except TypeError as e:                 
            error_message = f"Error Product creation:{str(e)}"
            print(error_message)
            ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models) 
      
        return product_ids
    
    def create_product_without_no(product_lines,file_name,file_id, error_folder_id):
        uid, url, db, password = ServerConnection.connection()
        product_data={}
        try:
          #without material no 
          #product_data['id'] = product_lines[2]['product_id']   #product id
          product_data['name']=product_lines[2]['name']  #product name             
          #product_data['default_code']=product_lines[2]['product_id']  #internal refrence
          print(product_data)
          #creating product            
          try:
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))           
            product_ids = models.execute_kw(db, uid, password, 'product.product', 'create', [product_data]) #creating product
            print("created product ->", product_ids)
          except (Exception,xmlrpc.client.Fault) as e:                    
            error_message = f"Unexpected error occurred during product creation:{str(e)}"
            print(error_message)                     
            ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models)
        except ValueError as e:                    
            error_message = f"Error: Invalid value in XML for product:{str(e)}"
            print(error_message)
            ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models)        
        except TypeError as e:                 
            error_message = f"Error Product creation:{str(e)}"
            print(error_message)
            ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models) 
      
        return product_ids            