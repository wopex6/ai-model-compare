/**
 * File Upload Handler for Chat Applications
 * Handles file/audio/video uploads for user-admin chat and AI chat
 */

class FileUploadHandler {
    constructor() {
        this.attachedFiles = {
            'admin-chat': null,
            'chat': null,
            'admin-reply': null
        };
        this.uploadedFileData = {
            'admin-chat': null,
            'chat': null,
            'admin-reply': null
        };
        this.maxFileSize = 10 * 1024 * 1024; // 10MB limit
        this.init();
    }

    init() {
        // Admin Chat File Upload
        this.setupFileInput('admin-chat-attach-btn', 'admin-chat-file-input', 'admin-chat-file-preview', 'admin-chat');
        
        // AI Chat File Upload
        this.setupFileInput('chat-attach-btn', 'chat-file-input', 'chat-file-preview', 'chat');
        
        // Admin Reply File Upload
        this.setupFileInput('admin-reply-attach-btn', 'admin-reply-file-input', 'admin-reply-file-preview', 'admin-reply');
    }

    setupFileInput(buttonId, inputId, previewId, context) {
        const button = document.getElementById(buttonId);
        const input = document.getElementById(inputId);
        
        if (button && input) {
            button.addEventListener('click', () => {
                input.click();
            });

            input.addEventListener('change', (e) => {
                this.handleFileSelect(e, previewId, context);
            });
        }
    }

    async handleFileSelect(event, previewId, context) {
        const file = event.target.files[0];
        if (!file) return;

        console.log('File selected:', file.name, 'Context:', context);

        // Check file size
        if (file.size > this.maxFileSize) {
            alert(`File is too large. Maximum size is ${this.maxFileSize / 1024 / 1024}MB`);
            event.target.value = '';
            return;
        }

        // Store file reference
        this.attachedFiles[context] = file;
        console.log('File stored in attachedFiles:', this.attachedFiles);

        // Show uploading preview
        this.showUploadingPreview(file, previewId, context);

        // Upload file to server
        const uploadedData = await this.uploadFileToServer(file, context);
        
        if (uploadedData) {
            // Show final preview with uploaded file
            this.showFilePreview(file, previewId, context, uploadedData);
        } else {
            // Upload failed, clear the file
            this.removeFile(context, previewId);
        }
    }

    showUploadingPreview(file, previewId, context) {
        /**Show uploading state */
        const preview = document.getElementById(previewId);
        if (!preview) return;

        const fileName = file.name;
        const fileSize = this.formatFileSize(file.size);

        preview.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px; padding: 12px; background: #f0f0f0; border-radius: 8px; border: 1px solid #ddd;">
                <i class="fas fa-spinner fa-spin" style="font-size: 24px; color: #667eea;"></i>
                <div style="flex: 1;">
                    <div style="font-weight: 500; color: #333;">Uploading ${fileName}...</div>
                    <div style="font-size: 0.85rem; color: #666;">${fileSize}</div>
                </div>
            </div>
        `;
        preview.style.display = 'block';
    }

    showFilePreview(file, previewId, context, uploadedData = null) {
        const preview = document.getElementById(previewId);
        if (!preview) return;

        const fileType = file.type.split('/')[0]; // audio, video, image, etc.
        const fileName = uploadedData ? uploadedData.original_filename : file.name;
        const fileSize = this.formatFileSize(uploadedData ? uploadedData.file_size : file.size);

        let icon = 'fa-file';
        if (fileType === 'image') icon = 'fa-image';
        else if (fileType === 'audio') icon = 'fa-music';
        else if (fileType === 'video') icon = 'fa-video';
        else if (file.type.includes('pdf')) icon = 'fa-file-pdf';
        else if (file.type.includes('word')) icon = 'fa-file-word';

        preview.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px; padding: 12px; background: #d4edda; border-radius: 8px; border: 1px solid #c3e6cb;">
                <i class="fas ${icon}" style="font-size: 24px; color: #667eea;"></i>
                <div style="flex: 1;">
                    <div style="font-weight: 500; color: #333;">${fileName}</div>
                    <div style="font-size: 0.85rem; color: #666;">${fileSize} <i class="fas fa-check-circle" style="color: #28a745;"></i> Ready</div>
                </div>
                <button onclick="window.fileUploadHandler.removeFile('${context}', '${previewId}')" style="background: none; border: none; color: #ff4757; cursor: pointer; padding: 8px;">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        preview.style.display = 'block';
    }

    removeFile(context, previewId) {
        this.attachedFiles[context] = null;
        const preview = document.getElementById(previewId);
        if (preview) {
            preview.innerHTML = '';
            preview.style.display = 'none';
        }

        // Clear file input
        const inputMap = {
            'admin-chat': 'admin-chat-file-input',
            'chat': 'chat-file-input',
            'admin-reply': 'admin-reply-file-input'
        };
        const input = document.getElementById(inputMap[context]);
        if (input) input.value = '';
    }

    getAttachedFile(context) {
        return this.attachedFiles[context];
    }

    getUploadedFileData(context) {
        return this.uploadedFileData[context];
    }

    async uploadFileToServer(file, context) {
        /**Upload file to server and store the response */
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload-file', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                this.uploadedFileData[context] = data;
                console.log('File uploaded successfully:', data);
                return data;
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            alert('Failed to upload file: ' + error.message);
            return null;
        }
    }

    clearAttachedFile(context) {
        this.attachedFiles[context] = null;
        this.uploadedFileData[context] = null;
        const previewMap = {
            'admin-chat': 'admin-chat-file-preview',
            'chat': 'chat-file-preview',
            'admin-reply': 'admin-reply-file-preview'
        };
        const preview = document.getElementById(previewMap[context]);
        if (preview) {
            preview.innerHTML = '';
            preview.style.display = 'none';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    renderFileAttachment(file) {
        /**Generate HTML for displaying an attached file in a message */
        const fileType = file.type ? file.type.split('/')[0] : 'file';
        const fileName = file.name || 'Attached File';
        const fileSize = file.size ? this.formatFileSize(file.size) : '';

        let icon = 'fa-file';
        let bgColor = '#e9ecef';
        if (fileType === 'image') {
            icon = 'fa-image';
            bgColor = '#d3f9d8';
        } else if (fileType === 'audio') {
            icon = 'fa-music';
            bgColor = '#d0ebff';
        } else if (fileType === 'video') {
            icon = 'fa-video';
            bgColor = '#ffe066';
        } else if (file.type && file.type.includes('pdf')) {
            icon = 'fa-file-pdf';
            bgColor = '#ffdeeb';
        }

        return `
            <div style="display: inline-flex; align-items: center; gap: 10px; padding: 10px; background: ${bgColor}; border-radius: 8px; margin-top: 8px; max-width: 300px;">
                <i class="fas ${icon}" style="font-size: 20px; color: #667eea;"></i>
                <div style="flex: 1; min-width: 0;">
                    <div style="font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${fileName}</div>
                    ${fileSize ? `<div style="font-size: 0.85rem; opacity: 0.8;">${fileSize}</div>` : ''}
                </div>
                <i class="fas fa-download" style="color: #667eea; cursor: pointer;" title="Download"></i>
            </div>
        `;
    }
}

// Initialize global file upload handler
document.addEventListener('DOMContentLoaded', () => {
    window.fileUploadHandler = new FileUploadHandler();
});
