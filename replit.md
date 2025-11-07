# Fondant Color Mixer AI

## Overview
A web-based application that helps professional bakers determine precise gel color ratios to match target fondant colors. Users upload photos of their desired color, and the app analyzes the image to calculate exact measurements needed for color mixing.

**Project Name:** fondant-mix-ai  
**Last Updated:** November 4, 2025  
**Current State:** Production-ready MVP

## Purpose & Goals
- Help bakers achieve consistent, accurate fondant colors
- Eliminate guesswork in color mixing
- Provide precise measurements for professional results
- Support multiple gel color brands with different concentration levels

## Features

### Current Features (MVP)
1. **Image Upload & Color Analysis**
   - Drag-and-drop image upload
   - Paste from clipboard (Ctrl+V)
   - Automatic dominant color extraction using ColorThief and Pillow
   - Visual color preview

2. **Customizable Input Parameters**
   - Fondant weight in grams (1-10,000g)
   - Gel color brand selection (Wilton, AmeriColor, Sugarflair, Generic)
   - 10 primary colors to choose from (red, yellow, blue, white, black, green, orange, purple, pink, brown)

3. **Color Mixing Calculations**
   - Brand-specific concentration adjustments
   - Precise measurements in grams and milligrams
   - RGB color matching algorithm
   - Similarity-based ratio calculations

4. **Results Display**
   - Visual target color preview
   - RGB values display
   - Detailed gel amounts for each color
   - Step-by-step mixing instructions
   - Professional baking tips

5. **Mobile-Responsive Design**
   - Works on desktop, tablet, and mobile devices
   - Baker-friendly interface with visual color swatches
   - Smooth animations and transitions

## Project Architecture

### Technology Stack
- **Backend:** Flask (Python 3.11)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Image Processing:** Pillow (PIL), ColorThief
- **Server:** Flask development server on port 5000

### File Structure
```
fondant-mix-ai/
├── app.py                 # Flask backend with color analysis logic
├── templates/
│   └── index.html        # Main HTML interface
├── static/
│   ├── style.css         # Styling and responsive design
│   └── script.js         # Frontend interactivity
├── .gitignore            # Python and environment files
├── pyproject.toml        # Python dependencies (uv managed)
├── uv.lock              # Locked dependency versions
└── replit.md            # This documentation file
```

### Key Components

#### Backend (app.py)
- **Color Extraction:** Uses ColorThief to analyze uploaded images and extract dominant RGB values
- **Mixing Algorithm:** Calculates gel ratios based on color similarity to target RGB
- **Brand Adjustments:** Applies concentration multipliers for different gel brands
- **API Endpoints:**
  - `GET /` - Serves the main application interface
  - `POST /analyze` - Processes image and returns mixing ratios

#### Frontend
- **HTML (index.html):** Three-step user interface with upload, configuration, and results sections
- **CSS (style.css):** Gradient backgrounds, responsive grid layout, visual color swatches
- **JavaScript (script.js):** Handles file upload, drag-and-drop, paste events, and API communication

### Color Calculation Logic
1. Extract dominant RGB color from uploaded image
2. Calculate Euclidean distance between target color and each selected primary color
3. Compute similarity scores (inverse of distance)
4. Normalize ratios to sum to 1.0
5. Apply base concentration factor (0.0003) and brand-specific multiplier
6. Calculate final gel amounts in grams

### Brand Intensity Factors
- **Wilton:** 1.0 (baseline)
- **AmeriColor:** 1.2 (more concentrated, use less)
- **Sugarflair:** 0.9 (slightly less concentrated)
- **Generic:** 0.8 (basic, may need more)

## Recent Changes
- **November 4, 2025:** Initial project creation
  - Implemented complete MVP with all core features
  - Added color extraction using Pillow and ColorThief
  - Created responsive, baker-friendly UI
  - Configured Flask workflow on port 5000
  - Added comprehensive mixing instructions and tips

## Dependencies
- flask (3.1.2) - Web framework
- pillow (12.0.0) - Image processing
- colorthief (0.2.1) - Color extraction
- flask-cors (6.0.1) - Cross-origin resource sharing

## Running the Application
The app runs automatically via the configured workflow:
- **Command:** `python app.py`
- **Port:** 5000
- **Access:** Web preview in Replit

## User Preferences
None specified yet.

## Future Enhancements
- Color matching accuracy score
- Recipe save/history feature
- Camera capture for mobile users
- Printable mixing guide with color swatches
- Fine-tuning slider for color adjustment
- Support for custom gel brands
- Batch recipe creation
- Export recipes as PDF
