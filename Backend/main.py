import os
import queue
import threading
import time
import wave
from tempfile import NamedTemporaryFile

import numpy as np
import openai
import sounddevice as sd
from pynput import keyboard

"""
ホットキー：
  Mac の ⌘（command）キー＋スペースを同時に押している間だけ録音し、離すと録音が終了します。
  録音は最大 30 秒まで。録音した音声を Whisper で文字起こしし、ChatGPT に質問文として送信して回答を取得します。

必要なパッケージのインストール例：
  python3 -m pip install pynput sounddevice numpy openai

API キーについて：
  OpenAI API キーを環境変数「OPENAI_API_KEY」に設定してから実行してください。
"""

# ここに OpenAI API キーを設定するか、環境変数として設定してください
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# 録音設定
SAMPLE_RATE = 16000  # Whisper が推奨する 16 kHz
CHANNELS = 1  # モノラル

# ホットキー設定（Mac の command + space）
HOTKEY_COMBO = {keyboard.Key.cmd, keyboard.Key.space}

# 最大録音時間（秒）
MAX_DURATION = 30

# 録音データを一時的に保持するキュー
audio_queue = queue.Queue()
recording_event = threading.Event()
recording_thread = None

def find_system_audio_device() -> int | None:
    """
    システム音声をキャプチャする仮想デバイス（例：BlackHole や Soundflower）の
    デバイス番号を自動で探します。見つからなければ None を返します。
    """
    try:
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            name = dev.get("name", "").lower()
            if "blackhole" in name or "soundflower" in name:
                return idx
    except Exception:
        pass
    return None

def audio_callback(indata, frames, time_info, status):
    """
    サウンドデバイスからの録音データが届くたびに呼び出されます。
    """
    if status:
        print(f"Sounddevice status: {status}")
    audio_queue.put(indata.copy())

def start_recording():
    """
    音声録音を開始します。`recording_event` を使って停止まで待ちます。
    """
    # 収録対象をシステム音声デバイスに切り替えたい場合は find_system_audio_device() を使う
    system_device = find_system_audio_device()
    if system_device is not None:
        sd.default.device = (system_device, system_device)

    print("録音を開始します…")
    with sd.InputStream(samplerate=SAMPLE_RATE,
                        channels=CHANNELS,
                        callback=audio_callback):
        recording_event.wait(timeout=MAX_DURATION)
    print("録音を停止しました。処理中…")

def on_press(key):
    """
    ホットキーの押下状態を監視します。必要なキーが全て押されると録音開始。
    """
    if key in HOTKEY_COMBO:
        pressed_keys.add(key)
        if pressed_keys == HOTKEY_COMBO and not recording_event.is_set():
            recording_event.clear()
            # 録音スレッドを開始
            global recording_thread
            recording_thread = threading.Thread(target=start_recording)
            recording_thread.start()

def on_release(key):
    """
    ホットキーの離脱状態を監視します。どれかのキーが離されると録音を終了。
    """
    if key in HOTKEY_COMBO:
        pressed_keys.discard(key)
        if not pressed_keys and not recording_event.is_set():
            recording_event.set()
            if recording_thread:
                recording_thread.join()
                process_recording()

def process_recording():
    """
    キューに溜まった録音データを WAV に保存し、Whisper で文字起こし、
    ChatGPT で回答を取得します。
    """
    # キューから録音データをまとめて取得
    frames = []
    while not audio_queue.empty():
        frames.append(audio_queue.get())
    if not frames:
        print("音声データがありません。")
        return

    audio_data = np.concatenate(frames, axis=0)
    # 一時ファイルに WAV として保存
    with NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        with wave.open(tmp_wav.name, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(sd.default.dtype[0].itemsize)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())
        wav_path = tmp_wav.name

    try:
        # Whisper で文字起こし
        with open(wav_path, "rb") as audio_file:
            whisper_result = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                language="ja"  # 日本語の音声なら "ja" にしておくと精度が上がります
            )
        question_text = whisper_result["text"]
        print(f"質問文（文字起こし結果）：{question_text}")

        # ChatGPT で回答を取得
        gpt_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question_text},
            ],
            temperature=0.7,
        )
        answer = gpt_response["choices"][0]["message"]["content"].strip()
        print(f"回答：\n{answer}")
    except Exception as e:
        print(f"API 呼び出しでエラーが発生しました: {e}")
    finally:
        # 録音データをリセット
        while not audio_queue.empty():
            audio_queue.get()

if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("OpenAI API キーが設定されていません。環境変数 OPENAI_API_KEY を設定してください。")
        exit(1)

    pressed_keys = set()
    print("⌘（command）キーとスペースキーを同時に長押しで録音を開始します。離すと録音終了です。")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
