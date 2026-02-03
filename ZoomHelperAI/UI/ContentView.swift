import SwiftUI

struct ContentView: View {
    @StateObject private var recorder = AudioRecorder()
    @State private var hotKey: HotKeyManager?

    var body: some View {
        VStack(spacing: 12) {
            Text(recorder.isRecording ? "🎙 Listening…" : "待機中")
                .font(.headline)

            Text("⌘ + Space を押し続けて話す")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .onAppear {
            hotKey = HotKeyManager(recorder: recorder)
        }
    }
}
