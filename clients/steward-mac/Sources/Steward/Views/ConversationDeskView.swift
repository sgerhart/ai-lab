import SwiftUI

public struct ConversationDeskView: View {
    @ObservedObject var client: StewardClient
    @State private var inputText: String = ""
    @FocusState private var isInputFocused: Bool

    public init(client: StewardClient) {
        self.client = client
    }

    public var body: some View {
        VStack(spacing: 0) {
            topBar
            Divider().background(AppTheme.border)

            if client.messages.isEmpty {
                emptyState
            } else {
                messageList
            }

            if client.isThinking {
                thinkingBanner
            }

            composerBar
        }
        .background(AppTheme.windowBackground)
    }

    // MARK: - Top Bar
    private var topBar: some View {
        HStack(spacing: 12) {
            HStack(spacing: 8) {
                Circle()
                    .fill(dotColor)
                    .frame(width: 9, height: 9)
                    .shadow(color: dotColor.opacity(0.8), radius: 3)
                VStack(alignment: .leading, spacing: 1) {
                    Text(currentConversationTitle)
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(AppTheme.textPrimary)
                    Text(client.presence.label)
                        .font(.system(size: 10))
                        .foregroundColor(AppTheme.textSecondary)
                }
            }

            Spacer()

            HStack(spacing: 8) {
                // Active watches badge
                HStack(spacing: 5) {
                    Image(systemName: "shield.fill")
                        .font(.system(size: 10))
                        .foregroundColor(AppTheme.accentTeal)
                    Text("\(client.goals.filter { $0.isActive }.count) active watches")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(AppTheme.textPrimary)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(AppTheme.tagBackground)
                .cornerRadius(12)

                Button(action: {
                    Task { _ = await client.createNewConversation() }
                }) {
                    HStack(spacing: 4) {
                        Image(systemName: "plus")
                        Text("New Chat")
                    }
                    .font(.system(size: 11, weight: .semibold))
                }
                .buttonStyle(.plain)
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(AppTheme.tagBackground)
                .foregroundColor(AppTheme.accentBlue)
                .cornerRadius(6)
            }
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 12)
        .background(AppTheme.headerBackground)
    }

    // MARK: - Empty State
    private var emptyState: some View {
        ScrollView {
            VStack(spacing: 20) {
                Spacer(minLength: 40)

                VStack(spacing: 10) {
                    ZStack {
                        Circle()
                            .fill(AppTheme.accentTeal.opacity(0.12))
                            .frame(width: 64, height: 64)
                        Image(systemName: "brain.head.profile")
                            .font(.system(size: 28))
                            .foregroundColor(AppTheme.accentTeal)
                    }

                    Text("Steward Companion Desk")
                        .font(.system(size: 18, weight: .bold))
                        .foregroundColor(AppTheme.textPrimary)

                    Text("Your personal agent is ready. Talk through ideas, explore memory,\nor hand off standing responsibilities.")
                        .font(.system(size: 13))
                        .foregroundColor(AppTheme.textSecondary)
                        .multilineTextAlignment(.center)
                        .frame(maxWidth: 440)
                }

                VStack(alignment: .leading, spacing: 10) {
                    Text("TRY ASKING OR HANDING OFF:")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(AppTheme.sectionHeader)
                        .tracking(1.0)

                    suggestionButton(
                        icon: "eye.fill",
                        title: "Keep watch on classroom notes daily",
                        subtitle: "Creates a standing goal to inspect classroom notes and report updates"
                    )

                    suggestionButton(
                        icon: "clock.arrow.circlepath",
                        title: "What did you observe in your latest wake?",
                        subtitle: "Summarizes observations from background wakes and vault entries"
                    )

                    suggestionButton(
                        icon: "magnifyingglass",
                        title: "Search local notes and vault for recent ideas",
                        subtitle: "Reads both local Mac markdown files and remote memory vault"
                    )
                }
                .frame(maxWidth: 500)
                .padding(.top, 12)

                Spacer()
            }
            .padding(.horizontal, 24)
        }
    }

    private func suggestionButton(icon: String, title: String, subtitle: String) -> some View {
        Button(action: {
            inputText = title
            isInputFocused = true
        }) {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .font(.system(size: 14))
                    .foregroundColor(AppTheme.accentBlue)
                    .frame(width: 28, height: 28)
                    .background(AppTheme.tagBackground)
                    .cornerRadius(6)

                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(AppTheme.textPrimary)
                    Text(subtitle)
                        .font(.system(size: 11))
                        .foregroundColor(AppTheme.textSecondary)
                }

                Spacer()
                Image(systemName: "arrow.up.right")
                    .font(.system(size: 11))
                    .foregroundColor(AppTheme.textSecondary)
            }
            .padding(12)
            .background(AppTheme.cardBackground)
            .cornerRadius(8)
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(AppTheme.border, lineWidth: 1))
        }
        .buttonStyle(.plain)
    }

    // MARK: - Message List
    private var messageList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 16) {
                    ForEach(client.messages) { msg in
                        messageRow(msg)
                            .id(msg.id)
                    }
                }
                .padding(18)
            }
            .onChange(of: client.messages.count) { _, _ in
                if let last = client.messages.last {
                    withAnimation {
                        proxy.scrollTo(last.id, anchor: .bottom)
                    }
                }
            }
        }
    }

    private func messageRow(_ msg: ChatMessage) -> some View {
        HStack(alignment: .top, spacing: 10) {
            if msg.isUser {
                Spacer(minLength: 40)
                VStack(alignment: .trailing, spacing: 4) {
                    Text(msg.content)
                        .font(.system(size: 13))
                        .foregroundColor(.white)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 10)
                        .background(AppTheme.userBubbleBackground)
                        .cornerRadius(14)
                }
            } else {
                // Steward Assistant Bubble
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 6) {
                        Image(systemName: "shield.lefthalf.filled")
                            .font(.system(size: 11))
                            .foregroundColor(AppTheme.accentTeal)
                        Text("Steward")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(AppTheme.accentTeal)
                    }

                    Text(msg.content)
                        .font(.system(size: 13))
                        .foregroundColor(AppTheme.textPrimary)
                        .lineSpacing(3)
                        .textSelection(.enabled)

                    // Quick inline action if response mentions watching
                    if msg.content.lowercased().contains("watch") || msg.content.lowercased().contains("goal") {
                        HStack {
                            Button(action: {
                                Task {
                                    _ = await client.createGoal(
                                        title: "Watch: \(msg.content.prefix(40))",
                                        rhythm: "daily",
                                        seeTools: ["vault_read", "files_read", "web_search"]
                                    )
                                }
                            }) {
                                HStack(spacing: 4) {
                                    Image(systemName: "plus.circle")
                                    Text("Add to Standing Watches")
                                }
                                .font(.system(size: 10, weight: .semibold))
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(AppTheme.tagBackground)
                                .foregroundColor(AppTheme.accentTeal)
                                .cornerRadius(5)
                            }
                            .buttonStyle(.plain)
                            Spacer()
                        }
                        .padding(.top, 4)
                    }
                }
                .padding(14)
                .background(AppTheme.cardBackground)
                .cornerRadius(12)
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(AppTheme.border, lineWidth: 1))
                .frame(maxWidth: 680, alignment: .leading)

                Spacer(minLength: 40)
            }
        }
    }

    // MARK: - Thinking Banner
    private var thinkingBanner: some View {
        HStack(spacing: 8) {
            ProgressView()
                .scaleEffect(0.6)
            Text("Steward is reviewing memory vault and running tools...")
                .font(.system(size: 11))
                .foregroundColor(AppTheme.accentBlue)
            Spacer()
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 6)
        .background(AppTheme.headerBackground)
    }

    // MARK: - Composer Bar
    private var composerBar: some View {
        VStack(spacing: 8) {
            HStack(spacing: 10) {
                TextField("Talk to Steward or hand off a responsibility...", text: $inputText, axis: .vertical)
                    .lineLimit(1...5)
                    .textFieldStyle(.plain)
                    .font(.system(size: 13))
                    .foregroundColor(AppTheme.textPrimary)
                    .focused($isInputFocused)
                    .onSubmit {
                        submitText()
                    }

                Button(action: submitText) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 26))
                        .foregroundColor(
                            inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || client.isThinking
                            ? Color(white: 0.5)
                            : AppTheme.accentTeal
                        )
                }
                .buttonStyle(.plain)
                .disabled(inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || client.isThinking)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(AppTheme.inputBackground)
            .cornerRadius(12)
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(AppTheme.border, lineWidth: 1))
        }
        .padding(14)
        .background(AppTheme.headerBackground)
    }

    private func submitText() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !client.isThinking else { return }
        inputText = ""
        Task {
            await client.sendMessage(text: text)
        }
    }

    private var currentConversationTitle: String {
        guard let cid = client.activeConversationId,
              let conv = client.conversations.first(where: { $0.id == cid }) else {
            return "Steward Desk"
        }
        return conv.displayTitle
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
