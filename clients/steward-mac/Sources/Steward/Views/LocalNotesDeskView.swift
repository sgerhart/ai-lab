import SwiftUI

public struct LocalNotesDeskView: View {
    @ObservedObject var client: StewardClient
    @State private var searchFilter: String = ""
    @State private var selectedNote: LocalNote?
    @State private var noteContent: String = ""

    public init(client: StewardClient) {
        self.client = client
    }

    private var filteredNotes: [LocalNote] {
        if searchFilter.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return client.localNotes
        }
        return client.localNotes.filter {
            $0.name.localizedCaseInsensitiveContains(searchFilter) ||
            $0.path.localizedCaseInsensitiveContains(searchFilter)
        }
    }

    public var body: some View {
        VStack(spacing: 0) {
            topBar
            Divider().background(AppTheme.border)

            HStack(spacing: 0) {
                // Left pane: Note list & System Status
                VStack(spacing: 12) {
                    if let status = client.localStatus {
                        systemStatusCard(status)
                    }

                    TextField("Search local notes...", text: $searchFilter)
                        .textFieldStyle(.plain)
                        .padding(8)
                        .background(AppTheme.inputBackground)
                        .cornerRadius(6)
                        .overlay(RoundedRectangle(cornerRadius: 6).stroke(AppTheme.border, lineWidth: 1))
                        .foregroundColor(AppTheme.textPrimary)
                        .padding(.horizontal, 14)

                    List(filteredNotes, id: \.self, selection: $selectedNote) { note in
                        VStack(alignment: .leading, spacing: 3) {
                            Text(note.name)
                                .font(.system(size: 13, weight: .semibold))
                                .foregroundColor(AppTheme.textPrimary)
                            HStack {
                                Text(note.path)
                                    .font(.system(size: 10))
                                    .foregroundColor(AppTheme.textSecondary)
                                Spacer()
                                Text(formatBytes(note.sizeBytes))
                                    .font(.system(size: 10))
                                    .foregroundColor(AppTheme.textSecondary)
                            }
                        }
                        .padding(.vertical, 4)
                        .tag(note)
                    }
                    .listStyle(.plain)
                }
                .frame(width: 320)
                .background(AppTheme.sidebarBackground)

                Divider().background(AppTheme.border)

                // Right pane: Note Content Preview
                VStack(alignment: .leading, spacing: 10) {
                    if let note = selectedNote {
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(note.name)
                                    .font(.system(size: 15, weight: .bold))
                                    .foregroundColor(AppTheme.textPrimary)
                                Text(note.path)
                                    .font(.system(size: 11))
                                    .foregroundColor(AppTheme.textSecondary)
                            }
                            Spacer()
                            Button("Copy Path") {
                                NSPasteboard.general.clearContents()
                                NSPasteboard.general.setString(note.path, forType: .string)
                            }
                            .buttonStyle(.plain)
                            .font(.system(size: 11))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(AppTheme.tagBackground)
                            .foregroundColor(AppTheme.textPrimary)
                            .cornerRadius(4)
                        }
                        .padding(.horizontal, 16)
                        .padding(.top, 14)

                        Divider().background(AppTheme.border)

                        ScrollView {
                            Text(noteContent)
                                .font(.system(size: 12, design: .monospaced))
                                .foregroundColor(AppTheme.textPrimary)
                                .lineSpacing(3)
                                .padding(16)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    } else {
                        VStack(spacing: 10) {
                            Spacer()
                            Image(systemName: "doc.text")
                                .font(.system(size: 32))
                                .foregroundColor(AppTheme.textSecondary)
                            Text("Select a local note to preview")
                                .font(.system(size: 13))
                                .foregroundColor(AppTheme.textSecondary)
                            Spacer()
                        }
                        .frame(maxWidth: .infinity)
                    }
                }
                .background(AppTheme.windowBackground)
            }
        }
        .onChange(of: selectedNote) { _, newValue in
            if let note = newValue {
                loadNoteContent(note: note)
            }
        }
        .onAppear {
            client.scanLocalEnvironment()
        }
    }

    private var topBar: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("Mac Local Sources & Bridge")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(AppTheme.textPrimary)
                Text("Local personal notes inspected by Steward via governed MCP bridge")
                    .font(.system(size: 11))
                    .foregroundColor(AppTheme.textSecondary)
            }
            Spacer()
            Button(action: { client.scanLocalEnvironment() }) {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 12))
                    .foregroundColor(AppTheme.textSecondary)
            }
            .buttonStyle(.plain)
            .padding(6)
            .background(AppTheme.tagBackground)
            .cornerRadius(6)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 14)
        .background(AppTheme.headerBackground)
    }

    private func systemStatusCard(_ status: SystemState) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("MAC HARDWARE STATUS")
                    .font(.system(size: 9, weight: .bold))
                    .foregroundColor(AppTheme.accentBlue)
                Spacer()
                Text(status.hostname)
                    .font(.system(size: 10))
                    .foregroundColor(AppTheme.textSecondary)
            }
            Text(status.batteryInfo)
                .font(.system(size: 11))
                .foregroundColor(AppTheme.textPrimary)
            Text(status.powerSource)
                .font(.system(size: 10))
                .foregroundColor(AppTheme.textSecondary)
        }
        .padding(10)
        .background(AppTheme.cardBackground)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(AppTheme.border, lineWidth: 1))
        .padding(.horizontal, 14)
        .padding(.top, 10)
    }

    private func loadNoteContent(note: LocalNote) {
        guard let status = client.localStatus else { return }
        let fullPath = URL(fileURLWithPath: status.notesPath).appendingPathComponent(note.path)
        if let data = try? Data(contentsOf: fullPath), let str = String(data: data, encoding: .utf8) {
            self.noteContent = str
        } else {
            self.noteContent = "(Unable to read note file)"
        }
    }

    private func formatBytes(_ bytes: Int64) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: bytes)
    }
}
