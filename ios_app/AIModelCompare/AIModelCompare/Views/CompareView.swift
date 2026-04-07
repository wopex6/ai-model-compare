import SwiftUI

struct CompareView: View {
    @StateObject private var viewModel = CompareViewModel()
    @State private var showingModelSelector = false
    @State private var showingExportSheet = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Input section
                inputSection
                
                // Results section
                resultsSection
            }
            .navigationTitle("Compare Models")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Button(action: { showingModelSelector = true }) {
                            Label("Select Models", systemImage: "checkmark.circle")
                        }
                        
                        Button(action: { showingExportSheet = true }) {
                            Label("Export Results", systemImage: "square.and.arrow.up")
                        }
                        
                        Button(action: { viewModel.loadResults() }) {
                            Label("Refresh", systemImage: "arrow.clockwise")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .sheet(isPresented: $showingModelSelector) {
                CompareModelSelectionView(viewModel: viewModel)
            }
            .sheet(isPresented: $showingExportSheet) {
                ExportSheet(exportText: viewModel.exportResults())
            }
            .alert("Error", isPresented: .constant(viewModel.errorMessage != nil)) {
                Button("OK") {
                    viewModel.errorMessage = nil
                }
            } message: {
                if let error = viewModel.errorMessage {
                    Text(error)
                }
            }
        }
    }
    
    // MARK: - Input Section
    private var inputSection: some View {
        VStack(spacing: 16) {
            // Prompt input
            VStack(alignment: .leading, spacing: 8) {
                Text("Prompt")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                TextEditor(text: $viewModel.prompt)
                    .font(.body)
                    .padding(8)
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                    .frame(minHeight: 100)
            }
            
            // Selected models
            if !viewModel.selectedModels.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Selected Models")
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(viewModel.getSelectedModels()) { model in
                                SelectedModelChip(model: model) {
                                    viewModel.toggleModel(model.id)
                                }
                            }
                        }
                        .padding(.horizontal)
                    }
                }
            }
            
            // Run button
            Button(action: viewModel.runComparison) {
                HStack {
                    if viewModel.isRunning {
                        ProgressView()
                            .scaleEffect(0.8)
                            .foregroundColor(.white)
                    } else {
                        Image(systemName: "play.circle.fill")
                            .font(.title2)
                    }
                    
                    Text(viewModel.isRunning ? "Running..." : "Run Comparison")
                        .font(.headline)
                }
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding()
                .background(
                    viewModel.prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                    || viewModel.selectedModels.isEmpty
                    || viewModel.isRunning
                    ? Color(.systemGray3)
                    : Color.blue
                )
                .cornerRadius(12)
            }
            .disabled(
                viewModel.prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                || viewModel.selectedModels.isEmpty
                || viewModel.isRunning
            )
            
            if viewModel.selectedModels.isEmpty {
                Text("Select at least one model to compare")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .overlay(
            Rectangle()
                .frame(height: 0.5)
                .foregroundColor(Color(.separator)),
            alignment: .bottom
        )
    }
    
    // MARK: - Results Section
    private var resultsSection: some View {
        ScrollView {
            LazyVStack(spacing: 16) {
                if viewModel.results.isEmpty {
                    EmptyResultsView()
                } else {
                    ForEach(viewModel.results) { result in
                        ComparisonResultCard(
                            result: result,
                            onRate: { modelId, rating in
                                viewModel.rateResponse(result, modelId: modelId, rating: rating)
                            },
                            onSelectWinner: { modelId in
                                viewModel.selectWinner(result, modelId: modelId)
                            },
                            onDelete: {
                                viewModel.deleteResult(result)
                            }
                        )
                    }
                }
            }
            .padding()
        }
    }
}

// MARK: - Selected Model Chip
struct SelectedModelChip: View {
    let model: AIModel
    let onTap: () -> Void
    
    var body: some View {
        HStack(spacing: 4) {
            Text(model.name)
                .font(.caption)
                .foregroundColor(.primary)
            
            Button(action: onTap) {
                Image(systemName: "xmark.circle.fill")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

// MARK: - Empty Results View
struct EmptyResultsView: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "chart.bar.doc.horizontal")
                .font(.system(size: 48))
                .foregroundColor(.secondary)
            
            Text("No Comparisons Yet")
                .font(.headline)
                .foregroundColor(.primary)
            
            Text("Run your first comparison to see how different AI models respond to the same prompt.")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .padding(.vertical, 40)
    }
}

// MARK: - Comparison Result Card
struct ComparisonResultCard: View {
    let result: ComparisonResult
    let onRate: (String, Int) -> Void
    let onSelectWinner: (String) -> Void
    let onDelete: () -> Void
    
    @State private var showingDetail = false
    @State private var showingDeleteAlert = false
    
    var body: some View {
        VStack(spacing: 16) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Comparison")
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
                    
                    Button(action: { showingDeleteAlert = true }) {
                        Label("Delete", systemImage: "trash")
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .foregroundColor(.secondary)
                }
            }
            
            // Prompt
            VStack(alignment: .leading, spacing: 8) {
                Text("Prompt")
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                
                Text(result.prompt)
                    .font(.body)
                    .foregroundColor(.secondary)
                    .lineLimit(3)
                    .padding(12)
                    .background(Color(.systemGray6))
                    .cornerRadius(8)
            }
            
            // Response summary
            VStack(alignment: .leading, spacing: 8) {
                Text("Responses")
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                
                ForEach(result.responses.prefix(2)) { response in
                    ResponseSummaryRow(
                        response: response,
                        onRate: { rating in
                            onRate(response.modelId, rating)
                        },
                        onSelectWinner: {
                            onSelectWinner(response.modelId)
                        },
                        isWinner: result.winner == response.modelId
                    )
                }
                
                if result.responses.count > 2 {
                    Button(action: { showingDetail = true }) {
                        Text("View all \(result.responses.count) responses")
                            .font(.caption)
                            .foregroundColor(.blue)
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
        .sheet(isPresented: $showingDetail) {
            ComparisonDetailView(result: result, onRate: onRate, onSelectWinner: onSelectWinner)
        }
        .alert("Delete Comparison", isPresented: $showingDeleteAlert) {
            Button("Delete", role: .destructive) {
                onDelete()
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("Are you sure you want to delete this comparison?")
        }
    }
}

// MARK: - Response Summary Row
struct ResponseSummaryRow: View {
    let response: ComparisonResult.ModelResponse
    let onRate: (Int) -> Void
    let onSelectWinner: () -> Void
    let isWinner: Bool
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                if let model = AIModel.allModels.first(where: { $0.id == response.modelId }) {
                    Text(model.name)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                } else {
                    Text(response.modelId)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                }
                
                HStack(spacing: 8) {
                    Text("\(String(format: "%.2f", response.responseTime))s")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    if let tokenCount = response.tokenCount {
                        Text("•")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text("\(tokenCount) tokens")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            
            Spacer()
            
            HStack(spacing: 12) {
                // Rating
                if let rating = response.rating {
                    HStack(spacing: 2) {
                        ForEach(1...5) { star in
                            Image(systemName: star <= rating ? "star.fill" : "star")
                                .font(.caption)
                                .foregroundColor(.yellow)
                        }
                    }
                } else {
                    HStack(spacing: 2) {
                        ForEach(1...5) { star in
                            Button(action: { onRate(star) }) {
                                Image(systemName: "star")
                                    .font(.caption)
                                    .foregroundColor(.gray)
                            }
                        }
                    }
                }
                
                // Winner button
                Button(action: onSelectWinner) {
                    Image(systemName: isWinner ? "trophy.fill" : "trophy")
                        .font(.caption)
                        .foregroundColor(isWinner ? .yellow : .gray)
                }
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Comparison Detail View
struct ComparisonDetailView: View {
    let result: ComparisonResult
    let onRate: (String, Int) -> Void
    let onSelectWinner: (String) -> Void
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Prompt section
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Prompt")
                            .font(.headline)
                            .foregroundColor(.primary)
                        
                        Text(result.prompt)
                            .font(.body)
                            .foregroundColor(.secondary)
                            .padding()
                            .background(Color(.systemGray6))
                            .cornerRadius(12)
                    }
                    
                    // Responses
                    ForEach(result.responses) { response in
                        ResponseDetailView(
                            response: response,
                            onRate: { rating in
                                onRate(response.modelId, rating)
                            },
                            onSelectWinner: {
                                onSelectWinner(response.modelId)
                            },
                            isWinner: result.winner == response.modelId
                        )
                    }
                }
                .padding()
            }
            .navigationTitle("Comparison Details")
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

// MARK: - Response Detail View
struct ResponseDetailView: View {
    let response: ComparisonResult.ModelResponse
    let onRate: (Int) -> Void
    let onSelectWinner: () -> Void
    let isWinner: Bool
    
    var body: some View {
        VStack(spacing: 16) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    if let model = AIModel.allModels.first(where: { $0.id == response.modelId }) {
                        Text(model.name)
                            .font(.headline)
                            .foregroundColor(.primary)
                    } else {
                        Text(response.modelId)
                            .font(.headline)
                            .foregroundColor(.primary)
                    }
                    
                    HStack(spacing: 8) {
                        Text("\(String(format: "%.2f", response.responseTime))s")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        if let tokenCount = response.tokenCount {
                            Text("•")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text("\(tokenCount) tokens")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                
                Spacer()
                
                if isWinner {
                    Label("Winner", systemImage: "trophy.fill")
                        .font(.caption)
                        .foregroundColor(.yellow)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color(.systemGray6))
                        .cornerRadius(8)
                }
            }
            
            // Response text
            Text(response.response)
                .font(.body)
                .foregroundColor(.primary)
                .padding()
                .background(Color(.systemGray6))
                .cornerRadius(12)
            
            // Actions
            HStack(spacing: 20) {
                // Rating
                VStack(alignment: .leading, spacing: 8) {
                    Text("Rating")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    HStack(spacing: 4) {
                        if let rating = response.rating {
                            ForEach(1...5) { star in
                                Image(systemName: star <= rating ? "star.fill" : "star")
                                    .font(.caption)
                                    .foregroundColor(.yellow)
                            }
                        } else {
                            ForEach(1...5) { star in
                                Button(action: { onRate(star) }) {
                                    Image(systemName: "star")
                                        .font(.caption)
                                        .foregroundColor(.gray)
                                }
                            }
                        }
                    }
                }
                
                Spacer()
                
                // Winner button
                Button(action: onSelectWinner) {
                    HStack {
                        Image(systemName: isWinner ? "trophy.fill" : "trophy")
                        Text(isWinner ? "Winner" : "Select as Winner")
                    }
                    .font(.caption)
                    .foregroundColor(isWinner ? .yellow : .blue)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(Color(.systemGray6))
                    .cornerRadius(8)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
    }
}

// MARK: - Compare Model Selection View
struct CompareModelSelectionView: View {
    @ObservedObject var viewModel: CompareViewModel
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            List {
                ForEach(AIModel.allModels) { model in
                    ModelRow(
                        model: model,
                        isSelected: viewModel.selectedModels.contains(model.id)
                    ) {
                        viewModel.toggleModel(model.id)
                    }
                }
            }
            .navigationTitle("Select Models")
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

// MARK: - Export Sheet
struct ExportSheet: View {
    let exportText: String
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                Text(exportText)
                    .font(.system(.body, design: .monospaced))
                    .padding()
            }
            .navigationTitle("Export Results")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Share") {
                        // Share functionality would go here
                        dismiss()
                    }
                }
            }
        }
    }
}
