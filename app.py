"""
Fondant Color Mixer AI - Flask Backend

This application helps bakers calculate precise gel color ratios to match target fondant colors.
Users upload photos, and the app analyzes the dominant color to suggest exact mixing amounts.

Author: Replit Agent
Date: November 4, 2025
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from PIL import Image
from colorthief import ColorThief
import io
import base64
import os
import json

app = Flask(__name__)
CORS(app)

# Maximum upload size: 128MB
app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024

# Path to calibration data file
CALIBRATION_FILE = 'calibration.json'

# Allowed image file extensions for security
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# Allowed MIME types for uploaded images
ALLOWED_MIMETYPES = {'image/png', 'image/jpeg', 'image/gif', 'image/bmp', 'image/webp'}

# Gel color brands with intensity multipliers
# Higher intensity = more concentrated = less gel needed
GEL_BRANDS = {
    'Wilton': {
        'intensity': 1.0,
        'description': 'Standard intensity gel colors'
    },
    'AmeriColor': {
        'intensity': 1.2,
        'description': 'More concentrated, use less'
    },
    'Sugarflair': {
        'intensity': 0.9,
        'description': 'Slightly less concentrated'
    },
    'Generic': {
        'intensity': 0.8,
        'description': 'Basic gel colors, may need more'
    }
}

# RGB values for primary gel colors used in fondant mixing
PRIMARY_COLORS = {
    'red': (255, 0, 0),
    'yellow': (255, 255, 0),
    'blue': (0, 0, 255),
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'green': (0, 255, 0),
    'orange': (255, 165, 0),
    'purple': (128, 0, 128),
    'pink': (255, 192, 203),
    'brown': (139, 69, 19)
}


def load_calibration():
    """
    Load calibration data from JSON file.
    
    Calibration data includes:
    - brand_multipliers: Intensity multiplier for each gel color brand
    - drop_conversion: Settings for converting grams to drops
    
    Returns:
        dict: Calibration data with brand multipliers and drop conversion settings
        
    Note: If file doesn't exist or is invalid, returns default values
    """
    try:
        with open(CALIBRATION_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return default calibration values if file doesn't exist or is corrupted
        return {
            'brand_multipliers': {
                'Wilton': 1.0,
                'AmeriColor': 1.15,
                'Sugarflair': 1.05,
                'Generic': 0.8
            },
            'drop_conversion': {
                'enabled': False,
                'grams_per_drop': 0.04  # Standard: 1 drop = 0.04 grams
            }
        }


def save_calibration(calibration_data):
    """
    Save calibration data to JSON file.
    
    Args:
        calibration_data: Dictionary containing brand_multipliers and drop_conversion
        
    Returns:
        bool: True if save successful, False otherwise
    """
    try:
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump(calibration_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving calibration: {str(e)}")
        return False


def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    
    Args:
        filename: Name of the uploaded file
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image_file(file):
    """
    Validate that the uploaded file is a genuine image.
    Checks both MIME type and attempts to open with PIL.
    
    Args:
        file: FileStorage object from Flask request
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check MIME type
    if file.mimetype not in ALLOWED_MIMETYPES:
        return False, f"Invalid file type. Allowed types: {', '.join(ALLOWED_MIMETYPES)}"
    
    # Check file extension
    if not allowed_file(file.filename):
        return False, f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Verify it's actually an image by trying to open it with PIL
    try:
        file.seek(0)  # Reset file pointer to beginning
        img = Image.open(file)
        img.verify()  # Verify it's a valid image
        file.seek(0)  # Reset again for later processing
        return True, None
    except Exception as e:
        return False, "File is not a valid image"


def extract_color_from_image(image_file):
    """
    Extract the dominant color from an uploaded image using ColorThief.
    
    This function:
    1. Opens the image with PIL
    2. Converts to RGB format (required for ColorThief)
    3. Saves to a BytesIO buffer as PNG
    4. Uses ColorThief to extract the dominant color
    
    Args:
        image_file: File-like object containing the image
        
    Returns:
        tuple: RGB values as (r, g, b) where each value is 0-255
        
    Raises:
        Exception: If color extraction fails
    """
    try:
        # Open and validate the image
        img = Image.open(image_file)
        
        # Convert to RGB (required for ColorThief, handles RGBA, grayscale, etc.)
        img = img.convert('RGB')
        
        # Save to BytesIO buffer for ColorThief processing
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Extract dominant color using ColorThief
        color_thief = ColorThief(img_byte_arr)
        dominant_color = color_thief.get_color(quality=1)
        
        return dominant_color
    except Exception as e:
        raise Exception(f"Error extracting color: {str(e)}")


def calculate_color_distance(color1, color2):
    """
    Calculate Euclidean distance between two RGB colors.
    Used to measure similarity between target color and primary colors.
    
    Args:
        color1: RGB tuple (r, g, b)
        color2: RGB tuple (r, g, b)
        
    Returns:
        float: Distance value (0 = identical, higher = more different)
    """
    return sum((a - b) ** 2 for a, b in zip(color1, color2)) ** 0.5


def calculate_mixing_ratios(target_rgb, selected_colors, fondant_weight, brand_multiplier):
    """
    Calculate gel color amounts needed to match the target RGB color.
    
    Algorithm:
    1. Calculate similarity between target and each selected primary color
    2. Filter out colors with very low similarity (< 10%)
    3. Normalize ratios to sum to 1.0
    4. Apply base concentration factor and brand multiplier
    5. Calculate final gel amounts in grams
    
    Args:
        target_rgb: Target color as RGB tuple (r, g, b)
        selected_colors: List of primary color names selected by user
        fondant_weight: Weight of fondant in grams
        brand_multiplier: Calibrated intensity multiplier for the gel brand
        
    Returns:
        tuple: (gel_amounts dict, error_message)
               gel_amounts: {color_name: amount_in_grams}
    """
    # Use the calibrated brand multiplier (higher = more concentrated = less gel needed)
    brand_intensity = brand_multiplier
    
    # Filter selected colors from all available primary colors
    available_colors = {name: PRIMARY_COLORS[name] for name in selected_colors}
    
    if not available_colors:
        return None, "Please select at least one primary color"
    
    # Base concentration: typical gel color ratio is ~0.03% of fondant weight
    base_concentration = 0.0003
    
    # Calculate similarity scores for each color
    ratios = {}
    total_distance = 0
    
    for color_name, color_rgb in available_colors.items():
        # Calculate how different this color is from target
        distance = calculate_color_distance(target_rgb, color_rgb)
        max_distance = calculate_color_distance((0, 0, 0), (255, 255, 255))
        
        # Convert distance to similarity (1 = identical, 0 = opposite)
        similarity = 1 - (distance / max_distance)
        
        # Only include colors with meaningful similarity (> 10%)
        if similarity > 0.1:
            ratios[color_name] = similarity
            total_distance += similarity
    
    # If no colors are similar enough, use the nearest color
    if not ratios:
        nearest_color = min(available_colors.items(), 
                          key=lambda x: calculate_color_distance(target_rgb, x[1]))
        ratios[nearest_color[0]] = 1.0
        total_distance = 1.0
    
    # Normalize ratios so they sum to 1.0
    normalized_ratios = {k: v / total_distance for k, v in ratios.items()}
    
    # Calculate actual gel amounts in grams
    gel_amounts = {}
    for color_name, ratio in normalized_ratios.items():
        # Formula: (fondant_weight * base_concentration * color_ratio) / brand_intensity
        # Higher brand intensity means more concentrated, so divide to use less
        amount = (fondant_weight * base_concentration * ratio) / brand_intensity
        gel_amounts[color_name] = round(amount, 4)
    
    return gel_amounts, None

@app.route('/')
def index():
    """
    Serve the main application page.
    
    Returns:
        Rendered HTML template
    """
    return render_template('index.html')


@app.route('/calibration', methods=['GET'])
def get_calibration():
    """
    Get current calibration settings.
    
    Returns:
        JSON with brand multipliers and drop conversion settings
    """
    calibration = load_calibration()
    return jsonify(calibration)


@app.route('/calibration', methods=['POST'])
def update_calibration():
    """
    Update calibration settings.
    
    Expected JSON body:
        {
            "brand_multipliers": {
                "Wilton": 1.0,
                "AmeriColor": 1.15,
                ...
            },
            "drop_conversion": {
                "enabled": true/false,
                "grams_per_drop": 0.04
            }
        }
    
    Returns:
        JSON response indicating success or error
    """
    try:
        calibration_data = request.get_json()
        
        # Validate required fields exist
        if 'brand_multipliers' not in calibration_data or 'drop_conversion' not in calibration_data:
            return jsonify({'error': 'Missing required calibration data'}), 400
        
        # Validate brand multipliers are numbers
        for brand, multiplier in calibration_data['brand_multipliers'].items():
            if not isinstance(multiplier, (int, float)) or multiplier <= 0:
                return jsonify({'error': f'Invalid multiplier for {brand}'}), 400
        
        # Validate drop conversion settings
        drop_settings = calibration_data['drop_conversion']
        if 'grams_per_drop' not in drop_settings or drop_settings['grams_per_drop'] <= 0:
            return jsonify({'error': 'Invalid grams_per_drop value'}), 400
        
        # Save calibration data
        if save_calibration(calibration_data):
            return jsonify({'success': True, 'message': 'Calibration saved successfully'})
        else:
            return jsonify({'error': 'Failed to save calibration'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze uploaded image and calculate gel color mixing ratios.
    
    Expected form data:
        - image: Image file (required)
        - weight: Fondant weight in grams (required)
        - brand: Gel color brand name (required)
        - colors[]: List of selected primary colors (required)
        - brand_multiplier: Custom multiplier override (optional)
        - show_drops: Whether to include drop conversion (optional)
    
    Returns:
        JSON response with:
        - success: Boolean
        - target_color: RGB values of extracted color
        - gel_amounts: Dictionary of color amounts in grams
        - gel_amounts_drops: Dictionary of color amounts in drops (if enabled)
        - mixing_instructions: List of step-by-step instructions
        - brand_info: Description of selected brand
    """
    try:
        # Validate image file is present
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'No image selected'}), 400
        
        # Security: Validate image file is genuine and safe
        is_valid, error_msg = validate_image_file(image_file)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Parse and validate form inputs
        try:
            fondant_weight = float(request.form.get('weight', 100))
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid fondant weight. Please enter a valid number.'}), 400
        
        brand = request.form.get('brand', 'Generic')
        selected_colors = request.form.getlist('colors[]')
        
        # Validate fondant weight is positive
        if fondant_weight <= 0:
            return jsonify({'error': 'Fondant weight must be greater than 0'}), 400
        
        # Validate brand is in our supported list
        if brand not in GEL_BRANDS:
            return jsonify({'error': 'Invalid gel brand'}), 400
        
        # Validate at least one color is selected
        if not selected_colors:
            return jsonify({'error': 'Please select at least one primary color'}), 400
        
        # Load calibration settings
        calibration = load_calibration()
        
        # Get brand multiplier (use custom value if provided, otherwise use calibrated value)
        brand_multiplier = request.form.get('brand_multiplier')
        if brand_multiplier:
            try:
                brand_multiplier = float(brand_multiplier)
            except (ValueError, TypeError):
                brand_multiplier = calibration['brand_multipliers'].get(brand, 1.0)
        else:
            brand_multiplier = calibration['brand_multipliers'].get(brand, 1.0)
        
        # Get drop conversion settings
        show_drops = request.form.get('show_drops', 'false').lower() == 'true'
        grams_per_drop = calibration['drop_conversion']['grams_per_drop']
        
        # Extract dominant color from the uploaded image
        dominant_color = extract_color_from_image(image_file)
        
        # Calculate gel color mixing ratios using calibrated multiplier
        gel_amounts, error = calculate_mixing_ratios(
            dominant_color, 
            selected_colors, 
            fondant_weight, 
            brand_multiplier
        )
        
        if error:
            return jsonify({'error': error}), 400
        
        # Convert to drops if requested
        gel_amounts_drops = None
        if show_drops:
            gel_amounts_drops = {
                color: round(amount / grams_per_drop, 1)  # Convert grams to drops
                for color, amount in gel_amounts.items()
            }
        
        # Generate user-friendly mixing instructions
        mixing_instructions = generate_mixing_instructions(
            gel_amounts, 
            fondant_weight, 
            brand, 
            gel_amounts_drops,
            grams_per_drop
        )
        
        # Prepare response
        response_data = {
            'success': True,
            'target_color': {
                'r': dominant_color[0],
                'g': dominant_color[1],
                'b': dominant_color[2]
            },
            'gel_amounts': gel_amounts,
            'mixing_instructions': mixing_instructions,
            'brand_info': GEL_BRANDS[brand]['description']
        }
        
        # Include drops in response if enabled
        if show_drops and gel_amounts_drops:
            response_data['gel_amounts_drops'] = gel_amounts_drops
        
        return jsonify(response_data)
    
    except Exception as e:
        # Catch any unexpected errors and return 500
        return jsonify({'error': str(e)}), 500


def generate_mixing_instructions(gel_amounts, fondant_weight, brand, gel_amounts_drops=None, grams_per_drop=0.04):
    """
    Generate step-by-step mixing instructions for bakers.
    
    Creates a formatted list of instructions including:
    - Precise measurements for each gel color (in grams and optionally drops)
    - Step-by-step mixing process
    - Professional tips for best results
    
    Args:
        gel_amounts: Dictionary of {color_name: amount_in_grams}
        fondant_weight: Total fondant weight in grams
        brand: Gel color brand name
        gel_amounts_drops: Optional dictionary of {color_name: amount_in_drops}
        grams_per_drop: Conversion factor for grams to drops (default: 0.04g per drop)
        
    Returns:
        list: Formatted instruction strings
    """
    instructions = []
    
    # Header with fondant weight and brand
    instructions.append(f"For {fondant_weight}g of white fondant using {brand} gel colors:")
    instructions.append("")
    
    # List measurements sorted by amount (largest first)
    instructions.append("Measurements needed:")
    for color, amount in sorted(gel_amounts.items(), key=lambda x: -x[1]):
        # Format based on amount size for readability
        if amount >= 0.01:
            measurement = f"  • {color.capitalize()}: {amount:.3f}g ({amount*1000:.1f}mg)"
        else:
            measurement = f"  • {color.capitalize()}: {amount:.4f}g ({amount*1000:.2f}mg)"
        
        # Add drop conversion if available
        if gel_amounts_drops and color in gel_amounts_drops:
            drops = gel_amounts_drops[color]
            measurement += f" ≈ {drops:.1f} drops"
        
        instructions.append(measurement)
    
    # Add drop conversion note if applicable
    if gel_amounts_drops:
        instructions.append("")
        instructions.append(f"Note: Using conversion rate of {grams_per_drop}g per drop")
    
    instructions.append("")
    
    # Step-by-step mixing process
    instructions.append("Mixing steps:")
    instructions.append("1. Start with your white fondant at room temperature")
    instructions.append("2. Add gel colors one at a time, starting with the largest amount")
    instructions.append("3. Knead thoroughly after each addition until color is uniform")
    
    # Adjust tool recommendation based on whether drops are shown
    if gel_amounts_drops:
        instructions.append("4. Use a dropper or toothpick for small amounts")
    else:
        instructions.append("4. Use a toothpick for very small amounts (under 0.01g)")
    
    instructions.append("5. Mix in small portions and check color frequently")
    instructions.append("6. Remember: you can always add more color, but can't remove it!")
    instructions.append("")
    
    # Professional tip
    instructions.append("Pro tip: Colors may deepen slightly as fondant rests. Test on a small piece first.")
    
    return instructions

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
