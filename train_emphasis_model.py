import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report,
    roc_curve, auc, precision_recall_curve, average_precision_score,
    matthews_corrcoef, cohen_kappa_score
)

df = pd.read_csv("emphasis_dataset.csv")

X = df[["pitch", "energy", "duration"]].values
y = df["label"].values

feature_mean = X.mean(axis=0)
feature_std  = X.std(axis=0)
X = (X - feature_mean) / feature_std

np.save(r"C:\Users\vignesh\Downloads\FYP\Emphasis_module\feature_mean.npy", feature_mean)
np.save(r"C:\Users\vignesh\Downloads\FYP\Emphasis_module\feature_std.npy",  feature_std)
print("✅ Normalization stats saved")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

X_train = torch.tensor(X_train, dtype=torch.float32)
X_test  = torch.tensor(X_test,  dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
y_test  = torch.tensor(y_test,  dtype=torch.float32)

############################################
# MODEL
############################################

class EmphasisModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = \
            (
            nn.Sequential(
            nn.Linear(3, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, 1)
        ))

    def forward(self, x):
        return self.model(x)

model = EmphasisModel()
criterion = nn.BCEWithLogitsLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', patience=5, factor=0.5
)

############################################
# TRAINING — track loss history
############################################

epochs = 100
train_losses = []

for epoch in range(epochs):
    model.train()
    optimizer.zero_grad()

    logits = model(X_train).squeeze()
    loss = criterion(logits, y_train)

    loss.backward()
    optimizer.step()
    scheduler.step(loss)

    train_losses.append(loss.item())

    if (epoch + 1) % 10 == 0:
        print(f"Epoch {epoch+1}/{epochs}  Loss: {loss.item():.4f}")

torch.save(model.state_dict(), "emphasis_model.pt")
print("✅ Model saved")

############################################
# EVALUATION
############################################

model.eval()
with torch.no_grad():
    logits = model(X_test).squeeze()
    probs  = torch.sigmoid(logits).numpy()

y_true = y_test.numpy().astype(int)
y_pred = (probs > 0.5).astype(int)

acc       = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred)
recall    = recall_score(y_true, y_pred)
f1        = f1_score(y_true, y_pred)
mcc       = matthews_corrcoef(y_true, y_pred)
kappa     = cohen_kappa_score(y_true, y_pred)
roc_auc   = auc(*roc_curve(y_true, probs)[:2])
avg_prec  = average_precision_score(y_true, probs)
cm        = confusion_matrix(y_true, y_pred)
tn, fp, fn, tp = cm.ravel()
specificity = tn / (tn + fp)

print("\n========== Evaluation Metrics ==========")
print(f"Accuracy        : {acc:.4f}")
print(f"Precision       : {precision:.4f}")
print(f"Recall          : {recall:.4f}")
print(f"F1 Score        : {f1:.4f}")
print(f"Specificity     : {specificity:.4f}")
print(f"ROC-AUC         : {roc_auc:.4f}")
print(f"Avg Precision   : {avg_prec:.4f}")
print(f"MCC             : {mcc:.4f}")
print(f"Cohen's Kappa   : {kappa:.4f}")
print("\nClassification Report:")
print(classification_report(y_true, y_pred, target_names=["Not Emphasized", "Emphasized"]))

############################################
# PLOT 1 — Loss Curve
############################################

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(range(1, epochs + 1), train_losses, color="#534AB7", linewidth=2)
ax.set_xlabel("Epoch", fontsize=12)
ax.set_ylabel("Loss (BCE)", fontsize=12)
ax.set_title("Training Loss Curve", fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.set_xlim(1, epochs)
plt.tight_layout()
plt.savefig("loss_curve.png", dpi=150, bbox_inches='tight')
plt.close()
print("✅ loss_curve.png saved")

############################################
# PLOT 2 — Confusion Matrix
############################################

fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(
    cm, annot=True, fmt='d', cmap='Purples',
    xticklabels=["Not Emphasized", "Emphasized"],
    yticklabels=["Not Emphasized", "Emphasized"],
    linewidths=0.5, ax=ax
)
ax.set_xlabel("Predicted Label", fontsize=12)
ax.set_ylabel("True Label", fontsize=12)
ax.set_title("Confusion Matrix", fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig("confusion_matrix.png", dpi=150, bbox_inches='tight')
plt.close()
print("✅ confusion_matrix.png saved")

############################################
# PLOT 3 — ROC Curve
############################################

fpr, tpr, _ = roc_curve(y_true, probs)

fig, ax = plt.subplots(figsize=(6, 5))
ax.plot(fpr, tpr, color="#534AB7", linewidth=2, label=f"ROC Curve (AUC = {roc_auc:.4f})")
ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label="Random Classifier")
ax.set_xlabel("False Positive Rate", fontsize=12)
ax.set_ylabel("True Positive Rate", fontsize=12)
ax.set_title("ROC Curve", fontsize=14, fontweight='bold')
ax.legend(loc="lower right", fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("roc_curve.png", dpi=150, bbox_inches='tight')
plt.close()
print("✅ roc_curve.png saved")

############################################
# PLOT 4 — Precision-Recall Curve
############################################

prec_vals, rec_vals, _ = precision_recall_curve(y_true, probs)

fig, ax = plt.subplots(figsize=(6, 5))
ax.plot(rec_vals, prec_vals, color="#1D9E75", linewidth=2, label=f"AP = {avg_prec:.4f}")
ax.set_xlabel("Recall", fontsize=12)
ax.set_ylabel("Precision", fontsize=12)
ax.set_title("Precision-Recall Curve", fontsize=14, fontweight='bold')
ax.legend(loc="upper right", fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("precision_recall_curve.png", dpi=150, bbox_inches='tight')
plt.close()
print("✅ precision_recall_curve.png saved")

############################################
# PLOT 5 — Classification Report Heatmap
############################################

report_dict = classification_report(
    y_true, y_pred,
    target_names=["Not Emphasized", "Emphasized"],
    output_dict=True
)
report_df = pd.DataFrame(report_dict).T.drop(columns=["support"], errors="ignore")
report_df = report_df.loc[["Not Emphasized", "Emphasized", "macro avg", "weighted avg"]]

fig, ax = plt.subplots(figsize=(7, 3.5))
sns.heatmap(
    report_df.astype(float), annot=True, fmt=".4f",
    cmap="Greens", linewidths=0.5, ax=ax,
    vmin=0, vmax=1
)
ax.set_title("Classification Report", fontsize=14, fontweight='bold')
ax.set_ylabel("")
plt.tight_layout()
plt.savefig("classification_report.png", dpi=150, bbox_inches='tight')
plt.close()
print("✅ classification_report.png saved")

print("\n✅ All evaluation plots saved.")