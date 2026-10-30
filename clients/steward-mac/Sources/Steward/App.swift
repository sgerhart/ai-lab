import SwiftUI

@main
struct StewardApp: App {
    @StateObject private var client = StewardClient()

    var body: some Scene {
        WindowGroup("Steward Desk") {
            MainDeskView(client: client)
                .frame(minWidth: 960, idealWidth: 1120, minHeight: 620, idealHeight: 740)
                .preferredColorScheme(client.appearanceMode.colorScheme)
        }
        .windowStyle(.titleBar)
        .windowToolbarStyle(.unified)
        .commands {
            SidebarCommands()
            CommandGroup(replacing: .newItem) {
                Button("New Conversation") {
                    Task { _ = await client.createNewConversation() }
                }
                .keyboardShortcut("n", modifiers: .command)
            }
            CommandMenu("Appearance") {
                Button("Follow System") { client.appearanceMode = .system }
                Button("Light Mode") { client.appearanceMode = .light }
                Button("Dark Mode") { client.appearanceMode = .dark }
            }
        }

        // Minimalist compact Menu Bar presence indicator (single SF Symbol, no text pill)
        MenuBarExtra {
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 6) {
                    Circle()
                        .fill(menuBarTint)
                        .frame(width: 8, height: 8)
                    Text("Steward: \(client.presence.shortLabel)")
                        .font(.system(size: 13, weight: .bold))
                }
                Text("\(client.goals.filter { $0.isActive }.count) active standing watches")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)

                Divider()

                Button("Open Steward Desk Window") {
                    NSApp.activate(ignoringOtherApps: true)
                    for window in NSApp.windows {
                        window.makeKeyAndOrderFront(nil)
                    }
                }
                .keyboardShortcut("o", modifiers: .command)

                Button("Wake All Active Goals") {
                    for goal in client.goals where goal.isActive {
                        Task { _ = await client.wakeGoal(id: goal.id) }
                    }
                }

                Divider()

                Button("Quit Steward") {
                    NSApplication.shared.terminate(nil)
                }
                .keyboardShortcut("q", modifiers: .command)
            }
        } label: {
            Image(systemName: "sparkles")
                .symbolRenderingMode(.palette)
                .foregroundStyle(menuBarTint)
        }
    }

    private var menuBarTint: Color {
        switch client.presence {
        case .quiet: return Color(red: 0.0, green: 0.9, blue: 0.7)
        case .active: return Color(red: 0.22, green: 0.74, blue: 0.97)
        case .paused: return Color(white: 0.6)
        case .offline: return Color(red: 0.95, green: 0.45, blue: 0.35)
        }
    }
}
