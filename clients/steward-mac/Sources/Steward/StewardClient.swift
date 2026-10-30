import Foundation
import Combine
import SwiftUI

@MainActor
public class StewardClient: ObservableObject {
    @Published public var hostURL: String {
        didSet {
            UserDefaults.standard.set(hostURL, forKey: "steward_host_url")
        }
    }
    @Published public var apiToken: String {
        didSet {
            UserDefaults.standard.set(apiToken, forKey: "steward_api_token")
        }
    }
    @Published public var appearanceMode: AppAppearance {
        didSet {
            UserDefaults.standard.set(appearanceMode.rawValue, forKey: "steward_appearance_mode")
        }
    }
    @Published public var presence: StewardPresence = .offline
    @Published public var isConnected: Bool = false
    @Published public var conversations: [ConversationItem] = []
    @Published public var activeConversationId: String?
    @Published public var messages: [ChatMessage] = []
    @Published public var isThinking: Bool = false
    @Published public var goals: [Goal] = []
    @Published public var activity: [ActivityEntry] = []
    @Published public var localNotes: [LocalNote] = []
    @Published public var localStatus: SystemState?
    @Published public var errorMessage: String?
    @Published public var lastSyncTime: Date?

    private var pollTimer: Timer?

    public init() {
        let savedApp = UserDefaults.standard.string(forKey: "steward_appearance_mode") ?? AppAppearance.system.rawValue
        self.appearanceMode = AppAppearance(rawValue: savedApp) ?? .system

        let envHost = ProcessInfo.processInfo.environment["STEWARD_HOST"]
        let savedHost = UserDefaults.standard.string(forKey: "steward_host_url")
        self.hostURL = envHost ?? savedHost ?? "http://mac-mini:8088"

        let envToken = ProcessInfo.processInfo.environment["STEWARD_TOKEN"]
        let savedToken = UserDefaults.standard.string(forKey: "steward_api_token")
        var token = envToken ?? savedToken ?? ""

        if token.isEmpty {
            let home = FileManager.default.homeDirectoryForCurrentUser
            let t1 = home.appendingPathComponent(".ai-lab/mac-mini-api.token")
            let t2 = home.appendingPathComponent(".ai-lab/api.token")
            if let d = try? Data(contentsOf: t1), let s = String(data: d, encoding: .utf8) {
                token = s.trimmingCharacters(in: .whitespacesAndNewlines)
            } else if let d = try? Data(contentsOf: t2), let s = String(data: d, encoding: .utf8) {
                token = s.trimmingCharacters(in: .whitespacesAndNewlines)
            }
        }
        self.apiToken = token

        scanLocalEnvironment()
        startPeriodicSync()
    }

    public func startPeriodicSync() {
        pollTimer?.invalidate()
        Task { await syncAll() }
        pollTimer = Timer.scheduledTimer(withTimeInterval: 10.0, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                await self?.syncAll()
            }
        }
    }

    public func stopPeriodicSync() {
        pollTimer?.invalidate()
        pollTimer = nil
    }

    private func makeRequest(_ endpoint: String, method: String = "GET", body: Data? = nil) throws -> URLRequest {
        guard let base = URL(string: hostURL) else {
            throw URLError(.badURL)
        }
        let clean = endpoint.hasPrefix("/") ? String(endpoint.dropFirst()) : endpoint
        let url = base.appendingPathComponent(clean)
        var req = URLRequest(url: url)
        req.httpMethod = method
        req.timeoutInterval = 8.0
        if !apiToken.isEmpty {
            req.setValue("Bearer \(apiToken)", forHTTPHeaderField: "Authorization")
        }
        if let body = body {
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            req.httpBody = body
        }
        return req
    }

    public func syncAll() async {
        do {
            // 1. Health
            let hReq = try makeRequest("/health")
            let (_, hRes) = try await URLSession.shared.data(for: hReq)
            if let http = hRes as? HTTPURLResponse, (http.statusCode == 200 || http.statusCode == 401) {
                self.isConnected = true
            } else {
                self.isConnected = false
                self.presence = .offline
                return
            }

            // 2. Goals
            let gReq = try makeRequest("/v1/steward/goals")
            let (gData, gRes) = try await URLSession.shared.data(for: gReq)
            if let http = gRes as? HTTPURLResponse, http.statusCode == 200 {
                let dec = try JSONDecoder().decode(GoalsResponse.self, from: gData)
                self.goals = dec.goals
                let activeCount = dec.goals.filter { $0.isActive }.count
                if self.isThinking {
                    self.presence = .active
                } else if activeCount == 0 && !dec.goals.isEmpty {
                    self.presence = .paused
                } else {
                    self.presence = .quiet
                }
            }

            // 3. Activity
            let aReq = try makeRequest("/v1/steward/activity")
            let (aData, aRes) = try await URLSession.shared.data(for: aReq)
            if let http = aRes as? HTTPURLResponse, http.statusCode == 200 {
                let dec = try JSONDecoder().decode(ActivityResponse.self, from: aData)
                self.activity = dec.activity
            }

            // 4. Conversations
            await fetchConversations()

            self.lastSyncTime = Date()
            self.errorMessage = nil
        } catch {
            self.isConnected = false
            self.presence = .offline
            self.errorMessage = error.localizedDescription
        }
    }

    public func fetchConversations() async {
        do {
            let req = try makeRequest("/v1/conversations?limit=40")
            let (data, res) = try await URLSession.shared.data(for: req)
            if let http = res as? HTTPURLResponse, http.statusCode == 200 {
                let dec = try JSONDecoder().decode(ConversationsResponse.self, from: data)
                // Filter to personal agent conversations
                self.conversations = dec.conversations.filter { $0.agent == "personal" }

                if self.activeConversationId == nil && !self.conversations.isEmpty {
                    self.activeConversationId = self.conversations.first?.id
                    if let cid = self.activeConversationId {
                        await fetchMessages(conversationId: cid)
                    }
                }
            }
        } catch {
            // Ignore background error
        }
    }

    public func selectConversation(id: String) async {
        self.activeConversationId = id
        await fetchMessages(conversationId: id)
    }

    public func createNewConversation(title: String = "Steward Companion") async -> String? {
        do {
            let payload: [String: Any] = [
                "agent": "personal",
                "title": title
            ]
            let data = try JSONSerialization.data(withJSONObject: payload)
            let req = try makeRequest("/v1/conversations", method: "POST", body: data)
            let (resData, res) = try await URLSession.shared.data(for: req)
            if let http = res as? HTTPURLResponse, http.statusCode == 200 {
                let item = try JSONDecoder().decode(ConversationItem.self, from: resData)
                self.conversations.insert(item, at: 0)
                self.activeConversationId = item.id
                self.messages = []
                return item.id
            }
        } catch {
            self.errorMessage = error.localizedDescription
        }
        return nil
    }

    public func deleteConversation(id: String) async {
        do {
            let req = try makeRequest("/v1/conversations/\(id)", method: "DELETE")
            let (_, res) = try await URLSession.shared.data(for: req)
            if let http = res as? HTTPURLResponse, http.statusCode == 200 {
                self.conversations.removeAll { $0.id == id }
                if self.activeConversationId == id {
                    self.activeConversationId = self.conversations.first?.id
                    if let cid = self.activeConversationId {
                        await fetchMessages(conversationId: cid)
                    } else {
                        self.messages = []
                    }
                }
            }
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    public func fetchMessages(conversationId: String) async {
        do {
            let req = try makeRequest("/v1/conversations/\(conversationId)/messages")
            let (data, res) = try await URLSession.shared.data(for: req)
            if let http = res as? HTTPURLResponse, http.statusCode == 200 {
                let dec = try JSONDecoder().decode(MessagesResponse.self, from: data)
                self.messages = dec.messages
            }
        } catch {
            // Silently handle
        }
    }

    public func sendMessage(text: String) async {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        // Ensure active conversation
        var cid = activeConversationId
        if cid == nil {
            cid = await createNewConversation(title: text)
        }
        guard let targetCid = cid else { return }

        isThinking = true
        presence = .active
        defer {
            isThinking = false
            let activeCount = goals.filter { $0.isActive }.count
            presence = (activeCount == 0 && !goals.isEmpty) ? .paused : .quiet
        }

        // Add optimistic user message to local state
        let tempUserMsg = ChatMessage(
            id: UUID().uuidString,
            role: "user",
            content: text,
            created_at: ISO8601DateFormatter().string(from: Date()),
            meta: nil
        )
        self.messages.append(tempUserMsg)

        do {
            // 1. Post message
            let msgPayload: [String: Any] = [
                "content": text,
                "role": "user",
                "reply": false
            ]
            let msgData = try JSONSerialization.data(withJSONObject: msgPayload)
            let mReq = try makeRequest("/v1/conversations/\(targetCid)/messages", method: "POST", body: msgData)
            _ = try await URLSession.shared.data(for: mReq)

            // 2. Post agent run
            let runPayload: [String: Any] = [
                "agent": "personal",
                "objective": text,
                "execute": true,
                "backend": "ollama",
                "model": "auto",
                "billing_class": "local",
                "max_steps": 24
            ]
            let runData = try JSONSerialization.data(withJSONObject: runPayload)
            let rReq = try makeRequest("/v1/conversations/\(targetCid)/runs", method: "POST", body: runData)
            _ = try await URLSession.shared.data(for: rReq)

            // 3. Drain via worker tick if on local or mini
            let tickReq = try makeRequest("/v1/agent-runs/worker/tick", method: "POST")
            _ = try? await URLSession.shared.data(for: tickReq)

            // 4. Poll for assistant message
            for _ in 0..<14 {
                try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
                await fetchMessages(conversationId: targetCid)
                if let last = self.messages.last, last.isAssistant {
                    break
                }
            }

            // Refresh conversation titles & goals in case Steward set a watch
            await fetchConversations()
            await syncAll()
        } catch {
            self.errorMessage = "Failed to complete turn: \(error.localizedDescription)"
        }
    }

    public func createGoal(title: String, rhythm: String, seeTools: [String]) async -> Bool {
        guard !title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return false }
        do {
            let payload: [String: Any] = [
                "title": title.trimmingCharacters(in: .whitespacesAndNewlines),
                "rhythm": rhythm,
                "see_tools": seeTools,
            ]
            let data = try JSONSerialization.data(withJSONObject: payload)
            let req = try makeRequest("/v1/steward/goals", method: "POST", body: data)
            let (_, res) = try await URLSession.shared.data(for: req)
            if let http = res as? HTTPURLResponse, http.statusCode == 200 {
                await syncAll()
                return true
            }
        } catch {
            self.errorMessage = error.localizedDescription
        }
        return false
    }

    public func pauseGoal(id: String) async -> Bool {
        await postGoalAction(id: id, action: "pause")
    }

    public func resumeGoal(id: String) async -> Bool {
        await postGoalAction(id: id, action: "resume")
    }

    public func wakeGoal(id: String) async -> Bool {
        self.presence = .active
        return await postGoalAction(id: id, action: "wake")
    }

    public func closeGoal(id: String) async -> Bool {
        await postGoalAction(id: id, action: "close")
    }

    private func postGoalAction(id: String, action: String) async -> Bool {
        do {
            let req = try makeRequest("/v1/steward/goals/\(id)/\(action)", method: "POST")
            let (_, res) = try await URLSession.shared.data(for: req)
            if let http = res as? HTTPURLResponse, http.statusCode == 200 {
                await syncAll()
                return true
            }
        } catch {
            self.errorMessage = error.localizedDescription
        }
        return false
    }

    public func scanLocalEnvironment() {
        // 1. Local Notes scan
        var notesDir = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".ai-lab/notes")
        if let envNotes = ProcessInfo.processInfo.environment["STEWARD_MAC_NOTES_DIR"] {
            notesDir = URL(fileURLWithPath: envNotes)
        }

        var notesList: [LocalNote] = []
        if FileManager.default.fileExists(atPath: notesDir.path) {
            let enumerator = FileManager.default.enumerator(at: notesDir, includingPropertiesForKeys: [.contentModificationDateKey, .fileSizeKey])
            while let fileURL = enumerator?.nextObject() as? URL {
                if fileURL.pathExtension.lowercased() == "md" {
                    let rel = fileURL.path.replacingOccurrences(of: notesDir.path + "/", with: "")
                    let values = try? fileURL.resourceValues(forKeys: [.contentModificationDateKey, .fileSizeKey])
                    let mtime = values?.contentModificationDate.map { ISO8601DateFormatter().string(from: $0) } ?? "Recent"
                    let size = Int64(values?.fileSize ?? 0)
                    notesList.append(LocalNote(path: rel, name: fileURL.lastPathComponent, sizeBytes: size, modified: mtime))
                }
            }
        }
        self.localNotes = notesList.sorted { $0.name < $1.name }

        // 2. Battery & Power
        var pSource = "AC Power"
        var bInfo = "No battery / Desktop"
        let pipe = Pipe()
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/usr/bin/pmset")
        proc.arguments = ["-g", "batt"]
        proc.standardOutput = pipe
        try? proc.run()
        proc.waitUntilExit()
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        if let str = String(data: data, encoding: .utf8) {
            let lines = str.split(separator: "\n").map(String.init)
            if let first = lines.first { pSource = first }
            if lines.count > 1 { bInfo = lines[1] }
        }

        self.localStatus = SystemState(
            hostname: ProcessInfo.processInfo.hostName,
            powerSource: pSource,
            batteryInfo: bInfo,
            notesPath: notesDir.path
        )
    }
}
