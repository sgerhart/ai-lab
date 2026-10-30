import SwiftUI

public enum NavigationSection: Hashable {
    case chat(id: String)
    case watches
    case activity
    case localNotes
}

public struct MainDeskView: View {
    @ObservedObject var client: StewardClient
    @State private var selectedSection: NavigationSection = .watches
    @State private var showingSettings: Bool = false

    public init(client: StewardClient) {
        self.client = client
    }

    public var body: some View {
        NavigationSplitView {
            sidebarContent
                .navigationSplitViewColumnWidth(min: 220, ideal: 260, max: 320)
        } detail: {
            detailContent
                .background(AppTheme.windowBackground)
        }
        .sheet(isPresented: $showingSettings) {
            SettingsView(client: client)
        }
        .onAppear {
            if let cid = client.activeConversationId {
                selectedSection = .chat(id: cid)
            } else if !client.conversations.isEmpty {
                let first = client.conversations[0]
                selectedSection = .chat(id: first.id)
            }
        }
    }

    // MARK: - Sidebar
    private var sidebarContent: some View {
        VStack(spacing: 0) {
            // Sidebar Header
            HStack(spacing: 8) {
                Circle()
                    .fill(dotColor)
                    .frame(width: 9, height: 9)
                    .shadow(color: dotColor.opacity(0.8), radius: 3)

                Text("STEWARD")
                    .font(.system(size: 13, weight: .black, design: .rounded))
                    .foregroundColor(AppTheme.textPrimary)
                    .tracking(1.5)

                Spacer()

                Button(action: { Task { await client.syncAll() } }) {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(AppTheme.textSecondary)
                }
                .buttonStyle(.plain)
                .help("Refresh state")
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
            .background(AppTheme.headerBackground)

            Divider().background(AppTheme.border)

            // Navigation List
            List(selection: $selectedSection) {
                // Section: Standing Life
                Section(header: Text("STANDING LIFE")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(AppTheme.sectionHeader)
                    .tracking(0.8)
                ) {
                    NavigationLink(value: NavigationSection.watches) {
                        HStack(spacing: 8) {
                            Image(systemName: "shield.fill")
                                .font(.system(size: 13))
                                .foregroundColor(AppTheme.accentTeal)
                            Text("Standing Watches")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(AppTheme.textPrimary)
                            Spacer()
                            let activeCount = client.goals.filter { $0.isActive }.count
                            if activeCount > 0 {
                                Text("\(activeCount)")
                                    .font(.system(size: 10, weight: .bold))
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 1)
                                    .background(Color(red: 0.0, green: 0.5, blue: 0.35))
                                    .foregroundColor(Color(red: 0.0, green: 1.0, blue: 0.7))
                                    .cornerRadius(8)
                            }
                        }
                    }

                    NavigationLink(value: NavigationSection.activity) {
                        HStack(spacing: 8) {
                            Image(systemName: "clock.arrow.circlepath")
                                .font(.system(size: 13))
                                .foregroundColor(AppTheme.accentBlue)
                            Text("Activity Timeline")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(AppTheme.textPrimary)
                            Spacer()
                            if !client.activity.isEmpty {
                                Text("\(client.activity.count)")
                                    .font(.system(size: 10, weight: .semibold))
                                    .padding(.horizontal, 5)
                                    .padding(.vertical, 1)
                                    .background(AppTheme.tagBackground)
                                    .foregroundColor(AppTheme.tagText)
                                    .cornerRadius(6)
                            }
                        }
                    }
                }

                // Section: Conversational Desk
                Section(header:
                    HStack {
                        Text("COMPANION DESK")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(AppTheme.sectionHeader)
                            .tracking(0.8)
                        Spacer()
                        Button(action: {
                            Task {
                                if let newId = await client.createNewConversation() {
                                    selectedSection = .chat(id: newId)
                                }
                            }
                        }) {
                            Image(systemName: "plus")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(AppTheme.accentBlue)
                        }
                        .buttonStyle(.plain)
                        .help("New Conversation")
                    }
                ) {
                    if client.conversations.isEmpty {
                        Text("No conversations yet.")
                            .font(.system(size: 12))
                            .foregroundColor(AppTheme.textSecondary)
                            .padding(.vertical, 2)
                    } else {
                        ForEach(client.conversations) { conv in
                            NavigationLink(value: NavigationSection.chat(id: conv.id)) {
                                HStack(spacing: 8) {
                                    Image(systemName: "bubble.left.and.bubble.right.fill")
                                        .font(.system(size: 12))
                                        .foregroundColor(AppTheme.accentBlue)
                                    Text(conv.displayTitle)
                                        .font(.system(size: 13, weight: .regular))
                                        .foregroundColor(AppTheme.textPrimary)
                                        .lineLimit(1)
                                }
                            }
                            .contextMenu {
                                Button("Delete Conversation", role: .destructive) {
                                    Task { await client.deleteConversation(id: conv.id) }
                                }
                            }
                        }
                    }
                }

                // Section: Local Mac
                Section(header: Text("LOCAL MAC CONTEXT")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(AppTheme.sectionHeader)
                    .tracking(0.8)
                ) {
                    NavigationLink(value: NavigationSection.localNotes) {
                        HStack(spacing: 8) {
                            Image(systemName: "laptopcomputer")
                                .font(.system(size: 13))
                                .foregroundColor(AppTheme.textSecondary)
                            Text("Mac Notes & Hardware")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(AppTheme.textPrimary)
                            Spacer()
                            if !client.localNotes.isEmpty {
                                Text("\(client.localNotes.count)")
                                    .font(.system(size: 10, weight: .semibold))
                                    .padding(.horizontal, 5)
                                    .padding(.vertical, 1)
                                    .background(AppTheme.tagBackground)
                                    .foregroundColor(AppTheme.tagText)
                                    .cornerRadius(6)
                            }
                        }
                    }
                }
            }
            .listStyle(.sidebar)
            .background(AppTheme.sidebarBackground)

            Divider().background(AppTheme.border)

            // Sidebar Footer: Status, Theme Picker & Settings
            sidebarFooter
        }
        .background(AppTheme.sidebarBackground)
    }

    private var sidebarFooter: some View {
        VStack(spacing: 8) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: 5) {
                        Circle()
                            .fill(client.isConnected ? Color(red: 0.0, green: 0.9, blue: 0.7) : Color(red: 0.95, green: 0.45, blue: 0.35))
                            .frame(width: 7, height: 7)
                        Text(client.isConnected ? "Connected" : "Offline")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(client.isConnected ? AppTheme.accentTeal : Color(red: 0.95, green: 0.45, blue: 0.35))
                    }
                    Text(URL(string: client.hostURL)?.host ?? "control-plane")
                        .font(.system(size: 10))
                        .foregroundColor(AppTheme.textSecondary)
                }

                Spacer()

                // Theme switcher: System, Light, Dark
                HStack(spacing: 4) {
                    ForEach(AppAppearance.allCases) { mode in
                        Button(action: { client.appearanceMode = mode }) {
                            Image(systemName: mode.icon)
                                .font(.system(size: 11))
                                .foregroundColor(client.appearanceMode == mode ? AppTheme.accentBlue : AppTheme.textSecondary)
                                .frame(width: 22, height: 22)
                                .background(client.appearanceMode == mode ? AppTheme.tagBackground : Color.clear)
                                .cornerRadius(4)
                        }
                        .buttonStyle(.plain)
                        .help("Switch appearance to \(mode.label)")
                    }
                }
                .padding(2)
                .background(AppTheme.cardBackgroundSecondary)
                .cornerRadius(6)

                Button(action: openFullDesk) {
                    Image(systemName: "arrow.up.right.square")
                        .font(.system(size: 13))
                        .foregroundColor(AppTheme.textSecondary)
                }
                .buttonStyle(.plain)
                .help("Open Web Desk in Browser")

                Button(action: { showingSettings = true }) {
                    Image(systemName: "gearshape")
                        .font(.system(size: 13))
                        .foregroundColor(AppTheme.textSecondary)
                }
                .buttonStyle(.plain)
                .help("Settings")
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background(AppTheme.headerBackground)
    }

    // MARK: - Detail Content
    @ViewBuilder
    private var detailContent: some View {
        switch selectedSection {
        case .chat(let id):
            ConversationDeskView(client: client)
                .onAppear {
                    Task { await client.selectConversation(id: id) }
                }
        case .watches:
            StandingWatchesView(client: client)
        case .activity:
            ActivityTimelineView(client: client)
        case .localNotes:
            LocalNotesDeskView(client: client)
        }
    }

    private func openFullDesk() {
        guard let base = URL(string: client.hostURL) else { return }
        let url = base.appendingPathComponent("").appending(queryItems: [URLQueryItem(name: "open", value: "steward")])
        NSWorkspace.shared.open(url)
    }

    private var dotColor: Color {
        switch client.presence {
        case .quiet: return Color(red: 0.0, green: 0.9, blue: 0.7)
        case .active: return Color(red: 0.22, green: 0.74, blue: 0.97)
        case .paused: return Color(white: 0.6)
        case .offline: return Color(red: 0.95, green: 0.45, blue: 0.35)
        }
    }
}
