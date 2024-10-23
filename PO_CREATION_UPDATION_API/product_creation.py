from serverconncetion import ServerConnection
from error_handling import ErrorHandling

class ProductCreation:  

    def create_product_with_no(self, product_lines, models, db, uid, password, file_name, file_id, error_folder_id):

        product_data = {}

        try:
            # with material no
            product_data['id'] = product_lines[2]['product_id']  # product id
            product_data['name'] = product_lines[2]['name']  # product name
            product_data['default_code'] = product_lines[2]['product_id']  # internal reference
            print(product_data)

            # creating product
            product_ids = models.execute_kw(db, uid, password, 'product.product', 'create', [product_data])
            print("Created product ->", product_ids)

        except (ValueError, TypeError) as e:
            error_message = f"Error during product creation: {str(e)}"
            print(error_message)
            ErrorHandling().handle_error(file_id, error_folder_id, file_name, error_message, uid, db, password, models)   

        return product_ids

