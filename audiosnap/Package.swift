// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "audiosnap",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "audiosnap",
            path: "Sources"
        )
    ]
)
