import SwiftUI

public struct ActivityTimelineView: View {
    @ObservedObject var client: StewardClient

    public init(client: StewardClient) {
        self.client = client
    }

    public var body: some View {
        VStack(spacing: 0) {
            topBar
            Divider().background(AppTheme.border)

            if client.activity.isEmpty {
                emptyView
            } else {
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(client.activity) { act in
                            activityCard(act)
                        }
                    }
                    .padding(20)
                }
            }
        }
        .background(AppTheme.windowBackground)
    }

    private var topBar: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("Activity Timeline")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(AppTheme.textPrimary)
                Text("Observations and dossiers filed during unattended background wakes")
                    .font(.system(size: 11))
                    .foregroundColor(AppTheme.textSecondary)
            }
            Spacer()
            Button(action: { Task { await client.syncAll() } }) {
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

    private var emptyView: some View {
        VStack(spacing: 14) {
            Spacer()
            Image(systemName: "clock.badge.questionmark")
                .font(.system(size: 40))
                .foregroundColor(AppTheme.textSecondary)
            Text("No Wakes Recorded Yet")
                .font(.system(size: 16, weight: .bold))
                .foregroundColor(AppTheme.textPrimary)
            Text("When Steward wakes on rhythm or via Wake Now, observations will appear here.")
                .font(.system(size: 12))
                .foregroundColor(AppTheme.textSecondary)
            Spacer()
        }
    }

    private func activityCard(_ act: ActivityEntry) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                HStack(spacing: 6) {
                    Circle()
                        .fill(AppTheme.accentBlue)
                        .frame(width: 7, height: 7)
                    Text(act.goal_title ?? "Wake Run")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(AppTheme.textPrimary)
                }
                Spacer()
                Text(act.formattedTime)
                    .font(.system(size: 11))
                    .foregroundColor(AppTheme.textSecondary)
            }

            if let tools = act.tools_called, !tools.isEmpty {
                HStack(spacing: 6) {
                    ForEach(tools, id: \.self) { tool in
                        Text("⚡ \(tool)")
                            .font(.system(size: 10))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(AppTheme.tagBackground)
                            .cornerRadius(4)
                            .foregroundColor(AppTheme.tagText)
                    }
                }
            }

            Text(act.displaySummary)
                .font(.system(size: 12))
                .foregroundColor(AppTheme.textPrimary)
                .lineSpacing(3)
                .padding(10)
                .background(AppTheme.cardBackgroundSecondary)
                .cornerRadius(6)
        }
        .padding(14)
        .background(AppTheme.cardBackground)
        .cornerRadius(10)
        .overlay(RoundedRectangle(cornerRadius: 10).stroke(AppTheme.border, lineWidth: 1))
    }
}
