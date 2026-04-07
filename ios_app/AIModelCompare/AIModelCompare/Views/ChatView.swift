import SwiftUI

struct ChatView: View {
    @ObservedObject var viewModel: ChatViewModel
    @State private var showingModelSelector = false
    @State private var showingNewChatSheet = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Header
                headerView
                
                // Messages
                messagesView
                
                // Streaming indicator
                if !viewModel.streamingText.isEmpty {
                    streamingView
                }
                
                // Input area
                inputView
            }
            .navigationTitle("AI Chat")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button(action: createNewChat) {
                        Image(systemName: "square.and.pencil")
                            .font(.title2)
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        if viewModel.personalizationService.currentUserCharacter == nil {
                            Button(action: { viewModel.startCharacterAnalysis() }) {
                                Label("Character Analysis", systemImage: "brain.head.profile")
                            }
                        }
                        
                        Button(action: { showingModelSelector = true }) {
                            Label("Select Models", systemImage: "checkmark.circle")
                        }
                        
                        Button(action: { viewModel.createNewChat() }) {
                            Label("New Chat", systemImage: "message")
                        }
                        
                        Button(action: { clearChat() }) {
                            Label("Clear Chat", systemImage: "trash")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                            .font(.title2)
                    }
                }
            }
            .sheet(isPresented: $showingModelSelector) {
                ModelSelectionView(viewModel: viewModel)
            }
            .sheet(isPresented: $showingNewChatSheet) {
                NewChatSheet(viewModel: viewModel)
            }
            .sheet(isPresented: $viewModel.showCharacterAnalysis) {
                UserCharacterAnalysisView()
            }
            .sheet(isPresented: $viewModel.showFeedbackCollection) {
                if let response = viewModel.currentFeedbackResponse {
                    FeedbackCollectionView(response: response) { feedback in
                        viewModel.submitFeedback(feedback)
                    }
                }
            }
            .alert("Error", isPresented: .constant(viewModel.errorMessage != nil)) {
                Button("OK") {
                    viewModel.errorMessage = nil
                }
            } message: {
                if let error = viewModel.errorMessage {
                    Text(error)
                }
            }
        }
    }
    
    // MARK: - Header View
    private var headerView: some View {
        VStack(spacing: 8) {
            if let session = viewModel.currentSession {
                Text(session.title)
                    .font(.headline)
                    .foregroundColor(.primary)
            }
            
            if !viewModel.selectedModels.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(viewModel.getSelectedModels()) { model in
                            HStack(spacing: 4) {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.green)
                                    .font(.caption)
                                Text(model.name)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color(.systemGray6))
                            .cornerRadius(12)
                        }
                    }
                    .padding(.horizontal)
                }
            }
        }
        .padding(.vertical, 8)
        .background(Color(.systemBackground))
        .overlay(
            Rectangle()
                .frame(height: 0.5)
                .foregroundColor(Color(.separator)),
            alignment: .bottom
        )
    }
    
    // MARK: - Messages View
    private var messagesView: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 16) {
                    ForEach(viewModel.messages) { message in
                        MessageView(message: message)
                            .id(message.id)
                    }
                    
                    if viewModel.isLoading {
                        LoadingIndicator()
                            .id("loading")
                    }
                }
                .padding()
            }
            .onChange(of: viewModel.messages.count) { _ in
                withAnimation {
                    proxy.scrollTo(viewModel.messages.last?.id, anchor: .bottom)
                }
            }
            .onChange(of: viewModel.isLoading) { isLoading in
                if isLoading {
                    withAnimation {
                        proxy.scrollTo("loading", anchor: .bottom)
                    }
                }
            }
        }
    }
    
    // MARK: - Streaming View
    private var streamingView: some View {
        HStack(alignment: .top, spacing: 12) {
            Rectangle()
                .fill(Color.blue)
                .frame(width: 32, height: 32)
                .cornerRadius(16)
            
            VStack(alignment: .leading, spacing: 4) {
                Text("AI Response")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text(viewModel.streamingText)
                    .font(.body)
                    .foregroundColor(.primary)
                
                HStack(spacing: 4) {
                    ForEach(0..<3) { index in
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 6, height: 6)
                            .scaleEffect(viewModel.isLoading ? 1 : 0.5)
                            .animation(
                                Animation.easeInOut(duration: 0.6)
                                    .repeatForever()
                                    .delay(Double(index) * 0.2),
                                value: viewModel.isLoading
                            )
                    }
                }
            }
            
            Spacer()
        }
        .padding()
    }
    
    // MARK: - Input View
    private var inputView: some View {
        VStack(spacing: 0) {
            Rectangle()
                .frame(height: 0.5)
                .foregroundColor(Color(.separator))
            
            HStack(alignment: .bottom, spacing: 12) {
                // Voice input button
                Button(action: {
                    if viewModel.isRecording {
                        viewModel.stopRecording()
                    } else {
                        viewModel.startRecording()
                    }
                }) {
                    Image(systemName: viewModel.isRecording ? "mic.fill" : "mic")
                        .font(.title2)
                        .foregroundColor(viewModel.isRecording ? .red : .blue)
                }
                .disabled(viewModel.isLoading)
                
                // Text input
                ZStack(alignment: .topLeading) {
                    TextEditor(text: $viewModel.inputText)
                        .font(.body)
                        .padding(8)
                        .background(Color(.systemGray6))
                        .cornerRadius(20)
                        .frame(minHeight: 36, maxHeight: 120)
                    
                    if viewModel.inputText.isEmpty {
                        Text("Type a message...")
                            .font(.body)
                            .foregroundColor(.secondary)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .allowsHitTesting(false)
                    }
                }
                
                // Send button
                Button(action: viewModel.sendMessage) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title2)
                        .foregroundColor(
                            viewModel.inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !viewModel.isLoading
                            ? Color(.systemGray3)
                            : Color.blue
                        )
                }
                .disabled(
                    viewModel.inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                    || viewModel.isLoading
                )
            }
            .padding()
        }
        .background(Color(.systemBackground))
    }
struct MessageView: View {
    let message: Message
    let viewModel: ChatViewModel
    @State private var showFeedback = false
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            if message.isUser {
                userAvatar
                Spacer()
                VStack(alignment: .trailing, spacing: 4) {
                    messageBubble
                    if !message.isUser && viewModel.personalizationService.currentUserCharacter != nil {
                        feedbackButton
                    }
                }
            } else {
                Spacer()
                VStack(alignment: .leading, spacing: 4) {
                    aiAvatar
                    messageBubble
                    if !message.isUser && viewModel.personalizationService.currentUserCharacter != nil {
                        feedbackButton
                    }
                }
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 4)
    }
    
    private var userMessageView: some View {
        HStack {
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text("You")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text(message.content)
                    .font(.body)
                    .foregroundColor(.white)
                    .padding(12)
                    .background(Color.blue)
                    .cornerRadius(16)
                
                Text(message.timestamp, style: .time)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            Circle()
                .fill(Color.blue)
                .frame(width: 32, height: 32)
                .overlay(
                    Text("You")
                        .font(.caption)
                        .foregroundColor(.white)
                )
        }
    }
    
    private var aiMessageView: some View {
        HStack {
            Circle()
                .fill(Color(.systemGray5))
                .frame(width: 32, height: 32)
                .overlay(
                    Image(systemName: "brain.head.profile")
                        .font(.caption)
                        .foregroundColor(.secondary)
                )
            
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    if let modelId = message.modelId,
                       let model = AIModel.allModels.first(where: { $0.id == modelId }) {
                        Text(model.name)
                            .font(.caption)
                            .fontWeight(.medium)
                            .foregroundColor(.primary)
                    } else {
                        Text("AI")
                            .font(.caption)
                            .fontWeight(.medium)
                            .foregroundColor(.primary)
                    }
                    
                    if let responseTime = message.metadata?["responseTime"] as? TimeInterval {
                        Text("•")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text("\(String(format: "%.1f", responseTime))s")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Text(message.content)
                    .font(.body)
                    .foregroundColor(.primary)
                    .padding(12)
                    .background(Color(.systemGray6))
                    .cornerRadius(16)
                
                Text(message.timestamp, style: .time)
                    .font(.caption2)
                    .foregroundColor(.secondary)
                
                // Feedback button for personalized responses
                if !message.isUser && viewModel.personalizationService.currentUserCharacter != nil {
                    Button(action: {
                        // Create a mock personalized response for feedback
                        let mockResponse = PersonalizedResponse(
                            id: UUID(),
                            content: message.content,
                            need: .balanced,
                            format: .conversational,
                            personalizationLevel: 0.8,
                            timestamp: message.timestamp,
                            modelId: message.modelId ?? ""
                        )
                        viewModel.showFeedbackForResponse(mockResponse)
                    }) {
                        HStack(spacing: 4) {
                            Image(systemName: "hand.thumbsup")
                                .font(.caption)
                            Text("Feedback")
                                .font(.caption2)
                        }
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color(.systemGray6))
                        .cornerRadius(12)
                    }
                    .foregroundColor(.secondary)
                }
            }
            
            Spacer()
        }
    }
}

// MARK: - Loading Indicator
struct LoadingIndicator: View {
    var body: some View {
        HStack(spacing: 8) {
            ForEach(0..<3) { index in
                Circle()
                    .fill(Color.blue)
                    .frame(width: 8, height: 8)
                    .scaleEffect(1)
                    .animation(
                        Animation.easeInOut(duration: 0.6)
                            .repeatForever()
                            .delay(Double(index) * 0.2),
                        value: true
                    )
            }
        }
        .padding()
    }
}

// MARK: - Model Selection View
struct ModelSelectionView: View {
    @ObservedObject var viewModel: ChatViewModel
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            List {
                ForEach(AIModel.allModels) { model in
                    ModelRow(
                        model: model,
                        isSelected: viewModel.selectedModels.contains(model.id)
                    ) {
                        viewModel.toggleModel(model.id)
                    }
                }
            }
            .navigationTitle("Select Models")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

// MARK: - Model Row
struct ModelRow: View {
    let model: AIModel
    let isSelected: Bool
    let onTap: () -> Void
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(model.name)
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Text(model.description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                HStack {
                    if model.supportsStreaming {
                        Label("Streaming", systemImage: "waveform")
                            .font(.caption2)
                            .foregroundColor(.blue)
                    }
                    
                    if model.supportsVision {
                        Label("Vision", systemImage: "eye")
                            .font(.caption2)
                            .foregroundColor(.green)
                    }
                    
                    Spacer()
                    
                    Text("$\(String(format: "%.6f", model.costPerToken))/token")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
            
            Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                .foregroundColor(isSelected ? .blue : .gray)
                .font(.title2)
        }
        .contentShape(Rectangle())
        .onTapGesture {
            onTap()
        }
    }
}

// MARK: - New Chat Sheet
struct NewChatSheet: View {
    @ObservedObject var viewModel: ChatViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var chatTitle = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Chat Details")) {
                    TextField("Chat Title", text: $chatTitle)
                }
                
                Section(header: Text("Selected Models")) {
                    ForEach(viewModel.getSelectedModels()) { model in
                        Text(model.name)
                    }
                }
            }
            .navigationTitle("New Chat")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Create") {
                        let title = chatTitle.isEmpty ? "Chat \(Date())" : chatTitle
                        viewModel.createNewSession(title: title)
                        dismiss()
                    }
                    .disabled(chatTitle.isEmpty && viewModel.getSelectedModels().isEmpty)
                }
            }
        }
    }
}
