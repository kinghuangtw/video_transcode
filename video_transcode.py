import os
import dotenv
import json

# Load the .env file
dotenv.load_dotenv()

# Function to fetch encoding parameters based on resolution

def get_encoding_parameters(resolution):
    encoding_parameters = json.loads(os.getenv('ENCODING_PARAMETERS', '{}'))
    return encoding_parameters.get(resolution, {})

# Example usage
resolution = '1080p'  # This should be set dynamically
encoding_settings = get_encoding_parameters(resolution)

# Proceed with the transcoding process using encoding_settings...