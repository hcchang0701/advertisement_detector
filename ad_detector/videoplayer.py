from dataclasses import dataclass
from time import time, sleep

import numpy as np
import wave
import pyaudio
import cv2


@dataclass
class CombinedFrame:
    bgr: np.ndarray
    audio: bytes


class VideoPlayer:
    def __init__(self, player_format):
        self.is_paused = False
        self.format = player_format
        self.data = []
    
    def load(self, video_path, audio_path):
        t1 = time()
        
        # Load Video
        width = self.format['video_width']
        height = self.format['video_height']
        fps = self.format['video_fps']
        
        raw_bytes = np.fromfile(video_path, np.dtype('B'))
        frame_count = len(raw_bytes) // (height*width*3)
        frames = raw_bytes.reshape((frame_count, 3, height, width))
        frames = np.moveaxis(frames, 1, -1)  # pack rgb values per pixel
        
        # Load Audio
        audio_rate = self.format['audio_rate']
        
        self.wf = wave.open(audio_path, 'rb')
        self.audio_sample_width = audio_rate // fps
        
        # Combine video and audio and append it to self.data
        for i, frame in enumerate(frames):
            frame[:, :, [2, 0]] = frame[:, :, [0, 2]]  # swap from RGB to BGR
            combined_frame = CombinedFrame(bgr=frame,
                                           audio=self.wf.readframes(self.audio_sample_width))
            self.data.append(combined_frame)
            
        print(f'Loading completed, time eclipsed: {time() - t1} s')
    
    def play(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(self.wf.getsampwidth()),
                        channels=self.wf.getnchannels(),
                        rate=self.wf.getframerate(),
                        output=True)
        
        for i, frame in enumerate(self.data):
            if not self.is_paused:
                start_time = time()
                
                cv2.imshow('film', frame.bgr)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                wait_time = 1 / self.format['video_fps'] - (time() - start_time)
                if wait_time > 0:
                    stream.write(frame.audio) # Sequencial
                    sleep(wait_time)
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        cv2.destroyAllWindows()