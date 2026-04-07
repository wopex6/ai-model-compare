import SwiftUI

// MARK: - User Character Analysis View
struct UserCharacterAnalysisView: View {
    @StateObject private var personalizationService = AdvancedAIResponseSystem()
    @State private var currentStep = 0
    @State private var analysisResponses: [String] = []
    @State private var isAnalyzing = false
    @State private var showResults = false
    
    private let analysisQuestions = [
        "How do you prefer to receive information - detailed explanations or quick answers?",
        "When facing a problem, do you prefer to think it through logically or discuss it with others?",
        "What motivates you most - achieving goals, learning new things, or helping others?",
        "How do you handle stress - do you need practical solutions or emotional support?",
        "What's your learning style - do you prefer reading, watching, or doing?"
    ]
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Progress indicator
                progressIndicator
                
                // Question area
                if currentStep < analysisQuestions.count {
                    questionView
                } else {
                    analysisView
                }
                
                Spacer()
            }
            .navigationTitle("Character Analysis")
            .navigationBarTitleDisplayMode(.inline)
            .background(Color(.systemGroupedBackground))
        }
        .sheet(isPresented: $showResults) {
            CharacterResultsView(character: personalizationService.currentUserCharacter)
        }
    }
    
    // MARK: - Progress Indicator
    private var progressIndicator: some View {
        VStack(spacing: 8) {
            HStack {
                Text("Step \(currentStep + 1) of \(analysisQuestions.count + 1)")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text("\(Int((Double(currentStep) / Double(analysisQuestions.count + 1)) * 100))%")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            ProgressView(value: Double(currentStep), total: Double(analysisQuestions.count + 1))
                .tint(.blue)
        }
        .padding()
    }
    
    // MARK: - Question View
    private var questionView: some View {
        VStack(spacing: 24) {
            Text(analysisQuestions[currentStep])
                .font(.title2)
                .fontWeight(.medium)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            VStack(spacing: 12) {
                ForEach(responseOptions(for: currentStep), id: \.self) { option in
                    Button(action: {
                        analysisResponses.append(option)
                        nextStep()
                    }) {
                        HStack {
                            Text(option)
                                .font(.body)
                                .foregroundColor(.primary)
                                .multilineTextAlignment(.leading)
                            
                            Spacer()
                            
                            Image(systemName: "chevron.right")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding()
                        .background(Color(.systemBackground))
                        .cornerRadius(12)
                        .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
                    }
                }
            }
            .padding(.horizontal)
        }
    }
    
    // MARK: - Analysis View
    private var analysisView: some View {
        VStack(spacing: 24) {
            if isAnalyzing {
                VStack(spacing: 16) {
                    ProgressView()
                        .scaleEffect(1.5)
                        .tint(.blue)
                    
                    Text("Analyzing your responses...")
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    Text("We're creating your personalized AI experience based on your unique character and preferences.")
                        .font(.body)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }
            } else {
                VStack(spacing: 16) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 60))
                        .foregroundColor(.blue)
                    
                    Text("Ready to complete analysis")
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    Text("Based on your responses, we'll create a personalized AI experience that adapts to your unique communication style and emotional needs.")
                        .font(.body)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                    
                    Button(action: {
                        isAnalyzing = true
                        completeAnalysis()
                    }) {
                        Text("Complete Analysis")
                            .font(.headline)
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.blue)
                            .cornerRadius(12)
                    }
                    .padding(.horizontal)
                }
            }
        }
    }
    
    // MARK: - Helper Methods
    private func responseOptions(for step: Int) -> [String] {
        switch step {
        case 0:
            return ["Detailed explanations with examples", "Quick, direct answers", "Visual descriptions", "Interactive discussions"]
        case 1:
            return ["Think it through logically myself", "Discuss with others", "Look for practical solutions", "Consider emotional aspects"]
        case 2:
            return ["Achieving specific goals", "Learning and growing", "Helping others succeed", "Creating something new"]
        case 3:
            return ["Practical solutions and action plans", "Emotional support and understanding", "Time to process and reflect", "Different perspectives"]
        case 4:
            return ["Reading detailed information", "Watching demonstrations", "Hands-on practice", "Interactive learning"]
        default:
            return []
        }
    }
    
    private func nextStep() {
        if currentStep < analysisQuestions.count - 1 {
            currentStep += 1
        } else {
            // Move to analysis view
            currentStep = analysisQuestions.count
        }
    }
    
    private func completeAnalysis() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            isAnalyzing = false
            showResults = true
        }
    }
}

// MARK: - Character Results View
struct CharacterResultsView: View {
    let character: UserCharacter?
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    if let character = character {
                        // Personality Type
                        personalityCard(character: character)
                        
                        // Communication Style
                        communicationCard(character: character)
                        
                        // Emotional Profile
                        emotionalCard(character: character)
                        
                        // Learning Style
                        learningCard(character: character)
                        
                        // Goal Orientation
                        goalCard(character: character)
                        
                        // Action Button
                        actionButton
                    } else {
                        emptyState
                    }
                }
                .padding()
            }
            .navigationTitle("Your Character Profile")
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
    
    // MARK: - Personality Card
    private func personalityCard(character: UserCharacter) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "brain.head.profile")
                    .foregroundColor(.blue)
                    .font(.title2)
                
                Text("Personality Type")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Spacer()
            }
            
            Text(character.personalityType.rawValue)
                .font(.title3)
                .fontWeight(.medium)
                .foregroundColor(.blue)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.blue.opacity(0.1))
                .cornerRadius(8)
            
            VStack(alignment: .leading, spacing: 4) {
                ForEach(character.personalityType.characteristics, id: \.self) { trait in
                    HStack {
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 6, height: 6)
                        
                        Text(trait.capitalized)
                            .font(.body)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
    }
    
    // MARK: - Communication Card
    private func communicationCard(character: UserCharacter) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "bubble.left.and.bubble.right")
                    .foregroundColor(.green)
                    .font(.title2)
                
                Text("Communication Style")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Spacer()
            }
            
            VStack(spacing: 8) {
                styleRow(title: "Directness", value: character.communicationStyle.directness)
                styleRow(title: "Formality", value: character.communicationStyle.formality)
                styleRow(title: "Detail Level", value: character.communicationStyle.verbosity)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
    }
    
    private func styleRow(title: String, value: Double) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
            
            ProgressView(value: value, total: 1.0)
                .tint(value > 0.6 ? .green : .orange)
            
            Text(value < 0.3 ? "Low" : value < 0.7 ? "Medium" : "High")
                .font(.caption2)
                .foregroundColor(.secondary)
        }
    }
    
    // MARK: - Emotional Card
    private func emotionalCard(character: UserCharacter) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "heart")
                    .foregroundColor(.red)
                    .font(.title2)
                
                Text("Emotional Profile")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Spacer()
                
                Text(character.emotionalProfile.moodState.rawValue.capitalized)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(.systemGray6))
                    .cornerRadius(6)
            }
            
            VStack(spacing: 8) {
                emotionRow(title: "Emotional Intelligence", value: character.emotionalProfile.emotionalIntelligence)
                emotionRow(title: "Stability", value: character.emotionalProfile.emotionalStability)
                emotionRow(title: "Openness", value: character.emotionalProfile.openness)
                emotionRow(title: "Empathy", value: character.emotionalProfile.empathy)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
    }
    
    private func emotionRow(title: String, value: Double) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
            
            ProgressView(value: value, total: 1.0)
                .tint(value > 0.6 ? .green : value > 0.3 ? .orange : .red)
        }
    }
    
    // MARK: - Learning Card
    private func learningCard(character: UserCharacter) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "graduationcap")
                    .foregroundColor(.purple)
                    .font(.title2)
                
                Text("Learning Style")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Spacer()
            }
            
            Text(character.learningStyle.rawValue.capitalized)
                .font(.title3)
                .fontWeight(.medium)
                .foregroundColor(.purple)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.purple.opacity(0.1))
                .cornerRadius(8)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
    }
    
    // MARK: - Goal Card
    private func goalCard(character: UserCharacter) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "target")
                    .foregroundColor(.orange)
                    .font(.title2)
                
                Text("Goal Orientation")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Spacer()
            }
            
            Text(character.goalOrientation.rawValue.capitalized)
                .font(.title3)
                .fontWeight(.medium)
                .foregroundColor(.orange)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.orange.opacity(0.1))
                .cornerRadius(8)
            
            Text("Motivated by \(character.goalOrientation.primaryMotivation)")
                .font(.body)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
    }
    
    // MARK: - Action Button
    private var actionButton: some View {
        Button(action: {
            dismiss()
        }) {
            Text("Start Using Personalized AI")
                .font(.headline)
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.blue)
                .cornerRadius(12)
        }
    }
    
    // MARK: - Empty State
    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "person.crop.circle.badge.questionmark")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            
            Text("Character Analysis Not Complete")
                .font(.headline)
                .foregroundColor(.primary)
            
            Text("Please complete the character analysis to get personalized AI responses.")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
    }
}

// MARK: - Feedback Collection View
struct FeedbackCollectionView: View {
    let response: PersonalizedResponse
    let onSubmit: (FeedbackResponse) -> Void
    
    @State private var selectedRating: Int = 0
    @State private var feedbackType: FeedbackType = .general
    @State private var feedbackText: String = ""
    @State private var emotionalReaction: EmotionalReaction?
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    // Response Preview
                    responsePreview
                    
                    // Emotional Reaction
                    emotionalReactionSection
                    
                    // Rating
                    ratingSection
                    
                    // Feedback Type
                    feedbackTypeSection
                    
                    // Detailed Feedback
                    feedbackTextSection
                    
                    // Submit Button
                    submitButton
                }
                .padding()
            }
            .navigationTitle("Feedback")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Cancel") {
                        // Handle cancel
                    }
                }
            }
        }
    }
    
    // MARK: - Response Preview
    private var responsePreview: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("AI Response")
                .font(.headline)
                .foregroundColor(.primary)
            
            Text(response.content)
                .font(.body)
                .foregroundColor(.secondary)
                .padding()
                .background(Color(.systemGray6))
                .cornerRadius(8)
        }
    }
    
    // MARK: - Emotional Reaction Section
    private var emotionalReactionSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("How did this response make you feel?")
                .font(.headline)
                .foregroundColor(.primary)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 3), spacing: 12) {
                ForEach(EmotionalReaction.allCases, id: \.self) { reaction in
                    Button(action: {
                        emotionalReaction = reaction
                    }) {
                        VStack(spacing: 4) {
                            Text(reaction.emoji)
                                .font(.title2)
                            
                            Text(reaction.rawValue)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding()
                        .background(
                            emotionalReaction == reaction ?
                            Color.blue.opacity(0.2) :
                            Color(.systemGray6)
                        )
                        .cornerRadius(8)
                    }
                }
            }
        }
    }
    
    // MARK: - Rating Section
    private var ratingSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Rate this response")
                .font(.headline)
                .foregroundColor(.primary)
            
            HStack(spacing: 8) {
                ForEach(1...5, id: \.self) { rating in
                    Button(action: {
                        selectedRating = rating
                    }) {
                        Image(systemName: rating <= selectedRating ? "star.fill" : "star")
                            .font(.title2)
                            .foregroundColor(rating <= selectedRating ? .yellow : .gray)
                    }
                }
            }
            
            if selectedRating > 0 {
                Text(ratingDescription(selectedRating))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
    }
    
    // MARK: - Feedback Type Section
    private var feedbackTypeSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("What type of feedback is this?")
                .font(.headline)
                .foregroundColor(.primary)
            
            VStack(spacing: 8) {
                ForEach(FeedbackType.allCases, id: \.self) { type in
                    Button(action: {
                        feedbackType = type
                    }) {
                        HStack {
                            Text(type.rawValue)
                                .font(.body)
                                .foregroundColor(.primary)
                            
                            Spacer()
                            
                            Image(systemName: feedbackType == type ? "checkmark.circle.fill" : "circle")
                                .foregroundColor(feedbackType == type ? .blue : .gray)
                        }
                        .padding()
                        .background(Color(.systemGray6))
                        .cornerRadius(8)
                    }
                }
            }
        }
    }
    
    // MARK: - Feedback Text Section
    private var feedbackTextSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Additional feedback (optional)")
                .font(.headline)
                .foregroundColor(.primary)
            
            TextEditor(text: $feedbackText)
                .font(.body)
                .padding(8)
                .background(Color(.systemGray6))
                .cornerRadius(8)
                .frame(minHeight: 100)
        }
    }
    
    // MARK: - Submit Button
    private var submitButton: some View {
        Button(action: {
            let feedback = FeedbackResponse(
                responseId: response.id,
                rating: selectedRating,
                feedbackType: feedbackType,
                feedbackText: feedbackText,
                emotionalReaction: emotionalReaction,
                timestamp: Date()
            )
            onSubmit(feedback)
        }) {
            Text("Submit Feedback")
                .font(.headline)
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding()
                .background(selectedRating > 0 ? Color.blue : Color(.systemGray3))
                .cornerRadius(12)
        }
        .disabled(selectedRating == 0)
    }
    
    // MARK: - Helper Methods
    private func ratingDescription(_ rating: Int) -> String {
        switch rating {
        case 1: return "Not helpful"
        case 2: return "Somewhat helpful"
        case 3: return "Good"
        case 4: return "Very helpful"
        case 5: return "Perfect!"
        default: return ""
        }
    }
}

// MARK: - Supporting Models
enum EmotionalReaction: String, CaseIterable {
    case happy = "Happy"
    case relieved = "Relieved"
    case confused = "Confused"
    case frustrated = "Frustrated"
    case inspired = "Inspired"
    case neutral = "Neutral"
    
    var emoji: String {
        switch self {
        case .happy: return "😊"
        case .relieved: return "😌"
        case .confused: return "😕"
        case .frustrated: return "😤"
        case .inspired: return "💡"
        case .neutral: return "😐"
        }
    }
}

enum FeedbackType: String, CaseIterable {
    case general = "General Feedback"
    case accuracy = "Accuracy Issue"
    case tone = "Tone/Style Issue"
    case personalization = "Personalization Issue"
    case technical = "Technical Problem"
}

struct FeedbackResponse {
    let responseId: UUID
    let rating: Int
    let feedbackType: FeedbackType
    let feedbackText: String
    let emotionalReaction: EmotionalReaction?
    let timestamp: Date
}
