import SwiftUI

public struct SettingsView: View {
    @ObservedObject var client: StewardClient
    @Environment(\.dismiss) private var dismiss

    @State private var tempHost: String = ""
    @State private var tempToken: String = ""
    @State private var testStatus: String? = nil

    public init(client: StewardClient) {
        self.client = client
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            HStack {
                Text("Steward Connection Settings")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(AppTheme.textPrimary)
                Spacer()
                Button("Done") {
                    saveAndClose()
                }
                .font(.system(size: 12, weight: .semibold))
                .buttonStyle(.plain)
                .padding(.horizontal, 14)
                .padding(.vertical, 6)
                .background(Color(red: 0.0, green: 0.8, blue: 0.6))
                .foregroundColor(.black)
                .cornerRadius(6)
            }

            // Appearance Mode Selector
            VStack(alignment: .leading, spacing: 8) {
                Text("APPEARANCE THEME")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(AppTheme.accentBlue)

                Picker("", selection: $client.appearanceMode) {
                    ForEach(AppAppearance.allCases) { mode in
                        HStack {
                            Image(systemName: mode.icon)
                            Text(mode.label)
                        }
                        .tag(mode)
                    }
                }
                .pickerStyle(.segmented)
            }

            VStack(alignment: .leading, spacing: 10) {
                Text("CONTROL PLANE HOST")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(AppTheme.accentBlue)

                TextField("http://mac-mini:8088", text: $tempHost)
                    .textFieldStyle(.plain)
                    .padding(8)
                    .background(AppTheme.inputBackground)
                    .cornerRadius(6)
                    .overlay(RoundedRectangle(cornerRadius: 6).stroke(AppTheme.border, lineWidth: 1))
                    .foregroundColor(AppTheme.textPrimary)

                HStack(spacing: 8) {
                    Button("Preset: Mac Mini (Lab Always-On)") {
                        tempHost = "http://mac-mini:8088"
                    }
                    .font(.system(size: 11))
                    .buttonStyle(.plain)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(AppTheme.tagBackground)
                    .foregroundColor(AppTheme.textPrimary)
                    .cornerRadius(4)

                    Button("Preset: Localhost (127.0.0.1:8088)") {
                        tempHost = "http://127.0.0.1:8088"
                    }
                    .font(.system(size: 11))
                    .buttonStyle(.plain)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(AppTheme.tagBackground)
                    .foregroundColor(AppTheme.textPrimary)
                    .cornerRadius(4)
                }
            }

            VStack(alignment: .leading, spacing: 8) {
                Text("API BEARER TOKEN")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(AppTheme.accentBlue)

                SecureField("Bearer token (or leave empty to auto-load from ~/.ai-lab/)", text: $tempToken)
                    .textFieldStyle(.plain)
                    .padding(8)
                    .background(AppTheme.inputBackground)
                    .cornerRadius(6)
                    .overlay(RoundedRectangle(cornerRadius: 6).stroke(AppTheme.border, lineWidth: 1))
                    .foregroundColor(AppTheme.textPrimary)

                Text("Automatically detects ~/.ai-lab/mac-mini-api.token and ~/.ai-lab/api.token if present.")
                    .font(.system(size: 10))
                    .foregroundColor(AppTheme.textSecondary)
            }

            HStack {
                Button("Test Connection Now") {
                    client.hostURL = tempHost
                    client.apiToken = tempToken
                    Task {
                        await client.syncAll()
                        if client.isConnected {
                            testStatus = "✅ Connected successfully to \(tempHost)!"
                        } else {
                            testStatus = "❌ Connection failed: \(client.errorMessage ?? "Unreachable")"
                        }
                    }
                }
                .font(.system(size: 12, weight: .medium))
                .buttonStyle(.plain)
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(AppTheme.tagBackground)
                .foregroundColor(AppTheme.accentBlue)
                .cornerRadius(6)

                Spacer()

                if let status = testStatus {
                    Text(status)
                        .font(.system(size: 11))
                        .foregroundColor(status.starts(with: "✅") ? AppTheme.accentTeal : Color(red: 0.95, green: 0.45, blue: 0.35))
                }
            }

            Spacer()
        }
        .padding(24)
        .frame(width: 480, height: 420)
        .background(AppTheme.cardBackground)
        .onAppear {
            tempHost = client.hostURL
            tempToken = client.apiToken
        }
    }

    private func saveAndClose() {
        client.hostURL = tempHost
        client.apiToken = tempToken
        Task {
            await client.syncAll()
        }
        dismiss()
    }
}
