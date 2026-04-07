import XCTest
@testable import AIModelCompare

final class AIModelCompareUITests: XCTestCase {
    
    override func setUpWithError() throws {
        continueAfterFailure = false
    }
    
    override func tearDownWithError() throws {
    }
    
    func testAppLaunch() throws {
        let app = XCUIApplication()
        app.launch()
        
        // Verify main tab bar exists
        XCTAssertTrue(app.tabBars.buttons["Chat"].exists)
        XCTAssertTrue(app.tabBars.buttons["Compare"].exists)
        XCTAssertTrue(app.tabBars.buttons["History"].exists)
        XCTAssertTrue(app.tabBars.buttons["Settings"].exists)
    }
    
    func testChatViewElements() throws {
        let app = XCUIApplication()
        app.launch()
        
        // Navigate to Chat tab
        app.tabBars.buttons["Chat"].tap()
        
        // Verify chat elements exist
        XCTAssertTrue(app.navigationBars["AI Chat"].exists)
        XCTAssertTrue(app.textViews["Type a message..."].exists)
        XCTAssertTrue(app.buttons["square.and.pencil"].exists)
        XCTAssertTrue(app.buttons["ellipsis.circle"].exists)
    }
    
    func testCompareViewElements() throws {
        let app = XCUIApplication()
        app.launch()
        
        // Navigate to Compare tab
        app.tabBars.buttons["Compare"].tap()
        
        // Verify compare elements exist
        XCTAssertTrue(app.navigationBars["Compare Models"].exists)
        XCTAssertTrue(app.textViews["Prompt"].exists)
        XCTAssertTrue(app.buttons["Run Comparison"].exists)
    }
    
    func testHistoryViewElements() throws {
        let app = XCUIApplication()
        app.launch()
        
        // Navigate to History tab
        app.tabBars.buttons["History"].tap()
        
        // Verify history elements exist
        XCTAssertTrue(app.navigationBars["History"].exists)
        XCTAssertTrue(app.searchFields["Search history..."].exists)
        XCTAssertTrue(app.buttons["Chats"].exists)
        XCTAssertTrue(app.buttons["Comparisons"].exists)
    }
    
    func testSettingsViewElements() throws {
        let app = XCUIApplication()
        app.launch()
        
        // Navigate to Settings tab
        app.tabBars.buttons["Settings"].tap()
        
        // Verify settings elements exist
        XCTAssertTrue(app.navigationBars["Settings"].exists)
        XCTAssertTrue(app.staticTexts["Account"].exists)
        XCTAssertTrue(app.staticTexts["API Keys"].exists)
        XCTAssertTrue(app.staticTexts["Appearance"].exists)
        XCTAssertTrue(app.staticTexts["Voice & Input"].exists)
    }
}
