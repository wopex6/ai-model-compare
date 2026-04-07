# iPhone Development Installation Guide

## 📱 Install AI Model Compare on Your iPhone (Development)

### Prerequisites
- **iPhone** (iPhone 7 Plus or newer)
- **Mac** with Xcode 14+
- **Apple Developer Account** (Free or Paid)
- **USB Cable** to connect iPhone to Mac

---

## 🔧 Step-by-Step Installation

### 1. Setup Your Apple Developer Account
```bash
# If you don't have one, create a free account:
# 1. Go to https://developer.apple.com
# 2. Sign in with your Apple ID
# 3. Accept the terms and conditions
```

### 2. Open the Project in Xcode
```bash
# Navigate to the project folder
cd "c:\Users\trabc\CascadeProjects\ai-model-compare - Claude\ios_app\AIModelCompare"

# Open in Xcode
open AIModelCompare.xcodeproj
```

### 3. Configure Project Settings
In Xcode:
1. **Select the Project** in the navigator (left sidebar)
2. **Select the Target** "AIModelCompare"
3. **Signing & Capabilities** tab:
   - **Team**: Select your Apple Developer account
   - **Bundle Identifier**: Change to something unique (e.g., `com.yourname.aicompare`)
   - **Automatically manage signing**: ✅ Enabled

### 4. Connect Your iPhone
1. **Connect iPhone** to Mac with USB cable
2. **Trust This Computer** on iPhone when prompted
3. **Select your iPhone** from device dropdown in Xcode (top toolbar)

### 5. Build and Install
```bash
# In Xcode, press Cmd+R or click the Run button
# The app will build and install on your iPhone
```

### 6. Trust the Developer Certificate
On your iPhone:
1. **Settings** → **General** → **VPN & Device Management**
2. **Find your Apple ID** under "Developer App"
3. **Tap** your name → **Trust**

---

## 🔑 Configure API Keys in the App

Once the app is installed:

### 1. Open AI Model Compare on iPhone
2. **Go to Settings tab** (bottom right)
3. **Tap "API Keys" section**
4. **Add your API keys**:

#### OpenAI API Key
- Visit: https://platform.openai.com/api-keys
- Click "Create new secret key"
- Copy and paste into app

#### Anthropic API Key  
- Visit: https://console.anthropic.com/
- Go to API Keys → Create key
- Copy and paste into app

#### Google AI API Key
- Visit: https://makersuite.google.com/app/apikey
- Create API key
- Copy and paste into app

---

## 🧪 Testing on Your iPhone

### Basic Functionality Tests
- [ ] **App launches** successfully
- [ ] **Tab navigation** works (Chat, Compare, History, Settings)
- [ ] **Chat interface** accepts text input
- [ ] **Voice input** records and transcribes
- [ ] **Model selection** works in settings
- [ ] **Comparison feature** generates results
- [ ] **History search** finds previous conversations
- [ ] **Dark/Light theme** switches properly

### Advanced Features Tests
- [ ] **Multiple model chat** (select 2+ models)
- [ ] **Streaming responses** work in real-time
- [ ] **Model comparison** with ratings
- [ ] **Export functionality** shares results
- [ ] **Data persistence** (restart app, data remains)

---

## 🐛 Troubleshooting Common Issues

### Build Issues
**"Failed to create provisioning profile"**
- Solution: Change Bundle Identifier to something unique
- Example: `com.johnsmith.aicompare2024`

**"iPhone is busy: Please try again"**
- Solution: Disconnect/reconnect iPhone
- Restart Xcode if needed

**"Code signing error"**
- Solution: Check Team selection in Signing & Capabilities
- Ensure you're logged into Apple Developer in Xcode preferences

### Runtime Issues
**"App crashes on launch"**
- Check Xcode console for error details
- Ensure iOS 13.0+ on your iPhone

**"Voice input not working"**
- Check Microphone permissions in Settings → Privacy
- Ensure physical device (not simulator) for voice features

**"API calls failing"**
- Verify API keys are correct
- Check internet connection
- Ensure API provider service is available

---

## 🔄 Development Workflow

### Making Changes
1. **Edit code** in Xcode
2. **Build and run** (Cmd+R) - app updates automatically
3. **Test changes** on device
4. **Debug** using Xcode console if needed

### Testing Features
```bash
# Enable debug logging in Xcode console
# Product → Scheme → Edit Scheme → Run → Arguments
# Add environment variable: OS_ACTIVITY_MODE = debug
```

### Performance Testing
- Use **Instruments** in Xcode for performance profiling
- Monitor memory usage, CPU, network
- Test on different iPhone models if available

---

## 📸 Screenshots for App Store (Future Reference)

When ready for App Store submission, you'll need:

### Required Screenshots
- **iPhone 6.7" Display**: 1290 x 2796 pixels
- **iPhone 6.5" Display**: 1242 x 2208 pixels  
- **iPhone 5.5" Display**: 1242 x 2208 pixels

### Screenshots to Capture
1. **Chat interface** with multiple models
2. **Comparison view** with results
3. **History view** with search
4. **Settings view** with API keys
5. **Voice input** recording screen

---

## 🚀 Next Steps After Testing

### If Everything Works:
1. **Test thoroughly** on your iPhone
2. **Gather feedback** from friends/family
3. **Fix any bugs** discovered
4. **Prepare for App Store submission**

### For Production Release:
1. **Create App Store Connect account**
2. **Add app metadata** and screenshots
3. **Submit for review** to Apple
4. **Wait for approval** (typically 1-7 days)

---

## 🆘 Get Help

### Xcode Issues
- **Apple Developer Forums**: https://developer.apple.com/forums/
- **Stack Overflow**: Search for "Xcode iOS development"

### API Issues
- **OpenAI**: https://platform.openai.com/docs
- **Anthropic**: https://docs.anthropic.com/
- **Google AI**: https://ai.google.dev/docs

### Project-Specific Help
- Review the **BUILD_GUIDE.md** in the project folder
- Check **test results** for any failing components
- Use **Xcode Console** for runtime debugging

---

## 🎯 Success Checklist

- [ ] Xcode project opens without errors
- [ ] iPhone connects and appears in device list
- [ ] App builds and installs successfully
- [ ] App launches and runs on iPhone
- [ ] All main features work as expected
- [ ] API keys configured and working
- [ ] Voice features functional on physical device
- [ ] Data persists between app launches

**🎉 Once all these are checked, your app is ready for real-world testing!**
