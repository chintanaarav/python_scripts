import xmlrpc.client
from serverconncetion import ServerConnection
from error_handling import ErrorHandling

class ProductCreation:
    def __init__(self, product_lines, file_name, file_id, error_folder_id, models, uid, db, password):
        self.product_lines = product_lines
        self.file_name = file_name
        self.file_id = file_id
        self.error_folder_id = error_folder_id
        self.models = models  # Use the models passed in the constructor
        self.uid = uid  # Store UID for use in methods
        self.db = db  # Store DB for use in methods
        self.password = password  # Store password for use in methods        

    def create_product_with_no(self):

        product_data = {}

        try:
            # with material no
            product_data['id'] = self.product_lines[2]['product_id']  # product id
            product_data['name'] = self.product_lines[2]['name']  # product name
            product_data['default_code'] = self.product_lines[2]['product_id']  # internal reference
            print(product_data)

            # creating product
            product_ids = self.models.execute_kw(self.db, self.uid, self.password, 'product.product', 'create', [product_data])
            print("Created product ->", product_ids)

        except (ValueError, TypeError) as e:
            error_message = f"Error during product creation: {str(e)}"
            print(error_message)
            ErrorHandling.handle_error(self.file_id, self.error_folder_id, self.file_name, error_message, self.uid, self.db, self.password, self.models)

        return product_ids

    def create_product_without_no(self):

        product_data = {}

        try:
            # without material no
            product_data['name'] = self.product_lines[2]['name']  # product name
            print(product_data)

            # creating product
            product_ids = self.models.execute_kw(self.db, self.uid, self.password, 'product.product', 'create', [product_data])  # creating product
            print("Created product ->", product_ids)

        except (ValueError, TypeError) as e:
            error_message = f"Error during product creation: {str(e)}"
            print(error_message)
            ErrorHandling.handle_error(self.file_id, self.error_folder_id, self.file_name, error_message, self.uid, self.db, self.password, self.models)

        return product_ids
