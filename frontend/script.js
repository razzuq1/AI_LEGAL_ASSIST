const API_BASE = 'http://localhost:5000/api';

// DOM Elements
const fileInput = document.getElementById('f');
const uploadZone = document.getElementById('z');
const progressContainer = document.getElementById('pc');
const progressFill = document.getElementById('pf');
const progressText = document.getElementById('pt');
const loadingScreen = document.getElementById('l');
const analysisSection = document.getElementById('as');
const summaryContent = document.getElementById('sc');
const risksContent = document.getElementById('rc');
const chatHistory = document.getElementById('ch');
const questionInput = document.getElementById('qi');
const askButton = document.getElementById('ab');

let currentDocument = null;

// Event Listeners
uploadZone.addEventListener('click', () => {
    if (!uploadZone.classList.contains('uploading')) {
        fileInput.click();
    }
});

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('d');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('d');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('d');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});

askButton.addEventListener('click', handleQuestion);
questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleQuestion();
    }
});

// Main Functions
async function handleFileUpload(file) {
    if (!validateFile(file)) {
        showError('Invalid file type. Please upload PDF, DOC, DOCX, or TXT files.');
        return;
    }

    if (file.size > 50 * 1024 * 1024) {
        showError('File size too large. Maximum 50MB allowed.');
        return;
    }

    try {
        // Show progress
        showProgress();
        updateProgress(10, 'Starting upload...');

        // Upload file
        const uploadResult = await uploadDocument(file);
        
        if (uploadResult.success) {
            currentDocument = uploadResult.document_id;
            updateProgress(50, 'Processing document...');
            
            // Analyze document
            const analysisResult = await analyzeDocument(currentDocument);
            
            if (analysisResult.success) {
                updateProgress(100, 'Complete!');
                setTimeout(() => {
                    hideProgress();
                    displayAnalysis(analysisResult.data);
                    showAnalysisSection();
                }, 500);
            } else {
                throw new Error(analysisResult.error || 'Analysis failed');
            }
        } else {
            throw new Error(uploadResult.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        hideProgress();
        showError('Error: ' + error.message);
        resetUploadZone();
    }
}

async function uploadDocument(file) {
    const formData = new FormData();
    formData.append('document', file);

    updateProgress(20, 'Uploading file...');

    const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
    });

    return await response.json();
}

async function analyzeDocument(documentId) {
    updateProgress(40, 'Analyzing content...');

    const response = await fetch(`${API_BASE}/analyze/${documentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    });

    return await response.json();
}

async function handleQuestion() {
    const question = questionInput.value.trim();
    if (!question || !currentDocument) return;

    addMessage(question, 'user');
    questionInput.value = '';

    const loadingMessage = addMessage('Thinking...', 'ai');

    try {
        const response = await fetch(`${API_BASE}/question`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                document_id: currentDocument,
                question: question
            })
        });

        const result = await response.json();
        
        chatHistory.removeChild(loadingMessage);
        
        if (result.success) {
            addMessage(result.answer, 'ai');
        } else {
            addMessage('Sorry, I could not process your question. Please try again.', 'ai');
        }
    } catch (error) {
        console.error('Question error:', error);
        chatHistory.removeChild(loadingMessage);
        addMessage('Error processing question. Please try again.', 'ai');
    }
}

function displayAnalysis(data) {
    // Display summary
    summaryContent.innerHTML = `
        <div class="analysis-header">
            <h4><i class="fas fa-file-alt"></i> ${data.document_type || 'Legal Document'}</h4>
            <div class="document-description">
                <small>${getDocumentDescription(data.document_type)}</small>
            </div>
            <div class="analysis-summary">
                <p>${data.summary || 'Document processed successfully.'}</p>
            </div>
        </div>
        
        ${data.parties && data.parties.length > 0 ? `
        <div class="analysis-section">
            <h5><i class="fas fa-users"></i> Parties Involved</h5>
            <ul class="parties-list">
                ${data.parties.map(party => `<li>${party}</li>`).join('')}
            </ul>
        </div>
        ` : ''}
        
        ${data.key_terms && data.key_terms.length > 0 ? `
        <div class="analysis-section">
            <h5><i class="fas fa-key"></i> Key Terms</h5>
            <div class="key-terms">
                ${data.key_terms.map(term => `
                    <div class="term-item">
                        <strong>${term.term}:</strong> ${term.definition}
                    </div>
                `).join('')}
            </div>
        </div>
        ` : ''}
        
        ${data.financial_terms && data.financial_terms.length > 0 ? `
        <div class="analysis-section">
            <h5><i class="fas fa-dollar-sign"></i> Financial Terms</h5>
            <ul class="financial-list">
                ${data.financial_terms.map(term => `<li>${term}</li>`).join('')}
            </ul>
        </div>
        ` : ''}
        
        ${data.dates && data.dates.length > 0 ? `
        <div class="analysis-section">
            <h5><i class="fas fa-calendar"></i> Important Dates</h5>
            <ul class="dates-list">
                ${data.dates.map(date => `<li>${date}</li>`).join('')}
            </ul>
        </div>
        ` : ''}
        
        <div class="analysis-stats">
            <div class="stat-item">
                <span class="stat-number">${data.key_terms ? data.key_terms.length : 0}</span>
                <span class="stat-label">Key Terms</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">${data.risks ? data.risks.length : 0}</span>
                <span class="stat-label">Risk Areas</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">${data.parties ? data.parties.length : 0}</span>
                <span class="stat-label">Parties</span>
            </div>
        </div>
    `;

    // Display risks
    risksContent.innerHTML = '';
    if (data.risks && data.risks.length > 0) {
        data.risks.forEach(risk => {
            const riskElement = document.createElement('div');
            riskElement.className = `risk-item risk-${risk.level.toLowerCase()}`;
            riskElement.innerHTML = `
                <div class="risk-header">
                    <h5>${risk.title}</h5>
                    <span class="risk-level">${risk.level}</span>
                </div>
                <p>${risk.description}</p>
            `;
            risksContent.appendChild(riskElement);
        });
    } else {
        risksContent.innerHTML = '<p class="no-risks">No specific risks identified in this document.</p>';
    }

    // Clear chat and add welcome message
    chatHistory.innerHTML = '';
    addMessage(`Document analysis complete! I've analyzed your ${data.document_type.toLowerCase()} and found ${data.key_terms ? data.key_terms.length : 0} key terms and ${data.risks ? data.risks.length : 0} potential risks. Feel free to ask me any questions about the document.`, 'ai');
    
    // Generate and display dynamic prompts
    generateDynamicPrompts(data);
}

function generateDynamicPrompts(analysisData) {
    // Request dynamic prompts from backend
    fetch(`${API_BASE}/generate-prompts`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            document_id: currentDocument,
            analysis_data: analysisData
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success && result.prompts) {
            updateSuggestionButtons(result.prompts);
        } else {
            // Fallback to default prompts based on document type
            const defaultPrompts = getDefaultPrompts(analysisData.document_type);
            updateSuggestionButtons(defaultPrompts);
        }
    })
    .catch(error => {
        console.error('Failed to generate dynamic prompts:', error);
        const defaultPrompts = getDefaultPrompts(analysisData.document_type);
        updateSuggestionButtons(defaultPrompts);
    });
}

function getDefaultPrompts(documentType) {
    const prompts = {
        'Employment Contract': [
            "What is the salary and compensation structure?",
            "What are the termination conditions?",
            "Are there any non-compete clauses?",
            "What benefits are included?"
        ],
        'Service Agreement': [
            "What services are being provided?",
            "What are the payment terms?",
            "What are the deliverables and timelines?",
            "What happens if services are unsatisfactory?"
        ],
        'Non-Disclosure Agreement': [
            "What information is considered confidential?",
            "How long does confidentiality last?",
            "What are the penalties for disclosure?",
            "What are the exceptions to confidentiality?"
        ],
        'Lease Agreement': [
            "What is the rental amount and schedule?",
            "What are tenant responsibilities?",
            "Are pets allowed?",
            "What are the renewal terms?"
        ]
    };
    
    return prompts[documentType] || [
        "What are the main obligations of each party?",
        "What are the payment terms?",
        "When does this agreement expire?",
        "What happens if someone breaches the contract?"
    ];
}

function updateSuggestionButtons(prompts) {
    const suggestionsContainer = document.querySelector('.suggestion-buttons');
    if (!suggestionsContainer) return;
    
    suggestionsContainer.innerHTML = '';
    
    prompts.slice(0, 6).forEach(prompt => {
        const button = document.createElement('button');
        button.className = 'suggestion-btn';
        button.textContent = prompt;
        button.onclick = () => {
            document.getElementById('qi').value = prompt;
            handleQuestion();
        };
        suggestionsContainer.appendChild(button);
    });
}

function getDocumentDescription(docType) {
    const descriptions = {
        'Employment Contract': 'Governs the relationship between employer and employee',
        'Service Agreement': 'Defines services to be provided and terms',
        'Non-Disclosure Agreement': 'Protects confidential information',
        'Lease Agreement': 'Rental terms for property or equipment', 
        'Purchase Agreement': 'Terms for buying/selling goods or services',
        'Partnership Agreement': 'Structure and terms for business partnership',
        'License Agreement': 'Terms for using intellectual property'
    };
    return descriptions[docType] || 'Contains legal terms and obligations';
}


function addMessage(message, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    if (sender === 'ai') {
        messageDiv.innerHTML = `<div class="message-content">${message}</div>`;
    } else {
        messageDiv.innerHTML = `<div class="message-content">${message}</div>`;
    }
    
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return messageDiv;
}

// UI Helper Functions
function showProgress() {
    progressContainer.style.display = 'block';
    uploadZone.classList.add('uploading');
}

function hideProgress() {
    progressContainer.style.display = 'none';
    loadingScreen.style.display = 'none';
    uploadZone.classList.remove('uploading');
}

function updateProgress(percentage, text) {
    progressFill.style.width = `${percentage}%`;
    progressText.textContent = text;
    
    if (percentage > 30) {
        loadingScreen.style.display = 'block';
    }
}

function showAnalysisSection() {
    analysisSection.style.display = 'block';
    analysisSection.scrollIntoView({ behavior: 'smooth' });
}

function resetUploadZone() {
    uploadZone.classList.remove('uploading');
    currentDocument = null;
}

function validateFile(file) {
    const allowedTypes = [
        'application/pdf',
        'text/plain',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    return allowedTypes.includes(file.type);
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <div class="error-content">
            <i class="fas fa-exclamation-triangle"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.insertBefore(errorDiv, document.body.firstChild);
    
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 5000);
}

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const health = await response.json();
        console.log('Application health:', health);
        
        if (!health.components.gemini_analyzer) {
            showError('AI analysis not available. Please configure Gemini API key for full functionality.');
        }
    } catch (error) {
        console.error('Health check failed:', error);
        showError('Backend connection failed. Please ensure the server is running.');
    }
});