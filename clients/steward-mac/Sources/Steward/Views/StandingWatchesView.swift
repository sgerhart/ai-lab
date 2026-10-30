import SwiftUI

public struct StandingWatchesView: View {
    @ObservedObject var client: StewardClient
    @State private var showingAddSheet: Bool = false

    @State private var newTitle: String = ""
    @State private var newRhythm: String = "hourly"
    @State private var selectedTools: Set<String> = ["vault_read", "files_read", "web_search", "mcp/mock-mcp/mac_notes_read"]

    public init(client: StewardClient) {
        self.client = client
    }

    private let availableTools = [
        ("vault_read", "Memory Vault"),
        ("files_read", "Personal Notes"),
        ("web_search", "Web Lookup"),
        ("report_read", "Research Reports"),
        ("nexus_search", "Nexus Library"),
        ("mcp/mock-mcp/mac_notes_read", "Mac Notes (MCP)"),
    ]

    public var body: some View {
        VStack(spacing: 0) {
            topBar
            Divider().background(AppTheme.border)

            if client.goals.isEmpty {
                emptyView
            } else {
                ScrollView {
                    LazyVStack(spacing: 14) {
                        ForEach(client.goals) { goal in
                            goalCard(goal)
                        }
                    }
                    .padding(20)
                }
            }
        }
        .background(AppTheme.windowBackground)
        .sheet(isPresented: $showingAddSheet) {
            addWatchSheet
        }
    }

    private var topBar: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("Standing Watches")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(AppTheme.textPrimary)
                Text("\(client.goals.count) goals registered on always-on host")
                    .font(.system(size: 11))
                    .foregroundColor(AppTheme.textSecondary)
            }

            Spacer()

            Button(action: { showingAddSheet = true }) {
                HStack(spacing: 4) {
                    Image(systemName: "plus")
                    Text("Add Watch")
                }
                .font(.system(size: 12, weight: .semibold))
            }
            .buttonStyle(.plain)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(Color(red: 0.0, green: 0.8, blue: 0.6))
            .foregroundColor(.black)
            .cornerRadius(6)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 14)
        .background(AppTheme.headerBackground)
    }

    private var emptyView: some View {
        VStack(spacing: 14) {
            Spacer()
            Image(systemName: "shield.slash")
                .font(.system(size: 40))
                .foregroundColor(AppTheme.textSecondary)
            Text("No Standing Watches")
                .font(.system(size: 16, weight: .bold))
                .foregroundColor(AppTheme.textPrimary)
            Text("Hand a standing watch to Steward in conversation or click Add Watch above.")
                .font(.system(size: 12))
                .foregroundColor(AppTheme.textSecondary)
            Spacer()
        }
    }

    private func goalCard(_ goal: Goal) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(goal.title)
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(AppTheme.textPrimary)

                    HStack(spacing: 8) {
                        Text(goal.rhythm.uppercased())
                            .font(.system(size: 9, weight: .bold))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(AppTheme.tagBackground)
                            .foregroundColor(AppTheme.tagText)
                            .cornerRadius(4)

                        Text(goal.isActive ? "ACTIVE" : "PAUSED")
                            .font(.system(size: 9, weight: .bold))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(goal.isActive ? Color(red: 0.0, green: 0.5, blue: 0.35) : AppTheme.tagBackground)
                            .foregroundColor(goal.isActive ? Color(red: 0.0, green: 1.0, blue: 0.7) : AppTheme.textSecondary)
                            .cornerRadius(4)

                        Text("Last wake: \(goal.formattedWake)")
                            .font(.system(size: 11))
                            .foregroundColor(AppTheme.textSecondary)
                    }
                }

                Spacer()

                HStack(spacing: 8) {
                    Button(action: {
                        Task {
                            if goal.isActive {
                                _ = await client.pauseGoal(id: goal.id)
                            } else {
                                _ = await client.resumeGoal(id: goal.id)
                            }
                        }
                    }) {
                        Text(goal.isActive ? "Pause" : "Resume")
                            .font(.system(size: 11, weight: .medium))
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(AppTheme.tagBackground)
                            .foregroundColor(AppTheme.textPrimary)
                            .cornerRadius(5)
                    }
                    .buttonStyle(.plain)

                    Button(action: {
                        Task { _ = await client.wakeGoal(id: goal.id) }
                    }) {
                        HStack(spacing: 4) {
                            Image(systemName: "bolt.fill")
                            Text("Wake Now")
                        }
                        .font(.system(size: 11, weight: .semibold))
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(Color(red: 0.12, green: 0.32, blue: 0.58))
                        .foregroundColor(.white)
                        .cornerRadius(5)
                    }
                    .buttonStyle(.plain)
                }
            }

            // Allowed tools chips
            if let tools = goal.see_tools, !tools.isEmpty {
                HStack(spacing: 6) {
                    Text("May read:")
                        .font(.system(size: 10))
                        .foregroundColor(AppTheme.textSecondary)
                    ForEach(tools, id: \.self) { tool in
                        Text(tool.replacingOccurrences(of: "mcp/mock-mcp/", with: "🔌 "))
                            .font(.system(size: 10))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(AppTheme.tagBackground)
                            .cornerRadius(4)
                            .foregroundColor(AppTheme.tagText)
                    }
                }
            }

            // Last note box
            if let note = goal.last_note, !note.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("LATEST OBSERVATION:")
                        .font(.system(size: 9, weight: .bold))
                        .foregroundColor(AppTheme.sectionHeader)
                    Text(note)
                        .font(.system(size: 12))
                        .foregroundColor(AppTheme.textPrimary)
                        .lineSpacing(2)
                }
                .padding(10)
                .background(AppTheme.cardBackgroundSecondary)
                .cornerRadius(6)
            }
        }
        .padding(16)
        .background(AppTheme.cardBackground)
        .cornerRadius(10)
        .overlay(RoundedRectangle(cornerRadius: 10).stroke(AppTheme.border, lineWidth: 1))
    }

    private var addWatchSheet: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Create Standing Watch")
                .font(.system(size: 16, weight: .bold))
                .foregroundColor(AppTheme.textPrimary)

            VStack(alignment: .leading, spacing: 6) {
                Text("Responsibility:")
                    .font(.system(size: 12))
                    .foregroundColor(AppTheme.textSecondary)
                TextField("e.g. Watch classroom notes and summarize daily updates", text: $newTitle)
                    .textFieldStyle(.plain)
                    .padding(8)
                    .background(AppTheme.inputBackground)
                    .cornerRadius(6)
                    .overlay(RoundedRectangle(cornerRadius: 6).stroke(AppTheme.border, lineWidth: 1))
                    .foregroundColor(AppTheme.textPrimary)
            }

            VStack(alignment: .leading, spacing: 6) {
                Text("Wake Rhythm:")
                    .font(.system(size: 12))
                    .foregroundColor(AppTheme.textSecondary)
                Picker("", selection: $newRhythm) {
                    Text("Hourly").tag("hourly")
                    Text("Daily").tag("daily")
                    Text("Manual").tag("manual")
                }
                .pickerStyle(.segmented)
            }

            VStack(alignment: .leading, spacing: 6) {
                Text("Allowed Read Sources (See Class):")
                    .font(.system(size: 12))
                    .foregroundColor(AppTheme.textSecondary)
                ForEach(availableTools, id: \.0) { tool in
                    Toggle(tool.1, isOn: Binding(
                        get: { selectedTools.contains(tool.0) },
                        set: { if $0 { selectedTools.insert(tool.0) } else { selectedTools.remove(tool.0) } }
                    ))
                    .toggleStyle(.checkbox)
                    .font(.system(size: 12))
                    .foregroundColor(AppTheme.textPrimary)
                }
            }

            HStack {
                Button("Cancel") { showingAddSheet = false }
                    .buttonStyle(.plain)
                    .foregroundColor(AppTheme.textSecondary)

                Spacer()

                Button("Save Watch") {
                    let title = newTitle
                    let rhythm = newRhythm
                    let tools = Array(selectedTools)
                    Task {
                        let ok = await client.createGoal(title: title, rhythm: rhythm, seeTools: tools)
                        if ok {
                            newTitle = ""
                            showingAddSheet = false
                        }
                    }
                }
                .buttonStyle(.plain)
                .padding(.horizontal, 14)
                .padding(.vertical, 6)
                .background(Color(red: 0.0, green: 0.8, blue: 0.6))
                .foregroundColor(.black)
                .cornerRadius(6)
                .disabled(newTitle.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
            .padding(.top, 10)
        }
        .padding(24)
        .frame(width: 440)
        .background(AppTheme.cardBackground)
    }
}
