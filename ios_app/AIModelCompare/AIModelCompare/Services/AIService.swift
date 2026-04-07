import Foundation
import Combine

// MARK: - AI Service Protocol
protocol AIServiceProtocol {
    func sendMessage(text: String, to modelId: String) async throws -> String
    func sendMessageWithStreaming(text: String, to modelId: String) -> AsyncThrowingStream<String, Error>
    func estimateTokens(text: String) -> Int
}

// MARK: - OpenAI Service
class OpenAIService: AIServiceProtocol {
    private let apiKey: String
    private let baseURL = "https://api.openai.com/v1"
    private let session = URLSession.shared
    
    init(apiKey: String) {
        self.apiKey = apiKey
    }
    
    func sendMessage(text: String, to modelId: String) async throws -> String {
        let request = try createChatRequest(messages: [ChatMessage(role: "user", content: text)], model: modelId, stream: false)
        
        let (data, _) = try await session.data(for: request)
        let response = try JSONDecoder().decode(ChatResponse.self, from: data)
        return response.choices.first?.message.content ?? "No response"
    }
    
    func sendMessageWithStreaming(text: String, to modelId: String) -> AsyncThrowingStream<String, Error> {
        AsyncThrowingStream { continuation in
            Task {
                do {
                    let request = try createChatRequest(messages: [ChatMessage(role: "user", content: text)], model: modelId, stream: true)
                    
                    let (result, _) = try await session.bytes(for: request)
                    var buffer = ""
                    
                    for try await line in result.lines {
                        if line.hasPrefix("data: ") && line != "data: [DONE]" {
                            let jsonString = String(line.dropFirst(6))
                            if let data = jsonString.data(using: .utf8) {
                                if let streamResponse = try? JSONDecoder().decode(StreamChatResponse.self, from: data),
                                   let delta = streamResponse.choices.first?.delta.content {
                                    continuation.yield(delta)
                                }
                            }
                        }
                    }
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }
    
    func estimateTokens(text: String) -> Int {
        // Rough estimation: ~4 characters per token
        return Int(ceil(Double(text.count) / 4.0))
    }
    
    private func createChatRequest(messages: [ChatMessage], model: String, stream: Bool) throws -> URLRequest {
        guard let url = URL(string: "\(baseURL)/chat/completions") else {
            throw AIServiceError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestBody = ChatRequest(
            model: model,
            messages: messages,
            stream: stream,
            max_tokens: 1000,
            temperature: 0.7
        )
        
        request.httpBody = try JSONEncoder().encode(requestBody)
        return request
    }
}

// MARK: - Anthropic Service
class AnthropicService: AIServiceProtocol {
    private let apiKey: String
    private let baseURL = "https://api.anthropic.com/v1"
    private let session = URLSession.shared
    
    init(apiKey: String) {
        self.apiKey = apiKey
    }
    
    func sendMessage(text: String, to modelId: String) async throws -> String {
        let request = try createMessageRequest(messages: [Message(role: "user", content: text)], model: modelId, stream: false)
        
        let (data, _) = try await session.data(for: request)
        let response = try JSONDecoder().decode(MessageResponse.self, from: data)
        return response.content.first?.text ?? "No response"
    }
    
    func sendMessageWithStreaming(text: String, to modelId: String) -> AsyncThrowingStream<String, Error> {
        AsyncThrowingStream { continuation in
            Task {
                do {
                    let request = try createMessageRequest(messages: [Message(role: "user", content: text)], model: modelId, stream: true)
                    
                    let (result, _) = try await session.bytes(for: request)
                    
                    for try await line in result.lines {
                        if line.hasPrefix("data: ") && line != "data: [DONE]" {
                            let jsonString = String(line.dropFirst(6))
                            if let data = jsonString.data(using: .utf8) {
                                if let streamResponse = try? JSONDecoder().decode(StreamMessageResponse.self, from: data),
                                   let delta = streamResponse.delta.text {
                                    continuation.yield(delta)
                                }
                            }
                        }
                    }
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }
    
    func estimateTokens(text: String) -> Int {
        // Rough estimation for Claude
        return Int(ceil(Double(text.count) / 4.0))
    }
    
    private func createMessageRequest(messages: [Message], model: String, stream: Bool) throws -> URLRequest {
        guard let url = URL(string: "\(baseURL)/messages") else {
            throw AIServiceError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue(apiKey, forHTTPHeaderField: "x-api-key")
        request.setValue("anthropic-version", forHTTPHeaderField: "2023-06-01")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestBody = MessageRequest(
            model: model,
            messages: messages,
            max_tokens: 1000,
            stream: stream
        )
        
        request.httpBody = try JSONEncoder().encode(requestBody)
        return request
    }
}

// MARK: - Google AI Service
class GoogleAIService: AIServiceProtocol {
    private let apiKey: String
    private let baseURL = "https://generativelanguage.googleapis.com/v1beta"
    private let session = URLSession.shared
    
    init(apiKey: String) {
        self.apiKey = apiKey
    }
    
    func sendMessage(text: String, to modelId: String) async throws -> String {
        let request = try createGenerateRequest(text: text, model: modelId)
        
        let (data, _) = try await session.data(for: request)
        let response = try JSONDecoder().decode(GenerateResponse.self, from: data)
        return response.candidates.first?.content.parts.first?.text ?? "No response"
    }
    
    func sendMessageWithStreaming(text: String, to modelId: String) -> AsyncThrowingStream<String, Error> {
        AsyncThrowingStream { continuation in
            Task {
                do {
                    let request = try createGenerateRequest(text: text, model: modelId, stream: true)
                    
                    let (result, _) = try await session.bytes(for: request)
                    
                    for try await line in result.lines {
                        if line.hasPrefix("data: ") && line != "data: [DONE]" {
                            let jsonString = String(line.dropFirst(6))
                            if let data = jsonString.data(using: .utf8) {
                                if let streamResponse = try? JSONDecoder().decode(StreamGenerateResponse.self, from: data),
                                   let text = streamResponse.candidates.first?.content.parts.first?.text {
                                    continuation.yield(text)
                                }
                            }
                        }
                    }
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }
    
    func estimateTokens(text: String) -> Int {
        // Rough estimation for Gemini
        return Int(ceil(Double(text.count) / 4.0))
    }
    
    private func createGenerateRequest(text: String, model: String, stream: Bool = false) throws -> URLRequest {
        guard let url = URL(string: "\(baseURL)/models/\(model):generateContent?key=\(apiKey)") else {
            throw AIServiceError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestBody = GenerateRequest(
            contents: [Content(parts: [Part(text: text)])],
            generationConfig: GenerationConfig(
                maxOutputTokens: 1000,
                temperature: 0.7
            )
        )
        
        request.httpBody = try JSONEncoder().encode(requestBody)
        return request
    }
}

// MARK: - Service Manager
class AIServiceManager: ObservableObject {
    private var services: [String: AIServiceProtocol] = [:]
    
    init() {
        setupServices()
    }
    
    private func setupServices() {
        // In a real app, these would come from secure storage
        // For demo purposes, using placeholder keys
        if let openAIKey = getAPIKey(for: "openai") {
            services["gpt-4"] = OpenAIService(apiKey: openAIKey)
            services["gpt-3.5-turbo"] = OpenAIService(apiKey: openAIKey)
        }
        
        if let anthropicKey = getAPIKey(for: "anthropic") {
            services["claude-3-opus"] = AnthropicService(apiKey: anthropicKey)
            services["claude-3-sonnet"] = AnthropicService(apiKey: anthropicKey)
        }
        
        if let googleKey = getAPIKey(for: "google") {
            services["gemini-pro"] = GoogleAIService(apiKey: googleKey)
        }
    }
    
    private func getAPIKey(for provider: String) -> String? {
        // In a real app, this would retrieve from Keychain or secure storage
        // For demo, return nil (user will need to configure)
        return nil
    }
    
    func getService(for modelId: String) -> AIServiceProtocol? {
        return services[modelId]
    }
    
    func configureAPIKey(_ key: String, for provider: String) {
        switch provider {
        case "openai":
            let service = OpenAIService(apiKey: key)
            services["gpt-4"] = service
            services["gpt-3.5-turbo"] = service
        case "anthropic":
            let service = AnthropicService(apiKey: key)
            services["claude-3-opus"] = service
            services["claude-3-sonnet"] = service
        case "google":
            let service = GoogleAIService(apiKey: key)
            services["gemini-pro"] = service
        default:
            break
        }
    }
}

// MARK: - Error Types
enum AIServiceError: LocalizedError {
    case invalidURL
    case invalidResponse
    case missingAPIKey
    case rateLimitExceeded
    case invalidRequest
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .missingAPIKey:
            return "API key is missing"
        case .rateLimitExceeded:
            return "Rate limit exceeded"
        case .invalidRequest:
            return "Invalid request"
        }
    }
}

// MARK: - API Response Models (simplified for demo)
struct ChatRequest: Codable {
    let model: String
    let messages: [ChatMessage]
    let stream: Bool
    let max_tokens: Int
    let temperature: Double
}

struct ChatMessage: Codable {
    let role: String
    let content: String
}

struct ChatResponse: Codable {
    let choices: [ChatChoice]
}

struct ChatChoice: Codable {
    let message: ChatMessage
}

struct StreamChatResponse: Codable {
    let choices: [StreamChatChoice]
}

struct StreamChatChoice: Codable {
    let delta: StreamDelta
}

struct StreamDelta: Codable {
    let content: String?
}

struct MessageRequest: Codable {
    let model: String
    let messages: [Message]
    let max_tokens: Int
    let stream: Bool
}

struct Message: Codable {
    let role: String
    let content: String
}

struct MessageResponse: Codable {
    let content: [MessageContent]
}

struct MessageContent: Codable {
    let text: String
}

struct StreamMessageResponse: Codable {
    let delta: StreamDeltaMessage
}

struct StreamDeltaMessage: Codable {
    let text: String
}

struct GenerateRequest: Codable {
    let contents: [Content]
    let generationConfig: GenerationConfig
}

struct Content: Codable {
    let parts: [Part]
}

struct Part: Codable {
    let text: String
}

struct GenerationConfig: Codable {
    let maxOutputTokens: Int
    let temperature: Double
}

struct GenerateResponse: Codable {
    let candidates: [Candidate]
}

struct Candidate: Codable {
    let content: Content
}

struct StreamGenerateResponse: Codable {
    let candidates: [StreamCandidate]
}

struct StreamCandidate: Codable {
    let content: Content
}
