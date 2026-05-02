# # ================= IMPORTS =================
# import tkinter as tk
# import numpy as np
# from tkinter import filedialog, messagebox
# import os
# import subprocess
# import cv2
# from PIL import Image, ImageTk
# from moviepy.editor import VideoFileClip
# from pydub import AudioSegment
# import noisereduce as nr
# import librosa
# import soundfile as sf
# from speech_to_text import transcribe_audio
# from gloss_predictor import predict_gloss
# import re
#
# from Emphasis_module.predict_emphasis import predict_emphasis
#
# print("✅ Emphasis model loaded")
#
# # ================= CONFIG =================
# ANIMATION_DIR = "animations"
# OUTPUT_DIR = "temp"
# OUTPUT_VIDEO = os.path.join(OUTPUT_DIR, "output.mp4")
# FFMPEG_PATH = "ffmpeg"
#
# AUDIO_DIR = "audio"
# RAW_AUDIO = os.path.join(AUDIO_DIR, "raw.wav")
# MONO_AUDIO = os.path.join(AUDIO_DIR, "mono.wav")
# DENOISED_AUDIO = os.path.join(AUDIO_DIR, "clean.wav")
# FINAL_AUDIO = os.path.join(AUDIO_DIR, "final.wav")
#
# # =========================================
#
# # 🔥 BUILD INDEX
# def build_animation_index():
#     index = {}
#     if not os.path.exists(ANIMATION_DIR):
#         return index
#
#     for file in os.listdir(ANIMATION_DIR):
#         if file.endswith(".mp4"):
#             key = file.replace(".mp4", "").upper()
#             index[key] = os.path.join(ANIMATION_DIR, file)
#
#     return index
#
# ANIMATION_INDEX = build_animation_index()
#
# # 🔥 LONGEST MATCH
# def resolve_gloss_sequence(glosses):
#     resolved = []
#     i = 0
#     n = len(glosses)
#
#     while i < n:
#         found = False
#
#         for j in range(n, i, -1):
#             phrase = "_".join(glosses[i:j]).upper()
#
#             if phrase in ANIMATION_INDEX:
#                 resolved.append(phrase)
#                 i = j
#                 found = True
#                 break
#
#         if not found:
#             resolved.append(glosses[i].upper())
#             i += 1
#
#     return resolved
#
# # 🔥 SMART MATCH + FINGER SPELLING
# def find_animation_clips(gloss):
#     clips = []
#     gloss = gloss.upper()
#
#     if gloss in ANIMATION_INDEX:
#         return [ANIMATION_INDEX[gloss]]
#
#     clean = re.sub(r"[^\w\s]", "", gloss).replace(" ", "_")
#
#     if clean in ANIMATION_INDEX:
#         return [ANIMATION_INDEX[clean]]
#
#     words = re.split(r"[_\s]", clean)
#
#     split_clips = []
#     for word in words:
#         if word in ANIMATION_INDEX:
#             split_clips.append(ANIMATION_INDEX[word])
#         else:
#             split_clips = []
#             break
#
#     if split_clips:
#         return split_clips
#
#     # 🔥 Fingerspelling fallback
#     print(f"🔤 Fingerspelling for: {gloss}")
#
#     for char in clean:
#         if char.isalpha() and char.upper() in ANIMATION_INDEX:
#             clips.append(ANIMATION_INDEX[char.upper()])
#
#     return clips
#
# # ================= AUDIO =================
# def extract_audio(video_path):
#     os.makedirs(AUDIO_DIR, exist_ok=True)
#     video = VideoFileClip(video_path)
#     video.audio.write_audiofile(RAW_AUDIO)
#     return RAW_AUDIO
#
# def convert_to_mono(input_audio):
#     audio = AudioSegment.from_file(input_audio)
#     audio = audio.set_channels(1).set_frame_rate(16000)
#     audio.export(MONO_AUDIO, format="wav")
#     return MONO_AUDIO
#
# def reduce_noise(input_audio):
#     data, rate = librosa.load(input_audio, sr=16000)
#     reduced = nr.reduce_noise(y=data, sr=rate)
#     sf.write(DENOISED_AUDIO, reduced, rate)
#     return DENOISED_AUDIO
#
# def trim_silence(input_audio):
#     audio = AudioSegment.from_wav(input_audio)
#     trimmed = audio.strip_silence(silence_len=800, silence_thresh=-40)
#     trimmed.export(FINAL_AUDIO, format="wav")
#     return FINAL_AUDIO
#
# def process_video_audio(video_path):
#     try:
#         raw = extract_audio(video_path)
#         mono = convert_to_mono(raw)
#         clean = reduce_noise(mono)
#         final = trim_silence(clean)
#         print("✅ Audio ready:", final)
#         return final
#     except Exception as e:
#         messagebox.showerror("Audio Error", str(e))
#         return None
#
# # ================= FULLSCREEN PLAYER =================
# def play_video_fullscreen(video_path):
#     full_window = tk.Toplevel(root)
#     full_window.attributes("-fullscreen", True)
#     full_window.bind("<Escape>", lambda e: full_window.destroy())
#
#     video_label_fs = tk.Label(full_window)
#     video_label_fs.pack(fill="both", expand=True)
#
#     full_window.update()  # 🔥 IMPORTANT
#
#     cap = cv2.VideoCapture(video_path)
#
#     def update():
#         ret, frame = cap.read()
#
#         if not ret:
#             cap.release()
#             full_window.destroy()
#             return
#
#         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#
#         screen_w = full_window.winfo_screenwidth()
#         screen_h = full_window.winfo_screenheight()
#
#         frame = cv2.resize(frame, (screen_w, screen_h))
#
#         img = Image.fromarray(frame)
#         imgtk = ImageTk.PhotoImage(image=img)
#
#         video_label_fs.imgtk = imgtk
#         video_label_fs.configure(image=imgtk)
#
#         full_window.after(30, update)
#
#     update()
#
# # ================= CONCAT =================
# def concatenate_videos(glosses, emphasis_scores):
#
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
#
#     clip_sequence = []
#
#     for gloss in glosses:
#
#         # ✅ Fix 1: match gloss to word scores by splitting gloss into words
#         gloss_words = gloss.lower().replace("_", " ").split()
#         matched_scores = [
#             emphasis_scores[w.upper()] for w in gloss_words if w.upper() in emphasis_scores
#         ]
#         score = float(np.mean(matched_scores)) if matched_scores else 0.3
#
#         # ✅ Fix 2: only slow down emphasized words (score > 0.5)
#         if score > 0.5:
#             speed = 1.0 - (score - 0.5) * 0.8
#             speed = max(speed, 0.5)
#         else:
#             speed = 1.0  # non-emphasized plays at normal speed
#
#         pts_factor = 1.0 / speed
#
#         clip_paths = find_animation_clips(gloss)
#
#         if not clip_paths:
#             print(f"❌ Missing: {gloss}")
#             continue
#
#         for clip_path in clip_paths:
#
#             processed_clip = os.path.join(
#                 OUTPUT_DIR,
#                 f"{len(clip_sequence)}_{os.path.basename(clip_path)}"
#             )
#
#             cmd = [
#                 FFMPEG_PATH,
#                 "-y",
#                 "-i", clip_path,
#                 "-filter:v", f"setpts={pts_factor:.4f}*PTS",
#                 processed_clip
#             ]
#
#             subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#
#             # ✅ store clip + gloss + score for display
#             clip_sequence.append((processed_clip, gloss, round(score, 2)))
#
#     if not clip_sequence:
#         messagebox.showerror("Error", "No animation clips found.")
#         return
#
#     play_sequence_fullscreen(clip_sequence)
#
# def format_gloss_display(gloss):
#     return gloss.replace("_", " ")
# def play_sequence_fullscreen(clip_sequence):
#
#     full_window = tk.Toplevel(root)
#     full_window.attributes("-fullscreen", True)
#     full_window.bind("<Escape>", lambda e: full_window.destroy())
#
#     # ✅ Top bar container
#     top_bar = tk.Frame(full_window, bg="black")
#     top_bar.pack(fill="x")
#
#     # Gloss label (left side of top bar)
#     gloss_label = tk.Label(
#         top_bar,
#         text="",
#         font=("Arial", 40, "bold"),
#         bg="black",
#         fg="white",
#         anchor="w"
#     )
#     gloss_label.pack(side="left", padx=20)
#
#     # ✅ Emphasis score label (right side of top bar)
#     score_label = tk.Label(
#         top_bar,
#         text="",
#         font=("Arial", 24),
#         bg="black",
#         fg="#AAAAAA",
#         anchor="e"
#     )
#     score_label.pack(side="right", padx=20)
#
#     # ✅ Emphasis tag label — shows EMPHASIZED / - below the top bar
#     tag_label = tk.Label(
#         full_window,
#         text="",
#         font=("Arial", 16, "italic"),
#         bg="black",
#         fg="#AAAAAA"
#     )
#     tag_label.pack(fill="x", padx=20)
#
#     # Video display
#     video_label = tk.Label(full_window, bg="black")
#     video_label.pack(fill="both", expand=True)
#
#     full_window.update()
#
#     index = 0
#     cap = None
#
#     def play_next_clip():
#
#         nonlocal index, cap
#
#         if index >= len(clip_sequence):
#             if cap:
#                 cap.release()
#             full_window.destroy()
#             return
#
#         clip_path, gloss, score = clip_sequence[index]
#
#         # ✅ Update gloss text
#         gloss_label.config(text=format_gloss_display(gloss))
#
#         # ✅ Update emphasis score — color changes based on level
#         if score > 0.5:
#             score_color = "#FF6B6B"   # red-ish for high emphasis
#             tag_text    = "EMPHASIZED"
#             tag_color   = "#FF6B6B"
#         elif score > 0.2:
#             score_color = "#FFD93D"   # yellow for moderate
#             tag_text    = "moderate"
#             tag_color   = "#FFD93D"
#         else:
#             score_color = "#AAAAAA"   # gray for low
#             tag_text    = "—"
#             tag_color   = "#AAAAAA"
#
#         score_label.config(text=f"emphasis: {score:.2f}", fg=score_color)
#         tag_label.config(text=tag_text, fg=tag_color)
#
#         cap = cv2.VideoCapture(clip_path)
#
#         def update_frame():
#             nonlocal cap, index
#
#             ret, frame = cap.read()
#
#             if not ret:
#                 cap.release()
#                 index += 1
#                 play_next_clip()
#                 return
#
#             frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#
#             screen_w = full_window.winfo_screenwidth()
#             screen_h = full_window.winfo_screenheight() - 120  # ✅ account for top bar + tag
#
#             frame = cv2.resize(frame, (screen_w, screen_h))
#
#             img = Image.fromarray(frame)
#             imgtk = ImageTk.PhotoImage(image=img)
#
#             video_label.imgtk = imgtk
#             video_label.configure(image=imgtk)
#
#             full_window.after(30, update_frame)
#
#         update_frame()
#
#     play_next_clip()
# # ================= MAIN =================
# def on_generate():
#     text = input_text.get("1.0", tk.END).strip()
#
#     if not text:
#         messagebox.showerror("Error", "Enter text")
#         return
#
#     glosses = predict_gloss(text)
#     glosses = resolve_gloss_sequence(glosses)
#
#     # 🔥 HANDLE TEXT-ONLY CASE
#     if os.path.exists(FINAL_AUDIO):
#         emphasis_scores = predict_emphasis(glosses, FINAL_AUDIO)
#     else:
#         emphasis_scores = {g: 0.3 for g in glosses}
#
#     concatenate_videos(glosses, emphasis_scores)
#
# def upload_video():
#     path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov")])
#
#     if path:
#         final_audio = process_video_audio(path)
#
#         if not final_audio:
#             return
#
#         text = transcribe_audio(final_audio)
#
#         input_text.delete("1.0", tk.END)
#         input_text.insert(tk.END, text)
#
#         on_generate()
#
# # ================= UI =================
# root = tk.Tk()
# root.title("ISL Avatar Generator")
# root.geometry("540x650")
#
# tk.Label(root, text="Enter Text", font=("Arial", 12)).pack(pady=5)
#
# input_text = tk.Text(root, height=4, width=50)
# input_text.pack(pady=5)
#
# tk.Button(root, text="Generate Sign Animation", command=on_generate, width=30).pack(pady=10)
#
# tk.Label(root, text="OR").pack()
#
# tk.Button(root, text="Upload Video", command=upload_video, width=30).pack(pady=10)
#
# tk.Label(root, text="Generated ISL Avatar Output", font=("Arial", 12)).pack(pady=10)
#
# video_label = tk.Label(root)
# video_label.pack(pady=5)
#
# root.mainloop()



# ================= IMPORTS =================
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess
import cv2
from PIL import Image, ImageTk
import numpy as np
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
import noisereduce as nr
import librosa
import soundfile as sf
from speech_to_text import transcribe_audio
from gloss_predictor import predict_gloss
import re
import threading
import time

from Emphasis_module.predict_emphasis import predict_emphasis

print("✅ Emphasis model loaded")

# ================= CONFIG =================
ANIMATION_DIR  = "animations"
OUTPUT_DIR     = "temp"
FFMPEG_PATH    = "ffmpeg"
AUDIO_DIR      = "audio"
RAW_AUDIO      = os.path.join(AUDIO_DIR, "raw.wav")
MONO_AUDIO     = os.path.join(AUDIO_DIR, "mono.wav")
DENOISED_AUDIO = os.path.join(AUDIO_DIR, "clean.wav")
FINAL_AUDIO    = os.path.join(AUDIO_DIR, "final.wav")

# ================= THEME =================
T = {
    "bg":            "#F7F8FC",
    "bg_card":       "#FFFFFF",
    "bg_input":      "#F1F3F9",
    "accent":        "#5B7CFA",
    "accent_light":  "#EBF0FF",
    "accent_dark":   "#3A58D4",
    "text_primary":  "#1A1D2E",
    "text_secondary":"#5A607A",
    "text_hint":     "#9AA0BA",
    "success":       "#2ECC8E",
    "warning":       "#F0A500",
    "danger":        "#E05555",
    "border":        "#DDE1EF",
    "border_focus":  "#5B7CFA",
}

# ================= BUILD INDEX =================
def build_animation_index():
    index = {}
    if not os.path.exists(ANIMATION_DIR):
        return index
    for file in os.listdir(ANIMATION_DIR):
        if file.endswith(".mp4"):
            key = file.replace(".mp4", "").upper()
            index[key] = os.path.join(ANIMATION_DIR, file)
    return index

ANIMATION_INDEX = build_animation_index()

# ================= LONGEST MATCH =================
def resolve_gloss_sequence(glosses):
    resolved = []
    i = 0
    n = len(glosses)
    while i < n:
        found = False
        for j in range(n, i, -1):
            phrase = "_".join(glosses[i:j]).upper()
            if phrase in ANIMATION_INDEX:
                resolved.append(phrase)
                i = j
                found = True
                break
        if not found:
            resolved.append(glosses[i].upper())
            i += 1
    return resolved

# ================= SMART MATCH + FINGERSPELLING =================
def find_animation_clips(gloss):
    clips = []
    gloss = gloss.upper()
    if gloss in ANIMATION_INDEX:
        return [ANIMATION_INDEX[gloss]]
    clean = re.sub(r"[^\w\s]", "", gloss).replace(" ", "_")
    if clean in ANIMATION_INDEX:
        return [ANIMATION_INDEX[clean]]
    words = re.split(r"[_\s]", clean)
    split_clips = []
    for word in words:
        if word in ANIMATION_INDEX:
            split_clips.append(ANIMATION_INDEX[word])
        else:
            split_clips = []
            break
    if split_clips:
        return split_clips
    # Fingerspelling fallback
    print(f"🔤 Fingerspelling for: {gloss}")
    for char in clean:
        if char.isalpha() and char.upper() in ANIMATION_INDEX:
            clips.append(ANIMATION_INDEX[char.upper()])
    return clips

# ================= AUDIO PIPELINE =================
def extract_audio(video_path):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(RAW_AUDIO)
    return RAW_AUDIO

def convert_to_mono(input_audio):
    audio = AudioSegment.from_file(input_audio)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(MONO_AUDIO, format="wav")
    return MONO_AUDIO

def reduce_noise(input_audio):
    data, rate = librosa.load(input_audio, sr=16000)
    reduced = nr.reduce_noise(y=data, sr=rate)
    sf.write(DENOISED_AUDIO, reduced, rate)
    return DENOISED_AUDIO

def trim_silence(input_audio):
    audio = AudioSegment.from_wav(input_audio)
    trimmed = audio.strip_silence(silence_len=800, silence_thresh=-40)
    trimmed.export(FINAL_AUDIO, format="wav")
    return FINAL_AUDIO

def process_video_audio(video_path):
    try:
        raw   = extract_audio(video_path)
        mono  = convert_to_mono(raw)
        clean = reduce_noise(mono)
        final = trim_silence(clean)
        print("✅ Audio ready:", final)
        return final
    except Exception as e:
        messagebox.showerror("Audio Error", str(e))
        return None

# ================= CONCAT + SPEED =================
def concatenate_videos(glosses, emphasis_scores):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    clip_sequence = []

    for gloss in glosses:
        gloss_words    = gloss.lower().replace("_", " ").split()
        matched_scores = [
            emphasis_scores[w.upper()] for w in gloss_words
            if w.upper() in emphasis_scores
        ]
        score = float(np.mean(matched_scores)) if matched_scores else 0.3

        if score > 0.5:
            speed = 1.0 - (score - 0.5) * 0.8
            speed = max(speed, 0.5)
        else:
            speed = 1.0

        pts_factor = 1.0 / speed
        clip_paths = find_animation_clips(gloss)

        if not clip_paths:
            print(f"❌ Missing: {gloss}")
            continue

        for clip_path in clip_paths:
            processed_clip = os.path.join(
                OUTPUT_DIR,
                f"{len(clip_sequence)}_{os.path.basename(clip_path)}"
            )
            cmd = [
                FFMPEG_PATH, "-y", "-i", clip_path,
                "-filter:v", f"setpts={pts_factor:.4f}*PTS",
                processed_clip
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            clip_sequence.append((processed_clip, gloss, round(score, 2)))

    if not clip_sequence:
        messagebox.showerror("Error", "No animation clips found.")
        return

    play_sequence_fullscreen(clip_sequence)

def format_gloss_display(gloss):
    return gloss.replace("_", " ")

# ================= FULLSCREEN PLAYER =================
def play_sequence_fullscreen(clip_sequence):
    player = tk.Toplevel(root)
    player.attributes("-fullscreen", True)
    player.configure(bg="#0D0D12")
    player.bind("<Escape>", lambda e: player.destroy())

    sw    = player.winfo_screenwidth()
    sh    = player.winfo_screenheight()
    bar_h = 96

    # Video area
    video_lbl = tk.Label(player, bg="#0D0D12")
    video_lbl.place(x=0, y=0, width=sw, height=sh - bar_h)

    # Info bar
    bar = tk.Frame(player, bg="#12121A", height=bar_h)
    bar.place(x=0, y=sh - bar_h, width=sw, height=bar_h)
    tk.Frame(bar, bg=T["accent"], height=2).pack(fill="x")

    row = tk.Frame(bar, bg="#12121A")
    row.pack(fill="both", expand=True, padx=28, pady=10)

    gloss_var = tk.StringVar()
    tk.Label(row, textvariable=gloss_var,
             font=("Helvetica Neue", 30, "bold"),
             bg="#12121A", fg="#FFFFFF",
             anchor="w").pack(side="left")

    right = tk.Frame(row, bg="#12121A")
    right.pack(side="right")

    tag_var   = tk.StringVar()
    score_var = tk.StringVar()

    tag_lbl = tk.Label(right, textvariable=tag_var,
                       font=("Helvetica Neue", 11, "bold"),
                       bg="#12121A", fg="#9AA0BA", anchor="e")
    tag_lbl.pack(anchor="e")

    score_lbl = tk.Label(right, textvariable=score_var,
                         font=("Helvetica Neue", 10),
                         bg="#12121A", fg="#5A607A", anchor="e")
    score_lbl.pack(anchor="e")

    tk.Label(bar, text="ESC to close",
             font=("Helvetica Neue", 8),
             bg="#12121A", fg="#2A2A3A",
             anchor="e", padx=20).pack(side="bottom", fill="x")

    index = [0]
    cap   = [None]

    def play_next():
        if index[0] >= len(clip_sequence):
            if cap[0]:
                cap[0].release()
            player.destroy()
            return

        clip_path, gloss, score = clip_sequence[index[0]]
        gloss_var.set(format_gloss_display(gloss))
        score_var.set(f"emphasis: {score:.2f}")

        if score > 0.5:
            tag_var.set("emphasized")
            tag_lbl.config(fg="#7B9EFF")
            score_lbl.config(fg="#7B9EFF")
        elif score > 0.2:
            tag_var.set("moderate")
            tag_lbl.config(fg="#F0A500")
            score_lbl.config(fg="#F0A500")
        else:
            tag_var.set("low")
            tag_lbl.config(fg="#5A607A")
            score_lbl.config(fg="#5A607A")

        cap[0] = cv2.VideoCapture(clip_path)

        def update():
            ret, frame = cap[0].read()
            if not ret:
                cap[0].release()
                index[0] += 1
                play_next()
                return
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (sw, sh - bar_h))
            img   = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            video_lbl.imgtk = imgtk
            video_lbl.configure(image=imgtk)
            player.after(30, update)

        update()

    play_next()

# ================= MAIN APP =================
class ISLApp:

    def __init__(self, root):
        self.root = root
        self.root.title("ISL Avatar Generator")
        self.root.geometry("580x680")
        self.root.configure(bg=T["bg"])
        self.root.resizable(False, False)
        self._processing    = False
        self.selected_video = None
        self._tab_refs      = []
        self._build_ui()

    # ── build ──────────────────────────────────────
    def _build_ui(self):

        # Header card
        hdr = tk.Frame(self.root, bg=T["bg_card"],
                       highlightbackground=T["border"],
                       highlightthickness=1)
        hdr.pack(fill="x")

        hi = tk.Frame(hdr, bg=T["bg_card"])
        hi.pack(fill="x", padx=24, pady=16)

        tk.Frame(hi, width=4, height=40,
                 bg=T["accent"]).pack(side="left", padx=(0, 14))

        tf = tk.Frame(hi, bg=T["bg_card"])
        tf.pack(side="left")
        tk.Label(tf, text="ISL Avatar Generator",
                 font=("Helvetica Neue", 16, "bold"),
                 bg=T["bg_card"], fg=T["text_primary"]).pack(anchor="w")
        tk.Label(tf, text="Prosody-Aware Sign Language Synthesis",
                 font=("Helvetica Neue", 9),
                 bg=T["bg_card"], fg=T["text_hint"]).pack(anchor="w")

        self._sbg = "#E8F8F1"
        self._sf  = tk.Frame(hi, bg=self._sbg,
                             highlightbackground=T["success"],
                             highlightthickness=1)
        self._sf.pack(side="right")
        self._sl = tk.Label(self._sf, text="  Ready  ",
                            font=("Helvetica Neue", 9),
                            bg=self._sbg, fg="#1A7A50")
        self._sl.pack(padx=6, pady=3)

        # Body
        body = tk.Frame(self.root, bg=T["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=18)

        # Mode label + tabs
        tk.Label(body, text="Input mode",
                 font=("Helvetica Neue", 9),
                 bg=T["bg"], fg=T["text_hint"]).pack(anchor="w", pady=(0, 4))

        tab_wrap = tk.Frame(body, bg=T["border"], padx=1, pady=1)
        tab_wrap.pack(anchor="w", pady=(0, 12))

        self.mode = tk.StringVar(value="text")
        for val, lbl in [("text", "  Text Input  "), ("video", "  Video Upload  ")]:
            rb = tk.Radiobutton(
                tab_wrap, text=lbl,
                variable=self.mode, value=val,
                font=("Helvetica Neue", 10),
                bg=T["bg_card"], fg=T["text_secondary"],
                activebackground=T["accent_light"],
                activeforeground=T["accent"],
                selectcolor=T["accent_light"],
                indicatoron=False, relief="flat", bd=0,
                padx=14, pady=7, cursor="hand2",
                command=self._on_mode_change
            )
            rb.pack(side="left")
            if val == "text":
                rb.config(bg=T["accent_light"], fg=T["accent"])
            self._tab_refs.append((val, rb))

        # Text card
        self.text_card = self._card(body)
        self.text_card.pack(fill="x", pady=(0, 10))

        tk.Label(self.text_card, text="Enter text to translate",
                 font=("Helvetica Neue", 9),
                 bg=T["bg_card"], fg=T["text_hint"],
                 anchor="w").pack(anchor="w", padx=16, pady=(12, 4))

        self.text_input = tk.Text(
            self.text_card, height=5,
            font=("Helvetica Neue", 12),
            bg=T["bg_input"], fg=T["text_primary"],
            insertbackground=T["accent"],
            relief="flat", bd=0, wrap="word",
            padx=12, pady=10,
            highlightthickness=1,
            highlightbackground=T["border"],
            highlightcolor=T["border_focus"]
        )
        self.text_input.pack(fill="x", padx=16)
        self.text_input.bind("<FocusIn>",
            lambda e: self.text_input.config(highlightbackground=T["border_focus"]))
        self.text_input.bind("<FocusOut>",
            lambda e: self.text_input.config(highlightbackground=T["border"]))

        self.char_var = tk.StringVar(value="0 characters")
        tk.Label(self.text_card, textvariable=self.char_var,
                 font=("Helvetica Neue", 8),
                 bg=T["bg_card"], fg=T["text_hint"],
                 anchor="e", padx=16, pady=6).pack(fill="x")
        self.text_input.bind("<KeyRelease>", self._update_char)

        # Video card (hidden by default)
        self.video_card = self._card(body)

        drop = tk.Frame(self.video_card, bg=T["bg_input"],
                        highlightbackground=T["border"],
                        highlightthickness=1)
        drop.pack(fill="x", padx=16, pady=14)
        tk.Label(drop, text="↑",
                 font=("Helvetica Neue", 24),
                 bg=T["bg_input"], fg=T["accent"]).pack(pady=(14, 2))
        tk.Label(drop, text="Select a video file",
                 font=("Helvetica Neue", 11, "bold"),
                 bg=T["bg_input"], fg=T["text_primary"]).pack()
        tk.Label(drop, text=".mp4  ·  .avi  ·  .mov",
                 font=("Helvetica Neue", 9),
                 bg=T["bg_input"], fg=T["text_hint"]).pack(pady=(2, 14))

        self.file_var = tk.StringVar(value="No file selected")
        self.file_lbl = tk.Label(
            self.video_card, textvariable=self.file_var,
            font=("Helvetica Neue", 9),
            bg=T["bg_card"], fg=T["text_hint"],
            anchor="w", padx=16)
        self.file_lbl.pack(fill="x")

        tk.Button(
            self.video_card, text="Browse…",
            font=("Helvetica Neue", 10),
            bg=T["bg_card"], fg=T["accent"],
            activebackground=T["accent_light"],
            activeforeground=T["accent_dark"],
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=T["accent"],
            padx=12, pady=5,
            cursor="hand2",
            command=self._browse_video
        ).pack(anchor="e", padx=16, pady=(4, 12))

        self.video_card.pack_forget()

        # Generate button
        self.gen_btn = tk.Button(
            body,
            text="Generate Sign Animation",
            font=("Helvetica Neue", 12, "bold"),
            bg=T["accent"], fg="#FFFFFF",
            activebackground=T["accent_dark"],
            activeforeground="#FFFFFF",
            relief="flat", bd=0,
            pady=13, cursor="hand2",
            command=self._on_generate
        )
        self.gen_btn.pack(fill="x", pady=(2, 14))

        # Log card
        log_card = self._card(body)
        log_card.pack(fill="both", expand=True)

        lh = tk.Frame(log_card, bg=T["bg_card"])
        lh.pack(fill="x", padx=16, pady=(10, 4))
        tk.Label(lh, text="Activity Log",
                 font=("Helvetica Neue", 9, "bold"),
                 bg=T["bg_card"], fg=T["text_secondary"]).pack(side="left")
        tk.Button(lh, text="Clear",
                  font=("Helvetica Neue", 8),
                  bg=T["bg_card"], fg=T["text_hint"],
                  relief="flat", bd=0, cursor="hand2",
                  command=self._clear_log).pack(side="right")

        tk.Frame(log_card, bg=T["border"], height=1).pack(fill="x", padx=16)

        self.log = tk.Text(
            log_card, height=8,
            font=("Courier", 10),
            bg=T["bg_card"], fg=T["text_secondary"],
            relief="flat", bd=0, state="disabled",
            padx=16, pady=10, wrap="word", cursor="arrow"
        )
        self.log.pack(fill="both", expand=True)
        self.log.tag_config("ok",   foreground=T["success"])
        self.log.tag_config("err",  foreground=T["danger"])
        self.log.tag_config("info", foreground=T["accent"])
        self.log.tag_config("warn", foreground=T["warning"])
        self.log.tag_config("ts",   foreground=T["text_hint"])

        # Footer
        tk.Label(self.root,
                 text="Transformer-Based Video to ISL  ·  Prosody-Aware Animation",
                 font=("Helvetica Neue", 8),
                 bg=T["bg"], fg=T["border"]).pack(pady=(0, 8))

        self._log("System ready.", "ok")
        self._log(f"Animation index: {len(ANIMATION_INDEX)} clips loaded.", "info")

    # ── helpers ──────────────────────────────────
    def _card(self, parent):
        return tk.Frame(parent, bg=T["bg_card"],
                        highlightbackground=T["border"],
                        highlightthickness=1)

    def _log(self, msg, tag=""):
        self.log.config(state="normal")
        ts    = time.strftime("%H:%M:%S")
        icons = {"ok": "✓", "err": "✗", "info": "›", "warn": "!"}
        icon  = icons.get(tag, " ")
        self.log.insert("end", f"[{ts}]  ", "ts")
        self.log.insert("end", f"{icon}  {msg}\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")

    def _clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

    def _update_char(self, event=None):
        n = len(self.text_input.get("1.0", "end-1c"))
        self.char_var.set(f"{n} character{'s' if n != 1 else ''}")

    def _set_status(self, state):
        cfg = {
            "ready":      ("#E8F8F1", "#1A7A50", T["success"], "  Ready  "),
            "processing": ("#FFF8E6", "#7A4A00", T["warning"], "  Processing…  "),
            "error":      ("#FDECEA", "#7A1A1A", T["danger"],  "  Error  "),
        }.get(state, ("#E8F8F1", "#1A7A50", T["success"], "  Ready  "))
        self._sf.config(bg=cfg[0], highlightbackground=cfg[2])
        self._sl.config(bg=cfg[0], fg=cfg[1], text=cfg[3])

    def _set_busy(self, busy):
        self._processing = busy
        if busy:
            self.gen_btn.config(state="disabled",
                                bg=T["border"], fg=T["text_hint"],
                                text="Generating…")
            self._set_status("processing")
        else:
            self.gen_btn.config(state="normal",
                                bg=T["accent"], fg="#FFFFFF",
                                text="Generate Sign Animation")
            self._set_status("ready")

    def _on_mode_change(self):
        mode = self.mode.get()
        for val, rb in self._tab_refs:
            rb.config(bg=T["accent_light"] if val == mode else T["bg_card"],
                      fg=T["accent"] if val == mode else T["text_secondary"])
        if mode == "text":
            self.video_card.pack_forget()
            self.text_card.pack(fill="x", pady=(0, 10), before=self.gen_btn)
        else:
            self.text_card.pack_forget()
            self.video_card.pack(fill="x", pady=(0, 10), before=self.gen_btn)

    def _browse_video(self):
        path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mov")]
        )
        if path:
            self.selected_video = path
            name = os.path.basename(path)
            self.file_var.set(f"  {name}")
            self.file_lbl.config(fg=T["accent"])
            self._log(f"Video selected: {name}", "info")

    # ── generate flow ─────────────────────────────
    def _on_generate(self):
        if self._processing:
            return
        if self.mode.get() == "text":
            text = self.text_input.get("1.0", tk.END).strip()
            if not text:
                messagebox.showerror("Error", "Please enter some text first.")
                return
            self._run(lambda: self._from_text(text))
        else:
            if not self.selected_video:
                messagebox.showerror("Error", "Please select a video file first.")
                return
            self._run(lambda: self._from_video(self.selected_video))

    def _run(self, fn):
        self._set_busy(True)
        threading.Thread(target=fn, daemon=True).start()

    def _from_text(self, text):
        try:
            self._log("Predicting gloss sequence…", "info")
            glosses = predict_gloss(text)
            glosses = resolve_gloss_sequence(glosses)
            self._log(f"Glosses: {' › '.join(glosses)}", "info")

            if os.path.exists(FINAL_AUDIO):
                self._log("Running emphasis prediction…", "info")
                scores = predict_emphasis(glosses, FINAL_AUDIO)
                self._log("Emphasis scores computed.", "ok")
            else:
                scores = {g: 0.3 for g in glosses}
                self._log("No audio found — using default emphasis.", "warn")

            self._log("Assembling animation clips…", "info")
            self.root.after(0, lambda: concatenate_videos(glosses, scores))
            self._log("Done. Playing animation.", "ok")
        except Exception as e:
            self._log(f"Error: {e}", "err")
            self.root.after(0, lambda: self._set_status("error"))
        finally:
            self.root.after(0, lambda: self._set_busy(False))

    def _from_video(self, video_path):
        try:
            self._log("Extracting audio from video…", "info")
            final_audio = process_video_audio(video_path)
            if not final_audio:
                self._log("Audio extraction failed.", "err")
                return
            self._log("Transcribing audio…", "info")
            text = transcribe_audio(final_audio)
            preview = text[:60] + ("…" if len(text) > 60 else "")
            self._log(f'Transcribed: "{preview}"', "ok")
            self.root.after(0, lambda: self._set_transcription(text))
        except Exception as e:
            self._log(f"Error: {e}", "err")
            self.root.after(0, lambda: self._set_status("error"))
        finally:
            self.root.after(0, lambda: self._set_busy(False))

    def _set_transcription(self, text):
        self.text_input.delete("1.0", tk.END)
        self.text_input.insert("1.0", text)
        self._update_char()
        self._run(lambda: self._from_text(text))


# ================= LAUNCH =================
root = tk.Tk()
app  = ISLApp(root)
root.mainloop()