import Foundation

public struct Goal: Codable, Identifiable, Hashable {
    public let id: String
    public let title: String
    public let rhythm: String
    public let status: String
    public let see_tools: [String]?
    public let mcp_server_ids: [String]?
    public let last_wake_at: String?
    public let last_note: String?
    public let last_run_id: String?
    public let next_due_at: String?

    public var isActive: Bool {
        status == "active"
    }

    public var isPaused: Bool {
        status == "paused"
    }

    public var formattedWake: String {
        guard let lw = last_wake_at, !lw.isEmpty else { return "Not yet wake" }
        return lw.replacingOccurrences(of: "T", with: " ").prefix(19).description
    }
}

public struct GoalsResponse: Codable {
    public let goals: [Goal]
}

public struct ActivityEntry: Codable, Identifiable, Hashable {
    public var id: String {
        "\(goal_id ?? "unknown")-\(wake_at ?? UUID().uuidString)"
    }
    public let goal_id: String?
    public let goal_title: String?
    public let wake_at: String?
    public let tools_called: [String]?
    public let observation: String?
    public let note: String?
    public let status: String?

    public var formattedTime: String {
        guard let wa = wake_at, !wa.isEmpty else { return "Recent" }
        return wa.replacingOccurrences(of: "T", with: " ").prefix(19).description
    }

    public var displaySummary: String {
        if let obs = observation, !obs.isEmpty { return obs }
        if let n = note, !n.isEmpty { return n }
        if let tc = tools_called, !tc.isEmpty { return "Inspected \(tc.joined(separator: ", "))" }
        return "Wake finished cleanly"
    }
}

public struct ActivityResponse: Codable {
    public let activity: [ActivityEntry]
}

public struct ConversationItem: Codable, Identifiable, Hashable {
    public let id: String
    public let agent: String
    public var title: String
    public let created_at: String?
    public let project_id: String?

    public var displayTitle: String {
        if title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || title == "New conversation" {
            return "Steward Desk Session"
        }
        return title
    }
}

public struct ConversationsResponse: Codable {
    public let conversations: [ConversationItem]
}

public struct ChatMessage: Codable, Identifiable, Hashable {
    public let id: String
    public let role: String
    public let content: String
    public let created_at: String?
    public let meta: [String: AnyCodable]?

    public var isUser: Bool {
        role == "user"
    }

    public var isAssistant: Bool {
        role == "assistant"
    }
}

public struct MessagesResponse: Codable {
    public let conversation_id: String
    public let messages: [ChatMessage]
}

public struct LocalNote: Identifiable, Hashable {
    public var id: String { path }
    public let path: String
    public let name: String
    public let sizeBytes: Int64
    public let modified: String
}

public struct SystemState {
    public let hostname: String
    public let powerSource: String
    public let batteryInfo: String
    public let notesPath: String
}

public enum StewardPresence {
    case quiet
    case active
    case paused
    case offline

    public var label: String {
        switch self {
        case .quiet: return "Quiet & Resting"
        case .active: return "Thinking & Working"
        case .paused: return "Watches Paused"
        case .offline: return "Control Plane Offline"
        }
    }

    public var shortLabel: String {
        switch self {
        case .quiet: return "Quiet"
        case .active: return "Active"
        case .paused: return "Paused"
        case .offline: return "Offline"
        }
    }
}

// Helper for loose JSON meta dict decoding
public struct AnyCodable: Codable, Hashable {
    public let value: Any

    public init(_ value: Any) {
        self.value = value
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let b = try? container.decode(Bool.self) {
            value = b
        } else if let i = try? container.decode(Int.self) {
            value = i
        } else if let d = try? container.decode(Double.self) {
            value = d
        } else if let s = try? container.decode(String.self) {
            value = s
        } else if let a = try? container.decode([AnyCodable].self) {
            value = a.map { $0.value }
        } else if let dict = try? container.decode([String: AnyCodable].self) {
            value = dict.mapValues { $0.value }
        } else {
            value = ""
        }
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        if let s = value as? String {
            try container.encode(s)
        } else if let b = value as? Bool {
            try container.encode(b)
        } else if let i = value as? Int {
            try container.encode(i)
        } else if let d = value as? Double {
            try container.encode(d)
        } else {
            try container.encode(String(describing: value))
        }
    }

    public static func == (lhs: AnyCodable, rhs: AnyCodable) -> Bool {
        String(describing: lhs.value) == String(describing: rhs.value)
    }

    public func hash(into hasher: inout Hasher) {
        hasher.combine(String(describing: value))
    }
}
