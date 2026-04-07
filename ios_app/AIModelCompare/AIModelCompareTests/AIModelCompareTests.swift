import XCTest
@testable import AIModelCompare

final class AIModelCompareTests: XCTestCase {
    
    func testAIModelCreation() throws {
        let model = AIModel.allModels.first!
        
        XCTAssertNotNil(model.id)
        XCTAssertFalse(model.name.isEmpty)
        XCTAssertFalse(model.provider.isEmpty)
        XCTAssertGreaterThan(model.maxTokens, 0)
    }
    
    func testMessageCreation() throws {
        let message = Message(content: "Test message", isUser: true)
        
        XCTAssertNotNil(message.id)
        XCTAssertEqual(message.content, "Test message")
        XCTAssertTrue(message.isUser)
        XCTAssertNil(message.modelId)
    }
    
    func testChatSessionCreation() throws {
        let session = ChatSession(title: "Test Chat")
        
        XCTAssertNotNil(session.id)
        XCTAssertEqual(session.title, "Test Chat")
        XCTAssertTrue(session.messages.isEmpty)
        XCTAssertTrue(session.selectedModels.isEmpty)
    }
    
    func testComparisonResultCreation() throws {
        let result = ComparisonResult(
            prompt: "Test prompt",
            responses: [
                ComparisonResult.ModelResponse(
                    id: UUID(),
                    modelId: "gpt-4",
                    response: "Test response",
                    responseTime: 1.5,
                    tokenCount: 100,
                    rating: 5
                )
            ]
        )
        
        XCTAssertEqual(result.prompt, "Test prompt")
        XCTAssertEqual(result.responses.count, 1)
        XCTAssertEqual(result.responses.first?.modelId, "gpt-4")
    }
    
    func testUserSettingsDefaults() throws {
        let settings = UserSettings.default
        
        XCTAssertEqual(settings.selectedTheme, .system)
        XCTAssertTrue(settings.voiceInputEnabled)
        XCTAssertFalse(settings.voiceOutputEnabled)
        XCTAssertTrue(settings.autoSaveChats)
        XCTAssertEqual(settings.maxTokenUsage, 100000)
        XCTAssertNil(settings.preferredModel)
    }
    
    func testAppThemeCases() throws {
        XCTAssertEqual(AppTheme.light.displayName, "Light")
        XCTAssertEqual(AppTheme.dark.displayName, "Dark")
        XCTAssertEqual(AppTheme.system.displayName, "System")
    }
}
