import Foundation
import Combine
import AVFoundation

@MainActor
class ChatViewModel: ObservableObject {
    @Published var messages: [Message] = []
    @Published var currentSession: ChatSession?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var selectedModels: [String] = []
    @Published var isRecording = false
    @Published var streamingText: String = ""
    @Published var isStreaming = false
    @Published var showCharacterAnalysis = false
    @Published var showFeedbackCollection = false
    @Published var currentFeedbackResponse: PersonalizedResponse?
    
    private let dataStore = DataStore.shared
    private let aiServiceManager = AIServiceManager()
    private let speechRecognizer = SpeechRecognizer()
    private let personalizationService = AdvancedAIResponseSystem()
    private var currentStreamingTask: Task<Void, Never>?
    private var cancellables = Set<AnyCancellable>()
    private var audioEngine: AVAudioEngine?
    private var speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    
    init() {
        setupSpeechRecognition()
        loadCurrentSession()
    }
    
    // MARK: - Session Management
    func loadCurrentSession() {
        currentSession = dataStore.fetchChatSessions().first
        messages = currentSession?.messages ?? []
        selectedModels = Set(currentSession?.selectedModels ?? [])
    }
    
    func createNewSession(title: String = "New Chat") {
        let session = ChatSession(title: title, selectedModels: Array(selectedModels))
        currentSession = session
        messages = []
        dataStore.saveChatSession(session)
    }
    
    func saveCurrentSession() {
        guard var session = currentSession else { return }
        session = ChatSession(
            id: session.id,
            title: session.title,
            createdAt: session.createdAt,
            updatedAt: Date(),
            messages: messages,
            selectedModels: Array(selectedModels)
        )
        dataStore.saveChatSession(session)
        currentSession = session
    }
    
    // MARK: - Message Handling
    func sendMessage(_ message: String) async {
        guard !message.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        // Add user message
        let userMessage = Message(
            content: message,
            isUser: true,
            timestamp: Date(),
            modelId: nil
        )
        messages.append(userMessage)
        
        // Save to current session
        if let session = currentSession {
            dataStore.addMessageToSession(userMessage, sessionId: session.id)
        }
        
        isLoading = true
        errorMessage = nil
        
                self.saveCurrentSession()
            }
        }
    }
    
    private func sendToModel(_ text: String, modelId: String) async -> (String, String, TimeInterval) {
        guard let service = aiServiceManager.getService(for: modelId) else {
            return (modelId, "Model not available", 0)
        }
        
        let startTime = Date()
        do {
            let response = try await service.sendMessage(text: text, to: modelId)
            let responseTime = Date().timeIntervalSince(startTime)
            return (modelId, response, responseTime)
        } catch {
            let responseTime = Date().timeIntervalSince(startTime)
            return (modelId, "Error: \(error.localizedDescription)", responseTime)
        }
    }
    
    private func handleModelResponses(_ results: [(modelId: String, response: String, responseTime: TimeInterval)]) {
        for result in results {
            let model = AIModel.allModels.first { $0.id == result.modelId }
            let modelResponse = Message(
                content: result.response,
                isUser: false,
                modelId: result.modelId,
                metadata: [
                    "responseTime": result.responseTime,
                    "modelName": model?.name ?? result.modelId
                ]
            )
            messages.append(modelResponse)
        }
    }
    
    // MARK: - Voice Input
    private func setupSpeechRecognition() {
        speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
        speechRecognizer?.delegate = self
        
        AVAudioSession.sharedInstance.requestRecordPermission { granted in
            if granted {
                print("Microphone permission granted")
            } else {
                print("Microphone permission denied")
            }
        }
    }
    
    func startRecording() {
        guard let recognizer = speechRecognizer, recognizer.isAvailable else {
            errorMessage = "Speech recognition not available"
            return
        }
        
        try? AVAudioSession.sharedInstance.setCategory(.record)
        try? AVAudioSession.sharedInstance.setActive(true, options: .notifyOthersOnDeactivation)
        
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else { return }
        
        recognitionRequest.shouldReportPartialResults = true
        
        audioEngine = AVAudioEngine()
        let inputNode = audioEngine?.inputNode
        
        let recordingFormat = inputNode?.outputFormat(forBus: 0)
        
        inputNode?.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            recognitionRequest.append(buffer)
        }
        
        audioEngine?.prepare()
        do {
            try audioEngine?.start()
            isRecording = true
            
            recognitionTask = recognizer.recognitionTask(with: recognitionRequest) { result, error in
                if let result = result {
                    DispatchQueue.main.async {
                        self.inputText = result.bestTranscription.formattedString
                    }
                }
                
                if error != nil || result?.isFinal == true {
                    self.stopRecording()
                }
            }
        } catch {
            print("Error starting audio engine: \(error)")
            stopRecording()
        }
    }
    
    func stopRecording() {
        audioEngine?.stop()
        audioEngine?.inputNode.removeTap(onBus: 0)
        
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        recognitionTask?.cancel()
        recognitionTask = nil
        
        try? AVAudioSession.sharedInstance.setActive(false)
        
        isRecording = false
    }
    
    // MARK: - Model Selection
    func toggleModel(_ modelId: String) {
        if selectedModels.contains(modelId) {
            selectedModels.remove(modelId)
        } else {
            selectedModels.insert(modelId)
        }
        saveCurrentSession()
    }
    
    func getSelectedModels() -> [AIModel] {
        return AIModel.allModels.filter { selectedModels.contains($0.id) }
    }
    
    // MARK: - Streaming Support
    func startStreamingResponse(text: String, modelId: String) {
        guard let service = aiServiceManager.getService(for: modelId) else { return }
        
        Task {
            do {
                streamingText = ""
                let stream = service.sendMessageWithStreaming(text: text, to: modelId)
                
                for try await chunk in stream {
                    await MainActor.run {
                        streamingText += chunk
                    }
                }
                
                await MainActor.run {
                    let message = Message(content: streamingText, isUser: false, modelId: modelId)
                    messages.append(message)
                    streamingText = ""
                    saveCurrentSession()
                }
            } catch {
                await MainActor.run {
                    errorMessage = "Streaming error: \(error.localizedDescription)"
                }
            }
        }
    }
}

// MARK: - Speech Recognition Delegate
extension ChatViewModel: SFSpeechRecognizerDelegate {
    func speechRecognizer(_ speechRecognizer: SFSpeechRecognizer, availabilityDidChange available: Bool) {
        if !available {
            stopRecording()
        }
    }
}
