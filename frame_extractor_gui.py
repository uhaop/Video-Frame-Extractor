import os
import sys
import cv2
import json
import time
import threading
import multiprocessing as mp
from tkinter import filedialog, StringVar, DoubleVar, IntVar, BooleanVar, Text, Scrollbar, END, VERTICAL, RIGHT, LEFT, Y, BOTH
from ttkbootstrap import Window, Label, Button, Entry, Progressbar, Frame, Checkbutton, Scale, Combobox
from ttkbootstrap import Combobox

SESSION_FILE = "session.json"
LOG_CSV = "log.csv"

class FrameExtractorApp:
    def __init__(self):
        self.root = Window(themename="darkly")
        self.root.title("Video Frame Extractor")
        self.root.geometry("950x750")
        self.root.resizable(True, True)
        self.worker_progress_bars = []
        self.worker_progress_labels = []
        self.worker_progress_frame = None

        try:
            base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
            icon_path = os.path.join(base_path, "icon.ico")
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"⚠️ Icon load failed: {e}")
        

        # GUI State Variables
        self.video_path = StringVar()
        self.output_dir = StringVar()
        self.fps = IntVar(value=30)
        self.blur_thresh = DoubleVar(value=5.0)
        self.progress_var = IntVar()
        self.reset = BooleanVar()
        self.use_multicore = BooleanVar()
        self.worker_count = IntVar(value=4)
        self.save_csv_log = BooleanVar()
        self.processing_mode = StringVar(value="CPU")

        self.build_ui()
    
    def build_worker_progress(self, count):
        if self.worker_progress_frame:
            self.worker_progress_frame.destroy()

        self.worker_progress_frame = Frame(self.container, padding=(20, 0, 20, 0))
        self.worker_progress_frame.grid(row=12, column=0, columnspan=3, sticky="ew")
        self.container.rowconfigure(12, weight=0)

        self.worker_progress_bars.clear()
        self.worker_progress_labels.clear()

        for i in range(count):
            label = Label(self.worker_progress_frame, text=f"[Worker {i}] 0% | 0 / 0", font=("Segoe UI Emoji", 10))
            label.pack(anchor="w", pady=(6, 2))
            self.worker_progress_labels.append(label)

            bar = Progressbar(self.worker_progress_frame, maximum=100)
            bar.pack(fill="x", padx=10, pady=(0, 5))
            self.worker_progress_bars.append(bar)

        # 🪟 Resize window to fit new content
        self.root.update_idletasks()
        total_height = self.root.winfo_reqheight()
        self.root.geometry(f"950x{total_height}")

    def build_ui(self):
        self.container = Frame(self.root, padding=20)
        self.container.pack(fill="both", expand=True)

        # Row 0-1: File input
        Label(self.container, text="Video File:").grid(row=0, column=0, sticky="w", pady=5)
        Entry(self.container, textvariable=self.video_path, width=70).grid(row=0, column=1, pady=5)
        Button(self.container, text="Browse", command=self.browse_video).grid(row=0, column=2, padx=10)

        Label(self.container, text="Output Folder:").grid(row=1, column=0, sticky="w", pady=5)
        Entry(self.container, textvariable=self.output_dir, width=70).grid(row=1, column=1, pady=5)
        Button(self.container, text="Browse", command=self.browse_output).grid(row=1, column=2, padx=10)

        # Row 2-3: Settings
        Label(self.container, text="FPS (Frames Per Second):").grid(row=2, column=0, sticky="w", pady=5)
        Entry(self.container, textvariable=self.fps, width=10).grid(row=2, column=1, sticky="w", pady=5)

        Label(self.container, text="Blur Threshold:").grid(row=3, column=0, sticky="w", pady=5)
        blur_frame = Frame(self.container)
        blur_frame.grid(row=3, column=1, pady=5, sticky="w")
        Scale(blur_frame, variable=self.blur_thresh, from_=1.0, to=100.0, orient="horizontal", length=300).pack(side="left", padx=(0, 10))
        Entry(blur_frame, textvariable=self.blur_thresh, width=5).pack(side="left")

        # Row 4-7: Options
        Checkbutton(self.container, text="Reset Session", variable=self.reset).grid(row=4, column=1, sticky="w", pady=10)
        Checkbutton(self.container, text="Use Multi-Core Mode", variable=self.use_multicore, command=self.toggle_worker_dropdown).grid(row=5, column=1, sticky="w", pady=(10, 5))
        Label(self.container, text="Number of Workers:").grid(row=6, column=0, sticky="w")
        self.worker_dropdown = Combobox(self.container, textvariable=self.worker_count, values=[4, 8, 16], width=5, state="disabled")
        self.worker_dropdown.grid(row=6, column=1, sticky="w", pady=2)

        Checkbutton(self.container, text="Save CSV Log", variable=self.save_csv_log).grid(row=7, column=1, sticky="w", pady=(10, 5))

        # Row 8: Processing Mode
        Label(self.container, text="Processing Mode:").grid(row=8, column=0, sticky="w")
        Combobox(self.container, textvariable=self.processing_mode, values=["CPU", "GPU"], width=8, state="readonly").grid(row=8, column=1, sticky="w")

        # Row 9: Start Button
        Button(self.container, text="▶ Start Extraction", bootstyle="success", command=self.start_thread).grid(row=9, column=1, pady=15)

        # Row 10-11: Status + Overall Progress Bar
        self.status_label = Label(self.container, text="", font=("Segoe UI Emoji", 9))
        self.status_label.grid(row=10, column=1, sticky="w", pady=(0, 10))

        self.progress_label = Label(self.container, text="Progress:")
        self.progress_label.grid(row=11, column=1, sticky="w")

        Progressbar(self.container, variable=self.progress_var, maximum=100).grid(row=12, column=0, columnspan=3, sticky="ew", pady=5)

        for i in range(3):
            self.container.columnconfigure(i, weight=1)


    def browse_video(self):
        file = filedialog.askopenfilename(filetypes=[("Video Files", "*.mov *.mp4 *.avi *.mkv")])
        if file:
            self.video_path.set(file)

    def browse_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_dir.set(folder)

    def toggle_worker_dropdown(self):
        self.worker_dropdown.config(state="readonly" if self.use_multicore.get() else "disabled")

    def start_thread(self):
        thread = threading.Thread(target=self.run_extraction, daemon=True)
        thread.start()

    def log(self, msg):
        # Skip logging if log_text is not defined
        if hasattr(self, "log_text"):
            self.log_text.insert(END, f"{msg}\n")
            self.log_text.see(END)
        else:
            print(msg)  # optional: print to console for dev/debug


    def run(self):
        self.root.mainloop()
    
    def run_extraction(self):
        extract_frames(self)

def save_session(data):
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return None

def format_eta(seconds):
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hours:02}:{minutes:02}:{secs:02}"
    elif hours > 0:
        return f"{hours:02}:{minutes:02}:{secs:02}"
    else:
        return f"{minutes:02}:{secs:02}"

def run_worker(video_path, output_dir, fps, blur_threshold, start_frame, end_frame, return_dict, proc_id):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frame_id = start_frame
    saved = 0
    start_time = time.time()

    # Just record the range
    return_dict[proc_id] = {
        "start": start_frame,
        "end": end_frame
    }

    while frame_id < end_frame:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_id % int(cap.get(cv2.CAP_PROP_FPS) / fps) == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if lap_var > blur_threshold:
                filename = os.path.join(output_dir, f"frame_{frame_id:06}.jpg")
                if not os.path.exists(filename):
                    cv2.imwrite(filename, frame)
                saved += 1  # count even if already exists

        frame_id += 1

    elapsed = time.time() - start_time
    return_dict[proc_id].update({
        "saved": saved,
        "time": round(elapsed, 2)
    })
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frame_id = start_frame
    saved = 0
    total_to_check = 0
    start_time = time.time()

    return_dict[proc_id] = {"done": 0, "total": 0}

    while frame_id < end_frame:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_id % int(cap.get(cv2.CAP_PROP_FPS) / fps) == 0:
            total_to_check += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if lap_var > blur_threshold:
                filename = os.path.join(output_dir, f"frame_{frame_id:06}.jpg")
                if not os.path.exists(filename):
                    cv2.imwrite(filename, frame)
                saved += 1

        frame_id += 1

        if (frame_id - start_frame) % 10 == 0:
            return_dict[proc_id]["done"] = saved
            return_dict[proc_id]["total"] = total_to_check

    elapsed = time.time() - start_time
    return_dict[proc_id].update({
        "start": start_frame,
        "end": end_frame,
        "saved": saved,
        "time": round(elapsed, 2)
    })
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frame_id = start_frame
    saved = 0
    total_to_check = 0
    start_time = time.time()

    # Init dict BEFORE starting loop
    return_dict[proc_id] = {"done": 0, "total": end_frame - start_frame}

    while frame_id < end_frame:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_id % int(cap.get(cv2.CAP_PROP_FPS) / fps) == 0:
            total_to_check += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if lap_var > blur_threshold:
                filename = os.path.join(output_dir, f"frame_{frame_id:06}.jpg")
                if not os.path.exists(filename):
                    cv2.imwrite(filename, frame)
                saved += 1  # Count it even if already exists

        frame_id += 1

        if (frame_id - start_frame) % 10 == 0:
            return_dict[proc_id]["done"] = saved
            return_dict[proc_id]["total"] = total_to_check

    elapsed = time.time() - start_time
    return_dict[proc_id].update({
        "start": start_frame,
        "end": end_frame,
        "saved": saved,
        "time": round(elapsed, 2)
    })
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    saved = 0
    frame_id = start_frame
    total = 0
    start_time = time.time()

    # 🔧 Initialize progress tracking
    return_dict[proc_id] = {"done": 0, "total": end_frame - start_frame}

    while frame_id < end_frame:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_id % int(cap.get(cv2.CAP_PROP_FPS) / fps) == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if lap_var > blur_threshold:
                filename = os.path.join(output_dir, f"frame_{frame_id:06}.jpg")
                cv2.imwrite(filename, frame)
                saved += 1
        frame_id += 1
        total += 1

        # 🔄 Update progress every 10 frames
        if (frame_id - start_frame) % 10 == 0:
            return_dict[proc_id]["done"] = saved  # only count frames actually written


    elapsed = time.time() - start_time
    return_dict[proc_id].update({
        "start": start_frame,
        "end": end_frame,
        "saved": saved,
        "total": total,
        "time": round(elapsed, 2)
    })

def monitor_workers(jobs, return_dict, app, worker_count):
    output_dir = app.output_dir.get()

    # Wait until all worker ranges are populated
    while any(p.is_alive() for p in jobs) and len(return_dict.keys()) < worker_count:
        time.sleep(0.2)

    # Snapshot worker frame ranges
    worker_ranges = {}
    for i in range(worker_count):
        start = return_dict.get(i, {}).get("start", 0)
        end = return_dict.get(i, {}).get("end", 0)
        worker_ranges[i] = (start, end)

    while any(p.is_alive() for p in jobs):
        try:
            files = [f for f in os.listdir(output_dir) if f.startswith("frame_") and f.endswith(".jpg")]
        except:
            continue  # skip temporarily if I/O error

        for i in range(worker_count):
            if i >= len(app.worker_progress_bars):
                continue

            start, end = worker_ranges.get(i, (0, 0))
            total = end - start
            count = sum(
                1 for f in files
                if f.startswith("frame_")
                and start <= int(f[6:12]) < end
            )
            percent = int((count / total) * 100) if total else 0
            status = f"{percent}% | {count} / {total}"

            app.worker_progress_bars[i].config(value=percent)
            app.worker_progress_labels[i].config(text=f"[Worker {i}] {status}")
        time.sleep(0.5)
    while any(p.is_alive() for p in jobs):
        for i in range(worker_count):
            if i in return_dict and i < len(app.worker_progress_bars):
                done = return_dict[i].get("done", 0)
                total = return_dict[i].get("total", 1)
                percent = int((done / total) * 100) if total > 0 else 0
                status = f"{percent}% | {done} / {total}" if total > 0 else "Starting..."

                app.worker_progress_bars[i].config(value=percent)
                app.worker_progress_labels[i].config(text=f"[Worker {i}] {status}")
        time.sleep(0.5)
    while any(p.is_alive() for p in jobs):
        for i in range(worker_count):
            if i in return_dict:
                done = return_dict[i].get("done", 0)
                total = return_dict[i].get("total", 1)
                percent = int((done / total) * 100) if total > 0 else 0
                status = f"{percent}% | {done} / {total}" if total > 0 else "Starting..."

                app.worker_progress_bars[i].config(value=percent)
                app.worker_progress_labels[i].config(text=f"[Worker {i}] {status}")
        time.sleep(0.5)
    while any(p.is_alive() for p in jobs):
        for i in range(worker_count):
            if i in return_dict:
                done = return_dict[i].get("done", 0)
                total = return_dict[i].get("total", 1)
                percent = int((done / total) * 100) if total > 0 else 0
                status = f"{percent}% | {done} / {total}" if total > 0 else "Starting..."

                app.worker_progress_bars[i].config(value=percent)
                app.worker_progress_labels[i].config(text=f"[Worker {i}] {status}")
        time.sleep(0.5)

def extract_frames(app):
    video_path = app.video_path.get()
    output_dir = app.output_dir.get()
    fps = app.fps.get()
    blur_threshold = app.blur_thresh.get()
    reset = app.reset.get()
    use_multicore = app.use_multicore.get()
    worker_count = app.worker_count.get()
    save_csv = app.save_csv_log.get()

    if not os.path.isfile(video_path) or not output_dir:
        app.log("❌ Please select a valid video file and output folder.")
        return

    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    step = max(int(video_fps / fps), 1)
    cap.release()

    if use_multicore:
        chunk_size = total_frames // worker_count
        manager = mp.Manager()
        return_dict = manager.dict()
        jobs = []

        app.status_label.config(text=f"🚀 Launching {worker_count} processes...")
        app.build_worker_progress(worker_count)
        start_time = time.time()

        for i in range(worker_count):
            start_f = i * chunk_size
            end_f = total_frames if i == worker_count - 1 else (i + 1) * chunk_size
            p = mp.Process(
                target=run_worker,
                args=(video_path, output_dir, fps, blur_threshold, start_f, end_f, return_dict, i)
            )
            jobs.append(p)
            p.start()

        # ✅ Start monitor thread only ONCE, after all workers are started
        monitor_thread = threading.Thread(
            target=lambda: monitor_workers(jobs, return_dict, app, worker_count),
            daemon=True
        )
        monitor_thread.start()

        for job in jobs:
            job.join()

        total_saved = sum([v["saved"] for v in return_dict.values()])
        app.log(f"\n✅ All processes complete! Total saved: {total_saved} frames.")
        app.progress_var.set(100)
        app.progress_label.config(text="Done")

        # CSV Export or Console Log Summary
        lines = []
        for pid, stats in return_dict.items():
            summary = f"[Worker {pid}] Frames {stats['start']}-{stats['end']} | Saved: {stats['saved']} | Time: {stats['time']}s"
            lines.append(summary)
            app.log(summary)

        if save_csv:
            with open(LOG_CSV, "w") as f:
                f.write("Worker,Start Frame,End Frame,Saved Frames,Total Processed,Time (s)\n")
                for pid, stats in return_dict.items():
                    f.write(f"{pid},{stats['start']},{stats['end']},{stats['saved']},{stats['total']},{stats['time']}\n")
            app.log(f"\n📁 Log saved as '{LOG_CSV}'")

    else:
        extract_frames_singlecore(app)
    video_path = app.video_path.get()
    output_dir = app.output_dir.get()
    fps = app.fps.get()
    blur_threshold = app.blur_thresh.get()
    reset = app.reset.get()
    use_multicore = app.use_multicore.get()
    worker_count = app.worker_count.get()
    save_csv = app.save_csv_log.get()

    if not os.path.isfile(video_path) or not output_dir:
        app.log("❌ Please select a valid video file and output folder.")
        return

    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    step = max(int(video_fps / fps), 1)
    cap.release()

    if use_multicore:
        chunk_size = total_frames // worker_count
        manager = mp.Manager()
        return_dict = manager.dict()
        jobs = []

        app.status_label.config(text=f"🚀 Launching {worker_count} processes...")
        app.build_worker_progress(worker_count)
        start_time = time.time()

        for i in range(worker_count):
            start_f = i * chunk_size
            end_f = total_frames if i == worker_count - 1 else (i + 1) * chunk_size
            p = mp.Process(target=run_worker, args=(video_path, output_dir, fps, blur_threshold, start_f, end_f, return_dict, i))
            jobs.append(p)
            p.start()
            monitor_thread = threading.Thread(
                target=lambda: monitor_workers(jobs, return_dict, app, worker_count),
                daemon=True
            )
            monitor_thread.start()

        for job in jobs:
            job.join()

        total_saved = sum([v["saved"] for v in return_dict.values()])
        app.log(f"\n✅ All processes complete! Total saved: {total_saved} frames.")
        app.progress_var.set(100)
        app.progress_label.config(text="Done")

        # CSV Export or Console Log Summary
        lines = []
        for pid, stats in return_dict.items():
            summary = f"[Worker {pid}] Frames {stats['start']}-{stats['end']} | Saved: {stats['saved']} | Time: {stats['time']}s"
            lines.append(summary)
            app.log(summary)

        if save_csv:
            with open(LOG_CSV, "w") as f:
                f.write("Worker,Start Frame,End Frame,Saved Frames,Total Processed,Time (s)\n")
                for pid, stats in return_dict.items():
                    f.write(f"{pid},{stats['start']},{stats['end']},{stats['saved']},{stats['total']},{stats['time']}\n")
            app.log(f"\n📁 Log saved as '{LOG_CSV}'")

    else:
        # fallback to single-threaded version (in part 3)
        extract_frames_singlecore(app)

def extract_frames_singlecore(app):
    video_path = app.video_path.get()
    output_dir = app.output_dir.get()
    fps = app.fps.get()
    blur_threshold = app.blur_thresh.get()
    reset = app.reset.get()

    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(int(video_fps / fps), 1)

    # Session
    session = {
        "video_path": video_path,
        "output_dir": output_dir,
        "fps": fps,
        "blur_threshold": blur_threshold,
        "last_frame": 0
    }

    existing = load_session()
    if existing and not reset and existing["video_path"] == video_path:
        session["last_frame"] = existing["last_frame"]

    start_frame = session["last_frame"]
    saved = len([f for f in os.listdir(output_dir) if f.endswith(".jpg")])
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frame_id = start_frame

    app.log(f"▶ Starting from frame {start_frame} / {total_frames} | Saving every {step} frames")
    start_time = time.time()
    time_buffer = []

    while frame_id < total_frames:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_id % step == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if lap_var > blur_threshold:
                filename = os.path.join(output_dir, f"frame_{frame_id:06}.jpg")
                if not os.path.exists(filename):
                    cv2.imwrite(filename, frame)
                    saved += 1
                else:
                    saved += 1  # Count it toward progress if already exists

        frame_id += 1
        session["last_frame"] = frame_id
        save_session(session)

        elapsed = time.time() - start_time
        time_buffer.append(elapsed)
        if len(time_buffer) > 10:
            time_buffer.pop(0)

        avg = sum(time_buffer) / len(time_buffer)
        remaining = int((total_frames - frame_id) * (avg / step))
        eta = format_eta(remaining)
        percent = int((frame_id / total_frames) * 100)

        app.progress_var.set(percent)
        app.progress_label.config(text=f"{percent}% | ETA: {eta}")
        app.root.update_idletasks()

    cap.release()
    app.progress_var.set(100)
    app.progress_label.config(text="Done")
    app.log(f"\n✅ Done! Total saved: {saved} frames.")

if __name__ == "__main__":
    mp.freeze_support()
    app = FrameExtractorApp()
    app.run()

