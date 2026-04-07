import Foundation
import CoreData
import Combine

// MARK: - Core Data Store
class DataStore: ObservableObject {
    static let shared = DataStore()
    
    lazy var container: NSPersistentContainer = {
        let container = NSPersistentContainer(name: "AIModelCompare")
        container.loadPersistentStores { _, error in
            if let error = error {
                fatalError("Core Data failed to load: \(error.localizedDescription)")
            }
        }
        return container
    }()
    
    var context: NSManagedObjectContext {
        return container.viewContext
    }
    
    private init() {}
    
    // MARK: - Chat Session Management
    func saveChatSession(_ session: ChatSession) {
        let entity = ChatSessionEntity(context: context)
        entity.id = session.id
        entity.title = session.title
        entity.createdAt = session.createdAt
        entity.updatedAt = session.updatedAt
        entity.selectedModels = session.selectedModels.joined(separator: ",")
        
        for message in session.messages {
            let messageEntity = MessageEntity(context: context)
            messageEntity.id = message.id
            messageEntity.content = message.content
            messageEntity.timestamp = message.timestamp
            messageEntity.isUser = message.isUser
            messageEntity.modelId = message.modelId
            messageEntity.session = entity
        }
        
        saveContext()
    }
    
    func fetchChatSessions() -> [ChatSession] {
        let request: NSFetchRequest<ChatSessionEntity> = ChatSessionEntity.fetchRequest()
        request.sortDescriptors = [NSSortDescriptor(keyPath: \ChatSessionEntity.updatedAt, ascending: false)]
        
        do {
            let entities = try context.fetch(request)
            return entities.compactMap { entity in
                guard let id = entity.id,
                      let title = entity.title,
                      let createdAt = entity.createdAt,
                      let updatedAt = entity.updatedAt else {
                    return nil
                }
                
                let messages = (entity.messages?.allObjects as? [MessageEntity])?.compactMap { messageEntity in
                    guard let id = messageEntity.id,
                          let content = messageEntity.content,
                          let timestamp = messageEntity.timestamp else {
                        return nil
                    }
                    return Message(
                        id: id,
                        content: content,
                        timestamp: timestamp,
                        isUser: messageEntity.isUser,
                        modelId: messageEntity.modelId
                    )
                } ?? []
                
                let selectedModels = entity.selectedModels?.components(separatedBy: ",") ?? []
                
                return ChatSession(
                    id: id,
                    title: title,
                    createdAt: createdAt,
                    updatedAt: updatedAt,
                    messages: messages,
                    selectedModels: selectedModels
                )
            }
        } catch {
            print("Error fetching chat sessions: \(error)")
            return []
        }
    }
    
    func deleteChatSession(_ sessionId: UUID) {
        let request: NSFetchRequest<ChatSessionEntity> = ChatSessionEntity.fetchRequest()
        request.predicate = NSPredicate(format: "id == %@", sessionId as CVarArg)
        
        do {
            let entities = try context.fetch(request)
            for entity in entities {
                context.delete(entity)
            }
            saveContext()
        } catch {
            print("Error deleting chat session: \(error)")
        }
    }
    
    // MARK: - Comparison Results Management
    func saveComparisonResult(_ result: ComparisonResult) {
        let entity = ComparisonResultEntity(context: context)
        entity.id = result.id
        entity.prompt = result.prompt
        entity.timestamp = result.timestamp
        entity.winner = result.winner
        
        for response in result.responses {
            let responseEntity = ModelResponseEntity(context: context)
            responseEntity.id = response.id
            responseEntity.modelId = response.modelId
            responseEntity.response = response.response
            responseEntity.responseTime = response.responseTime
            responseEntity.tokenCount = Int32(response.tokenCount ?? 0)
            responseEntity.rating = Int16(response.rating ?? 0)
            responseEntity.comparisonResult = entity
        }
        
        saveContext()
    }
    
    func fetchComparisonResults() -> [ComparisonResult] {
        let request: NSFetchRequest<ComparisonResultEntity> = ComparisonResultEntity.fetchRequest()
        request.sortDescriptors = [NSSortDescriptor(keyPath: \ComparisonResultEntity.timestamp, ascending: false)]
        
        do {
            let entities = try context.fetch(request)
            return entities.compactMap { entity in
                guard let id = entity.id,
                      let prompt = entity.prompt,
                      let timestamp = entity.timestamp else {
                    return nil
                }
                
                let responses = (entity.responses?.allObjects as? [ModelResponseEntity])?.compactMap { responseEntity in
                    guard let id = responseEntity.id,
                          let modelId = responseEntity.modelId,
                          let response = responseEntity.response else {
                        return nil
                    }
                    return ComparisonResult.ModelResponse(
                        id: id,
                        modelId: modelId,
                        response: response,
                        responseTime: responseEntity.responseTime,
                        tokenCount: responseEntity.tokenCount > 0 ? Int(responseEntity.tokenCount) : nil,
                        rating: responseEntity.rating > 0 ? Int(responseEntity.rating) : nil
                    )
                } ?? []
                
                return ComparisonResult(
                    id: id,
                    prompt: prompt,
                    timestamp: timestamp,
                    responses: responses,
                    winner: entity.winner
                )
            }
        } catch {
            print("Error fetching comparison results: \(error)")
            return []
        }
    }
    
    // MARK: - Settings Management
    func saveSettings(_ settings: UserSettings) {
        let entity = SettingsEntity(context: context)
        entity.theme = settings.selectedTheme.rawValue
        entity.voiceInputEnabled = settings.voiceInputEnabled
        entity.voiceOutputEnabled = settings.voiceOutputEnabled
        entity.autoSaveChats = settings.autoSaveChats
        entity.maxTokenUsage = Int32(settings.maxTokenUsage)
        entity.preferredModel = settings.preferredModel
        
        saveContext()
    }
    
    func fetchSettings() -> UserSettings {
        let request: NSFetchRequest<SettingsEntity> = SettingsEntity.fetchRequest()
        
        do {
            let entities = try context.fetch(request)
            if let entity = entities.first,
               let themeRaw = entity.theme,
               let theme = AppTheme(rawValue: themeRaw) {
                return UserSettings(
                    selectedTheme: theme,
                    voiceInputEnabled: entity.voiceInputEnabled,
                    voiceOutputEnabled: entity.voiceOutputEnabled,
                    autoSaveChats: entity.autoSaveChats,
                    maxTokenUsage: Int(entity.maxTokenUsage),
                    preferredModel: entity.preferredModel
                )
            }
        } catch {
            print("Error fetching settings: \(error)")
        }
        
        return .default
    }
    
    // MARK: - Core Data Helpers
    private func saveContext() {
        if context.hasChanges {
            do {
                try context.save()
            } catch {
                print("Error saving context: \(error)")
            }
        }
    }
}

// MARK: - Core Data Entities
@objc(ChatSessionEntity)
public class ChatSessionEntity: NSManagedObject {
    @NSManaged public var id: UUID?
    @NSManaged public var title: String?
    @NSManaged public var createdAt: Date?
    @NSManaged public var updatedAt: Date?
    @NSManaged public var selectedModels: String?
    @NSManaged public var messages: NSSet?
}

@objc(MessageEntity)
public class MessageEntity: NSManagedObject {
    @NSManaged public var id: UUID?
    @NSManaged public var content: String?
    @NSManaged public var timestamp: Date?
    @NSManaged public var isUser: Bool
    @NSManaged public var modelId: String?
    @NSManaged public var session: ChatSessionEntity?
}

@objc(ComparisonResultEntity)
public class ComparisonResultEntity: NSManagedObject {
    @NSManaged public var id: UUID?
    @NSManaged public var prompt: String?
    @NSManaged public var timestamp: Date?
    @NSManaged public var winner: String?
    @NSManaged public var responses: NSSet?
}

@objc(ModelResponseEntity)
public class ModelResponseEntity: NSManagedObject {
    @NSManaged public var id: UUID?
    @NSManaged public var modelId: String?
    @NSManaged public var response: String?
    @NSManaged public var responseTime: Double
    @NSManaged public var tokenCount: Int32
    @NSManaged public var rating: Int16
    @NSManaged public var comparisonResult: ComparisonResultEntity?
}

@objc(SettingsEntity)
public class SettingsEntity: NSManagedObject {
    @NSManaged public var theme: String?
    @NSManaged public var voiceInputEnabled: Bool
    @NSManaged public var voiceOutputEnabled: Bool
    @NSManaged public var autoSaveChats: Bool
    @NSManaged public var maxTokenUsage: Int32
    @NSManaged public var preferredModel: String?
}
