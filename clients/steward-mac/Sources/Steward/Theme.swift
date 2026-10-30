import SwiftUI
import AppKit

public enum AppAppearance: String, CaseIterable, Identifiable {
    case system = "system"
    case light = "light"
    case dark = "dark"

    public var id: String { rawValue }

    public var label: String {
        switch self {
        case .system: return "System"
        case .light: return "Light"
        case .dark: return "Dark"
        }
    }

    public var icon: String {
        switch self {
        case .system: return "circle.righthalf.filled"
        case .light: return "sun.max.fill"
        case .dark: return "moon.fill"
        }
    }

    public var colorScheme: ColorScheme? {
        switch self {
        case .system: return nil
        case .light: return .light
        case .dark: return .dark
        }
    }
}

public struct AppTheme {
    // Dynamic NSColor provider helper
    private static func dynamic(light: NSColor, dark: NSColor) -> Color {
        Color(nsColor: NSColor(name: nil, dynamicProvider: { appearance in
            appearance.bestMatch(from: [.darkAqua, .aqua]) == .darkAqua ? dark : light
        }))
    }

    // Backgrounds
    public static let windowBackground = dynamic(
        light: NSColor(red: 0.96, green: 0.97, blue: 0.99, alpha: 1.0), // #f5f7fc
        dark: NSColor(red: 0.06, green: 0.08, blue: 0.12, alpha: 1.0)   // #0f141f
    )

    public static let sidebarBackground = dynamic(
        light: NSColor(red: 0.92, green: 0.94, blue: 0.97, alpha: 1.0), // #ebf0f7
        dark: NSColor(red: 0.08, green: 0.10, blue: 0.15, alpha: 1.0)   // #141a26
    )

    public static let cardBackground = dynamic(
        light: NSColor.white,
        dark: NSColor(red: 0.10, green: 0.13, blue: 0.19, alpha: 1.0)   // #1a2130
    )

    public static let cardBackgroundSecondary = dynamic(
        light: NSColor(red: 0.94, green: 0.95, blue: 0.98, alpha: 1.0),
        dark: NSColor(red: 0.07, green: 0.09, blue: 0.14, alpha: 1.0)
    )

    public static let headerBackground = dynamic(
        light: NSColor(red: 0.94, green: 0.95, blue: 0.98, alpha: 1.0),
        dark: NSColor(red: 0.09, green: 0.11, blue: 0.16, alpha: 1.0)
    )

    public static let inputBackground = dynamic(
        light: NSColor.white,
        dark: NSColor(red: 0.11, green: 0.14, blue: 0.20, alpha: 1.0)
    )

    // Borders & Dividers
    public static let border = dynamic(
        light: NSColor(red: 0.84, green: 0.87, blue: 0.92, alpha: 1.0), // #d6deeb
        dark: NSColor(red: 0.20, green: 0.25, blue: 0.35, alpha: 1.0)   // #334059
    )

    public static let subtleBorder = dynamic(
        light: NSColor(white: 0.88, alpha: 1.0),
        dark: NSColor(white: 0.20, alpha: 1.0)
    )

    // Typography
    public static let textPrimary = dynamic(
        light: NSColor(red: 0.08, green: 0.11, blue: 0.18, alpha: 1.0), // #141c2e
        dark: NSColor(red: 0.96, green: 0.97, blue: 0.99, alpha: 1.0)   // #f5f7fc
    )

    public static let textSecondary = dynamic(
        light: NSColor(red: 0.35, green: 0.42, blue: 0.52, alpha: 1.0), // #596b85
        dark: NSColor(red: 0.65, green: 0.72, blue: 0.82, alpha: 1.0)   // #a6b8d1
    )

    public static let textMuted = dynamic(
        light: NSColor(red: 0.52, green: 0.58, blue: 0.68, alpha: 1.0),
        dark: NSColor(red: 0.48, green: 0.54, blue: 0.64, alpha: 1.0)
    )

    public static let sectionHeader = dynamic(
        light: NSColor(red: 0.28, green: 0.35, blue: 0.46, alpha: 1.0), // #475975
        dark: NSColor(red: 0.60, green: 0.68, blue: 0.80, alpha: 1.0)   // #99aecd
    )

    // Accents & Badges
    public static let accentTeal = dynamic(
        light: NSColor(red: 0.0, green: 0.60, blue: 0.48, alpha: 1.0),
        dark: NSColor(red: 0.0, green: 0.90, blue: 0.70, alpha: 1.0)
    )

    public static let accentBlue = dynamic(
        light: NSColor(red: 0.08, green: 0.45, blue: 0.85, alpha: 1.0),
        dark: NSColor(red: 0.22, green: 0.74, blue: 0.97, alpha: 1.0)
    )

    public static let userBubbleBackground = dynamic(
        light: NSColor(red: 0.08, green: 0.45, blue: 0.85, alpha: 1.0),
        dark: NSColor(red: 0.12, green: 0.32, blue: 0.58, alpha: 1.0)
    )

    public static let tagBackground = dynamic(
        light: NSColor(red: 0.88, green: 0.91, blue: 0.96, alpha: 1.0),
        dark: NSColor(red: 0.14, green: 0.18, blue: 0.26, alpha: 1.0)
    )

    public static let tagText = dynamic(
        light: NSColor(red: 0.15, green: 0.25, blue: 0.42, alpha: 1.0),
        dark: NSColor(red: 0.75, green: 0.85, blue: 0.98, alpha: 1.0)
    )
}
