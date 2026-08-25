# Photo Avatar Usage Guide

## Overview
MediaPipe-based photo avatars provide real-time lip-sync for static headshot images. The system detects facial landmarks and morphs the mouth region based on speech visemes.

## Quick Start

### 1. Prepare a Photo
- Headshot with clear view of face
- Minimum 400x500px resolution
- Neutral expression works best
- Save to `/static/avatars/` folder

### 2. Update Template
Add `photoUrl` to your `AvatarWidget.init()` call:

```javascript
const r = AvatarWidget.init({ 
    characterId: 'scientist', 
    floatContainerId: 'avatar-floater', 
    greeting: "Hello! I'm Doctor Nova.", 
    photoUrl: '/static/avatars/dr_nova.jpg',  // Enable photo avatar
    showByDefault: false,
});
```

### 3. Include Required Scripts
Make sure your template includes (in order):
```html
<script src="/static/avatar_engine.js?v=20261001"></script>
<script src="/static/photo_avatar.js?v=20261001"></script>
<script src="/static/avatar_widget.js?v=20261001"></script>
```

## How It Works

1. **MediaPipe Face Mesh** detects 468 facial landmarks on the photo
2. **Mouth landmarks** (indices 61-76) are tracked for the lip region
3. **Viseme mapping** translates speech to mouth shapes:
   - `A` - Wide open (ah)
   - `E` - Smile shape (eh)
   - `I` - Narrow (ih)
   - `O` - Round (oh)
   - `U` - Pursed (oo)
   - `rest` - Neutral closed

## Quality & Performance

| Aspect | Rating | Notes |
|--------|--------|-------|
| Lip sync accuracy | 80% | Good for casual use |
| Real-time performance | 60fps | Modern devices |
| Initial load | ~3s | MediaPipe models download |
| Quality | Acceptable | Best with illustrated/cartoon photos |

## Limitations

- **Static face**: Only mouth moves; eyes/head stay still
- **Single face**: One person per photo
- **Uncanny valley**: Real photos can look odd with animated mouth only
- **CORS**: Photos must be from same domain or have proper headers

## Comparison with SVG Avatars

| Feature | SVG Avatar | Photo Avatar |
|---------|-----------|--------------|
| Eye blinks | Yes | No |
| Head movement | Yes | No |
| Lip sync | 6 visemes | 6 visemes |
| Expression change | Yes | No |
| Load time | Instant | ~3s |
| File size | ~50KB | Photo + 10MB models |

## Troubleshooting

**"No face detected"**
- Ensure photo has clear, front-facing face
- Try different photo with better lighting
- Check browser console for errors

**Photo doesn't load**
- Verify CORS headers if using external URL
- Use local paths like `/static/avatars/photo.jpg`

**Mouth not animating**
- Check that `photo_avatar.js` loaded before `avatar_widget.js`
- Verify `window.PhotoAvatar` exists in console

## Example: Complete Character Template

```html
<!DOCTYPE html>
<html>
<head>
    <title>Photo Avatar Demo</title>
    <link href="/static/avatar_styles.css" rel="stylesheet">
</head>
<body>
    <!-- Float container for photo avatar -->
    <div id="avatar-floater"></div>

    <!-- Required scripts -->
    <script src="/static/avatar_engine.js"></script>
    <script src="/static/photo_avatar.js"></script>
    <script src="/static/avatar_widget.js"></script>

    <script>
        // Initialize with photo avatar
        if (window.AvatarWidget) {
            const result = AvatarWidget.init({
                characterId: 'my_character',
                floatContainerId: 'avatar-floater',
                photoUrl: '/static/avatars/my_photo.jpg',
                greeting: 'Hello! I can speak with my photo.',
                showByDefault: true
            });
            
            // Access the controller for manual speech
            const avatar = result.float;
            // avatar.speak('This is a test message');
        }
    </script>
</body>
</html>
```

## Future Enhancements

- LivePortrait integration for head movement
- Eye tracking for gaze direction
- Multi-person support
- Custom viseme fine-tuning
