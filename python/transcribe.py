import sys
import os
import json
import wave
import subprocess
import tempfile
from vosk import Model, KaldiRecognizer


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "vosk-model-small-fa-0.5")


PERSIAN_NUMBER_MAP = {
    "صفر": 0,
    "یک": 1,
    "يه": 1,
    "دو": 2,
    "سه": 3,
    "چهار": 4,
    "چار": 4,
    "پنج": 5,
    "شش": 6,
    "شیش": 6,
    "هفت": 7,
    "هشت": 8,
    "نه": 9,
}


def convert_to_wav(input_path):
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_wav.close()

    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        "-f", "wav",
        temp_wav.name,
    ]

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    return temp_wav.name


def transcribe_wav(wav_path):
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    model = Model(MODEL_PATH)

    grammar = json.dumps([
        "صفر",
        "یک",
        "دو",
        "سه",
        "چهار",
        "چار",
        "پنج",
        "شش",
        "شیش",
        "هفت",
        "هشت",
        "نه",
        "[unk]"
    ], ensure_ascii=False)

    with wave.open(wav_path, "rb") as wf:
        recognizer = KaldiRecognizer(model, wf.getframerate(), grammar)
        recognizer.SetWords(True)

        text_parts = []

        while True:
            data = wf.readframes(4000)

            if len(data) == 0:
                break

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                if "text" in result:
                    text_parts.append(result["text"])

        final_result = json.loads(recognizer.FinalResult())

        if "text" in final_result:
            text_parts.append(final_result["text"])

    return " ".join(text_parts).strip()


def extract_numbers(text):
    rows = []
    words = text.split()
    index = 1

    for word in words:
        cleaned = word.strip(".,،!?؟:;؛")

        if cleaned in PERSIAN_NUMBER_MAP:
            rows.append({
                "row": index,
                "spoken": cleaned,
                "number": PERSIAN_NUMBER_MAP[cleaned],
            })
            index += 1

        elif cleaned.isdigit():
            rows.append({
                "row": index,
                "spoken": cleaned,
                "number": int(cleaned),
            })
            index += 1

    return rows


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No audio path provided"}, ensure_ascii=False))
        sys.exit(1)

    input_audio = sys.argv[1]
    wav_path = None

    try:
        wav_path = convert_to_wav(input_audio)
        text = transcribe_wav(wav_path)
        rows = extract_numbers(text)

        print(json.dumps({
            "transcript": text,
            "table": rows,
        }, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)

    finally:
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)


if __name__ == "__main__":
    main()