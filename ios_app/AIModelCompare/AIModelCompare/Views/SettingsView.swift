import SwiftUI

struct SettingsView: View {
    @StateObject private var settingsManager = SettingsManager()
    @State private var showingAPIKeySheet = false
    @State private var selectedProvider: String = ""
    
    var body: some View {
        NavigationView {
            List {
                // Account Section
                Section("Account") {
                    HStack {
                        Image(systemName: "person.circle")
                            .foregroundColor(.blue)
                            .font(.title2)
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Guest User")
                                .font(.headline)
                                .foregroundColor(.primary)
                            Text("Sign in to sync across devices")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        Button("Sign In") {
                            // Sign in functionality
                        }
                        .font(.caption)
                        .foregroundColor(.blue)
                    }
                    .padding(.vertical, 4)
                }
                
                // API Keys Section
                Section("API Keys") {
                    ForEach(["OpenAI", "Anthropic", "Google"], id: \.self) { provider in
                        APIKeyRow(
                            provider: provider,
                            hasKey: settingsManager.hasAPIKey(for: provider),
                            onTap: {
                                selectedProvider = provider
                                showingAPIKeySheet = true
                            }
                        )
                    }
                }
                
                // Appearance Section
                Section("Appearance") {
                    Picker("Theme", selection: $settingsManager.settings.selectedTheme) {
                        ForEach(AppTheme.allCases, id: \.self) { theme in
                            Text(theme.displayName).tag(theme)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }
                
                // Voice & Input Section
                Section("Voice & Input") {
                    Toggle("Voice Input", isOn: $settingsManager.settings.voiceInputEnabled)
                    Toggle("Voice Output", isOn: $settingsManager.settings.voiceOutputEnabled)
                }
                
                // Storage Section
                Section("Storage") {
                    Toggle("Auto-save Chats", isOn: $settingsManager.settings.autoSaveChats)
                    
                    HStack {
                        Text("Max Token Usage")
                        Spacer()
                        Text("\(settingsManager.settings.maxTokenUsage)")
                            .foregroundColor(.secondary)
                    }
                    
                    Slider(
                        value: Binding(
                            get: { Double(settingsManager.settings.maxTokenUsage) },
                            set: { settingsManager.settings.maxTokenUsage = Int($0) }
                        ),
                        range: 10000...1000000,
                        step: 10000
                    )
                }
                
                // Model Preferences
                Section("Model Preferences") {
                    Picker("Preferred Model", selection: Binding(
                        get: { settingsManager.settings.preferredModel ?? "" },
                        set: { settingsManager.settings.preferredModel = $0.isEmpty ? nil : $0 }
                    )) {
                        Text("None").tag("")
                        ForEach(AIModel.allModels) { model in
                            Text(model.name).tag(model.id)
                        }
                    }
                }
                
                // About Section
                Section("About") {
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Text("Build")
                        Spacer()
                        Text("2024.03")
                            .foregroundColor(.secondary)
                    }
                    
                    Link("Privacy Policy", destination: URL(string: "https://example.com/privacy")!)
                    Link("Terms of Service", destination: URL(string: "https://example.com/terms")!)
                    Link("Support", destination: URL(string: "https://example.com/support")!)
                }
                
                // Danger Zone
                Section("Reset") {
                    Button("Clear All Data") {
                        settingsManager.clearAllData()
                    }
                    .foregroundColor(.red)
                }
            }
            .navigationTitle("Settings")
            .sheet(isPresented: $showingAPIKeySheet) {
                APIKeySheet(provider: selectedProvider) { key in
                    settingsManager.setAPIKey(key, for: selectedProvider)
                }
            }
        }
    }
}

// MARK: - API Key Row
struct APIKeyRow: View {
    let provider: String
    let hasKey: Bool
    let onTap: () -> Void
    
    var body: some View {
        HStack {
            Image(systemName: iconForProvider(provider))
                .foregroundColor(colorForProvider(provider))
                .font(.title2)
                .frame(width: 32)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(provider)
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Text(hasKey ? "API key configured" : "No API key set")
                    .font(.caption)
                    .foregroundColor(hasKey ? .green : .orange)
            }
            
            Spacer()
            
            Button(action: onTap) {
                Text(hasKey ? "Edit" : "Add")
                    .font(.caption)
                    .foregroundColor(.blue)
            }
        }
        .padding(.vertical, 4)
    }
    
    private func iconForProvider(_ provider: String) -> String {
        switch provider {
        case "OpenAI":
            return "brain.head.profile"
        case "Anthropic":
            return "graduationcap"
        case "Google":
            return "magnifyingglass"
        default:
            return "key"
        }
    }
    
    private func colorForProvider(_ provider: String) -> Color {
        switch provider {
        case "OpenAI":
            return .green
        case "Anthropic":
            return .purple
        case "Google":
            return .blue
        default:
            return .gray
        }
    }
}

// MARK: - API Key Sheet
struct APIKeySheet: View {
    let provider: String
    let onSave: (String) -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var apiKey = ""
    @State private var showingKey = false
    
    var body: some View {
        NavigationView {
            Form {
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Enter your \(provider) API key")
                            .font(.headline)
                        
                        Text("Your API key is stored securely on your device and is never shared with third parties.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Section("API Key") {
                    HStack {
                        if showingKey {
                            TextField("API Key", text: $apiKey)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                        } else {
                            TextField("API Key", text: $apiKey)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .secureFieldEntry(true)
                        }
                        
                        Button(action: { showingKey.toggle() }) {
                            Image(systemName: showingKey ? "eye.slash" : "eye")
                                .foregroundColor(.secondary)
                        }
                    }
                }
                
                Section("Help") {
                    Link("Get \(provider) API Key", destination: urlForProvider(provider))
                    
                    if provider == "OpenAI" {
                        Text("Visit platform.openai.com → API Keys → Create new secret key")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    } else if provider == "Anthropic" {
                        Text("Visit console.anthropic.com → API Keys → Create key")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    } else if provider == "Google" {
                        Text("Visit makersuite.google.com → Get API Key")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("\(provider) API Key")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        onSave(apiKey)
                        dismiss()
                    }
                    .disabled(apiKey.isEmpty)
                }
            }
        }
    }
    
    private func urlForProvider(_ provider: String) -> URL {
        switch provider {
        case "OpenAI":
            return URL(string: "https://platform.openai.com/api-keys")!
        case "Anthropic":
            return URL(string: "https://console.anthropic.com/")!
        case "Google":
            return URL(string: "https://makersuite.google.com/app/apikey")!
        default:
            return URL(string: "https://example.com")!
        }
    }
}

// MARK: - Settings Manager
class SettingsManager: ObservableObject {
    @Published var settings: UserSettings
    
    private let dataStore = DataStore.shared
    private var apiKeys: [String: String] = [:]
    
    init() {
        self.settings = dataStore.fetchSettings()
        loadAPIKeys()
    }
    
    func saveSettings() {
        dataStore.saveSettings(settings)
    }
    
    func hasAPIKey(for provider: String) -> Bool {
        return apiKeys[provider] != nil && !apiKeys[provider]!.isEmpty
    }
    
    func setAPIKey(_ key: String, for provider: String) {
        apiKeys[provider] = key
        saveAPIKeys()
        
        // Update AI service manager
        let serviceManager = AIServiceManager()
        serviceManager.configureAPIKey(key, for: provider.lowercased())
    }
    
    func clearAllData() {
        // Clear Core Data
        let context = dataStore.context
        let entities = ["ChatSessionEntity", "MessageEntity", "ComparisonResultEntity", "ModelResponseEntity", "SettingsEntity"]
        
        for entity in entities {
            let fetchRequest = NSFetchRequest<NSFetchRequestResult>(entityName: entity)
            let deleteRequest = NSBatchDeleteRequest(fetchRequest: fetchRequest)
            
            do {
                try context.execute(deleteRequest)
            } catch {
                print("Error deleting \(entity): \(error)")
            }
        }
        
        // Reset settings
        settings = .default
        saveSettings()
        
        // Clear API keys
        apiKeys.removeAll()
        saveAPIKeys()
    }
    
    private func loadAPIKeys() {
        // In a real app, this would load from Keychain
        // For demo, we'll use UserDefaults (not secure for production)
        if let keysData = UserDefaults.standard.data(forKey: "APIKeys"),
           let keys = try? JSONDecoder().decode([String: String].self, from: keysData) {
            apiKeys = keys
        }
    }
    
    private func saveAPIKeys() {
        // In a real app, this would save to Keychain
        // For demo, we'll use UserDefaults (not secure for production)
        if let keysData = try? JSONEncoder().encode(apiKeys) {
            UserDefaults.standard.set(keysData, forKey: "APIKeys")
        }
    }
}

// MARK: - Extensions
extension View {
    func hideKeyboard() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
    }
}
