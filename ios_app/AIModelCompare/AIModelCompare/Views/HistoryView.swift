import SwiftUI

struct HistoryView: View {
    @State private var selectedTab = 0
    @State private var chatSessions: [ChatSession] = []
    @State private var comparisonResults: [ComparisonResult] = []
    @State private var searchText = ""
    @State private var showingDeleteAlert = false
    @State private var itemToDelete: Any?
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Search bar
                searchBar
                
                // Tab selector
                tabSelector
                
                // Content
                TabView(selection: $selectedTab) {
                    List {
                        ForEach(filteredChatSessions) { session in
                            NavigationLink(destination: ChatHistoryCard(session: session, onDelete: { itemToDelete = session; showingDeleteAlert = true })) {
                                VStack(alignment: .leading) {
                                    Text(session.title)
                                        .font(.headline)
                                    Text(session.messages.first?.content ?? "")
                                        .foregroundColor(.secondary)
                                }
                            }
                        }
                    }
                    .tag(0)
                    
                    List {
                        ForEach(filteredComparisonResults) { result in
                            NavigationLink(destination: ComparisonHistoryCard(result: result, onDelete: { itemToDelete = result; showingDeleteAlert = true })) {
                                VStack(alignment: .leading) {
                                    Text(result.prompt)
                                        .font(.headline)
                                    Text(result.responses.first?.response ?? "")
                                        .foregroundColor(.secondary)
                                }
                            }
                        }
                    }
                    .tag(1)
                }
                .tabViewStyle(PageTabViewStyle(indexDisplayMode: .never))
            }
            .navigationTitle("History")
            .navigationBarTitleDisplayMode(.large)
            .onAppear {
                loadData()
            }
            .alert("Delete Item", isPresented: $showingDeleteAlert) {
                Button("Delete", role: .destructive) {
                    deleteItem()
                }
                Button("Cancel", role: .cancel) { }
            } message: {
                Text("Are you sure you want to delete this item? This action cannot be undone.")
            }
        }
    }
    
    // MARK: - Search Bar
    private var searchBar: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.secondary)
            
            TextField("Search history...", text: $searchText)
                .textFieldStyle(RoundedBorderTextFieldStyle())
            
            if !searchText.isEmpty {
                Button(action: { searchText = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
    }
    
    // MARK: - Tab Selector
    private var tabSelector: some View {
        HStack(spacing: 0) {
            Button(action: { selectedTab = 0 }) {
                VStack(spacing: 4) {
                    Text("Chats")
                        .font(selectedTab == 0 ? .headline : .subheadline)
                        .fontWeight(selectedTab == 0 ? .semibold : .regular)
                        .foregroundColor(selectedTab == 0 ? .blue : .secondary)
                    
                    Rectangle()
                        .fill(selectedTab == 0 ? Color.blue : Color.clear)
                        .frame(height: 2)
                }
            }
            .frame(maxWidth: .infinity)
            
            Button(action: { selectedTab = 1 }) {
                VStack(spacing: 4) {
                    Text("Comparisons")
                        .font(selectedTab == 1 ? .headline : .subheadline)
                        .fontWeight(selectedTab == 1 ? .semibold : .regular)
                        .foregroundColor(selectedTab == 1 ? .blue : .secondary)
                    
                    Rectangle()
                        .fill(selectedTab == 1 ? Color.blue : Color.clear)
                        .frame(height: 2)
                }
            }
            .frame(maxWidth: .infinity)
        }
        .padding(.horizontal)
        .background(Color(.systemBackground))
        .overlay(
            Rectangle()
                .frame(height: 0.5)
                .foregroundColor(Color(.separator)),
            alignment: .bottom
        )
    }
    
    // MARK: - Data Management
    private var filteredChatSessions: [ChatSession] {
        if searchText.isEmpty {
            return chatSessions
        } else {
            return chatSessions.filter { session in
                session.title.localizedCaseInsensitiveContains(searchText) ||
                session.messages.contains { message in
                    message.content.localizedCaseInsensitiveContains(searchText)
                }
            }
        }
    }
    
    private var filteredComparisonResults: [ComparisonResult] {
        if searchText.isEmpty {
            return comparisonResults
        } else {
            return comparisonResults.filter { result in
                result.prompt.localizedCaseInsensitiveContains(searchText) ||
                result.responses.contains { response in
                    response.response.localizedCaseInsensitiveContains(searchText)
                }
            }
        }
    }
    
    private func loadData() {
        chatSessions = DataStore.shared.fetchChatSessions()
        comparisonResults = DataStore.shared.fetchComparisonResults()
    }
    
    private func deleteItem() {
        if let session = itemToDelete as? ChatSession {
            DataStore.shared.deleteChatSession(session.id)
            chatSessions.removeAll { $0.id == session.id }
        } else if let result = itemToDelete as? ComparisonResult {
            comparisonResults.removeAll { $0.id == result.id }
            // Would need to implement delete in DataStore
        }
        itemToDelete = nil
    }
}

// MARK: - Chat History View
struct ChatHistoryView: View {
    let sessions: [ChatSession]
    let onDelete: (ChatSession) -> Void
    
    var body: some View {
        ScrollView {
            LazyVStack(spacing: 16) {
                if sessions.isEmpty {
                    EmptyHistoryView(type: .chat)
                } else {
                    ForEach(sessions) { session in
                        ChatHistoryCard(session: session, onDelete: onDelete)
                    }
                }
            }
            .padding()
        }
    }
}

// MARK: - Comparison History View
struct ComparisonHistoryView: View {
    let results: [ComparisonResult]
    let onDelete: (ComparisonResult) -> Void
    
    var body: some View {
        ScrollView {
            LazyVStack(spacing: 16) {
                if results.isEmpty {
                    EmptyHistoryView(type: .comparison)
                } else {
                    ForEach(results) { result in
                        ComparisonHistoryCard(result: result, onDelete: onDelete)
                    }
                }
            }
            .padding()
        }
    }
}

// MARK: - Empty History View
struct EmptyHistoryView: View {
    let type: HistoryType
    
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: type.systemImage)
                .font(.system(size: 48))
                .foregroundColor(.secondary)
            
            Text(type.emptyTitle)
                .font(.headline)
                .foregroundColor(.primary)
            
            Text(type.emptyMessage)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .padding(.vertical, 40)
    }
}

enum HistoryType {
    case chat
    case comparison
    
    var systemImage: String {
        switch self {
        case .chat:
            return "message.circle"
        case .comparison:
            return "chart.bar.doc.horizontal"
        }
    }
    
    var emptyTitle: String {
        switch self {
        case .chat:
            return "No Chat History"
        case .comparison:
            return "No Comparison History"
        }
    }
    
    var emptyMessage: String {
        switch self {
        case .chat:
            return "Your chat conversations will appear here. Start a new chat to see it in your history."
        case .comparison:
            return "Your model comparisons will appear here. Run a comparison to see it in your history."
        }
    }
}

// MARK: - Chat History Card
struct ChatHistoryCard: View {
    let session: ChatSession
    let onDelete: (ChatSession) -> Void
    @State private var showingDetail = false
    
    var body: some View {
        VStack(spacing: 12) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(session.title)
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    HStack(spacing: 8) {
                        Text(session.updatedAt, style: .date)
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Text("•")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Text("\(session.messages.count) messages")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                Menu {
                    Button(action: { showingDetail = true }) {
                        Label("View Details", systemImage: "doc.text")
                    }
                    
                    Button(action: { onDelete(session) }) {
                        Label("Delete", systemImage: "trash")
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .foregroundColor(.secondary)
                }
            }
            
            // Last message preview
            if let lastMessage = session.messages.last {
                HStack(alignment: .top, spacing: 8) {
                    Circle()
                        .fill(lastMessage.isUser ? Color.blue : Color(.systemGray5))
                        .frame(width: 24, height: 24)
                        .overlay(
                            Image(systemName: lastMessage.isUser ? "person.fill" : "brain.head.profile")
                                .font(.caption2)
                                .foregroundColor(.white)
                        )
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text(lastMessage.content)
                            .font(.body)
                            .foregroundColor(.primary)
                            .lineLimit(2)
                        
                        Text(lastMessage.timestamp, style: .time)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                }
            }
            
            // Selected models
            if !session.selectedModels.isEmpty {
                HStack {
                    Text("Models:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 4) {
                            ForEach(session.selectedModels, id: \.self) { modelId in
                                if let model = AIModel.allModels.first(where: { $0.id == modelId }) {
                                    Text(model.name)
                                        .font(.caption)
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 2)
                                        .background(Color(.systemGray6))
                                        .cornerRadius(4)
                                }
                            }
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
        .sheet(isPresented: $showingDetail) {
            ChatSessionDetailView(session: session)
        }
    }
}

// MARK: - Comparison History Card
struct ComparisonHistoryCard: View {
    let result: ComparisonResult
    let onDelete: (ComparisonResult) -> Void
    @State private var showingDetail = false
    
    var body: some View {
        VStack(spacing: 12) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Model Comparison")
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    Text(result.timestamp, style: .date)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                if let winner = result.winner,
                   let model = AIModel.allModels.first(where: { $0.id == winner }) {
                    Label("\(model.name) Won", systemImage: "trophy.fill")
                        .font(.caption)
                        .foregroundColor(.yellow)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color(.systemGray6))
                        .cornerRadius(8)
                }
                
                Menu {
                    Button(action: { showingDetail = true }) {
                        Label("View Details", systemImage: "doc.text")
                    }
                    
                    Button(action: { onDelete(result) }) {
                        Label("Delete", systemImage: "trash")
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .foregroundColor(.secondary)
                }
            }
            
            // Prompt preview
            VStack(alignment: .leading, spacing: 4) {
                Text("Prompt")
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.secondary)
                
                Text(result.prompt)
                    .font(.body)
                    .foregroundColor(.primary)
                    .lineLimit(2)
            }
            
            // Response summary
            HStack {
                Text("\(result.responses.count) responses")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                if let avgTime = result.responses.map({ $0.responseTime }).reduce(0, +) / Double(result.responses.count) {
                    Text("Avg: \(String(format: "%.2f", avgTime))s")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
        .sheet(isPresented: $showingDetail) {
            ComparisonDetailView(
                result: result,
                onRate: { _, _ in },
                onSelectWinner: { _ in }
            )
        }
    }
}

// MARK: - Chat Session Detail View
struct ChatSessionDetailView: View {
    let session: ChatSession
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 16) {
                    // Session info
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Session Info")
                            .font(.headline)
                            .foregroundColor(.primary)
                        
                        HStack {
                            Text("Created:")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text(session.createdAt, style: .date)
                                .font(.caption)
                                .foregroundColor(.primary)
                        }
                        
                        HStack {
                            Text("Updated:")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text(session.updatedAt, style: .date)
                                .font(.caption)
                                .foregroundColor(.primary)
                        }
                        
                        HStack {
                            Text("Messages:")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text("\(session.messages.count)")
                                .font(.caption)
                                .foregroundColor(.primary)
                        }
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                    
                    // Messages
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Messages")
                            .font(.headline)
                            .foregroundColor(.primary)
                        
                        ForEach(session.messages) { message in
                            MessagePreviewView(message: message)
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("Chat Details")
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

// MARK: - Message Preview View
struct MessagePreviewView: View {
    let message: Message
    
    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Circle()
                .fill(message.isUser ? Color.blue : Color(.systemGray5))
                .frame(width: 24, height: 24)
                .overlay(
                    Image(systemName: message.isUser ? "person.fill" : "brain.head.profile")
                        .font(.caption2)
                        .foregroundColor(.white)
                )
            
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(message.isUser ? "You" : "AI")
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                    
                    if let modelId = message.modelId,
                       let model = AIModel.allModels.first(where: { $0.id == modelId }) {
                        Text("•")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text(model.name)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    Text(message.timestamp, style: .time)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
                
                Text(message.content)
                    .font(.body)
                    .foregroundColor(.primary)
            }
        }
        .padding(.vertical, 4)
    }
}
