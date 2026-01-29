// DOM Elements
const uploadBox = document.getElementById('uploadBox');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeFile = document.getElementById('removeFile');
const convertBtn = document.getElementById('convertBtn');
const btnText = document.getElementById('btnText');
const spinner = document.getElementById('spinner');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');
const daxOutput = document.getElementById('daxOutput');
const errorMessage = document.getElementById('errorMessage');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');

let currentFile = null;
let currentDax = null;
let currentFilename = null;

// Upload box click
uploadBox.addEventListener('click', () => fileInput.click());

// File input change
fileInput.addEventListener('change', (e) => {
    handleFile(e.target.files[0]);
});

// Drag and drop
uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadBox.classList.add('dragover');
});

uploadBox.addEventListener('dragleave', () => {
    uploadBox.classList.remove('dragover');
});

uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadBox.classList.remove('dragover');
    handleFile(e.dataTransfer.files[0]);
});

// Handle file
function handleFile(file) {
    if (!file) return;

    if (!file.name.endsWith('.sql')) {
        showError('Please upload a .sql file');
        return;
    }

    currentFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);

    uploadBox.style.display = 'none';
    fileInfo.style.display = 'flex';
    convertBtn.disabled = false;

    hideError();
    hideResult();
}

// Remove file
removeFile.addEventListener('click', () => {
    currentFile = null;
    fileInput.value = '';
    uploadBox.style.display = 'block';
    fileInfo.style.display = 'none';
    convertBtn.disabled = true;
    hideError();
    hideResult();
});

// Convert button
convertBtn.addEventListener('click', async () => {
    if (!currentFile) return;

    // Show loading state
    convertBtn.disabled = true;
    btnText.style.display = 'none';
    spinner.style.display = 'block';
    hideError();
    hideResult();

    try {
        const formData = new FormData();
        formData.append('file', currentFile);

        const response = await fetch('/convert', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            currentDax = data.dax;
            currentFilename = data.filename;
            showResult(data.dax);
        } else {
            showError(data.error || 'Conversion failed');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        // Reset button state
        convertBtn.disabled = false;
        btnText.style.display = 'block';
        spinner.style.display = 'none';
    }
});

// Copy button
copyBtn.addEventListener('click', async () => {
    try {
        await navigator.clipboard.writeText(currentDax);
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!';
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
        }, 2000);
    } catch (error) {
        showError('Failed to copy to clipboard');
    }
});

// Download button
downloadBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dax: currentDax,
                filename: currentFilename
            })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = currentFilename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            showError('Download failed');
        }
    } catch (error) {
        showError('Download error: ' + error.message);
    }
});

// Helper functions
function showResult(dax) {
    daxOutput.textContent = dax;
    resultSection.style.display = 'block';
}

function hideResult() {
    resultSection.style.display = 'none';
}

function showError(message) {
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
}

function hideError() {
    errorSection.style.display = 'none';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
