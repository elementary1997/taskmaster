
import winsound
import time

print("Testing sound...")
try:
    print("Playing 1046Hz for 120ms")
    winsound.Beep(1046, 120)
    time.sleep(0.1)
    print("Playing 1318Hz for 200ms")
    winsound.Beep(1318, 200)
    print("Sound test complete.")
except Exception as e:
    print(f"Error playing sound: {e}")
