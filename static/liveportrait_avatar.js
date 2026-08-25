/**
 * LivePortraitAvatar - Advanced photo avatar with real face warping
 * 
 * Uses MediaPipe Face Mesh for 468 landmark detection, then applies
 * actual mesh deformation to warp the face for lip sync, expressions,
 * and head movement. The face pixels actually move - not just overlay.
 */

class LivePortraitAvatar {
    constructor(containerOrId, imageUrl) {
        this.container = typeof containerOrId === 'string' 
            ? document.getElementById(containerOrId) 
            : containerOrId;
        this.imageUrl = imageUrl;
        
        // Core elements
        this.canvas = null;
        this.ctx = null;
        this.img = null;
        this.offscreenCanvas = null; // For original image storage
        this.offscreenCtx = null;
        
        // MediaPipe
        this.faceMesh = null;
        this.landmarks = null; // 468 points from MediaPipe
        this.baseLandmarks = null; // Neutral pose landmarks
        
        // Animation state
        this.isSpeaking = false;
        this.viseme = 'rest';
        this.visemeIntensity = 0;
        this.headPose = { pitch: 0, yaw: 0, roll: 0 };
        this.expression = 'neutral';
        this.eyeState = { open: 1.0, blinkTimer: 0 };
        
        // Lip sync shape interpolation
        this.currentShape = { open: 0, width: 1, round: 0 };
        this.targetShape = { open: 0, width: 1, round: 0 };
        
        // Idle animation
        this.idleTime = 0;
        this.breathingPhase = 0;
        
        // Render loop
        this._animationId = null;
        this._blinkInterval = null;
        
        // Triangulation for mesh warping
        this.triangles = null;
    }

    async init() {
        console.log('[LivePortrait] Initializing...');
        if (!this.container) throw new Error('Container not found');
        
        // Setup canvases
        this._setupCanvas();
        
        // Load image
        try {
            this.img = await this._loadImage(this.imageUrl);
            console.log('[LivePortrait] Image loaded:', this.img.width, 'x', this.img.height);
            
            // Scale to reasonable render size (max 480px on longest side)
            const maxRender = 480;
            const imgScale = Math.min(maxRender / this.img.width, maxRender / this.img.height, 1);
            const rw = Math.round(this.img.width * imgScale);
            const rh = Math.round(this.img.height * imgScale);
            console.log('[LivePortrait] Render size:', rw, 'x', rh);
            
            this.canvas.width = rw;
            this.canvas.height = rh;
            this.offscreenCanvas.width = rw;
            this.offscreenCanvas.height = rh;
            
            // Store scaled image
            this.offscreenCtx.drawImage(this.img, 0, 0, rw, rh);
        } catch (err) {
            console.error('[LivePortrait] Failed to load image:', err);
            throw err;
        }
        
        // Load MediaPipe
        try {
            await this._loadMediaPipe();
            console.log('[LivePortrait] MediaPipe loaded');
        } catch (err) {
            console.error('[LivePortrait] Failed to load MediaPipe:', err);
        }
        
        // Detect face landmarks
        try {
            await this._detectFace();
            console.log('[LivePortrait] Face detected, landmarks:', this.landmarks ? this.landmarks.length : 0);
            if (this.landmarks) {
                this.baseLandmarks = JSON.parse(JSON.stringify(this.landmarks));
                this._buildTriangleMesh();
            }
        } catch (err) {
            console.error('[LivePortrait] Face detection failed:', err);
        }
        
        // Start animations
        this._startBlinkAnimation();
        this._render();
        
        console.log('[LivePortrait] Ready');
        return this;
    }

    _setupCanvas() {
        // Visible canvas
        this.canvas = document.createElement('canvas');
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.borderRadius = '12px';
        this.canvas.style.objectFit = 'cover';
        this.canvas.style.display = 'block';
        this.container.innerHTML = '';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
        
        // Offscreen canvas for original image
        this.offscreenCanvas = document.createElement('canvas');
        this.offscreenCtx = this.offscreenCanvas.getContext('2d');
    }

    _loadImage(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            img.onload = () => resolve(img);
            img.onerror = () => reject(new Error('Failed to load image: ' + url));
            img.src = url;
        });
    }

    async _loadMediaPipe() {
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
        this.faceMesh = new window.FaceMesh({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
        });

        this.faceMesh.setOptions({
            maxNumFaces: 1,
            refineLandmarks: true,
            minDetectionConfidence: 0.3,
            minTrackingConfidence: 0.3
        });

        // Try detection up to 3 times (MediaPipe can need warm-up)
        for (let attempt = 1; attempt <= 3; attempt++) {
            console.log(`[LivePortrait] Face detection attempt ${attempt}/3...`);
            
            const results = await new Promise((resolve) => {
                this.faceMesh.onResults((r) => resolve(r));
                const tempCanvas = document.createElement('canvas');
                // Use a standard size to help detection
                const maxDim = 640;
                const scale = Math.min(maxDim / this.img.width, maxDim / this.img.height, 1);
                tempCanvas.width = Math.round(this.img.width * scale);
                tempCanvas.height = Math.round(this.img.height * scale);
                const tempCtx = tempCanvas.getContext('2d');
                tempCtx.drawImage(this.img, 0, 0, tempCanvas.width, tempCanvas.height);
                this.faceMesh.send({ image: tempCanvas });
            });

            if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
                this.landmarks = results.multiFaceLandmarks[0];
                console.log(`[LivePortrait] Face found on attempt ${attempt}!`);
                return;
            }
            
            console.warn(`[LivePortrait] No face found on attempt ${attempt}`);
            // Small delay before retry
            if (attempt < 3) await new Promise(r => setTimeout(r, 500));
        }
        
        console.error('[LivePortrait] No face detected after 3 attempts. Check image has a clear front-facing face.');
    }

    _buildTriangleMesh() {
        // Minimal mesh - only mouth region for lip sync performance
        // We now use direct canvas drawing instead of mesh warping
        this.triangles = null; // Not used anymore
        console.log('[LivePortrait] Using optimized lip sync rendering');
    }

    _getMorphedLandmarks() {
        if (!this.landmarks || !this.baseLandmarks) return null;
        
        // Clone only essential landmarks for performance
        const morphed = new Array(this.baseLandmarks.length);
        for (let i = 0; i < this.baseLandmarks.length; i++) {
            morphed[i] = { x: this.baseLandmarks[i].x, y: this.baseLandmarks[i].y };
        }
        
        // Smooth viseme interpolation - faster for more responsive speech
        const alpha = this.isSpeaking ? 0.5 : 0.1;
        this.currentShape.open += (this.targetShape.open - this.currentShape.open) * alpha;
        this.currentShape.width += (this.targetShape.width - this.currentShape.width) * alpha;
        
        // Head movement is now applied as canvas transform in _warpMesh
        // We store current head pose values for the render function
        // Head sway: idle ±4°, speaking adds ±3° more
        this._headYaw = Math.sin(this.idleTime * 0.0012) * 4
            + (this.isSpeaking ? Math.sin(this.idleTime * 0.005) * 3 : 0);
        this._headPitch = Math.cos(this.idleTime * 0.0008) * 3
            + (this.isSpeaking ? Math.cos(this.idleTime * 0.004) * 2 : 0);
        this._headRoll = Math.sin(this.idleTime * 0.0006) * 2; // degrees
        
        // Upper lip indices (move UP when mouth opens)
        const upperLipIndices = [
            0, 37, 39, 40, 185, 61,   // upper outer left
            267, 269, 270, 409, 291,  // upper outer right
            78, 191, 80, 81, 82,      // upper inner left
            312, 311, 310, 415, 308,  // upper inner right
            13                         // upper center
        ];
        // Lower lip indices (move DOWN when mouth opens)
        const lowerLipIndices = [
            146, 91, 181, 84, 17,     // lower outer left
            314, 405, 321, 375,       // lower outer right
            95, 88, 178, 87,          // lower inner left
            317, 402, 318, 324,       // lower inner right
            14                         // lower center
        ];
        // Corner indices (move for width)
        const cornerIndices = [61, 291, 78, 308];
        
        const mouthOpen = this.currentShape.open;
        const mouthWidth = this.currentShape.width;
        const mouthCenterX = (morphed[61].x + morphed[291].x) / 2;
        
        // Measure face height: forehead (10) to chin (152) in normalized coords
        const faceTop = this.baseLandmarks[10].y;
        const faceBottom = this.baseLandmarks[152].y;
        const faceHeight = faceBottom - faceTop; // typically ~0.25-0.45
        
        // Real human max mouth opening ≈ 12% of face height
        // Split: upper lip moves 1/3, lower lip moves 2/3
        const maxOpenNorm = faceHeight * 0.12;
        const upperMove = maxOpenNorm * 0.33 * mouthOpen;
        const lowerMove = maxOpenNorm * 0.67 * mouthOpen;
        
        // Debug: log every 120 frames (~2 sec)
        if (!this._dbgCount) this._dbgCount = 0;
        this._dbgCount++;
        if (this._dbgCount % 120 === 0) {
            console.log('[LP-DBG] open:', mouthOpen.toFixed(3),
                'faceH:', faceHeight.toFixed(3),
                'upperMove:', upperMove.toFixed(4), 'lowerMove:', lowerMove.toFixed(4),
                'speaking:', this.isSpeaking);
        }
        
        // Move upper lip UP
        upperLipIndices.forEach(idx => {
            morphed[idx].y -= upperMove;
        });
        
        // Move lower lip DOWN (jaw drop)
        lowerLipIndices.forEach(idx => {
            morphed[idx].y += lowerMove;
        });
        
        // Width: move corners
        cornerIndices.forEach(idx => {
            const dx = morphed[idx].x - mouthCenterX;
            morphed[idx].x = mouthCenterX + dx * mouthWidth;
        });
        
        // Round shape (O/U vowels)
        if (this.currentShape.round > 0.3) {
            const roundFactor = 1 - this.currentShape.round * 0.3;
            cornerIndices.forEach(idx => {
                const dx = morphed[idx].x - mouthCenterX;
                morphed[idx].x = mouthCenterX + dx * roundFactor;
            });
        }
        
        // Apply eye blink - derive from actual eye height
        if (this.eyeState.open < 0.9) {
            // Measure eye opening from landmarks: upper lid (159) to lower lid (145) for left eye
            const eyeHeight = Math.abs(this.baseLandmarks[145].y - this.baseLandmarks[159].y);
            const eyeCloseFactor = (1 - this.eyeState.open) * eyeHeight * 0.5;
            const eyeIndices = [159, 145, 144, 153, 154, 386, 374, 373, 380, 381];
            eyeIndices.forEach(idx => {
                if (idx < morphed.length) {
                    const p = morphed[idx];
                    if ([159, 145, 144, 386, 374, 373].includes(idx)) {
                        p.y += eyeCloseFactor;
                    } else {
                        p.y -= eyeCloseFactor;
                    }
                }
            });
        }
        
        return morphed;
    }

    _applyHeadTransform(ctx, w, h, sourceLandmarks) {
        const yaw = this._headYaw || 0;
        const pitch = this._headPitch || 0;
        const roll = this._headRoll || 0;
        
        const noseTip = sourceLandmarks[1];
        const pivotX = noseTip ? noseTip.x * w : w / 2;
        const pivotY = noseTip ? noseTip.y * h : h / 2;
        
        // Scale movement to canvas size (percentage-based)
        const yawPx = (yaw / 10) * w * 0.04;   // ±7° → ~±4% of width
        const pitchPx = (pitch / 10) * h * 0.03; // ±5° → ~±3% of height
        
        ctx.translate(pivotX, pivotY);
        ctx.rotate(roll * Math.PI / 180);
        ctx.translate(yawPx, pitchPx);
        const breathScale = 1 + this.breathingPhase;
        ctx.scale(breathScale, breathScale);
        ctx.translate(-pivotX, -pivotY);
    }

    _warpMesh(sourceLandmarks, targetLandmarks) {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        const srcCanvas = this.offscreenCanvas;
        
        // Clear canvas
        ctx.clearRect(0, 0, w, h);
        
        // ── Draw entire image with head transform ──────────────
        ctx.save();
        this._applyHeadTransform(ctx, w, h, sourceLandmarks);
        ctx.drawImage(srcCanvas, 0, 0);
        ctx.restore();
        
        // ── MOUTH WARP: same transform so it tracks with the face ──
        if (!this.landmarks) return;
        
        // Use landmark 0 (upper lip top) and 17 (lower lip bottom) for mouth measurement
        const baseTopY = sourceLandmarks[0].y * h;
        const baseBottomY = sourceLandmarks[17].y * h;
        const targetTopY = targetLandmarks[0].y * h;
        const targetBottomY = targetLandmarks[17].y * h;
        
        const baseOpen = baseBottomY - baseTopY;
        const targetOpen = targetBottomY - targetTopY;
        const stretchFactor = targetOpen / Math.max(baseOpen, 1);
        
        // Debug: log stretchFactor periodically
        if (this._dbgCount && this._dbgCount % 60 === 0) {
            console.log('[LP-DBG] stretchFactor:', stretchFactor.toFixed(4),
                'baseOpen:', baseOpen.toFixed(1), 'targetOpen:', targetOpen.toFixed(1),
                'lm0baseY:', sourceLandmarks[0].y.toFixed(4),
                'lm17baseY:', sourceLandmarks[17].y.toFixed(4),
                'lm0targetY:', targetLandmarks[0].y.toFixed(4),
                'lm17targetY:', targetLandmarks[17].y.toFixed(4));
        }
        
        if (stretchFactor > 1.01) {
            // Apply SAME head transform so mouth moves with face
            ctx.save();
            this._applyHeadTransform(ctx, w, h, sourceLandmarks);
            this._warpMouthRegion(ctx, srcCanvas, sourceLandmarks, targetLandmarks, w, h, stretchFactor);
            ctx.restore();
        }
    }

    _warpMouthRegion(ctx, srcCanvas, sourceLandmarks, targetLandmarks, w, h, stretchFactor) {
        // Source: where upper/lower lips are in the ORIGINAL image
        const srcUpperY = sourceLandmarks[13].y * h;  // Upper lip center
        const srcLowerY = sourceLandmarks[14].y * h;  // Lower lip center
        const srcMidY = (srcUpperY + srcLowerY) / 2;
        
        // Target: where they should be after morphing
        const tgtUpperY = targetLandmarks[13].y * h;
        const tgtLowerY = targetLandmarks[14].y * h;
        
        // How far lips have moved from original
        const upperShift = tgtUpperY - srcUpperY;  // negative = moved up
        const lowerShift = tgtLowerY - srcLowerY;  // positive = moved down
        const gapPixels = (tgtLowerY - tgtUpperY) - (srcLowerY - srcUpperY);
        
        if (Math.abs(gapPixels) < 1) return; // No significant change
        
        // Mouth corners for horizontal bounds
        const leftX = Math.min(targetLandmarks[61].x, sourceLandmarks[61].x) * w;
        const rightX = Math.max(targetLandmarks[291].x, sourceLandmarks[291].x) * w;
        const pad = w * 0.04;
        const regionLeft = Math.max(0, leftX - pad);
        const regionRight = Math.min(w, rightX + pad);
        const regionWidth = regionRight - regionLeft;
        
        // Vertical bounds for the warp zone
        const warpTop = Math.max(0, srcMidY - h * 0.06);
        const warpBottom = Math.min(h, srcMidY + h * 0.08);
        
        // Helper: draw lip-shaped path between upper inner and lower inner edges
        const _drawMouthPath = (ctx, lm, w, h) => {
            // Inner upper lip edge
            const upperInner = [61, 78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 291];
            // Inner lower lip edge (reverse)
            const lowerInner = [291, 324, 318, 402, 317, 14, 87, 178, 88, 95, 78, 61];
            ctx.beginPath();
            upperInner.forEach((idx, i) => {
                const x = lm[idx].x * w, y = lm[idx].y * h;
                i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
            });
            lowerInner.forEach(idx => {
                ctx.lineTo(lm[idx].x * w, lm[idx].y * h);
            });
            ctx.closePath();
        };
        
        // ── Step 1: Draw natural mouth interior (lip-shaped) ──
        ctx.save();
        _drawMouthPath(ctx, targetLandmarks, w, h);
        // Gradient from dark red-brown (top) to darker (bottom) like real mouth
        const mouthGradY1 = targetLandmarks[13].y * h;
        const mouthGradY2 = targetLandmarks[14].y * h;
        const grad = ctx.createLinearGradient(0, mouthGradY1, 0, mouthGradY2);
        grad.addColorStop(0, '#4a1a1a');   // Upper: dark reddish
        grad.addColorStop(0.4, '#2d0e0e'); // Mid: darker
        grad.addColorStop(1, '#1a0808');   // Bottom: darkest
        ctx.fillStyle = grad;
        ctx.fill();
        
        // ── Step 1b: Draw subtle teeth row at top of mouth ──
        // Teeth sit just below upper lip inner edge, clipped to mouth shape
        const teethLeft = targetLandmarks[78].x * w;
        const teethRight = targetLandmarks[308].x * w;
        const teethTop = mouthGradY1 + 1;
        const teethHeight = (mouthGradY2 - mouthGradY1) * 0.3; // Teeth = 30% of opening
        if (teethHeight > 2) {
            const teethGrad = ctx.createLinearGradient(0, teethTop, 0, teethTop + teethHeight);
            teethGrad.addColorStop(0, 'rgba(240, 235, 225, 0.85)'); // Off-white, slightly transparent
            teethGrad.addColorStop(1, 'rgba(200, 195, 185, 0.4)');  // Fades out
            ctx.fillStyle = teethGrad;
            // Rounded rectangle for teeth
            const teethW = teethRight - teethLeft;
            const r = Math.min(teethHeight * 0.4, teethW * 0.05);
            ctx.beginPath();
            ctx.moveTo(teethLeft + r, teethTop);
            ctx.lineTo(teethRight - r, teethTop);
            ctx.quadraticCurveTo(teethRight, teethTop, teethRight, teethTop + r);
            ctx.lineTo(teethRight, teethTop + teethHeight);
            ctx.lineTo(teethLeft, teethTop + teethHeight);
            ctx.lineTo(teethLeft, teethTop + r);
            ctx.quadraticCurveTo(teethLeft, teethTop, teethLeft + r, teethTop);
            ctx.closePath();
            ctx.fill();
        }
        ctx.restore();
        
        // ── Step 2: Draw upper half shifted UP, clipped to upper lip shape ──
        ctx.save();
        // Clip: outer upper lip + straight bottom edge
        const upperOuter = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291];
        ctx.beginPath();
        upperOuter.forEach((idx, i) => {
            const x = targetLandmarks[idx].x * w, y = targetLandmarks[idx].y * h;
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        });
        // Close with rectangle top
        ctx.lineTo(regionRight, warpTop);
        ctx.lineTo(regionLeft, warpTop);
        ctx.closePath();
        ctx.clip();
        ctx.drawImage(
            srcCanvas,
            regionLeft, warpTop, regionWidth, srcMidY - warpTop,
            regionLeft, warpTop + upperShift, regionWidth, srcMidY - warpTop
        );
        ctx.restore();
        
        // ── Step 3: Draw lower half shifted DOWN, clipped to lower lip shape ──
        ctx.save();
        const lowerOuter = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291];
        ctx.beginPath();
        lowerOuter.forEach((idx, i) => {
            const x = targetLandmarks[idx].x * w, y = targetLandmarks[idx].y * h;
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        });
        // Close with rectangle bottom
        ctx.lineTo(regionRight, warpBottom);
        ctx.lineTo(regionLeft, warpBottom);
        ctx.closePath();
        ctx.clip();
        ctx.drawImage(
            srcCanvas,
            regionLeft, srcMidY, regionWidth, warpBottom - srcMidY,
            regionLeft, srcMidY + lowerShift, regionWidth, warpBottom - srcMidY
        );
        ctx.restore();
    }

    setViseme(viseme) {
        this.viseme = viseme;
        // More exaggerated viseme shapes for better visibility
        const visemeMap = {
            'rest': { open: 0.0, width: 1.0, round: 0.0 },   // Closed
            'A':    { open: 0.9, width: 1.0, round: 0.0 },   // Wide open "ah"
            'E':    { open: 0.6, width: 1.1, round: 0.0 },   // Mid open, spread "eh"
            'I':    { open: 0.4, width: 0.85, round: 0.0 },   // Narrow "ee"
            'O':    { open: 0.7, width: 0.7, round: 1.0 },    // Rounded "oh"
            'U':    { open: 0.5, width: 0.6, round: 0.9 },    // Puckered "oo"
        };
        this.targetShape = visemeMap[viseme] || visemeMap['rest'];
        this.isSpeaking = viseme !== 'rest';
    }

    setExpression(expr) {
        this.expression = expr;
        // Map expressions to head pose and feature adjustments
        const expressions = {
            'neutral': { browLift: 0, smile: 0, headTilt: 0 },
            'happy': { browLift: 0.2, smile: 0.8, headTilt: 0.1 },
            'sad': { browLift: -0.3, smile: -0.2, headTilt: -0.1 },
            'surprised': { browLift: 0.6, smile: 0, headTilt: -0.2 },
            'thinking': { browLift: 0.1, smile: 0, headTilt: 0.3 }
        };
        this.exprParams = expressions[expr] || expressions['neutral'];
    }

    setHeadPose(pitch, yaw, roll) {
        this.headPose = { pitch, yaw, roll };
    }

    _startBlinkAnimation() {
        const scheduleBlink = () => {
            const delay = 2000 + Math.random() * 4000; // 2-6 seconds
            this._blinkTimer = setTimeout(() => {
                this._blink();
                scheduleBlink();
            }, delay);
        };
        scheduleBlink();
    }

    _blink() {
        // Animate eye closing and opening
        const duration = 150; // ms
        const startTime = performance.now();
        
        const animateBlink = (time) => {
            const elapsed = time - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Parabolic blink: 1 -> 0 -> 1
            this.eyeState.open = 1 - Math.sin(progress * Math.PI);
            
            if (progress < 1) {
                requestAnimationFrame(animateBlink);
            } else {
                this.eyeState.open = 1;
            }
        };
        
        requestAnimationFrame(animateBlink);
    }

    _render() {
        try {
            if (!this.ctx || !this.img) {
                this._animationId = requestAnimationFrame(() => this._render());
                return;
            }
            
            // Advance time
            this.idleTime += 16;
            this.breathingPhase = Math.sin(this.idleTime * 0.002) * 0.008;
            
            // Get morphed landmarks
            const morphedLandmarks = this._getMorphedLandmarks();
            
            if (morphedLandmarks && this.baseLandmarks) {
                // Warp the mesh - actual face deformation
                this._warpMesh(this.baseLandmarks, morphedLandmarks);
            } else {
                // Fallback: just draw original image
                const ctx = this.ctx;
                const w = this.canvas.width;
                const h = this.canvas.height;
                ctx.clearRect(0, 0, w, h);
                ctx.drawImage(this.img, 0, 0, w, h);
            }
            
        } catch (err) {
            console.error('[LivePortrait] Render error:', err);
        }
        
        this._animationId = requestAnimationFrame(() => this._render());
    }


    speak(text) {
        if (!window.speechSynthesis) return;
        
        // Stop any current speech
        window.speechSynthesis.cancel();
        clearInterval(this._visemeInterval);
        clearTimeout(this._visemeTimeout);
        
        this.isSpeaking = true;
        this.setExpression('happy');
        
        // Split text into words and generate per-word visemes
        const words = text.split(/\s+/).filter(w => w.length > 0);
        const wordVisemes = words.map(word => this._textToVisemes(word));
        
        const utter = new SpeechSynthesisUtterance(text);
        utter.rate = 1.0;
        utter.pitch = 1.0;
        
        let wordIndex = 0;
        let speechStartTime = 0;
        
        // Use boundary events for word-level sync
        utter.onboundary = (event) => {
            if (event.name === 'word' && wordIndex < wordVisemes.length) {
                const visemeSeq = wordVisemes[wordIndex];
                wordIndex++;
                
                // Animate through this word's visemes
                // Estimate word duration from char count (~70ms per char at rate 1.0)
                const wordLen = visemeSeq.length;
                const perViseme = Math.max(50, Math.min(90, 70));
                
                visemeSeq.forEach((v, i) => {
                    this._visemeTimeout = setTimeout(() => {
                        this.setViseme(v.viseme);
                    }, i * perViseme);
                });
                
                // Brief rest after word
                this._visemeTimeout = setTimeout(() => {
                    this.setViseme('rest');
                }, wordLen * perViseme);
            }
        };
        
        utter.onstart = () => {
            speechStartTime = performance.now();
            // Fallback: if no boundary events fire, use timed approach
            this._boundaryFired = false;
            setTimeout(() => {
                if (!this._boundaryFired && this.isSpeaking) {
                    this._fallbackVisemeSync(text);
                }
            }, 300);
        };
        
        // Track if boundary events are working
        const origOnBoundary = utter.onboundary;
        utter.onboundary = (event) => {
            this._boundaryFired = true;
            origOnBoundary.call(this, event);
        };
        
        const cleanup = () => {
            this.isSpeaking = false;
            this.setViseme('rest');
            this.setExpression('neutral');
            clearInterval(this._visemeInterval);
            clearTimeout(this._visemeTimeout);
        };
        
        utter.onend = cleanup;
        utter.onerror = cleanup;
        
        window.speechSynthesis.speak(utter);
    }
    
    _fallbackVisemeSync(text) {
        // Fallback when boundary events don't fire
        const visemes = this._textToVisemes(text);
        let idx = 0;
        // Estimate total duration: ~70ms per character
        const perChar = 70;
        
        this._visemeInterval = setInterval(() => {
            if (idx < visemes.length && this.isSpeaking) {
                this.setViseme(visemes[idx].viseme);
                idx++;
            } else {
                clearInterval(this._visemeInterval);
            }
        }, perChar);
    }

    _textToVisemes(text) {
        // More comprehensive phoneme-to-viseme mapping
        const map = {
            // Vowels - wide open mouth
            'a': 'A', 'A': 'A', 'æ': 'A', 'ɑ': 'A',
            // Vowels - mid open 
            'e': 'E', 'E': 'E', 'ɛ': 'E', 'ɜ': 'E',
            'o': 'O', 'O': 'O', 'ɔ': 'O', 'ɒ': 'O',
            // Vowels - narrow
            'i': 'I', 'I': 'I', 'ɪ': 'I', 'ɨ': 'I',
            // Vowels - rounded
            'u': 'U', 'U': 'U', 'ʊ': 'U', 'ʌ': 'A',
            // Consonants - closed mouth
            'm': 'rest', 'n': 'rest', 'ŋ': 'rest', 'p': 'rest', 'b': 'rest',
            // Consonants - lip biting
            'f': 'E', 'v': 'E',
            // Consonants - wide
            'w': 'U', 'r': 'O', 'l': 'O',
            // Spaces and punctuation
            ' ': 'rest', '.': 'rest', ',': 'rest', '!': 'rest', '?': 'rest'
        };
        
        const chars = text.toLowerCase().split('');
        const visemes = [];
        
        for (let i = 0; i < chars.length; i++) {
            const char = chars[i];
            const v = map[char] || 'rest';
            
            // Add the viseme
            visemes.push({ char, viseme: v });
            
            // Hold vowels a bit longer for better visibility
            if (v !== 'rest' && v !== undefined && i < chars.length - 1) {
                // Add a slight hold by duplicating
                if ('aeiou'.includes(char)) {
                    visemes.push({ char: '', viseme: v });
                }
            }
        }
        
        return visemes;
    }

    stop() {
        this.isSpeaking = false;
        this.setViseme('rest');
        this.setExpression('neutral');
        if (this._visemeInterval) clearInterval(this._visemeInterval);
        if (this._blinkTimer) clearTimeout(this._blinkTimer);
    }

    destroy() {
        this.stop();
        if (this._animationId) cancelAnimationFrame(this._animationId);
        if (this.container && this.canvas) {
            this.container.removeChild(this.canvas);
        }
    }
}

// Expose to window
if (typeof window !== 'undefined') {
    window.LivePortraitAvatar = LivePortraitAvatar;
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LivePortraitAvatar;
}
