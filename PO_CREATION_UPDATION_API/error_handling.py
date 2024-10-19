import xmlrpc.client
import os
from serverconncetion import ServerConnection
import xmlrpc.client
import base64


class ErrorHandling:
       def handle_error(file_id, error_folder_id, file_name, error_message, models):
        # Log the error and move the file to the error folder
        print(f'Handling error for file: {file_name}')
        
        # Create an error log file
        error_log_file_name = f'error_{file_name}.txt'
        with open(error_log_file_name, 'w') as log_file:
            log_file.write(f'Error processing file: {file_name}\n')
            log_file.write(error_message + '\n')

        # Upload the error log to Odoo
        with open(error_log_file_name, 'rb') as log_file:
            log_file_content = base64.b64encode(log_file.read()).decode('utf-8')
            error_log_attachment = {
                'name': error_log_file_name,
                'type': 'binary',
                'datas': log_file_content,
                'mimetype': 'text/plain',
                'folder_id': error_folder_id,
            }
            uid, url, db, password = ServerConnection.connection()
            models.execute_kw(db, uid, password, 'documents.document', 'create', [error_log_attachment])
        
        # Move the original XML file to the error folder
        models.execute_kw(db, uid, password, 'documents.document', 'write', [[file_id], {'folder_id': error_folder_id}])
        print(f'Moved {file_name} to error folder and created log file {error_log_file_name} in the error folder.')

