import time
import os
import pathlib
import glob
import subprocess
import numpy as np
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, PatternMatchingEventHandler

def read_request(request_file):
    with open (request_file, "r") as f:
        prompt = f.read()
    return prompt

def get_request_number(request_file):
    return int(os.path.basename(request_file).replace(".txt", ""))

def generate_initial_image(out_dir, request_number, h, w):
    arr = 255 * np.clip((np.random.randn(h,w,3) + 1)/2., 0, 1)
    print(arr.shape)
    Image.fromarray(arr.astype(np.uint8)).save(os.path.join(out_dir, f"interm_{request_number}_{0}.png"))

class Watcher:
    DIRECTORY_TO_WATCH = "outputs/txt2img-samples/frida_requests"
    SAMPLE_DIR = "outputs/txt2img-samples/frida"


    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler(patterns=["*"])
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()


class Handler(PatternMatchingEventHandler):
    def __init__(self, patterns):
        super().__init__(patterns=patterns)
        self.current_process = None

    #@staticmethod
    def on_any_event(self, event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print(f"Received created event - {pathlib.Path(event.src_path)}")
            list_of_files = [os.path.join(Watcher.DIRECTORY_TO_WATCH, f) for f in os.listdir(Watcher.DIRECTORY_TO_WATCH) if f.endswith(".txt")]
            latest_file = max(list_of_files, key=os.path.getctime)
            prompt = read_request(latest_file)
            request_number = get_request_number(latest_file)
            h = 256
            w = 256
            steps = 10
            eta = 0.0
            print(f"Request number: {request_number}")
            print(f"Latest request {latest_file}")
            print(f"Prompt: {prompt}")
            if self.current_process is not None:
                print("Killing current process...")
                self.current_process.terminate()
                self.current_process.wait()
                print("Current process killed, start new...")

            self.current_process = subprocess.Popen(f'python ./scripts/txt2img.py --prompt "{prompt}" --ddim_eta {eta} --n_samples 1 --n_iter 1 --scale 5.0  --ddim_steps {steps} --H 256 --W 512 --request_number {request_number}', shell=True)

        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            print(f"Received modified event - {event.src_path}")


if __name__ == '__main__':
    w = Watcher()
    w.run()
