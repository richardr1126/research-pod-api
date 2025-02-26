from api import server

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8888))
    server.run(host='0.0.0.0', port=port, debug=True)