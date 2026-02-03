import AppKit

final class HotKeyManager {
    private var monitor: Any?
    private let recorder: AudioRecorder

    init(recorder: AudioRecorder) {
        self.recorder = recorder
        startMonitoring()
    }

    private func startMonitoring() {
        monitor = NSEvent.addGlobalMonitorForEvents(
            matching: [.keyDown, .keyUp]
        ) { [weak self] event in
            self?.handle(event)
        }
    }

    private func handle(_ event: NSEvent) {
        let isCommand = event.modifierFlags.contains(.command)
        let isSpace = event.keyCode == 49   // Space key

        guard isCommand && isSpace else { return }

        if event.type == .keyDown {
            recorder.startRecording()
        } else if event.type == .keyUp {
            recorder.stopRecording()
        }
    }
}
