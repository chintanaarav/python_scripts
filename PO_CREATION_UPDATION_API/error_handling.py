import base64


class ErrorHandling:
       def handle_error(self,file_id, error_folder_id, file_name, error_message, uid, db, password, models):
        # Log the error and move the file to the error folder
        print(f'Handling error for file: {file_name}')

        # Create an error log message
        error_log_message = f'Error processing file: {file_name}\n{error_message}'

        # Create an error log attachment directly in Odoo without saving a local file
        error_log_attachment = {
            'name': f'error_{file_name}.txt',
            'type': 'binary',
            'datas': base64.b64encode(error_log_message.encode('utf-8')).decode('utf-8'),
            'mimetype': 'text/plain',
            'folder_id': error_folder_id,
        }
            
        models.execute_kw(db, uid, password, 'documents.document', 'create', [error_log_attachment])
        
        # Move the original XML file to the error folder
        models.execute_kw(db, uid, password, 'documents.document', 'write', [[file_id], {'folder_id': error_folder_id}])
        print(f'Moved {file_name} to error folder and created log file in the error folder.')

