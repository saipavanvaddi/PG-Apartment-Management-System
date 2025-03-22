from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# Your Supabase project URL and anon key
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Storage configuration
STORAGE_URL = f"{SUPABASE_URL}/storage/v1"
BUCKET_NAME = os.getenv('STORAGE_BUCKET_NAME')

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_supabase_connection():
    """Test the Supabase connection and bucket access"""
    try:
        # Try to list files in the bucket
        files = supabase.storage.from_(BUCKET_NAME).list()
        print(f"Successfully connected to Supabase storage bucket '{BUCKET_NAME}'")
        print(f"Current files in bucket: {files}")  # Print existing files for verification
        return True
    except Exception as e:
        error_message = str(e)
        if 'invalid signature' in error_message.lower():
            print("Authentication error: Invalid API key. Please check your SUPABASE_KEY.")
        elif '404' in error_message:
            print(f"Bucket '{BUCKET_NAME}' not found. Please check the bucket name.")
        elif '403' in error_message:
            print("Permission denied. Please run the SQL commands to set up bucket policies.")
        else:
            print(f"Error connecting to Supabase storage: {error_message}")
        return False

# Test connection when module is loaded
test_supabase_connection()

# Create bucket if it doesn't exist (you can uncomment this if you want to create bucket programmatically)
# try:
#     supabase.storage.create_bucket(BUCKET_NAME, {'public': True})
# except Exception as e:
#     print(f"Note: {str(e)}")  # Bucket might already exist