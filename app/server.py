import sys
import logging
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the python path so we can import src
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

try:
    from src.route_optimizer import route, graph
except ImportError as e:
    logger.error(f"Error importing route_optimizer: {e}")
    sys.exit(1)

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/route', methods=['POST'])
def get_route():
    data = request.json
    logger.info(f"Received route request: {data}")
    
    try:
        start_lat = float(data.get('start_lat'))
        start_lon = float(data.get('start_lon'))
        end_lat = float(data.get('end_lat'))
        end_lon = float(data.get('end_lon'))
        risk_tolerance = float(data.get('lambda', 0.5))

        # Call the route optimizer
        result = route(
            graph, 
            start_lat, 
            start_lon, 
            end_lat, 
            end_lon, 
            lambd=risk_tolerance
        )
        
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error calculating route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Server is running",
        "endpoints": {
            "health": "GET /health",
            "route": "POST /api/route"
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)