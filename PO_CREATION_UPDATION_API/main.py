import os
import xmltodict as ET
import xmlrpc.client
import base64
import traceback
from io import BytesIO
import re
from xmltodictionary import XmlToDictionary
from serverconncetion import ServerConnection
from vendor_creation import VendorCreation
from error_handling import  ErrorHandling
from product_creation import ProductCreation
from purchase_order_creation import PurchaseOrderCreation

class Main:
  
   def main():
        uid, url, db, password = ServerConnection.connection() 
       # Define folder IDs (replace with your folder IDs)
        source_folder_id = 9  # ID of the source folder containing XML files
        processed_folder_id = 12  # ID of the folder to move processed files
        error_folder_id = 13  # ID of the folder to move error files
        #getting details from odoo server                               
        if uid :
           print("authentication succeeded")
           models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))   
           # Fetch XML documents from the source folder based on timestamp  
           xml_files = models.execute_kw(db, uid, password, 'documents.document', 'search_read',
                                  [[['folder_id', '=', source_folder_id], ['name', 'ilike', '.xml']]],
                                  {'fields': ['id', 'name', 'datas']})
            
           if xml_files:
               # Sort files by timestamp in their names
               xml_files.sort(key=lambda x: re.search(r'\d{8}_\d{6}', x['name']).group(0) if re.search(r'\d{8}_\d{6}', x['name']) else '')
               # Process each XML file
               for xml_file in xml_files:
                  file_id = xml_file['id']
                  file_name = xml_file['name']
                  file_data = xml_file['datas']

                  # Decode the Base64 encoded data
                  decoded_data = base64.b64decode(file_data)
                  print(f"Contents of {file_name}:",decoded_data)

                  # Convert bytes to a file-like object using BytesIO
                  xml_data = ET.parse(BytesIO(decoded_data))
                  print("parsedata",xml_data)
                  order_data = XmlToDictionary.parse_xml(xml_data) 
                  print(order_data)                  

                  if  order_data: 
                      
                      #fetching PO creator detail
                      sap_user_id=order_data['sap_user_id']
                      user_id=models.execute_kw(db,uid,password,'res.users', 'search',
                                    [[['sap_user_id', '=',sap_user_id ]]])
                      print(user_id)
                      if user_id:
                         order_data['user_id']=user_id[0] #passing user_id into order_data for PO creation
                         order_data.pop('sap_user_id')
                         print(order_data)

                      #fetching vendor deta
                      vendor_id=order_data['partner_id']
                      try:
                         #searching vendor id
                         partner_id=models.execute_kw(db,uid,password,'res.partner', 'search',
                                    [[['sap_vendor_id', '=',vendor_id ]]])  
                         if partner_id: #checking vendor id
                             order_data['partner_id']=partner_id[0]
                         else: #creating vendor
                             partner_id=VendorCreation.create_vendor(order_data,file_name,file_id, error_folder_id)   
                             order_data['partner_id']=partner_id
                      except Exception as e:
                        error_message = f"Error creating vendor: {str(e)}"
                        print(error_message)
                        ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models)
                        continue
                         #product searching and creation
                      try:
                        product_lines= order_data['order_line'] 
                        #print(product_lines)
                        for p1 in product_lines:  
                            product_id = p1[2]['product_id']
                            product_name=p1[2]['name']
                            #searching product id
                            product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', 
                                     [['|', ['default_code', '=', product_id], ['name', '=', product_name]]])
                            print("Product id",product_ids)
                               #checking product id
                            if product_ids: 
                                  p1[2]['product_id']=product_ids[0]
                                  #creating product    
                            else:
                                  product_ids=ProductCreation.create_product_with_no(p1,file_name,file_id, error_folder_id)   
                                  p1[2]['product_id']=product_ids                                                         
                      except Exception as e:
                         # Construct the new path
                         error_message = f"Error creating vendor: {str(e)}"
                         print(error_message)
                         ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models) 
                         continue
                       #purchase order creation and updatation  
                      try: 
                          purchase_id=order_data['sap_po_number'] 
                          print("Purchase id",purchase_id)
                         #searching purchase order which dont have state purchase
                          purchase_ids = models.execute_kw(db, uid, password,'purchase.order', 'search',
                                      [[['sap_po_number', '=', purchase_id ],['state', '!=', 'purchase']]])
                          print("searching purchase order id",purchase_ids)
                              
                          if purchase_ids :                                   
                              #updating purhcase order
                              print(order_data)
                              result=PurchaseOrderCreation.update_purchase_order(order_data,file_name,file_id, error_folder_id,models,uid,db,password) 
                              print(result)                            
                              #reading purchase order
                              if result:  
                                 print(f"Purchase Order updated successfully: {purchase_ids}")
                                 message = f"Purchase Order {purchase_id} has been updated."
                                 models.execute_kw(db, uid, password, 'purchase.order', 'message_post', 
                                                                   [purchase_ids], {'body': message})                                                                       
                                 # Move file to processed folder
                                 models.execute_kw(db, uid, password, 'documents.document', 'write', [[file_id], {'folder_id': processed_folder_id}])        
                          else:                           
                            #creating purchase order 
                            order_id=PurchaseOrderCreation.create_purchase_order(order_data,file_name,file_id, error_folder_id) 
                            #reading purchase order
                            if order_id:
                              print("created Purchase order ->", order_id)                                        
                              # Rename (or move) the file to the new directory processed
                              models.execute_kw(db, uid, password, 'documents.document', 'write', [[file_id], {'folder_id': processed_folder_id}])                                        
                      except xmlrpc.client.Fault as e:
                         # Construct the new path
                         error_message = f"Unexpected error Error creating/updating purchase order:'{file_name}': {str(e)}"
                         print(error_message) 
                         ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models) 
                         continue   
                  else: 
                    error_message = f"Unexpected error while creating data:'{file_name}'"
                    print("Unexpected error while creating data")    
                    ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models) 
                    continue                      
           else:    
              error_message = "No files found in Doucments"
              print(error_message)
              ErrorHandling.handle_error(None, error_folder_id, "authentication_error.txt", error_message, None)              
              exit()                            
        else:
          error_message = "Authentication failed. Unable to connect to the Odoo server."
          print(error_message)
          ErrorHandling.handle_error(None, error_folder_id, "authentication_error.txt", error_message, None)
          exit()
                                  
#main()
if __name__ == "__main__":
    Main.main()