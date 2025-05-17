import sys
import time
import threading
import platform
import logging

try:
    import vlc
except ImportError:
    print("The python-vlc module is not installed. Please install it with: pip install python-vlc")
    sys.exit(1)

try:
    from yt_dlp import YoutubeDL
except ImportError:
    print("The yt-dlp module is not installed. Please install it with: pip install yt-dlp")
    sys.exit(1)

# Try to import the keyboard module; if not available, we'll fall back to manual input.
try:
    import keyboard  # pip install keyboard
    use_keyboard = True
except ImportError:
    use_keyboard = False
    print("The 'keyboard' module is not installed. For improved controls, install it with: pip install keyboard")
    print("Falling back to manual input commands.")

# Set up basic logging for yt_dlp debug messages.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_video_stream_url(yt_url):
    """
    Extract the direct video stream URL from a YouTube link using yt-dlp.
    """
    ydl_opts = {
        'quiet': False,
        'format': 'best',
        'logger': logger,
        'simulate': True,  # Extract info without downloading.
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)
        stream_url = info.get('url')
        if not stream_url:
            # Fallback: choose the first format with a video codec.
            for fmt in info.get('formats', []):
                if fmt.get('vcodec') != 'none':
                    stream_url = fmt.get('url')
                    break
        return stream_url
    except Exception as e:
        print("Error extracting video info:", e)
        return None

def listen_for_controls(player):
    """
    Listen for key presses for controlling playback.
    
    - Press 'q' to quit playback.
    - Press 'p' to toggle pause/play.
    
    Uses the keyboard module if available; otherwise falls back to manual input.
    """
    if use_keyboard:
        print("Press 'q' to stop playback or 'p' to toggle pause/resume.")
        while True:
            # Check for 'q' to stop
            if keyboard.is_pressed('q'):
                print("Detected 'q' key press. Stopping playback...")
                player.stop()
                break
            # Check for 'p' to toggle pause/play
            if keyboard.is_pressed('p'):
                print("Detected 'p' key press. Toggling pause/resume...")
                player.pause()  # pause() toggles pause state in VLC
                time.sleep(0.4)  # simple debounce delay
            time.sleep(0.1)  # avoid high CPU usage
    else:
        # Fallback: manual input loop.
        print("Enter command: 'q' to quit or 'p' to toggle pause/resume.")
        while True:
            command = input("Command: ").strip().lower()
            if command == 'q':
                print("Stop command received from input. Stopping playback...")
                player.stop()
                break
            elif command == 'p':
                print("Pause/resume command received from input. Toggling pause/resume...")
                player.pause()
            else:
                print("Invalid command. Please enter 'q' or 'p'.")

def main():
    yt_url = input("Enter YouTube URL: ").strip()
    if not yt_url:
        print("Invalid URL. Exiting.")
        sys.exit(1)

    stream_url = get_video_stream_url(yt_url)
    if not stream_url:
        print("Could not retrieve a valid video stream URL from the provided link.")
        sys.exit(1)

    print("Starting video playback...")
    try:
        player = vlc.MediaPlayer(stream_url)
    except Exception as e:
        print("Error initializing VLC MediaPlayer:", e)
        sys.exit(1)

    # Start playback.
    ret = player.play()
    if ret == -1:
        print("VLC failed to start playback. Check your VLC installation.")
        sys.exit(1)

    # Give VLC a moment to initialize.
    time.sleep(1)
    print("Initial VLC player state:", player.get_state())

    # Start a separate thread to listen for control commands.
    listener = threading.Thread(target=listen_for_controls, args=(player,), daemon=True)
    listener.start()

    # Main loop: Wait until playback ends.
    try:
        while True:
            state = player.get_state()
            if state in (vlc.State.Ended, vlc.State.Error):
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("Playback interrupted by user (KeyboardInterrupt).")
    
    print("Video playback ended.")

if __name__ == "__main__":
    main()
