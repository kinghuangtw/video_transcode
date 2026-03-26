import configparser

# Load the INI-style .env file
config = configparser.ConfigParser()
config.read('.env')

# Assuming the encoding parameters are based on resolution, here's an example of how to extract them
resolution = '1920x1080'  # Example resolution, this should be dynamic based on your needs

if resolution in config:
    encoding_params = config[resolution]
    # Now you can access the parameters like this:
    bitrate = encoding_params.get('bitrate')
    framerate = encoding_params.get('framerate')
    # Add logic to use these parameters in your encoding process
else:
    print(f'No encoding parameters found for resolution: {resolution}')
