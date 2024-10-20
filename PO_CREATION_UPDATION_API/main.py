import os
import xmltodict as ET
import xmlrpc.client
import xml.parsers.expat
import base64
from io import BytesIO
import re
from xmltodictionary import XmlToDictionary
from serverconncetion import ServerConnection
from vendor_creation import VendorCreation
from error_handling import ErrorHandling
from product_creation import ProductCreation
from purchase_order_creation import PurchaseOrderCreation


class Main:
    DOCUMENTS_MODEL = 'documents.document'  # Define the constant

    @staticmethod
    def main():
        uid, url, db, password = ServerConnection().connection()
        source_folder_id = 9  # Source folder ID
        processed_folder_id = 12  # Processed folder ID
        error_folder_id = 13  # Error folder ID

        if uid:
            print("Authentication succeeded")
            models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
            xml_files = Main.fetch_xml_files(models, db, uid, password, source_folder_id)

            if xml_files:
                Main.process_xml_files(xml_files, models, db, uid, password, processed_folder_id, error_folder_id)
            else:
                Main.handle_no_files_found()

        else:
            Main.handle_authentication_failure()

    @staticmethod
    def fetch_xml_files(models, db, uid, password, folder_id):
        return models.execute_kw(db, uid, password, Main.DOCUMENTS_MODEL, 'search_read',
                                 [[['folder_id', '=', folder_id], ['name', 'ilike', '.xml']]],
                                 {'fields': ['id', 'name', 'datas']})

    @staticmethod
    def process_xml_files(xml_files, models, db, uid, password, processed_folder_id, error_folder_id):
        xml_files.sort(key=lambda x: re.search(r'\d{8}_\d{6}', x['name']).group(0) if re.search(r'\d{8}_\d{6}', x['name']) else '')
        print(xml_files)
        for xml_file in xml_files:
            Main.process_single_xml_file(xml_file, models, db, uid, password, processed_folder_id, error_folder_id)

    @staticmethod
    def process_single_xml_file(xml_file, models, db, uid, password, processed_folder_id, error_folder_id):
        file_id = xml_file['id']
        file_name = xml_file['name']
        file_data = xml_file['datas']

        try:
          decoded_data = base64.b64decode(file_data)
          xml_data = ET.parse(BytesIO(decoded_data))
          order_data = XmlToDictionary().parse_xml(xml_data)

          if order_data:
            Main.process_order_data(order_data, models, db, uid, password, file_name, file_id, processed_folder_id, error_folder_id)
          else:
            Main.handle_unexpected_error(file_id, error_folder_id, file_name, uid, db, password, models)
            return
        except xml.parsers.expat.ExpatError as e:
            error_message = f"XML parsing error in file {xml_file['name']}: {e}"
            print(error_message)
            ErrorHandling().handle_error(file_id, error_folder_id, file_name, error_message,uid, db, password, models)
            return 
        # Move the file to the error folder or handle it appropriately
        except Exception as e:
            error_message = f"Unexpected error in file {xml_file['name']}: {e}"
            print(error_message)
            ErrorHandling().handle_error(file_id, error_folder_id, file_name, error_message,uid, db, password, models)
            return          
    @staticmethod
    def process_order_data(order_data, models, db, uid, password, file_name, file_id, processed_folder_id, error_folder_id):
        sap_user_id = order_data['sap_user_id']
        user_id = Main.fetch_user_id(models, db, uid, password, sap_user_id)

        if user_id:
            order_data['user_id'] = user_id[0]
            order_data.pop('sap_user_id')
            print(order_data)

        partner_id = Main.fetch_or_create_vendor(order_data, models, db, uid, password, file_name, file_id, error_folder_id)
        order_data['partner_id'] = partner_id

        Main.process_order_lines(order_data, models, db, uid, password, file_name, file_id, error_folder_id)

        Main.create_or_update_purchase_order(order_data, models, db, uid, password, file_name, file_id, processed_folder_id, error_folder_id)

    @staticmethod
    def fetch_user_id(models, db, uid, password, sap_user_id):
        return models.execute_kw(db, uid, password, 'res.users', 'search',
                                 [[['sap_user_id', '=', sap_user_id]]])

    @staticmethod
    def fetch_or_create_vendor(order_data, models, db, uid, password, file_name, file_id, error_folder_id):
        vendor_id = order_data['partner_id']
        try:
            partner_id = models.execute_kw(db, uid, password, 'res.partner', 'search',
                                           [[['sap_vendor_id', '=', vendor_id]]])
            if partner_id:
                return partner_id[0]
            else:
                return VendorCreation().create_vendor(order_data, models, db, uid, password, file_name, file_id, error_folder_id)
        except Exception as e:
            error_message = f"Error creating vendor: {str(e)}"
            print(error_message)
            ErrorHandling().handle_error(file_id, error_folder_id, file_name, error_message,uid, db, password, models)
            return 

    @staticmethod
    def process_order_lines(order_data, models, db, uid, password, file_name, file_id, error_folder_id):
        product_lines = order_data['order_line']
        for p1 in product_lines:
            product_id = p1[2]['product_id']
            product_name = p1[2]['name']
            product_ids = models.execute_kw(db, uid, password, 'product.product', 'search',
                                             [['|', ['default_code', '=', product_id], ['name', '=', product_name]]])
            print("Product id", product_ids)

            if product_ids:
                p1[2]['product_id'] = product_ids[0]
            else:
                product_ids = ProductCreation().create_product_with_no(p1, models, db, uid, password, file_name, file_id, error_folder_id)
                p1[2]['product_id'] = product_ids

    @staticmethod
    def create_or_update_purchase_order(order_data, models, db, uid, password, file_name, file_id, processed_folder_id, error_folder_id):
        purchase_id = order_data['sap_po_number']
        print("Purchase id", purchase_id)
        purchase_ids = models.execute_kw(db, uid, password, 'purchase.order', 'search',
                                          [[['sap_po_number', '=', purchase_id], ['state', '!=', 'purchase']]])
        print("Searching purchase order id", purchase_ids)

        try:
            if purchase_ids:
                result = PurchaseOrderCreation().update_purchase_order(order_data, file_name, file_id, error_folder_id, models, uid, db, password)

                if result:
                    print(f"Purchase Order updated successfully: {purchase_ids}")
                    message = f"Purchase Order {purchase_id} has been updated."
                    models.execute_kw(db, uid, password, 'purchase.order', 'message_post',
                                      [purchase_ids], {'body': message})

                    models.execute_kw(db, uid, password, Main.DOCUMENTS_MODEL, 'write', [[file_id], {'folder_id': processed_folder_id}])
            else:
                order_id = PurchaseOrderCreation().create_purchase_order(order_data, file_name, file_id, error_folder_id, models, uid, db, password)
                if order_id:
                    print("Created Purchase order ->", order_id)
                    models.execute_kw(db, uid, password, Main.DOCUMENTS_MODEL, 'write', [[file_id], {'folder_id': processed_folder_id}])
        except xmlrpc.client.Fault as e:
            error_message = f"Unexpected error while creating/updating purchase order: '{file_name}': {str(e)}"
            print(error_message)
            ErrorHandling().handle_error(file_id, error_folder_id, file_name, error_message,uid, db, password, models)
            return
    @staticmethod
    def handle_unexpected_error(file_id, error_folder_id, file_name, uid, db, password, models):
        error_message = f"Unexpected error while creating data: '{file_name}'"
        print("Unexpected error while creating data")
        ErrorHandling().handle_error(file_id, error_folder_id, file_name, error_message, uid, db, password, models)

    @staticmethod
    def handle_no_files_found():
        error_message = "No files found in Documents"
        print(error_message)
         # Get the directory where the script is located
        script_directory = os.path.dirname(os.path.abspath(__file__))
        error_file_path = os.path.join(script_directory, "no_file_found.txt")
        # Write the error message to a file in the current script's directory
        with open(error_file_path, 'w') as error_file:
          error_file.write(error_message)
        exit()

    @staticmethod
    def handle_authentication_failure():
        error_message = "Authentication failed. Unable to connect to the Odoo server."
        print(error_message)
        # Get the directory where the script is located
        script_directory = os.path.dirname(os.path.abspath(__file__))
        error_file_path = os.path.join(script_directory, "authentication_error.txt")
        # Write the error message to a file in the current script's directory
        with open(error_file_path, 'w') as error_file:
          error_file.write(error_message)
        exit()


# main()
if __name__ == "__main__":
    Main.main()
