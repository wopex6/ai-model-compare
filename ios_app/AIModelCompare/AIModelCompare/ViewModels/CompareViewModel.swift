import Foundation
import Combine

@MainActor
class CompareViewModel: ObservableObject {
    @Published var prompt: String = ""
    @Published var selectedModels: Set<String> = []
    @Published var isRunning = false
    @Published var results: [ComparisonResult] = []
    @Published var errorMessage: String?
    @Published var showingResultDetail = false
    @Published var selectedResult: ComparisonResult?
    
    private let aiServiceManager = AIServiceManager()
    private let dataStore = DataStore.shared
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        loadResults()
    }
    
    // MARK: - Comparison Logic
    func runComparison() {
        guard !prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            errorMessage = "Please enter a prompt to compare"
            return
        }
        
        guard !selectedModels.isEmpty else {
            errorMessage = "Please select at least one model to compare"
            return
        }
        
        isRunning = true
        errorMessage = nil
        
        Task {
            await performComparison()
        }
    }
    
    private func performComparison() async {
        let startTime = Date()
        var responses: [ComparisonResult.ModelResponse] = []
        
        await withTaskGroup(of: ComparisonResult.ModelResponse?.self) { group in
            for modelId in selectedModels {
                group.addTask {
                    await self.getResponseFromModel(modelId: modelId, prompt: self.prompt)
                }
            }
            
            for await response in group {
                if let response = response {
                    responses.append(response)
                }
            }
        }
        
        let result = ComparisonResult(
            prompt: prompt,
            responses: responses.sorted { $0.responseTime < $1.responseTime }
        )
        
        await MainActor.run {
            self.results.insert(result, at: 0)
            self.isRunning = false
            self.dataStore.saveComparisonResult(result)
        }
    }
    
    private func getResponseFromModel(modelId: String, prompt: String) async -> ComparisonResult.ModelResponse? {
        guard let service = aiServiceManager.getService(for: modelId) else {
            return nil
        }
        
        let startTime = Date()
        do {
            let response = try await service.sendMessage(text: prompt, to: modelId)
            let responseTime = Date().timeIntervalSince(startTime)
            let tokenCount = service.estimateTokens(text: response)
            
            return ComparisonResult.ModelResponse(
                id: UUID(),
                modelId: modelId,
                response: response,
                responseTime: responseTime,
                tokenCount: tokenCount,
                rating: nil
            )
        } catch {
            let responseTime = Date().timeIntervalSince(startTime)
            return ComparisonResult.ModelResponse(
                id: UUID(),
                modelId: modelId,
                response: "Error: \(error.localizedDescription)",
                responseTime: responseTime,
                tokenCount: nil,
                rating: nil
            )
        }
    }
    
    // MARK: - Result Management
    func loadResults() {
        results = dataStore.fetchComparisonResults()
    }
    
    func deleteResult(_ result: ComparisonResult) {
        results.removeAll { $0.id == result.id }
        // Also delete from Core Data
        // Implementation would depend on Core Data setup
    }
    
    func rateResponse(_ result: ComparisonResult, modelId: String, rating: Int) {
        if let index = results.firstIndex(where: { $0.id == result.id }),
           let responseIndex = results[index].responses.firstIndex(where: { $0.modelId == modelId }) {
            results[index].responses[responseIndex] = ComparisonResult.ModelResponse(
                id: results[index].responses[responseIndex].id,
                modelId: modelId,
                response: results[index].responses[responseIndex].response,
                responseTime: results[index].responses[responseIndex].responseTime,
                tokenCount: results[index].responses[responseIndex].tokenCount,
                rating: rating
            )
            dataStore.saveComparisonResult(results[index])
        }
    }
    
    func selectWinner(_ result: ComparisonResult, modelId: String) {
        if let index = results.firstIndex(where: { $0.id == result.id }) {
            results[index] = ComparisonResult(
                id: result.id,
                prompt: result.prompt,
                timestamp: result.timestamp,
                responses: result.responses,
                winner: modelId
            )
            dataStore.saveComparisonResult(results[index])
        }
    }
    
    // MARK: - Model Selection
    func toggleModel(_ modelId: String) {
        if selectedModels.contains(modelId) {
            selectedModels.remove(modelId)
        } else {
            selectedModels.insert(modelId)
        }
    }
    
    func getSelectedModels() -> [AIModel] {
        return AIModel.allModels.filter { selectedModels.contains($0.id) }
    }
    
    // MARK: - Analytics
    func getAverageResponseTime(for modelId: String) -> TimeInterval? {
        let allResponses = results.flatMap { $0.responses }.filter { $0.modelId == modelId }
        guard !allResponses.isEmpty else { return nil }
        return allResponses.reduce(0) { $0 + $1.responseTime } / Double(allResponses.count)
    }
    
    func getAverageRating(for modelId: String) -> Double? {
        let ratedResponses = results.flatMap { $0.responses }.filter { $0.modelId == modelId && $0.rating != nil }
        guard !ratedResponses.isEmpty else { return nil }
        return ratedResponses.reduce(0) { $0 + Double($1.rating!) } / Double(ratedResponses.count)
    }
    
    func getWinRate(for modelId: String) -> Double? {
        let totalComparisons = results.count
        let wins = results.filter { $0.winner == modelId }.count
        guard totalComparisons > 0 else { return nil }
        return Double(wins) / Double(totalComparisons)
    }
    
    // MARK: - Export
    func exportResults() -> String {
        var exportText = "AI Model Comparison Results\\n"
        exportText += "========================\\n\\n"
        
        for (index, result) in results.enumerated() {
            exportText += "Comparison #\\(index + 1)\\n"
            exportText += "Prompt: \\(result.prompt)\\n"
            exportText += "Date: \\(result.timestamp)\\n"
            if let winner = result.winner {
                exportText += "Winner: \\(winner)\\n"
            }
            exportText += "\\n"
            
            for response in result.responses {
                let model = AIModel.allModels.first { $0.id == response.modelId }
                exportText += "\\(model?.name ?? response.modelId):\\n"
                exportText += "Response Time: \\(String(format: "%.2f", response.responseTime))s\\n"
                if let rating = response.rating {
                    exportText += "Rating: \\(rating)/5\\n"
                }
                exportText += "Response: \\(response.response)\\n\\n"
            }
            exportText += "---\\n\\n"
        }
        
        return exportText
    }
}
