# Hand-controlled Equalizer
## Before use
### Install requirements:
```bat
pip install -r requirements.txt
```
### Install FFmpeg
#### Download FFmpeg from the official website: 
1. Go to the website: https://www.ffmpeg.org/
2. Hit download
3. Or, if you use Window, choose https://www.gyan.dev/ffmpeg/builds/
4. And download this version https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z
#### Add FFmpeg to PATH:
1. Extracting the ZIP
2. Copy the path to the bin folder inside the extracted directory (e.g., C:\ffmpeg\bin).
3. Open System Properties > Environment Variables.
4. Under System Variables, find Path and click Edit.
5. Click New, then paste the bin path.
6. Click OK on all dialogs.
#### Check if pydub can access FFmpeg
``` 
from pydub.utils import which
print(which("ffmpeg"))
```
If it prints None, then FFmpeg is not installed or not on the system path.

## How to use

**To Adjust Volume and EQ Settings:**
1. **Initialize Hand Detector**
   Press `Initialize Hand Detection` button in the top left
      1. First put all fingers up ✋, extend the thumb and index finger of the right hand as far as possible.
      2. Hold the right hand, close all 4 fingers of the left hand except for the thumb 👍, then squeeze the right hand's thumb and index finger as close as possible 🤏.
      3. Now close the left thumb. The initialization is done.
2. **Insert music**
   Press `Insert music` and choose your audio file then press ▶️ to play.
3. **Activate Adjustment Mode**
   Signal the system with the **🤟 gesture** to turn **ON** the adjustment controls.
4. **Make Your Changes**
   Select your desired **EQ settings** and **volume level**.
    - **Left hand** select frequency band (bass, mid, treble):
      - Fist ✊: Bass
      - Index up ☝: Mid
      - Pinky up: Treble
      - All fingers up ✋: All
      - 🤟: ON/OFF adjustment control
    - **Right hand** control gain:
      - If frequency selected: distance between thumb and index finger 🤏
      - If overall volume selected: rotation of the wrist
5. **Lock Your Settings**
   Signal the **🤟 gesture again** to **confirm and lock** the values.