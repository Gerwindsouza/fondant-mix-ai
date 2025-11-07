const fileInput = document.getElementById("fileInput");
const cameraButton = document.getElementById("cameraButton");
const captureButton = document.getElementById("captureButton");
const cameraContainer = document.getElementById("cameraContainer");
const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const resultDiv = document.getElementById("result");

// --- Handle file uploads ---
fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  if (file) await sendImage(file);
});

// --- Handle camera start ---
cameraButton.addEventListener("click", async () => {
  cameraContainer.style.display = "block";
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { exact: "environment" } } // Rear camera preferred
    });
    video.srcObject = stream;
  } catch (err) {
    console.warn("Rear camera not available, using default:", err);
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
  }
});

// --- Handle image capture from camera ---
captureButton.addEventListener("click", async () => {
  const context = canvas.getContext("2d");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  context.drawImage(video, 0, 0, canvas.width, canvas.height);

  const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg"));
  await sendImage(blob);
});

// --- Send image to backend for color analysis ---
async function sendImage(fileOrBlob) {
  resultDiv.innerHTML = "Analyzing image...";
  const formData = new FormData();
  formData.append("image", fileOrBlob, "photo.jpg");

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      body: formData
    });

    const data = await response.json();
    if (data.error) {
      resultDiv.innerHTML = `<span style="color:red;">${data.error}</span>`;
    } else {
      const rgb = data.dominant_color;
      const colorBox = `<div style="width:100px;height:100px;background:rgb(${rgb.join(",")});margin:auto;border-radius:8px;border:1px solid #ccc;"></div>`;
      resultDiv.innerHTML = `<p>Dominant Color: rgb(${rgb.join(",")})</p>${colorBox}`;
    }
  } catch (err) {
    resultDiv.innerHTML = `<span style="color:red;">Error analyzing image.</span>`;
  }
}
