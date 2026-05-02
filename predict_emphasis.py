import torch
import numpy as np
import torch.nn as nn
import librosa

############################################
# MODEL — must match trained architecture
############################################

class EmphasisModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(3, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(32, 1)
        )

    def forward(self, x):
        return self.model(x)

MODEL_PATH = r"C:\Users\vignesh\Downloads\FYP\Emphasis_module\emphasis_model.pt"
MEAN_PATH  = r"C:\Users\vignesh\Downloads\FYP\Emphasis_module\feature_mean.npy"
STD_PATH   = r"C:\Users\vignesh\Downloads\FYP\Emphasis_module\feature_std.npy"

model = EmphasisModel()
model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
model.eval()

# Load normalization stats saved during training
feature_mean = np.load(MEAN_PATH)
feature_std  = np.load(STD_PATH)

print("Feature mean:", feature_mean)
print("Feature std :", feature_std)
print("✅ Emphasis model loaded")

############################################
# FEATURE EXTRACTION — matches training exactly
############################################

def extract_prosody_features(audio_path, words):

    y, sr = librosa.load(audio_path, sr=16000)

    total_duration   = librosa.get_duration(y=y, sr=sr)
    word_count       = max(len(words), 1)
    segment_duration = total_duration / word_count

    features = []

    for i in range(word_count):

        start_sample = int(i * segment_duration * sr)
        end_sample   = int((i + 1) * segment_duration * sr)

        segment = y[start_sample:end_sample]

        if len(segment) == 0:
            features.append([0.0, 0.0, segment_duration])
            continue

        # ✅ Same as training: piptrack for pitch
        pitches, mags = librosa.piptrack(y=segment, sr=sr)
        pitch_values  = pitches[mags > np.median(mags)]
        pitch         = float(np.mean(pitch_values)) if len(pitch_values) > 0 else 0.0

        # ✅ Same as training: rms for energy
        energy = float(np.mean(librosa.feature.rms(y=segment)))

        features.append([pitch, energy, segment_duration])

    return features

############################################
# PREDICTION
############################################

def predict_emphasis(words, audio_path):

    features = extract_prosody_features(audio_path, words)
    features = np.array(features)

    # ✅ Normalize using same stats as training
    features = (features - feature_mean) / (feature_std + 1e-9)

    features = torch.tensor(features, dtype=torch.float32)

    model.eval()

    with torch.no_grad():
        logits = model(features).squeeze()

    scores = torch.sigmoid(logits).numpy()

    # ✅ Handle single word edge case
    if scores.ndim == 0:
        scores = scores.reshape(1)

    emphasis_scores = {}

    for word, score in zip(words, scores):
        emphasis_scores[word] = float(score)

    print("Emphasis Scores:", emphasis_scores)

    return emphasis_scores