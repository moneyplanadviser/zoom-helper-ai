import os
import wave
from tempfile import NamedTemporaryFile

import numpy as np
from openai import OpenAI

"""
テスト用：ホットキーなしで Whisper + ChatGPT の連携をテスト
サンプル音声ファイルなしで、テキストベースで動作確認できます
"""

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

SAMPLE_RATE = 16000
CHANNELS = 1

def test_api_integration():
    """API連携をテスト（テキスト入力）"""
    if not OPENAI_API_KEY:
        print("❌ OpenAI API キーが設定されていません。")
        print("環境変数 OPENAI_API_KEY を設定してください。")
        return

    print("✅ APIキーが正しく設定されました")
    
    # テキストベースのテスト
    test_question = "今日の天気を教えてください。東京の場合は特に。"
    print(f"\n📝 質問文（テスト）: {test_question}")

    try:
        # ChatGPT で回答を取得
        print("\n🔄 ChatGPT に問い合わせ中...")
        gpt_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Please respond in Japanese."},
                {"role": "user", "content": test_question},
            ],
            temperature=0.7,
        )
        answer = gpt_response.choices[0].message.content.strip()
        print(f"\n✅ 回答：\n{answer}")
    except Exception as e:
        print(f"❌ API 呼び出しでエラーが発生しました: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Zoom Helper AI - API テスト")
    print("=" * 50)
    test_api_integration()
