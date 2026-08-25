/**
 * PhotoAvatar - MediaPipe-based photo avatar with real-time lip sync
 * 
 * Usage:
 *   const avatar = new PhotoAvatar(containerId, imageUrl);
 *   await avatar.init();
 *   avatar.setViseme('A'); // or 'E', 'I', 'O', 'U', 'rest'
 *   avatar.speak(text);    // uses TTS with viseme callbacks
 */

class PhotoAvatar {
    constructor(containerOrId, imageUrl) {
        // Accept either element or ID string
        this.container = typeof containerOrId === 'string' 
            ? document.getElementById(containerOrId) 
            : containerOrId;
        this.imageUrl = imageUrl;
        this.canvas = null;
        this.ctx = null;
        this.img = null;
        this.faceMesh = null;
        this.landmarks = null;
        this.mouthOpenness = 0; // 0-1
        this.viseme = 'rest';
        this.targetShape = { open: 0.0, width: 1.0, round: 0.0 }; // default rest shape
        this.currentShape = null;
        this.isSpeaking = false;
        this._animationId = null;
    }

    async init() {
        console.log('[PhotoAvatar] init() called, container:', this.container);
        if (!this.container) {
            console.error('[PhotoAvatar] Container not found');
            throw new Error('Container not found');
        }
        
        // Create canvas - size to fit container
        this.canvas = document.createElement('canvas');
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.borderRadius = '12px';
        this.canvas.style.objectFit = 'cover';
        this.canvas.style.display = 'block';
        this.container.innerHTML = '';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
        console.log('[PhotoAvatar] Canvas created and appended');

        // Load photo
        try {
            this.img = await this._loadImage(this.imageUrl);
            console.log('[PhotoAvatar] Image loaded:', this.img.width, 'x', this.img.height);
        } catch (err) {
            console.error('[PhotoAvatar] Failed to load image:', err);
            throw err;
        }
        
        this.canvas.width = this.img.width;
        this.canvas.height = this.img.height;
        
        // Load MediaPipe Face Mesh
        try {
            await this._loadMediaPipe();
            console.log('[PhotoAvatar] MediaPipe loaded');
        } catch (err) {
            console.error('[PhotoAvatar] Failed to load MediaPipe:', err);
        }
        
        // Detect face landmarks once
        try {
            await this._detectFace();
            console.log('[PhotoAvatar] Face detection complete, landmarks:', this.landmarks ? 'found' : 'not found');
        } catch (err) {
            console.error('[PhotoAvatar] Face detection failed:', err);
        }
        
        // Start render loop
        this._render();
        console.log('[PhotoAvatar] Render loop started');
        
        return this;
    }

    _loadImage(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = url;
        });
    }

    async _loadMediaPipe() {
        // Load MediaPipe scripts dynamically
        const scripts = [
            'https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/face_mesh.js',
            'https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js',
        ];
        
        for (const src of scripts) {
            if (!document.querySelector(`script[src="${src}"]`)) {
                await new Promise((resolve, reject) => {
                    const script = document.createElement('script');
                    script.src = src;
                    script.onload = resolve;
                    script.onerror = reject;
                    document.head.appendChild(script);
                });
            }
        }
    }

    async _detectFace() {
        // Initialize Face Mesh
        this.faceMesh = new window.FaceMesh({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
        });

        this.faceMesh.setOptions({
            maxNumFaces: 1,
            refineLandmarks: true,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });

        // Detect landmarks from static image
        const results = await new Promise((resolve) => {
            this.faceMesh.onResults((results) => resolve(results));
            // Create a temporary canvas to feed the image
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = this.img.width;
            tempCanvas.height = this.img.height;
            const tempCtx = tempCanvas.getContext('2d');
            tempCtx.drawImage(this.img, 0, 0);
            this.faceMesh.send({ image: tempCanvas });
        });

        if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
            this.landmarks = results.multiFaceLandmarks[0];
            // Store baseline mouth shape
            this._storeBaselineMouth();
        } else {
            console.warn('[PhotoAvatar] No face detected in image');
        }
    }

    // Mouth landmark indices in MediaPipe Face Mesh
    // Outer lips: 61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291
    // Inner lips: 78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308
    _storeBaselineMouth() {
        if (!this.landmarks) return;
        
        const outerLip = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291];
        const innerLip = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308];
        
        this.baselineMouth = {
            outer: outerLip.map(i => ({ ...this.landmarks[i] })),
            inner: innerLip.map(i => ({ ...this.landmarks[i] })),
            center: { ...this.landmarks[13] }, // upper lip center
            bottom: { ...this.landmarks[14] } // lower lip center (inner)
        };
        
        // Calculate mouth center for transformations
        const allMouth = [...outerLip, ...innerLip];
        let cx = 0, cy = 0;
        allMouth.forEach(i => {
            cx += this.landmarks[i].x;
            cy += this.landmarks[i].y;
        });
        this.mouthCenter = { x: cx / allMouth.length, y: cy / allMouth.length };
    }

    setViseme(viseme) {
        this.viseme = viseme;
        // Map viseme to mouth openness/shape
        const visemeMap = {
            'rest': { open: 0.0, width: 1.0, round: 0.0 },
            'A':    { open: 0.7, width: 0.8, round: 0.0 }, // open wide
            'E':    { open: 0.4, width: 1.0, round: 0.0 }, // smile shape
            'I':    { open: 0.2, width: 0.9, round: 0.0 }, // narrow
            'O':    { open: 0.5, width: 0.7, round: 1.0 }, // round
            'U':    { open: 0.3, width: 0.6, round: 0.8 }, // pursed
        };
        this.targetShape = visemeMap[viseme] || visemeMap['rest'];
    }

    _interpolateMouthShape() {
        if (!this.currentShape) {
            this.currentShape = { 
                open: this.targetShape.open, 
                width: this.targetShape.width, 
                round: this.targetShape.round 
            };
            return;
        }
        // Smooth interpolation
        const alpha = 0.3;
        this.currentShape.open = this.currentShape.open * (1 - alpha) + this.targetShape.open * alpha;
        this.currentShape.width = this.currentShape.width * (1 - alpha) + this.targetShape.width * alpha;
        this.currentShape.round = this.currentShape.round * (1 - alpha) + this.targetShape.round * alpha;
    }

    _getMorphedLandmarks() {
        if (!this.landmarks || !this.baselineMouth) return null;
        
        this._interpolateMouthShape();
        const s = this.currentShape;
        
        // Clone all landmarks
        const morphed = this.landmarks.map(l => ({ ...l }));
        
        // Mouth indices
        const upperLip = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291];
        const lowerLip = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291];
        const innerUpper = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308];
        const innerLower = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308];
        
        const mouthIndices = [...new Set([...upperLip, ...lowerLip, ...innerUpper, ...innerLower])];
        
        const cx = this.mouthCenter.x;
        const cy = this.mouthCenter.y;
        
        morphed.forEach((p, i) => {
            if (!mouthIndices.includes(i)) return;
            
            const dx = p.x - cx;
            const dy = p.y - cy;
            
            // Apply width scaling
            p.x = cx + dx * s.width;
            
            // Apply openness (vertical stretch, asymmetric for upper/lower)
            if (dy < 0) {
                // Upper lip - moves up
                p.y = cy + dy * (1 - s.open * 0.3);
            } else {
                // Lower lip - moves down
                p.y = cy + dy * (1 + s.open * 1.5);
            }
            
            // Apply rounding (pull corners inward when round)
            if (Math.abs(dx) > 0.02) {
                p.x += (dx > 0 ? -1 : 1) * s.round * 0.01;
            }
        });
        
        return morphed;
    }

    _render() {
        try {
            if (!this.ctx || !this.img) {
                this._animationId = requestAnimationFrame(() => this._render());
                return;
            }
            
            const ctx = this.ctx;
            const w = this.canvas.width;
            const h = this.canvas.height;
            
            // Clear
            ctx.clearRect(0, 0, w, h);
            
            // Draw base image
            ctx.drawImage(this.img, 0, 0, w, h);
            
            if (this.landmarks && this.baselineMouth) {
                // Get morphed landmarks
                const morphed = this._getMorphedLandmarks();
                
                // Create mouth mask path
                ctx.save();
                ctx.globalCompositeOperation = 'source-over';
                
                // Draw mouth region with slight distortion
                this._drawMouthRegion(ctx, morphed, w, h);
                
                ctx.restore();
            }
        } catch (err) {
            console.error('[PhotoAvatar] Render error:', err);
        }
        
        this._animationId = requestAnimationFrame(() => this._render());
    }

    _drawMouthRegion(ctx, landmarks, w, h) {
        if (!landmarks) return;
        
        // Define mouth polygon
        const upperLip = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291];
        const lowerLip = [291, 375, 321, 405, 314, 17, 84, 181, 91, 146, 61];
        
        // Create clipping region for mouth
        ctx.beginPath();
        upperLip.forEach((idx, i) => {
            const p = landmarks[idx];
            const x = p.x * w;
            const y = p.y * h;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        lowerLip.forEach(idx => {
            const p = landmarks[idx];
            ctx.lineTo(p.x * w, p.y * h);
        });
        ctx.closePath();
        
        // Fill with slightly darker tone for inner mouth
        ctx.fillStyle = 'rgba(60, 20, 20, 0.3)';
        ctx.fill();
        
        // Draw lips outline
        ctx.strokeStyle = 'rgba(200, 100, 100, 0.5)';
        ctx.lineWidth = 2;
        ctx.stroke();
    }

    speak(text) {
        // Use Web Speech API with viseme callback
        if (!window.speechSynthesis) return;
        
        this.isSpeaking = true;
        
        // Simple viseme detection from text
        const visemes = this._textToVisemes(text);
        let currentIndex = 0;
        
        const utter = new SpeechSynthesisUtterance(text);
        utter.rate = 1.0;
        utter.pitch = 1.0;
        
        // Approximate viseme timing based on speech rate
        const charDuration = 60; // ms per character approx
        
        utter.onstart = () => {
            currentIndex = 0;
            this._visemeInterval = setInterval(() => {
                if (currentIndex < visemes.length) {
                    this.setViseme(visemes[currentIndex].viseme);
                    currentIndex++;
                }
            }, charDuration);
        };
        
        utter.onend = () => {
            this.isSpeaking = false;
            clearInterval(this._visemeInterval);
            this.setViseme('rest');
        };
        
        utter.onerror = () => {
            this.isSpeaking = false;
            clearInterval(this._visemeInterval);
            this.setViseme('rest');
        };
        
        window.speechSynthesis.speak(utter);
    }

    _textToVisemes(text) {
        // Map characters to visemes
        const map = {
            'a': 'A', 'A': 'A', 'e': 'E', 'E': 'E', 'i': 'I', 'I': 'I',
            'o': 'O', 'O': 'O', 'u': 'U', 'U': 'U',
            'm': 'rest', 'n': 'rest', 'p': 'rest', 'b': 'rest',
            'f': 'rest', 'v': 'rest', 'w': 'rest',
            ' ': 'rest', '.': 'rest', ',': 'rest'
        };
        
        return text.split('').map(char => ({
            char,
            viseme: map[char] || 'rest'
        }));
    }

    stop() {
        this.isSpeaking = false;
        if (this._visemeInterval) clearInterval(this._visemeInterval);
        if (this._animationId) cancelAnimationFrame(this._animationId);
        this.setViseme('rest');
    }

    destroy() {
        this.stop();
        if (this.faceMesh) {
            this.faceMesh.close();
        }
        if (this.container && this.canvas) {
            this.container.removeChild(this.canvas);
        }
    }
}

// Expose to window for browser use
if (typeof window !== 'undefined') {
    window.PhotoAvatar = PhotoAvatar;
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PhotoAvatar;
}
