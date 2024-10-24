import xmlrpc.client
import base64
from dotenv import load_dotenv
import os
import shutil

# Load the .env file
load_dotenv('/home/odoo/src/myenv/hashkey.env')

# Odoo credentials and URL
url = "https://cocreateaarav-itgnew-itgdev-15781887.dev.odoo.com/" # Odoo instance URL/IP address
db = "cocreateaarav-itgnew-itgdev-15781887" # Odoo database name
username = os.getenv("ODOO_USERNAME") # Instance username fetching from hashkey.env
password = os.getenv("ODOO_PASSWORD") # Instance password fetching from hashkey.env

# Directory containing XML files
directory_path = r'C:\Users\Jigar\Documents\SAP to odoo testing\upload'
error_directory = r'C:\Users\Jigar\Documents\SAP to odoo testing\error_files'
non_315_directory = r'C:\Users\Jigar\Documents\SAP to odoo testing\non_315'

# Function to log errors to a specified log file
def log_error(file_name, error_message):
    error_log_path = os.path.join(error_directory, f'error_{file_name}.txt')
    with open(error_log_path, 'w') as error_file:
        error_file.write(error_message)

# Function to handle errors to a specified log file
def handle_error(file_name, error_message, error_dir):
    print(error_message)
    shutil.move(os.path.join(directory_path, file_name), os.path.join(error_dir, file_name))
    log_error(file_name, error_message)

# Connect to the Odoo server
try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
except xmlrpc.client.Fault as e:
    log_error('no_files', f"Server connection error: {str(e)}")
    exit()

# Check authentication
if uid is False:
    # If authentication got failed, log the error
    log_error('no_files', "Authentication failed. Please check your credentials.")
    exit()

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
# Provide document module folder ID where we need to move the file
folder_id = 9  # Folder ID 

# Check if the directory contains files
if not os.listdir(directory_path):
    log_error('no_files', "No files found in the upload directory.")
    exit()

# Iterate over all files in the directory
for file_name in os.listdir(directory_path):
    file_path = os.path.join(directory_path, file_name)

    # Check if it is a file
    if os.path.isfile(file_path):
        if file_path.endswith('.xml'):
            print(f'Processing file: {file_name}')
            # Split the file name to check if the middle part is '315'
            file_parts = file_name.split('_')
            if len(file_parts) >= 2 and file_parts[1] == '315':
                # Read and encode the file
                try:
                    with open(file_path, 'rb') as file:
                        encoded_file = base64.b64encode(file.read()).decode('utf-8')
                except Exception as e:
                    handle_error(file_name, f"Error reading the XML file '{file_name}': {e}", error_directory)
                    continue # Skip to the next file
                 # Create an attachment
                attachment_data = {
                    'name': file_name,
                    'type': 'binary',
                    'datas': encoded_file,
                    'mimetype': 'application/xml',  # Appropriate MIME type for XML files
                    'folder_id': folder_id,
                }

                try:
                    attachment_id = models.execute_kw(db, uid, password, 'documents.document', 'create', [attachment_data])
                    print(f'File uploaded successfully with ID: {attachment_id}')
                    # Delete the file from the upload directory after successful upload
                    os.remove(file_path)
                except Exception as e:
                    handle_error(file_name, f"Error uploading XML file '{file_name}' to Odoo: {e}", error_directory)
                    continue
            else:
                # If the middle part is not '315', move it to the non_315 folder
                print(f"Moving file '{file_name}' to non_315 directory")
                shutil.move(file_path, os.path.join(non_315_directory, file_name))
        else:
            # Handle non-XML files
            handle_error(file_name, f"Non-XML file encountered: '{file_name}'", error_directory)
    else:
        #Handling non files item
        handle_error(file_name, f"Skipping non-file item: '{file_name}'", error_directory)