# AI Model Compare iOS App - Build & Deployment Guide

## Overview
A complete iOS app for comparing and interacting with multiple AI models, supporting iPhone 7 Plus through iPhone 14.

## Features Implemented
- **Multi-Model Chat**: Chat with multiple AI models simultaneously
- **Model Comparison**: Side-by-side comparison of model responses
- **Voice Input/Output**: Speech-to-text and text-to-speech capabilities
- **Offline Storage**: Core Data persistence for chats and comparisons
- **Responsive UI**: SwiftUI with iOS 13.0+ compatibility (iPhone 7 Plus)
- **API Key Management**: Secure storage for OpenAI, Anthropic, and Google API keys
- **Dark/Light Theme**: System theme support with manual override
- **History & Search**: Full search across chat and comparison history
- **Export Functionality**: Export comparison results

## Architecture
- **MVVM Pattern**: Clean separation of concerns
- **Combine Framework**: Reactive programming for data flow
- **Core Data**: Local persistence with relationships
- **URLSession**: Networking with streaming support
- **AVFoundation**: Voice input/output capabilities

## Requirements
- **Xcode 14+** (for iOS 13.0 deployment target)
- **iOS 13.0+** (iPhone 7 Plus compatibility)
- **Swift 5.7+**
- **Physical iOS device** for testing voice features
- **API Keys** from OpenAI, Anthropic, and/or Google

## Setup Instructions

### 1. Project Setup
```bash
# Clone or copy the project to your Mac
cd ios_app/AIModelCompare

# Open in Xcode
open AIModelCompare.xcodeproj
```

### 2. API Key Configuration
1. Open the app on device/simulator
2. Go to Settings → API Keys
3. Add your API keys:
   - **OpenAI**: Get from platform.openai.com/api-keys
   - **Anthropic**: Get from console.anthropic.com/
   - **Google**: Get from makersuite.google.com/app/apikey

### 3. Build Settings
In Xcode:
- **Team**: Select your Apple Developer account
- **Bundle Identifier**: Change to your unique identifier (e.g., com.yourname.aicompare)
- **Signing**: Enable automatic signing
- **Deployment Target**: iOS 13.0 (already set)

### 4. Build & Run
```bash
# In Xcode, select your device or simulator
# Press Cmd+R to build and run
```

## File Structure
```
AIModelCompare/
├── AIModelCompare/
│   ├── App/
│   │   └── App.swift                    # Main app entry point
│   ├── Views/
│   │   ├── ChatView.swift               # Chat interface
│   │   ├── CompareView.swift            # Model comparison
│   │   ├── HistoryView.swift            # Chat & comparison history
│   │   └── SettingsView.swift          # App settings
│   ├── ViewModels/
│   │   ├── ChatViewModel.swift          # Chat business logic
│   │   └── CompareViewModel.swift        # Comparison logic
│   ├── Models/
│   │   ├── DataModels.swift             # Core data models
│   │   └── AIModelCompare.xcdatamodeld  # Core Data model
│   ├── Services/
│   │   ├── AIService.swift              # AI API integration
│   │   └── DataStore.swift              # Core Data manager
│   ├── Resources/
│   │   ├── Assets.xcassets              # Images, icons
│   │   └── Info.plist                   # App metadata
│   └── Tests/
│       ├── AIModelCompareTests.swift    # Unit tests
│       └── AIModelCompareUITests.swift  # UI tests
```

## Key Components

### AI Services
- **OpenAI Service**: GPT-4, GPT-3.5 Turbo integration
- **Anthropic Service**: Claude 3 Opus, Claude 3 Sonnet
- **Google AI Service**: Gemini Pro integration
- **Streaming Support**: Real-time response streaming

### Data Models
- **Message**: Chat messages with metadata
- **ChatSession**: Conversation containers
- **ComparisonResult**: Model comparison results
- **UserSettings**: App preferences and API keys

### UI Components
- **MessageView**: Chat message display
- **ComparisonResultCard**: Comparison result display
- **ModelSelectionView**: AI model picker
- **APIKeySheet**: Secure API key input

## Testing

### Unit Tests
```bash
# Run unit tests in Xcode
Cmd+U
```

### UI Tests
```bash
# Run UI tests (requires simulator)
Cmd+U (with AIModelCompareUITests scheme)
```

### Manual Testing Checklist
- [ ] App launches on iPhone 7 Plus simulator
- [ ] Chat interface works with multiple models
- [ ] Voice input records and transcribes
- [ ] Model comparison generates results
- [ ] History search works correctly
- [ ] Settings save and persist
- [ ] Dark/light theme switches properly
- [ ] API keys configure securely

## Deployment

### App Store Distribution
1. **Archive the App**: Product → Archive
2. **Upload to App Store**: Xcode Organizer → Distribute App
3. **App Store Connect**: Complete metadata, screenshots, privacy info
4. **Submit for Review**: Wait for Apple approval

### Ad-Hoc Distribution
1. **Build for Device**: Select your device, Cmd+R
2. **Archive**: Product → Archive
3. **Export**: Distribute App → Ad Hoc
4. **Install**: Send IPA to testers via TestFlight or directly

### Enterprise Distribution
1. **Enterprise Certificate**: Required for internal distribution
2. **Manifest File**: For over-the-air installation
3. **Web Server**: Host IPA and manifest files

## API Integration Details

### OpenAI Integration
```swift
// Endpoint: https://api.openai.com/v1/chat/completions
// Models: gpt-4, gpt-3.5-turbo
// Streaming: Supported
// Vision: Not supported (in current implementation)
```

### Anthropic Integration
```swift
// Endpoint: https://api.anthropic.com/v1/messages
// Models: claude-3-opus, claude-3-sonnet
// Streaming: Supported
// Vision: Supported (in current implementation)
```

### Google AI Integration
```swift
// Endpoint: https://generativelanguage.googleapis.com/v1beta
// Models: gemini-pro
// Streaming: Supported
// Vision: Supported (in current implementation)
```

## Security Considerations
- **API Keys**: Stored in iOS Keychain (production)
- **Network**: HTTPS only, certificate pinning recommended
- **Data**: Local Core Data encryption optional
- **Privacy**: No analytics or tracking by default

## Performance Optimizations
- **Lazy Loading**: Messages and results load on demand
- **Image Caching**: Model icons cached in memory
- **Network**: Request timeouts and retry logic
- **Memory**: Core Data relationship faulting

## Troubleshooting

### Common Issues
1. **Build Fails**: Check Xcode version and deployment target
2. **API Errors**: Verify API keys and network connectivity
3. **Voice Issues**: Check microphone permissions
4. **Crashes**: Review device logs in Xcode Console

### Debug Tips
- Use Xcode Console for device logs
- Enable Network Link Conditioner for testing
- Use Simulator for basic UI testing
- Test on physical device for voice features

## Future Enhancements
- **Vision Input**: Camera integration for image analysis
- **Custom Models**: Support for custom AI endpoints
- **Collaboration**: Share comparisons with other users
- **Analytics**: Usage statistics and insights
- **Widgets**: Home screen widgets for quick access

## Support
For issues or questions:
1. Check Xcode build logs
2. Review Apple Developer documentation
3. Test on multiple device sizes
4. Verify API service status

## License
This project is provided as-is for educational and development purposes. Ensure compliance with AI service provider terms when distributing.
