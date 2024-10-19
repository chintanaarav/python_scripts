import xmlrpc.client
from serverconncetion import ServerConnection
from error_handling import ErrorHandling

class ProductCreation:
    def __init__(self, product_lines, file_name, file_id, error_folder_id):
        self.product_lines = product_lines
        self.file_name = file_name
        self.file_id = file_id
        self.error_folder_id = error_folder_id

    def create_product_with_no(self):
        uid, url, db, password = ServerConnection.connection()
        product_data = {}

        try:
            # with material no
            product_data['id'] = self.product_lines[2]['product_id']  # product id
            product_data['name'] = self.product_lines[2]['name']  # product name
            product_data['default_code'] = self.product_lines[2]['product_id']  # internal reference
            print(product_data)

            # creating product
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
            product_ids = models.execute_kw(db, uid, password, 'product.product', 'create', [product_data])
            print("Created product ->", product_ids)

        except (ValueError, TypeError) as e:
            error_message = f"Error during product creation: {str(e)}"
            print(error_message)
            ErrorHandling.handle_error(self.file_id, self.error_folder_id, self.file_name, error_message, None)

        return product_ids

    def create_product_without_no(self):
        uid, url, db, password = ServerConnection.connection()
        product_data = {}

        try:
            # without material no
            product_data['name'] = self.product_lines[2]['name']  # product name
            print(product_data)

            # creating product
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
            product_ids = models.execute_kw(db, uid, password, 'product.product', 'create', [product_data])  # creating product
            print("Created product ->", product_ids)

        except (ValueError, TypeError) as e:
            error_message = f"Error during product creation: {str(e)}"
            print(error_message)
            ErrorHandling.handle_error(self.file_id, self.error_folder_id, self.file_name, error_message, None)

        return product_ids
