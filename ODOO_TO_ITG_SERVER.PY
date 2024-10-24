import xmlrpc.client
import base64
from dotenv import load_dotenv
import os
from datetime import datetime

# Load the .env file
load_dotenv('/home/odoo/src/myenv/hashkey.env')
 
# Odoo credentials and URL
url = "https://cocreateaarav-itgnew-itgdev-15781887.dev.odoo.com/"  # Odoo instance URL/IP address
db = "cocreateaarav-itgnew-itgdev-15781887"  # Odoo database name
username = os.getenv("ODOO_USERNAME")  # Instance username fetching from hashkey.env
password = os.getenv("ODOO_PASSWORD")  # Instance password fetching from hashkey.env

# Directories for server and error files
server_directory = r'C:\Users\Jigar\Documents\SAP to odoo testing\Approved_PO'
error_directory = r'C:\Users\Jigar\Documents\SAP to odoo testing\error'

# Function to log errors to a specified log file
def log_error(file_name, error_message):
    error_log_path = os.path.join(error_directory, f'error_{file_name}.txt')
    with open(error_log_path, 'w') as error_file:
        error_file.write(error_message)

# Odoo folder ID where files are fetched and where the log file will be uploaded
folder_id = 14  # Folder ID in the document module

# Connect to Odoo
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
    # If authentication got failed, log the error and create a log file
    error_message = "Authentication failed. Please check your credentials."
    print(error_message)
    log_error('no_files', error_message)  # Use a generic file name for the log 
    exit() 

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
# Fetch the 'system notification' subtype (usually 'Discussions')
try:
    subtypes = models.execute_kw(db, uid, password, 'mail.message.subtype', 'search_read',
                                 [[['name', '=', 'Discussions']]], {'fields': ['id', 'name']})

    if subtypes:
        note_subtype_id = subtypes[0]['id']
        print(f"Found 'Discussions' subtype with ID: {note_subtype_id}")
    else:
        error_message = "Could not find 'Discussions' subtype."
        print(error_message)
        log_error('no_subtype_found', error_message)
        exit()
except Exception as e:
    error_message = f"An unexpected error occurred during seraching subtype: {e}"
    print(error_message)
    log_error('unexpected_error', error_message)       

# Fetch the documents from Odoo
try:
    documents = models.execute_kw(db, uid, password, 'documents.document', 'search_read',
                                  [[['folder_id', '=', folder_id], ['name', 'ilike', '.xml']]],
                                  {'fields': ['id', 'name', 'datas']})
    print(f"Found {len(documents)} documents in folder ID {folder_id}.")
except Exception as e:
        error_message = f"Error fetching documents: {e}"
        print(error_message)
        log_error('no_files', error_message)  # Use a generic file name for the log
        exit()

# Check if documents are empty
if not documents:  # If the documents list is empty
        error_message = f"No documents found in folder ID {folder_id} at {datetime.now()}.\n"
        print(error_message)
        log_error('no_documents_found', error_message)  # Use a generic file name for the log
        exit() # Exit the script if no documents are found

# List to store the names of successfully moved files
successfully_moved_files = []

# Process each document
for document in documents:
    file_name = document['name']
    file_data = document['datas']

    # Decode the base64 content from Odoo
    try:
        file_content = base64.b64decode(file_data)
    except Exception as e:
            error_message = f"Error decoding file '{file_name}': {e}\n"
            print(error_message)
            log_error(file_name, error_message)
            continue  # Skip to the next file if there's an error

    # Save the file to the local server directory
    file_path = os.path.join(server_directory, file_name)
    try:
        with open(file_path, 'wb') as file:
            file.write(file_content)
        print(f"File '{file_name}' saved to {file_path}.")
        successfully_moved_files.append(file_name)  # Add to the list of successful files

    except Exception as e:
            error_message = f"Error saving file '{file_name}': {e}\n"
            print(error_message)
            log_error(file_name, error_message)
            continue  # Skip to the next file if there's an error

# --- Notification Logic: Send a system notification ---

# Prepare the message body to include successfully moved files
if successfully_moved_files:
    files_list_str = "\n".join(successfully_moved_files)
    message_body = f"The following files were successfully moved:\n{files_list_str}"
else:
    message_body = "No files were successfully moved."

# Step 4: Send the system notification to the document
message_subject = "Files Moved Notification"
document_id = 1  #(general channel id) Replace this with the actual document ID from 'documents.document'

try:
    message_id = models.execute_kw(db, uid, password, 'discuss.channel', 'message_post', [document_id], {
        'body': message_body,              # Message content (HTML or plain text)
        'subject': message_subject,        # Message subject (optional)
        'message_type': 'comment',         # 'comment' for user posts
        'subtype_id': note_subtype_id,     # Use the subtype ID for 'Discussions'
    })

    print(f"System notification sent successfully to document with ID: {document_id}")

except Exception as e:
    print(f"Error sending system notification: {e}")