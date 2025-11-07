/**
 * Fondant Color Mixer AI - Frontend JavaScript
 * 
 * Handles user interactions including:
 * - Image upload (click, drag-and-drop, paste)
 * - Brand calibration and drop conversion settings
 * - Form validation
 * - API communication
 * - Results display
 */

// Store the uploaded image file for later submission
let uploadedImage = null;

// Store current calibration data loaded from backend
let currentCalibration = null;

// Get references to all DOM elements we'll interact with
const uploadArea = document.getElementById('uploadArea');
const imageInput = document.getElementById('imageInput');
const previewImage = document.getElementById('previewImage');
const colorPreview = document.getElementById('colorPreview');
const calculateBtn = document.getElementById('calculateBtn');
const resetBtn = document.getElementById('resetBtn');
const resultsSection = document.getElementById('resultsSection');
const loadingOverlay = document.getElementById('loadingOverlay');

// Calibration and drop conversion elements
const gelBrand = document.getElementById('gelBrand');
const brandMultiplier = document.getElementById('brandMultiplier');
const multiplierValue = document.getElementById('multiplierValue');
const showDrops = document.getElementById('showDrops');
const gramsPerDrop = document.getElementById('gramsPerDrop');
const saveCalibrationBtn = document.getElementById('saveCalibrationBtn');

/**
 * EVENT LISTENERS FOR IMAGE UPLOAD
 */

// When user clicks the upload area, trigger the hidden file input
uploadArea.addEventListener('click', () => {
    imageInput.click();
});

// Handle drag-over event to show visual feedback
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault(); // Required to allow drop
    uploadArea.classList.add('dragover'); // Visual feedback
});

// Remove visual feedback when drag leaves the area
uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

// Handle file drop event
uploadArea.addEventListener('drop', (e) => {
    e.preventDefault(); // Prevent browser from opening the file
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleImageFile(files[0]);
    }
});

// Handle traditional file input selection
imageInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleImageFile(e.target.files[0]);
    }
});

// Handle paste event (Ctrl+V) to allow pasting images
document.addEventListener('paste', (e) => {
    const items = e.clipboardData.items;
    // Loop through clipboard items to find an image
    for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf('image') !== -1) {
            const blob = items[i].getAsFile();
            handleImageFile(blob);
            break;
        }
    }
});

/**
 * CALIBRATION & DROP CONVERSION MANAGEMENT
 */

/**
 * Load calibration settings from backend and update UI
 */
async function loadCalibration() {
    try {
        const response = await fetch('/calibration');
        const calibration = await response.json();
        currentCalibration = calibration;
        
        // Update drop conversion settings in UI
        gramsPerDrop.value = calibration.drop_conversion.grams_per_drop;
        showDrops.checked = calibration.drop_conversion.enabled || false;
        
        // Load brand multiplier for currently selected brand
        updateBrandMultiplier();
    } catch (error) {
        console.error('Error loading calibration:', error);
    }
}

/**
 * Update the brand multiplier slider when brand selection changes
 */
function updateBrandMultiplier() {
    if (!currentCalibration) return;
    
    const selectedBrand = gelBrand.value;
    const multiplier = currentCalibration.brand_multipliers[selectedBrand] || 1.0;
    
    brandMultiplier.value = multiplier;
    multiplierValue.textContent = multiplier.toFixed(2);
}

/**
 * Save current calibration settings to backend
 */
async function saveCalibration() {
    if (!currentCalibration) return;
    
    const selectedBrand = gelBrand.value;
    const newMultiplier = parseFloat(brandMultiplier.value);
    const newGramsPerDrop = parseFloat(gramsPerDrop.value);
    const dropConversionEnabled = showDrops.checked;
    
    // Update calibration object with new values
    currentCalibration.brand_multipliers[selectedBrand] = newMultiplier;
    currentCalibration.drop_conversion.grams_per_drop = newGramsPerDrop;
    currentCalibration.drop_conversion.enabled = dropConversionEnabled;
    
    try {
        const response = await fetch('/calibration', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentCalibration)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`✓ Calibration saved! ${selectedBrand} multiplier: ${newMultiplier.toFixed(2)}, Drop conversion: ${dropConversionEnabled ? 'enabled' : 'disabled'}`);
        } else {
            alert('Error saving calibration: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error saving calibration: ' + error.message);
    }
}

// Event listener: Update multiplier display when slider changes
brandMultiplier.addEventListener('input', (e) => {
    multiplierValue.textContent = parseFloat(e.target.value).toFixed(2);
});

// Event listener: Load appropriate multiplier when brand changes
gelBrand.addEventListener('change', updateBrandMultiplier);

// Event listener: Save calibration when button clicked
saveCalibrationBtn.addEventListener('click', saveCalibration);

// Load calibration settings on page load
loadCalibration();

/**
 * Handle uploaded/pasted image file
 * Validates file type, stores reference, and displays preview
 * 
 * @param {File} file - The image file to process
 */
function handleImageFile(file) {
    // Basic client-side validation for image files
    if (!file.type.startsWith('image/')) {
        alert('Please upload an image file');
        return;
    }

    // Store file reference for later submission
    uploadedImage = file;

    // Read file and display preview
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        previewImage.classList.add('visible');
        document.querySelector('.upload-placeholder').style.display = 'none';
        calculateBtn.disabled = false; // Enable calculate button
    };
    reader.readAsDataURL(file);
}

/**
 * Handle Calculate button click
 * Validates inputs, sends data to backend, and displays results
 */
calculateBtn.addEventListener('click', async () => {
    // Ensure image is uploaded
    if (!uploadedImage) {
        alert('Please upload an image first');
        return;
    }

    // Collect form data
    const fondantWeight = parseFloat(document.getElementById('fondantWeight').value);
    const gelBrand = document.getElementById('gelBrand').value;
    const selectedColors = Array.from(document.querySelectorAll('input[name="colors"]:checked'))
        .map(cb => cb.value);

    // Validate that at least one color is selected
    if (selectedColors.length === 0) {
        alert('Please select at least one primary color');
        return;
    }

    // Validate fondant weight is positive
    if (fondantWeight <= 0) {
        alert('Please enter a valid fondant weight');
        return;
    }

    // Prepare form data for submission
    const formData = new FormData();
    formData.append('image', uploadedImage);
    formData.append('weight', fondantWeight);
    formData.append('brand', gelBrand);
    selectedColors.forEach(color => {
        formData.append('colors[]', color);
    });
    
    // Add calibration and drop conversion settings
    formData.append('brand_multiplier', brandMultiplier.value);
    formData.append('show_drops', showDrops.checked ? 'true' : 'false');

    // Show loading overlay while processing
    loadingOverlay.style.display = 'flex';

    try {
        // Send data to backend for analysis
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        // Display results if successful, otherwise show error
        if (data.success) {
            displayResults(data);
        } else {
            alert('Error: ' + (data.error || 'Unknown error occurred'));
        }
    } catch (error) {
        alert('Error analyzing image: ' + error.message);
    } finally {
        // Hide loading overlay regardless of success/failure
        loadingOverlay.style.display = 'none';
    }
});

/**
 * Display the calculated results from the backend
 * Creates visual elements showing target color, gel amounts, and instructions
 * 
 * @param {Object} data - Response data from backend containing:
 *   - target_color: {r, g, b} RGB values
 *   - gel_amounts: {color_name: amount_in_grams}
 *   - mixing_instructions: Array of instruction strings
 */
function displayResults(data) {
    // Extract target color and convert to CSS RGB format
    const targetColor = data.target_color;
    const targetColorRgb = `rgb(${targetColor.r}, ${targetColor.g}, ${targetColor.b})`;
    
    // Display target color swatch and RGB values
    document.getElementById('targetColorDisplay').style.backgroundColor = targetColorRgb;
    document.getElementById('rgbValues').textContent = 
        `RGB(${targetColor.r}, ${targetColor.g}, ${targetColor.b})`;

    // Clear previous results
    const gelAmountsContainer = document.getElementById('gelAmounts');
    gelAmountsContainer.innerHTML = '';

    // Map of color names to RGB values for visual swatches
    const colorMap = {
        'red': 'rgb(255, 0, 0)',
        'yellow': 'rgb(255, 255, 0)',
        'blue': 'rgb(0, 0, 255)',
        'white': 'rgb(255, 255, 255)',
        'black': 'rgb(0, 0, 0)',
        'green': 'rgb(0, 255, 0)',
        'orange': 'rgb(255, 165, 0)',
        'purple': 'rgb(128, 0, 128)',
        'pink': 'rgb(255, 192, 203)',
        'brown': 'rgb(139, 69, 19)'
    };

    // Create visual elements for each gel color amount
    Object.entries(data.gel_amounts).forEach(([color, amount]) => {
        const item = document.createElement('div');
        item.className = 'gel-amount-item';
        item.style.borderLeftColor = colorMap[color] || '#ccc';
        
        // Convert grams to milligrams for easier reading
        const mgAmount = (amount * 1000).toFixed(2);
        
        // Build measurement display string
        let measurementDisplay = `${amount >= 0.01 ? amount.toFixed(3) : amount.toFixed(4)}g (${mgAmount}mg)`;
        
        // Add drop conversion if available in response
        if (data.gel_amounts_drops && data.gel_amounts_drops[color]) {
            const drops = data.gel_amounts_drops[color];
            measurementDisplay += `<br><small>≈ ${drops.toFixed(1)} drops</small>`;
        }
        
        // Create HTML for gel amount display
        item.innerHTML = `
            <div class="gel-color-info">
                <div class="gel-color-swatch" style="background-color: ${colorMap[color]}; ${color === 'white' ? 'border: 1px solid #ddd;' : ''}"></div>
                <div class="gel-color-name">${color}</div>
            </div>
            <div class="gel-amount">${measurementDisplay}</div>
        `;
        
        gelAmountsContainer.appendChild(item);
    });

    // Display mixing instructions
    const instructionsContainer = document.getElementById('mixingInstructions');
    instructionsContainer.innerHTML = `<pre>${data.mixing_instructions.join('\n')}</pre>`;

    // Show results section and scroll to it
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Handle Reset button click
 * Clears all form data, uploaded image, and results to start fresh
 */
resetBtn.addEventListener('click', () => {
    // Clear all stored data
    uploadedImage = null;
    imageInput.value = '';
    previewImage.src = '';
    previewImage.classList.remove('visible');
    colorPreview.classList.remove('visible');
    
    // Reset UI to initial state
    document.querySelector('.upload-placeholder').style.display = 'block';
    calculateBtn.disabled = true;
    resultsSection.style.display = 'none';
    
    // Scroll to top for better UX
    window.scrollTo({ top: 0, behavior: 'smooth' });
});
