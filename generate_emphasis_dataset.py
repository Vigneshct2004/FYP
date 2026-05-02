import os
import pandas as pd
import numpy as np
import librosa
from tqdm import tqdm

DATASET_PATH = r"C:\Users\vignesh\Downloads\FYP\Emphasis_module\LJSpeech-1.1\LJSpeech-1.1"
WAV_PATH = os.path.join(DATASET_PATH, "wavs")

metadata = pd.read_csv(
    os.path.join(DATASET_PATH, "metadata.csv"),
    sep="|",
    header=None,
    names=["id", "text", "normalized"]
)

print("Total audio files:", len(metadata))

metadata = metadata.iloc[:2000]

dataset = []

for _, row in tqdm(metadata.iterrows(), total=len(metadata)):

    audio_id = row["id"]
    text = row["text"]
    audio_path = os.path.join(WAV_PATH, audio_id + ".wav")

    try:
        y, sr = librosa.load(audio_path, sr=16000)

        words = text.split()
        duration_total = librosa.get_duration(y=y, sr=sr)
        segment_duration = duration_total / len(words)
        start_time = 0

        for word in words:
            end_time = start_time + segment_duration
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            segment = y[start_sample:end_sample]

            if len(segment) == 0:
                start_time = end_time
                continue

            energy = np.mean(librosa.feature.rms(y=segment))

            pitches, mags = librosa.piptrack(y=segment, sr=sr)
            pitch_values = pitches[mags > np.median(mags)]
            pitch = np.mean(pitch_values) if len(pitch_values) > 0 else 0

            duration = segment_duration

            dataset.append([word, pitch, energy, duration])
            start_time = end_time

    except:
        continue

df = pd.DataFrame(dataset, columns=["word", "pitch", "energy", "duration"])
print("Total samples:", len(df))

# ── Strategy 2: Percentile Cutoff (Exact 50/50 Balance) ──────────────

EMPHASIS_RATIO = 0.5  # ← tune this: 0.3 = top 30% emphasized, 0.5 = top 50%

# Combined z-score across all 3 features
df["emphasis_score"] = (
    (df["pitch"]    - df["pitch"].mean())    / (df["pitch"].std()    + 1e-9) +
    (df["energy"]   - df["energy"].mean())   / (df["energy"].std()   + 1e-9) +
    (df["duration"] - df["duration"].mean()) / (df["duration"].std() + 1e-9)
)

# Label top EMPHASIS_RATIO % as emphasized (1), rest as not (0)
threshold = df["emphasis_score"].quantile(1 - EMPHASIS_RATIO)
df["label"] = (df["emphasis_score"] >= threshold).astype(int)

print("\nLabel Distribution:")
print(df["label"].value_counts(normalize=True))

# Save without the helper column
df[["word", "pitch", "energy", "duration", "label"]].to_csv("emphasis_dataset.csv", index=False)

print("✅ Dataset saved")