import xmlrpc.client
from serverconncetion import ServerConnection
from error_handling import ErrorHandling

class PurchaseOrderCreation:
    PURCHASE_ORDER_MODEL = 'purchase.order'  # Define the constant

    def create_purchase_order(self, order_data, file_name, file_id, error_folder_id):
        uid, url, db, password = ServerConnection.connection()
        created_id = None  # Initialize created_id to None
        try:
            models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
            # Creating purchase order  
            created_id = models.execute_kw(db, uid, password, self.PURCHASE_ORDER_MODEL, 'create', [order_data])
            # Confirming purchase order
            models.execute_kw(db, uid, password, self.PURCHASE_ORDER_MODEL, 'button_confirm', [created_id])
        except xmlrpc.client.Fault as e:
            error_message = f"Error while creating Purchase order: {str(e)}"
            ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models)
        except Exception as e:
            error_message = f"Unexpected error occurred during purchase order: {str(e)}"
            print(error_message)
            ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models)
        return created_id

    def update_purchase_order(self, order_data, file_name, file_id, error_folder_id, models, uid, db, password):
        try:
            purchase_order_id = order_data['sap_po_number']  # Assuming this is the identifier
            # Fetch the existing purchase order
            purchase_order = models.execute_kw(db, uid, password, self.PURCHASE_ORDER_MODEL, 'search_read', 
                                                [[['sap_po_number', '=', purchase_order_id]]])
            print("Purchase order", purchase_order)
            if not purchase_order:
                raise ValueError(f"Purchase order with ID {purchase_order_id} not found.")
        
            purchase_order_id = purchase_order[0]['id']  # Get the actual ID for further operations
            print("Purchase id", purchase_order_id)

            # Fetch existing order lines
            existing_order_line_ids = purchase_order[0]['order_line']
            print("Existing order line id", existing_order_line_ids)
            existing_order_lines = models.execute_kw(db, uid, password, 'purchase.order.line', 'read', 
                                                     [existing_order_line_ids])
            print("Existing order lines", existing_order_lines)

            # Prepare lists for updates and new lines
            updated_order_lines = []
            new_order_lines = []
        
            # Map existing product IDs for easy lookup
            existing_product_map = {line['product_id'][0]: line for line in existing_order_lines}

            # Loop through incoming order lines
            for incoming_line in order_data['order_line']:
                incoming_product_id = incoming_line[2]['product_id']

                if incoming_product_id in existing_product_map:
                    # Update the existing order line
                    existing_line = existing_product_map[incoming_product_id]
                    updated_order_lines.append(
                        (1, existing_line['id'], {
                            'product_qty': incoming_line[2]['product_qty'],
                            'price_unit': incoming_line[2]['price_unit'],
                            'date_planned': incoming_line[2]['date_planned']
                        })
                    )
                else:
                    # Add new order line
                    new_order_lines.append(incoming_line)

            # Combine updated and new lines into final order data
            order_data['order_line'] = updated_order_lines + new_order_lines

            print("Updated order data", order_data)

            # Update the purchase order
            result = models.execute_kw(db, uid, password, self.PURCHASE_ORDER_MODEL, 'write', [[purchase_order_id], order_data])

        except xmlrpc.client.Fault as e:
            error_message = f"Error updating purchase order: {str(e)}"
            print(error_message)
            ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models)

        except Exception as e:
            error_message = f"Unexpected error while updating purchase order: {str(e)}"
            print(error_message)
            ErrorHandling.handle_error(file_id, error_folder_id, file_name, error_message, models)

        return result
