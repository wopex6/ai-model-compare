import Foundation

// MARK: - AI Model
struct AIModel: Identifiable, Codable {
    let id: String
    let name: String
    let provider: String
    let description: String
    let maxTokens: Int
    let supportsStreaming: Bool
    let supportsVision: Bool
    let costPerToken: Double
    let isAvailable: Bool
    
    static let allModels: [AIModel] = [
        AIModel(
            id: "gpt-4",
            name: "GPT-4",
            provider: "OpenAI",
            description: "Most capable model, great for complex tasks",
            maxTokens: 8192,
            supportsStreaming: true,
            supportsVision: false,
            costPerToken: 0.00003,
            isAvailable: true
        ),
        AIModel(
            id: "gpt-3.5-turbo",
            name: "GPT-3.5 Turbo",
            provider: "OpenAI",
            description: "Fast and efficient for most tasks",
            maxTokens: 4096,
            supportsStreaming: true,
            supportsVision: false,
            costPerToken: 0.000002,
            isAvailable: true
        ),
        AIModel(
            id: "claude-3-opus",
            name: "Claude 3 Opus",
            provider: "Anthropic",
            description: "Highly capable with strong reasoning",
            maxTokens: 4096,
            supportsStreaming: true,
            supportsVision: true,
            costPerToken: 0.000075,
            isAvailable: true
        ),
        AIModel(
            id: "claude-3-sonnet",
            name: "Claude 3 Sonnet",
            provider: "Anthropic",
            description: "Balanced performance and speed",
            maxTokens: 4096,
            supportsStreaming: true,
            supportsVision: true,
            costPerToken: 0.000015,
            isAvailable: true
        ),
        AIModel(
            id: "gemini-pro",
            name: "Gemini Pro",
            provider: "Google",
            description: "Google's advanced AI model",
            maxTokens: 32768,
            supportsStreaming: true,
            supportsVision: true,
            costPerToken: 0.0000005,
            isAvailable: true
        )
    ]
}

// MARK: - Message
struct Message: Identifiable, Codable {
    let id: UUID
    let content: String
    let timestamp: Date
    let isUser: Bool
    let modelId: String?
    let metadata: [String: Any]?
    
    init(id: UUID = UUID(), content: String, timestamp: Date = Date(), isUser: Bool, modelId: String? = nil, metadata: [String: Any]? = nil) {
        self.id = id
        self.content = content
        self.timestamp = timestamp
        self.isUser = isUser
        self.modelId = modelId
        self.metadata = metadata
    }
    
    enum CodingKeys: String, CodingKey {
        case id, content, timestamp, isUser, modelId, metadata
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(UUID.self, forKey: .id)
        content = try container.decode(String.self, forKey: .content)
        timestamp = try container.decode(Date.self, forKey: .timestamp)
        isUser = try container.decode(Bool.self, forKey: .isUser)
        modelId = try container.decodeIfPresent(String.self, forKey: .modelId)
        metadata = try container.decodeIfPresent([String: Any].self, forKey: .metadata)
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(content, forKey: .content)
        try container.encode(timestamp, forKey: .timestamp)
        try container.encode(isUser, forKey: .isUser)
        try container.encodeIfPresent(modelId, forKey: .modelId)
        try container.encodeIfPresent(metadata, forKey: .metadata)
    }
}

// MARK: - Chat Session
struct ChatSession: Identifiable, Codable {
    let id: UUID
    let title: String
    let createdAt: Date
    let updatedAt: Date
    let messages: [Message]
    let selectedModels: [String]
    
    init(id: UUID = UUID(), title: String, createdAt: Date = Date(), updatedAt: Date = Date(), messages: [Message] = [], selectedModels: [String] = []) {
        self.id = id
        self.title = title
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.messages = messages
        self.selectedModels = selectedModels
    }
}

// MARK: - Comparison Result
struct ComparisonResult: Identifiable, Codable {
    let id: UUID
    let prompt: String
    let timestamp: Date
    let responses: [ModelResponse]
    let winner: String?
    
    struct ModelResponse: Identifiable, Codable {
        let id: UUID
        let modelId: String
        let response: String
        let responseTime: TimeInterval
        let tokenCount: Int?
        let rating: Int?
    }
    
    init(id: UUID = UUID(), prompt: String, timestamp: Date = Date(), responses: [ModelResponse] = [], winner: String? = nil) {
        self.id = id
        self.prompt = prompt
        self.timestamp = timestamp
        self.responses = responses
        self.winner = winner
    }
}

// MARK: - User Settings
struct UserSettings: Codable {
    var selectedTheme: AppTheme
    var voiceInputEnabled: Bool
    var voiceOutputEnabled: Bool
    var autoSaveChats: Bool
    var maxTokenUsage: Int
    var preferredModel: String?
    
    static let `default` = UserSettings(
        selectedTheme: .system,
        voiceInputEnabled: true,
        voiceOutputEnabled: false,
        autoSaveChats: true,
        maxTokenUsage: 100000,
        preferredModel: nil
    )
}

enum AppTheme: String, CaseIterable, Codable {
    case light = "light"
    case dark = "dark"
    case system = "system"
    
    var displayName: String {
        switch self {
        case .light: return "Light"
        case .dark: return "Dark"
        case .system: return "System"
        }
    }
}
