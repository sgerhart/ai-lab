// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Steward",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(
            name: "Steward",
            targets: ["Steward"]
        )
    ],
    targets: [
        .executableTarget(
            name: "Steward",
            path: "Sources/Steward"
        )
    ]
)
