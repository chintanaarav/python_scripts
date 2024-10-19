import xmlrpc.client
import xml.etree.ElementTree as ET
import base64
from datetime import datetime
import logging

# Set up logging
LOG_FILENAME = 'purchase_order_error_log.txt'
logging.basicConfig(filename=LOG_FILENAME, level=logging.ERROR, 
                    format='%(asctime)s %(levelname)s %(message)s')

# Odoo credentials and URL
url = "https://cocreateaarav-itgnew-itgdev-15781887.dev.odoo.com/"  # Odoo instance URL/IP address
db = "cocreateaarav-itgnew-itgdev-15781887"  # Odoo database name
username = "john@yopmail.com"  # Instance username
password = "123456"  # Instance password

# Folder ID in the Documents module where the file should be stored
FOLDER_ID = 14  # Replace this with the actual folder ID in your Odoo system

def fetch_purchase_orders(uid, models):
    try:
        # Fetch purchase orders where 'x_xml_generated' is False
        domain = [['state', '=', 'purchase'], ['xml_generated', '=', False]]
        fields = ['sap_po_number', 'amount_total', 'id']
        purchase_orders = models.execute_kw(
            db, uid, password,
            'purchase.order', 'search_read',
            [domain],
            {'fields': fields}
        )
        return purchase_orders
    except xmlrpc.client.Fault as fault:
        logging.error(f"XML-RPC Fault while fetching purchase orders: {fault}")
        raise
    except Exception as e:
        logging.error(f"Error fetching purchase orders: {e}")
        raise

def purchase_order_to_xml(purchase_order):
    """Convert a single purchase order to XML."""
    try:
        root = ET.Element('ORDERS05')
        idoc = ET.SubElement(root, 'IDOC')

        # Create 'E1EDK01' sub-element for purchase order header data
        order_elem = ET.SubElement(idoc, 'E1EDK01')
        belnr = ET.SubElement(order_elem, 'BELNR')
        belnr.text = purchase_order.get('sap_po_number', '')  # SAP purchase order number

        # Create 'E1EDS01' sub-element for amount data
        e1eds01_elem = ET.SubElement(idoc, 'E1EDS01')
        summe = ET.SubElement(e1eds01_elem, 'SUMME')
        summe.text = str(purchase_order.get('amount_total', 0))  # Total amount

        return ET.ElementTree(root)
    except Exception as e:
        logging.error(f"Error creating XML from purchase order {purchase_order['id']}: {e}")
        raise

def generate_filename_with_belnr(purchase_order):
    """Generate a filename using BELNR and a timestamp."""
    try:
        # Extract the BELNR (SAP Purchase Order Number) from the order
        belnr = purchase_order.get('sap_po_number', 'unknown')

        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Create filename with BELNR and timestamp
        return f'{belnr}_{timestamp}.xml'
    except Exception as e:
        logging.error(f"Error generating filename for purchase order {purchase_order['id']}: {e}")
        raise

def save_xml_to_odoo(tree, models, uid, file_name, folder_id):
    """Upload the XML file to Odoo's document management system."""
    try:
        # Convert XML tree to a string
        xml_str = ET.tostring(tree.getroot(), encoding='utf-8', method='xml')

        print(f"Generated XML:\n{xml_str.decode('utf-8')}")  # Print the XML content for debugging

        # Encode the XML content in base64
        xml_base64 = base64.b64encode(xml_str).decode('utf-8')

        # Create an attachment
        attachment_data = {
            'name': file_name,
            'type': 'binary',
            'datas': xml_base64,
            'res_model': 'documents.document',  # Model where the file should be attached
            'res_id': False,  # Can be linked to a specific record, or leave False for general upload
            'mimetype': 'application/xml',
            'folder_id': folder_id  # Folder ID where the file should be saved
        }

        # Create an attachment in Odoo's 'documents.document' model
        attachment_id = models.execute_kw(db, uid, password,
                                          'documents.document', 'create', [attachment_data])
        print(f"File uploaded to Odoo with attachment ID {attachment_id}, saved in folder ID {folder_id}")
    except xmlrpc.client.Fault as fault:
        logging.error(f"XML-RPC Fault while uploading XML: {fault}")
        raise
    except Exception as e:
        logging.error(f"Error uploading XML to Odoo for file {file_name}: {e}")
        raise

def update_purchase_order_status(models, uid, order_id):
    """Mark the purchase order as having its XML generated."""
    try:
        models.execute_kw(db, uid, password, 'purchase.order', 'write', [[order_id], {'xml_generated': True}])
        print(f"Purchase order {order_id} marked as XML generated.")
    except Exception as e:
        logging.error(f"Error updating purchase order status for order {order_id}: {e}")
        raise

def main():
    try:
        # Authenticate and get the purchase orders
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        if uid is False:
            logging.error(f"Authentication failed. Check your credentials.")
            raise
        
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

        # Fetch the purchase orders that haven't had XML generated
        purchase_orders = fetch_purchase_orders(uid, models)

        if purchase_orders:
            # Process each purchase order one by one
            for order in purchase_orders:
                try:
                    # Generate the XML structure for this purchase order
                    tree = purchase_order_to_xml(order)

                    # Generate a filename that includes BELNR and timestamp
                    file_name = generate_filename_with_belnr(order)

                    # Upload the XML as a document to Odoo's DMS (Documents module)
                    save_xml_to_odoo(tree, models, uid, file_name, FOLDER_ID)

                    # Mark the purchase order as having its XML generated
                    update_purchase_order_status(models, uid, order['id'])

                except Exception as e:
                    logging.error(f"Error processing purchase order {order['id']}: {e}")
                    continue  # Continue with the next purchase order if there's an error
        else:
            print("No purchase orders to process.")
    except Exception as e:
        logging.error(f"An error occurred during execution: {e}")

if __name__ == '__main__':
    main()