import xmlrpc.client
import base64
from dotenv import load_dotenv
import os
import shutil
  
  
# Load the .env file
load_dotenv('/home/odoo/src/myenv/hashkey.env')
 
# Odoo credentials and URL
url = "https://cocreateaarav-itgnew-itgdev-15781887.dev.odoo.com/"  # Odoo instance URL/IP address
db = "cocreateaarav-itgnew-itgdev-15781887"  # Odoo database name
username = os.getenv("ODOO_USERNAME")  # Instance username fetching from hashkey.env
password = os.getenv("ODOO_PASSWORD")  # Instance password fetching from hashkey.env


# Directory containing XML files
directory_path = r'C:\Users\Jigar\Documents\SAP to odoo testing\upload'  # Change this to your directory path
error_directory = r'C:\Users\Jigar\Documents\SAP to odoo testing\error_files'  # Specify your error directory path
non_315_directory = r'C:\Users\Jigar\Documents\SAP to odoo testing\non_315'  # Directory for non-315 files

# Function to log errors to a specified log file
def log_error(file_name, error_message):
    error_log_path = os.path.join(error_directory, f'error_{file_name}.txt')
    with open(error_log_path, 'w') as error_file:
        error_file.write(error_message)

# Connect to the Odoo server
try:
  common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
  uid = common.authenticate(db, username, password, {})
except xmlrpc.client.Fault as e:
     error_message = f"Server connection error: {str(e)}"
     print(error_message)
     log_error('no_files', error_message)  # Use a generic file name for the log
     exit()        

# Check authentication
if uid is False:
    # If authentication got failed, log the error
    error_message = "Authentication failed. Please check your credentials."
    print(error_message)
    log_error('no_files', error_message)  # Use a generic file name for the log
    exit()
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Provide document module folder ID where we need to move the file
folder_id = 9  # Hardcoded value of folder where we put the XML on Odoo side

# Check if the directory contains files
if not os.listdir(directory_path):
    # If no files are present in the upload directory, log the error
    error_message = "No files found in the upload directory."
    print(error_message)
    log_error('no_files', error_message)  # Use a generic file name for the log
    exit()

# Iterate over all files in the directory
for file_name in os.listdir(directory_path):
    file_path = os.path.join(directory_path, file_name)

    # Check if it is a file
    if os.path.isfile(file_path):
        # Check if the file has the correct extension
        if file_path.endswith('.xml'):
            print(f'Processing file: {file_name}')
            
            # Split the file name to check if the middle part is '315'
            file_parts = file_name.split('_')
            if len(file_parts) >= 2 and file_parts[1] == '315':
                # Read and encode the file
                try:
                    with open(file_path, 'rb') as file:
                        file_content = file.read()
                        encoded_file = base64.b64encode(file_content).decode('utf-8')
                except Exception as e:
                    error_message = f"Error reading the XML file '{file_name}': {e}"
                    print(error_message)
                    shutil.move(file_path, os.path.join(error_directory, file_name))
                    log_error(file_name, error_message)  # Log the specific error for this file
                    continue  # Skip to the next file

                # Create an attachment
                attachment_data = {
                    'name': file_name,
                    'type': 'binary',
                    'datas': encoded_file,
                    'mimetype': 'application/xml',  # Appropriate MIME type for XML files
                    'folder_id': folder_id,
                }

                try:
                    attachment_id = models.execute_kw(db, uid, password,
                                                      'documents.document', 'create', [attachment_data])
                    print(f'File uploaded successfully with ID: {attachment_id}')
                    # Delete the file from the upload directory after successful upload
                    os.remove(file_path)  # Delete the processed file
                except Exception as e:
                    error_message = f"Error uploading XML file '{file_name}' to Odoo: {e}"
                    print(error_message)
                    shutil.move(file_path, os.path.join(error_directory, file_name))
                    log_error(file_name, error_message)  # Log the specific error for this file
                    continue  # Skip to the next file    
            else:
                # If the middle part is not '315', move it to the non_315 folder
                print(f"Moving file '{file_name}' to non_315 directory")
                shutil.move(file_path, os.path.join(non_315_directory, file_name))

        else:
            # Handle non-XML files
            error_message = f"Non-XML file encountered: '{file_name}'"
            print(error_message)
            shutil.move(file_path, os.path.join(error_directory, file_name))
            log_error(file_name, error_message)  # Log the specific error for this file

    else:
        #Handling non files item
        error_message = f"Skipping non-file item: '{file_name}'"
        print(error_message)
        shutil.move(file_path, os.path.join(error_directory, file_name))
        log_error(file_name, error_message)  # Log the specific error for this file    
