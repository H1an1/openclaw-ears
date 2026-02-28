import AVFoundation
import CoreMedia
import Foundation
import ScreenCaptureKit

// MARK: - Audio Writer

final class AudioWriter: NSObject, SCStreamOutput, @unchecked Sendable {
    private let writer: AVAssetWriter
    private let input: AVAssetWriterInput
    private var started = false
    private var sampleCount = 0

    init(outputURL: URL, sampleRate: Double = 48000, channels: Int = 2) throws {
        if FileManager.default.fileExists(atPath: outputURL.path) {
            try FileManager.default.removeItem(at: outputURL)
        }

        writer = try AVAssetWriter(outputURL: outputURL, fileType: .wav)

        let settings: [String: Any] = [
            AVFormatIDKey: kAudioFormatLinearPCM,
            AVSampleRateKey: sampleRate,
            AVNumberOfChannelsKey: channels,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false,
            AVLinearPCMIsBigEndianKey: false,
            AVLinearPCMIsNonInterleaved: false,
        ]

        input = AVAssetWriterInput(mediaType: .audio, outputSettings: settings)
        input.expectsMediaDataInRealTime = true
        writer.add(input)
        super.init()
    }

    func stream(
        _ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer,
        of type: SCStreamOutputType
    ) {
        guard type == .audio, sampleBuffer.isValid else { return }

        if !started {
            writer.startWriting()
            writer.startSession(atSourceTime: sampleBuffer.presentationTimeStamp)
            started = true
        }

        if input.isReadyForMoreMediaData {
            input.append(sampleBuffer)
            sampleCount += sampleBuffer.numSamples
        }
    }

    func finish() async {
        guard started else { return }
        input.markAsFinished()
        await writer.finishWriting()
    }

    var hasSamples: Bool { sampleCount > 0 }
}

// MARK: - Help

func printUsage() {
    let help = """
        audiosnap — Capture system audio on macOS via ScreenCaptureKit

        USAGE:
            audiosnap [duration] [output] [options]

        ARGUMENTS:
            duration        Recording duration in seconds (default: 5)
            output          Output file path (default: audiosnap-output.wav)

        OPTIONS:
            -h, --help      Show this help
            --exclude-self  Exclude this process's audio from capture
            --sample-rate N Sample rate in Hz (default: 48000)
            --channels N    Number of channels (default: 2)

        EXAMPLES:
            audiosnap                           # Record 5s → audiosnap-output.wav
            audiosnap 10                        # Record 10s
            audiosnap 30 meeting.wav            # Record 30s → meeting.wav
            audiosnap 5 - | ffmpeg -i - ...     # Pipe to ffmpeg (future)

        REQUIREMENTS:
            macOS 13+ with Screen Recording permission granted.
            First run will prompt for permission — grant it, then re-run.

        ABOUT:
            A lightweight CLI for capturing system audio without virtual audio
            drivers (no BlackHole/Soundflower needed). Uses Apple's native
            ScreenCaptureKit API.

            https://github.com/AudioSnap/audiosnap
        """
    print(help)
}

// MARK: - Main

@main
struct AudioSnap {
    static func main() async throws {
        var args = Array(CommandLine.arguments.dropFirst())

        // Flags
        if args.contains("-h") || args.contains("--help") {
            printUsage()
            return
        }

        let excludeSelf = args.contains("--exclude-self")
        args.removeAll { $0 == "--exclude-self" }

        var sampleRate: Double = 48000
        if let idx = args.firstIndex(of: "--sample-rate"), idx + 1 < args.count {
            sampleRate = Double(args[idx + 1]) ?? 48000
            args.removeSubrange(idx...idx + 1)
        }

        var channels: Int = 2
        if let idx = args.firstIndex(of: "--channels"), idx + 1 < args.count {
            channels = Int(args[idx + 1]) ?? 2
            args.removeSubrange(idx...idx + 1)
        }

        // Positional args
        let duration: Double = args.count > 0 ? (Double(args[0]) ?? 5) : 5
        let outputPath: String = args.count > 1 ? args[1] : "audiosnap-output.wav"
        let outputURL = URL(fileURLWithPath: outputPath)

        // Get shareable content
        let content: SCShareableContent
        do {
            content = try await SCShareableContent.excludingDesktopWindows(
                false, onScreenWindowsOnly: false)
        } catch {
            fputs(
                "❌ Screen recording permission denied. Grant access in:\n   System Settings → Privacy & Security → Screen Recording\n",
                stderr)
            Foundation.exit(1)
        }

        guard let display = content.displays.first else {
            fputs("❌ No display found\n", stderr)
            Foundation.exit(1)
        }

        // Configure stream
        let config = SCStreamConfiguration()
        config.capturesAudio = true
        config.excludesCurrentProcessAudio = excludeSelf
        config.channelCount = channels
        config.sampleRate = Int(sampleRate)

        // Minimal video (required by API)
        config.width = 2
        config.height = 2
        config.minimumFrameInterval = CMTime(value: 1, timescale: 1)
        config.showsCursor = false

        let filter = SCContentFilter(display: display, excludingWindows: [])
        let stream = SCStream(filter: filter, configuration: config, delegate: nil)

        let writer = try AudioWriter(
            outputURL: outputURL, sampleRate: sampleRate, channels: channels)
        try stream.addStreamOutput(writer, type: .audio, sampleHandlerQueue: .global())

        fputs("🎤 Recording system audio for \(Int(duration))s → \(outputPath)\n", stderr)

        do {
            try await stream.startCapture()
        } catch {
            fputs("❌ Failed to start capture: \(error.localizedDescription)\n", stderr)
            Foundation.exit(1)
        }

        try await Task.sleep(nanoseconds: UInt64(duration * 1_000_000_000))

        try await stream.stopCapture()
        await writer.finish()

        if writer.hasSamples {
            let fileSize = (try? FileManager.default.attributesOfItem(atPath: outputPath))?[
                .size] as? Int ?? 0
            let sizeKB = fileSize / 1024
            fputs("✅ Done: \(outputPath) (\(sizeKB)KB)\n", stderr)
        } else {
            fputs("⚠️  Recorded but got no audio samples. Is anything playing?\n", stderr)
        }
    }
}
