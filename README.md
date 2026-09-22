# RetinaScan AI 👁️
### Early Sight, Lasting Sight
RetinaScan AI is an explainable, AI-powered retinal screening system designed to assist in the early detection of **Diabetic Retinopathy (DR)** from fundus retinal images.

The system analyzes retinal images, identifies potential abnormal patterns, and provides an easy-to-understand screening result along with a confidence score.
> ⚠️ *Disclaimer: RetinaScan AI is a screening and educational prototype, not a replacement for professional medical diagnosis.

---
## 🚀 Key Features

- 🩺 **Diabetic Retinopathy Screening**
- 👁️ Retinal fundus image analysis
- 🤖 AI-assisted detection
- 📊 Confidence-based results
- 🔍 Explainable screening approach
- 📁 Patient medical history
- 🔐 User Login & Logout
- 📝 Previous screening reports
- 💻 Simple and responsive medical UI
- 🌐 Web-based application
- 📱 Designed with accessibility and rural healthcare use cases in mind

---
## 🎯 Problem Statement

Diabetic Retinopathy is one of the major causes of preventable vision loss.

Early-stage DR can often show subtle changes in the retina before severe vision problems occur. However, access to ophthalmologists and specialized retinal screening facilities can be limited, particularly in rural and underserved areas.

RetinaScan AI aims to provide an accessible first-level screening system that can help identify retinal images that may require further medical evaluation.

---
## 💡 Our Solution

RetinaScan AI allows a user to upload a retinal fundus image.

The system then:
1. Accepts the retinal image.
2. Preprocesses the image.
3. Analyzes retinal regions and abnormal visual patterns.
4. Calculates a screening score.
5. Generates a result.
6. Displays the confidence level.
7. Stores the screening report for future reference.

The goal is to make retinal screening **simple, explainable, and accessible**.

---

## 🧠 Explainable AI
Unlike a completely black-box prediction system, RetinaScan AI focuses on making the screening process understandable.

The analysis considers retinal image characteristics such as:

- Dark retinal lesions
- Bright yellow/white regions
- Abnormal spot patterns
- Retinal region characteristics
- Overall image intensity and distribution
These features contribute to the final screening score.

The system can classify an image into categories such as:

- **Healthy**
- **DR Detected**

along with an associated confidence score.

---

## 🛠️ Tech Stack

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python
- Flask
### Image Processing
- Pillow
- NumPy

### Database
- SQLite

### Development Tools
- Visual Studio Code
- Git
- GitHub

---
## 📂 Project Structure

```text
RetinaScan/
│
├── app.py
├── retina_scan.db
├── requirements.txt
├── README.md
retina scan ke liye send readme raw code

Haan, ye RetinaScan AI ke GitHub ke liye proper README.md raw code hai — directly README.md mein paste kar dena:

# RetinaScan AI 👁️
### Early Sight, Lasting Sight

RetinaScan AI is an explainable, AI-powered retinal screening system designed to assist in the early detection of **Diabetic Retinopathy (DR)** from fundus retinal images.

The system analyzes retinal images, identifies potential abnormal patterns, and provides an easy-to-understand screening result along with a confidence score.

> ⚠️ **Disclaimer:** RetinaScan AI is a screening and educational prototype, not a replacement for professional medical diagnosis.

---

## 🚀 Key Features

- 🩺 **Diabetic Retinopathy Screening**
- 👁️ Retinal fundus image analysis
- 🤖 AI-assisted detection
- 📊 Confidence-based results
- 🔍 Explainable screening approach
- 📁 Patient medical history
- 🔐 User Login & Logout
- 📝 Previous screening reports
- 💻 Simple and responsive medical UI
- 🌐 Web-based application
- 📱 Designed with accessibility and rural healthcare use cases in mind

---

## 🎯 Problem Statement

Diabetic Retinopathy is one of the major causes of preventable vision loss.

Early-stage DR can often show subtle changes in the retina before severe vision problems occur. However, access to ophthalmologists and specialized retinal screening facilities can be limited, particularly in rural and underserved areas.

RetinaScan AI aims to provide an accessible first-level screening system that can help identify retinal images that may require further medical evaluation.

---

## 💡 Our Solution

RetinaScan AI allows a user to upload a retinal fundus image.

The system then:

1. Accepts the retinal image.
2. Preprocesses the image.
3. Analyzes retinal regions and abnormal visual patterns.
4. Calculates a screening score.
5. Generates a result.
6. Displays the confidence level.
7. Stores the screening report for future reference.

The goal is to make retinal screening **simple, explainable, and accessible**.

---

## 🧠 Explainable AI

Unlike a completely black-box prediction system, RetinaScan AI focuses on making the screening process understandable.

The analysis considers retinal image characteristics such as:

- Dark retinal lesions
- Bright yellow/white regions
- Abnormal spot patterns
- Retinal region characteristics
- Overall image intensity and distribution

These features contribute to the final screening score.

The system can classify an image into categories such as:

- **Healthy**
- **DR Detected**

along with an associated confidence score.

---

## 🛠️ Tech Stack

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python
- Flask

### Image Processing
- Pillow
- NumPy

### Database
- SQLite

### Development Tools
- Visual Studio Code
- Git
- GitHub

---

## 📂 Project Structure

```text
RetinaScan/
│
├── app.py
├── retina_scan.db
├── requirements.txt
├── README.md
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│   ├── upload.html
│   ├── result.html
│   ├── history.html
│   └── ...
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   ├── js/
│   │   └── script.js
│   │
│   └── uploads/
│
└── ...
