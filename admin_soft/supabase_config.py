from supabase import create_client
import os

# Your Supabase project URL and anon key
SUPABASE_URL = "https://czuouxtbvcnugnmcbbcu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN6dW91eHRidmNudWdubWNiYmN1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIzODIxMzgsImV4cCI6MjA1Nzk1ODEzOH0.GxvzoPfOlNqi8TbkTtS3Bo0yBRSXJgqUm55FoeMnQO8"

# Storage configuration
STORAGE_URL = f"{SUPABASE_URL}/storage/v1"
BUCKET_NAME = "mediabucket"  # Updated bucket name

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_file(file, folder_path):
    """Upload a file to Supabase storage"""
    try:
        # Generate a unique filename
        file_extension = file.name.split('.')[-1]
        file_name = f"{folder_path}/{os.urandom(8).hex()}.{file_extension}"
        
        # Upload file to Supabase storage
        result = supabase.storage.from_(BUCKET_NAME).upload(
            file_name,
            file.read(),
            {"content-type": file.content_type}
        )
        
        # Get the public URL
        file_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)
        
        return file_url
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return None

def test_supabase_connection():
    """Test the Supabase connection"""
    try:
        # Try to list files in the bucket
        files = supabase.storage.from_(BUCKET_NAME).list()
        print(f"Successfully connected to Supabase storage bucket '{BUCKET_NAME}'")
        print(f"Current files in bucket: {files}")
        return True
    except Exception as e:
        error_message = str(e)
        if 'invalid signature' in error_message.lower():
            print("Authentication error: Invalid API key. Please check your SUPABASE_KEY.")
        elif '404' in error_message:
            print(f"Bucket '{BUCKET_NAME}' not found. Please check the bucket name.")
        elif '403' in error_message:
            print("Permission denied. Please check the storage policies.")
        else:
            print(f"Error connecting to Supabase storage: {error_message}")
        return False

# Test connection when module is loaded
test_supabase_connection() 