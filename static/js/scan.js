document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("fileInput");
    const dropzone = document.getElementById("dropzone");

    const uploadStage = document.getElementById("uploadStage");
    const previewStage = document.getElementById("previewStage");
    const loadingStage = document.getElementById("loadingStage");
    const resultStage = document.getElementById("resultStage");

    const previewImage = document.getElementById("previewImage");
    const resultImage = document.getElementById("resultImage");

    const analyzeBtn = document.getElementById("analyzeBtn");
    const retakeBtn = document.getElementById("retakeBtn");
    const scanAgainBtn = document.getElementById("scanAgainBtn");

    const resultBadge = document.getElementById("resultBadge");
    const resultTitle = document.getElementById("resultTitle");
    const confidenceFill = document.getElementById("confidenceFill");
    const confidenceLabel = document.getElementById("confidenceLabel");
    const resultExplanation = document.getElementById("resultExplanation");
    const riskNote = document.getElementById("riskNote");
    const viewReportBtn = document.getElementById("viewReportBtn");

    const stepItems = document.querySelectorAll(".step-item");

    let selectedFile = null;

    // -------------------------
    // STEP UI
    // -------------------------

    function setStep(step) {
        stepItems.forEach(item => {
            const itemStep = Number(item.dataset.step);

            item.classList.toggle("active", itemStep === step);

            if (itemStep < step) {
                item.classList.add("completed");
            } else {
                item.classList.remove("completed");
            }
        });
    }

    function showStage(stage) {
        uploadStage.classList.add("hidden");
        previewStage.classList.add("hidden");
        loadingStage.classList.add("hidden");
        resultStage.classList.add("hidden");

        stage.classList.remove("hidden");
    }

    // -------------------------
    // FILE VALIDATION
    // -------------------------

    function handleFile(file) {
        if (!file) return;

        if (!file.type.startsWith("image/")) {
            alert("Please select a valid image file.");
            return;
        }

        const maxSize = 10 * 1024 * 1024;

        if (file.size > maxSize) {
            alert("Image is too large. Please select an image smaller than 10 MB.");
            return;
        }

        selectedFile = file;

        const reader = new FileReader();

        reader.onload = function (event) {
            previewImage.src = event.target.result;

            showStage(previewStage);
            setStep(2);
        };

        reader.onerror = function () {
            alert("Could not read the selected image.");
        };

        reader.readAsDataURL(file);
    }

    // -------------------------
    // FILE INPUT
    // -------------------------

    fileInput.addEventListener("change", function () {
        const file = this.files[0];

        if (file) {
            handleFile(file);
        }
    });

    // -------------------------
    // DRAG & DROP
    // -------------------------

    dropzone.addEventListener("dragover", function (event) {
        event.preventDefault();
        dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", function () {
        dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", function (event) {
        event.preventDefault();

        dropzone.classList.remove("dragover");

        const file = event.dataTransfer.files[0];

        if (file) {
            handleFile(file);
        }
    });

    // -------------------------
    // ANALYZE IMAGE
    // -------------------------

    analyzeBtn.addEventListener("click", async function () {
        if (!selectedFile) {
            alert("Please select an image first.");
            return;
        }

        showStage(loadingStage);
        setStep(3);

        const formData = new FormData();
        formData.append("image", selectedFile);

        try {
            const response = await fetch("/analyze", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Analysis failed.");
            }

            displayResult(data);

        } catch (error) {
            console.error("Analysis error:", error);

            alert("Analysis failed: " + error.message);

            showStage(previewStage);
            setStep(2);
        }
    });

    // -------------------------
    // DISPLAY RESULT
    // -------------------------

    function displayResult(data) {
        resultTitle.textContent = data.result || "Analysis complete";

        resultBadge.textContent = data.result || "Result";

        resultExplanation.textContent =
            data.explanation || "No explanation was provided.";

        // Confidence
        let confidence = parseFloat(data.confidence);

        if (isNaN(confidence)) {
            confidence = 0;
        }

        // Handle both 0.85 and 85 formats
        if (confidence <= 1) {
            confidence *= 100;
        }

        confidence = Math.max(0, Math.min(100, confidence));

        confidenceFill.style.width = confidence + "%";

        confidenceLabel.textContent =
            "Confidence: " + confidence.toFixed(1) + "%";

        // Risk note
        const resultText = String(data.result || "").toLowerCase();

        if (
            resultText.includes("positive") ||
            resultText.includes("severe") ||
            resultText.includes("moderate") ||
            resultText.includes("refer")
        ) {
            riskNote.textContent =
                "This screening result may require further evaluation by an eye-care professional.";
        } else {
            riskNote.textContent =
                "No significant signs were detected by the screening system. Regular eye examinations are still recommended.";
        }

        // Show uploaded image in result
        const imageURL = URL.createObjectURL(selectedFile);
        resultImage.src = imageURL;

        // Report link
        if (data.report_url) {
            viewReportBtn.href = data.report_url;
        } else {
            viewReportBtn.href = "#";
        }

        showStage(resultStage);
    }

    // -------------------------
    // RETAKE
    // -------------------------

    retakeBtn.addEventListener("click", function () {
        selectedFile = null;

        fileInput.value = "";
        previewImage.src = "";

        showStage(uploadStage);
        setStep(1);
    });

    // -------------------------
    // SCAN AGAIN
    // -------------------------

    scanAgainBtn.addEventListener("click", function () {
        selectedFile = null;

        fileInput.value = "";
        previewImage.src = "";
        resultImage.src = "";

        showStage(uploadStage);
        setStep(1);
    });
});