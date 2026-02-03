import Foundation
import AVFoundation

final class AudioRecorder: NSObject, ObservableObject {
    private var audioRecorder: AVAudioRecorder?
    private var stopTimer: Timer?

    @Published var isRecording = false

    private let maxDuration: TimeInterval = 30

    func startRecording() {
        guard !isRecording else { return }

        let session = AVAudioSession.sharedInstance()
        try? session.setCategory(.record, mode: .default)
        try? session.setActive(true)

        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("temp.wav")

        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: 44_100,
            AVNumberOfChannelsKey: 1,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false
        ]

        audioRecorder = try? AVAudioRecorder(url: url, settings: settings)
        audioRecorder?.record()

        isRecording = true

        // 30秒安全装置
        stopTimer = Timer.scheduledTimer(withTimeInterval: maxDuration, repeats: false) { [weak self] _ in
            self?.stopRecording()
        }
    }

    func stopRecording() {
        guard isRecording else { return }

        audioRecorder?.stop()
        audioRecorder = nil

        stopTimer?.invalidate()
        stopTimer = nil

        isRecording = false

        // ⚠️ 音声ファイルはこのあと使ってもいいし、即削除でもOK
    }
}
