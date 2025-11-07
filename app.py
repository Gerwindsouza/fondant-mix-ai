from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': 'Empty file name'}), 400

    try:
        image = Image.open(image_file.stream).convert('RGB')
        colors = image.getcolors(maxcolors=1000000)
        if not colors:
            return jsonify({'error': 'No color detected'}), 400

        # Find the most common color
        dominant_color = max(colors, key=lambda x: x[0])[1]
        return jsonify({'dominant_color': dominant_color})
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Error analyzing image'}), 500

@app.route('/calibration')
def calibration():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
