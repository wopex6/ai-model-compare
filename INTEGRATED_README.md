# Integrated AI Chatbot - Multi-User Environment

A comprehensive AI chatbot system that combines multi-user authentication, personalized conversations, psychology trait profiling, and real AI model integration.

## 🚀 Features

### 🔐 Multi-User Authentication
- **Secure Login/Signup**: JWT-based authentication system
- **Password Management**: Change password functionality
- **Session Management**: Persistent user sessions
- **User Isolation**: Complete data separation between users

### 🤖 AI-Powered Conversations
- **Real AI Responses**: Integration with multiple AI models (GPT, Claude, etc.)
- **Personalized Interactions**: AI responses tailored to user profiles and psychology traits
- **Conversation Persistence**: All conversations saved and accessible across sessions
- **Multiple Chat Sessions**: Create and manage multiple conversation threads

### 👤 User Profile System
- **Personal Information**: Name, bio, location, avatar
- **Profile-Based Context**: AI uses profile information for personalized responses
- **Editable Profiles**: Update information anytime

### 🧠 Psychology Trait Integration
- **Personality Profiling**: Track psychological characteristics (Big Five traits)
- **AI Personalization**: AI adapts responses based on user's psychological profile
- **Trait Management**: Add, edit, and manage psychology traits
- **Behavioral Insights**: AI considers user traits for more appropriate responses

### 💬 Advanced Conversation Management
- **Session Persistence**: Conversations survive browser restarts
- **Message History**: Complete conversation history
- **Context Awareness**: AI maintains context across conversation turns
- **Real-time Messaging**: Instant AI responses

## 🏗️ System Architecture

### Backend Components
- **Flask Web Server**: Main application server
- **Integrated Database**: SQLite database with user management and conversation storage
- **AI Model Integration**: Connection to existing AI comparison system
- **Authentication System**: JWT-based secure authentication
- **Personality Profiler**: Psychology trait analysis and management

### Frontend Components
- **Multi-User Interface**: Complete web-based UI
- **Responsive Design**: Works on desktop and mobile
- **Real-time Updates**: Dynamic content loading
- **Modern UI/UX**: Beautiful, intuitive interface

### Database Schema
- **users**: Authentication and basic user info
- **user_profiles**: Extended profile information
- **psychology_traits**: Individual psychological characteristics
- **ai_conversations**: Conversation metadata and session management
- **messages**: Individual messages with full context
- **user_interactions**: Interaction tracking and analytics

## 🎯 Default User

The system comes pre-configured with a test user:
- **Username**: `Wai Tse`
- **Password**: `.//`
- **Features**: Complete profile, psychology traits, and sample conversations

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Installation Steps

1. **Navigate to the project directory**:
   ```bash
   cd C:\Users\trabc\CascadeProjects\ai-model-compare
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (create `.env` file):
   ```
   SECRET_KEY=your-secret-key-here
   JWT_SECRET=your-jwt-secret-here
   OPENAI_API_KEY=your-openai-key
   ANTHROPIC_API_KEY=your-anthropic-key
   ```

4. **Start the server**:
   ```bash
   python app.py
   ```

5. **Access the application**:
   - Original AI Compare: `http://localhost:5000/`
   - **New Multi-User Interface**: `http://localhost:5000/multi-user`

## 🎮 Usage Guide

### Getting Started
1. **Access the Multi-User Interface**: Navigate to `http://localhost:5000/multi-user`
2. **Login**: Use "Wai Tse" / ".//." or create a new account
3. **Explore Features**: Navigate through the different tabs

### Main Features

#### 🤖 AI Chat Tab
- **Start Conversations**: Click "New Chat" to begin
- **Real AI Responses**: Get responses from actual AI models
- **Personalized Experience**: AI considers your profile and traits
- **Session Management**: Switch between different chat sessions

#### 👤 Profile Tab
- **Personal Information**: Add your details for better AI personalization
- **Bio Section**: Tell the AI about yourself for more relevant responses
- **Profile Updates**: Modify information anytime

#### 🧠 Psychology Tab
- **Add Traits**: Define your psychological characteristics
- **Trait Values**: Rate traits on a 0-1 scale
- **AI Integration**: AI uses these traits to adapt its communication style
- **Trait Management**: Edit existing traits or add new ones

#### 💬 Conversations Tab
- **View All Conversations**: See all your chat history
- **Message History**: Complete conversation records
- **Session Selection**: Jump to any previous conversation

#### ⚙️ Settings Tab
- **Password Management**: Change your password securely
- **Account Settings**: Manage your account preferences

### AI Personalization

The AI system uses your information to provide personalized responses:

1. **Profile Context**: Your bio and interests influence AI responses
2. **Psychology Traits**: AI adapts communication style based on your traits
3. **Conversation History**: AI maintains context across sessions
4. **Behavioral Patterns**: System learns from your interaction patterns

## 🔧 Technical Details

### API Endpoints

#### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/change-password` - Password update
- `GET /api/auth/user` - Get current user info

#### Profile Management
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update user profile

#### Psychology Traits
- `GET /api/user/psychology-traits` - Get user's traits
- `POST /api/user/psychology-traits` - Create new trait
- `PUT /api/user/psychology-traits/<trait_name>` - Update trait

#### Conversations
- `GET /api/user/conversations` - Get user's conversations
- `POST /api/user/conversations` - Create new conversation
- `GET /api/user/conversations/<session_id>/messages` - Get messages
- `POST /api/user/conversations/<session_id>/messages` - Send message (gets AI response)

### Security Features
- **Password Hashing**: bcrypt encryption for all passwords
- **JWT Authentication**: Secure token-based authentication
- **Data Isolation**: Users can only access their own data
- **Input Validation**: Server-side validation for all inputs
- **SQL Injection Protection**: Parameterized queries

### AI Integration
- **Model Selection**: Automatic selection of best available AI model
- **Context Enhancement**: User profile and traits added to prompts
- **Response Processing**: AI responses saved and managed
- **Error Handling**: Graceful handling of AI service issues

## 🔄 Integration Benefits

This integrated system combines the best of both worlds:

### From Original AI Chatbot:
- ✅ Real AI model integration
- ✅ Advanced conversation management
- ✅ Personality profiling system
- ✅ Multiple AI model support

### From Multi-User Environment:
- ✅ User authentication and management
- ✅ Individual user profiles
- ✅ Psychology trait tracking
- ✅ Modern web interface

### New Integrated Features:
- ✅ **Personalized AI Responses**: AI considers user profile and traits
- ✅ **Persistent User Sessions**: Conversations survive across logins
- ✅ **Multi-User Support**: Multiple users with isolated data
- ✅ **Enhanced Security**: JWT authentication with bcrypt passwords
- ✅ **Comprehensive Database**: All data properly structured and stored

## 🚀 Advanced Usage

### For Developers
- **Extend AI Models**: Add new AI providers in the `ai_compare` module
- **Custom Traits**: Modify psychology trait system for specific use cases
- **API Integration**: Use the REST API for external integrations
- **Database Queries**: Direct database access for analytics

### For Researchers
- **User Behavior Analysis**: Track interaction patterns
- **Psychology Research**: Analyze trait-response correlations
- **Conversation Analysis**: Study AI-human interaction patterns
- **A/B Testing**: Compare different AI personalities

## 🔮 Future Enhancements

Potential improvements:
- **Real-time Messaging**: WebSocket integration for instant responses
- **Voice Integration**: Speech-to-text and text-to-speech
- **Advanced Analytics**: User behavior and conversation insights
- **Mobile App**: Native mobile application
- **Team Conversations**: Multi-user group chats
- **AI Model Comparison**: Side-by-side model comparisons
- **Export Features**: Conversation export in various formats

## 🐛 Troubleshooting

### Common Issues
1. **Database Errors**: Delete `integrated_users.db` to reset
2. **Authentication Issues**: Clear browser localStorage
3. **AI Response Errors**: Check API keys in `.env` file
4. **Port Conflicts**: Change port in `app.py` if needed

### Debug Mode
Run with debug enabled:
```bash
python app.py
```
Debug info will be printed to console.

## 📝 License

This integrated system combines multiple components and maintains compatibility with the original AI chatbot system while adding comprehensive multi-user functionality.

---

**Ready to experience personalized AI conversations? Start at `http://localhost:5000/multi-user`!**
