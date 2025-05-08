# Hand-controlled Equalizer
## Before use
Install requirements:
```bat
pip install -r requirements.txt
```
## How to use
- Left hand select frequency band (bass, mid, treble):
    - Fist: Bass
    - Index up: Mid
    - Pinky up: Treble
    - All fingers up: All
- Right hand control gain:
  - If frequency selected: distance between thumb and index finger
  - If overall volume selected: rotation of the wrist

## Install FFmpeg
### Download FFmpeg from the official website: 
1. Go to the website: https://www.ffmpeg.org/
2. Hit download
3. Or, if you use Window, choose https://www.gyan.dev/ffmpeg/builds/
4. And download this version https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z
### Add FFmpeg to PATH:
1. Extracting the ZIP
2. Copy the path to the bin folder inside the extracted directory (e.g., C:\ffmpeg\bin).
3. Open System Properties > Environment Variables.
4. Under System Variables, find Path and click Edit.
5. Click New, then paste the bin path.
6. Click OK on all dialogs.
### Check if pydub can access FFmpeg
``` 
from pydub.utils import which
print(which("ffmpeg"))
```
If it prints None, then FFmpeg is not installed or not on the system path.
