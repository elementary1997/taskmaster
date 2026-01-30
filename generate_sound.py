import wave
import math
import struct
import os

def generate_chime(filename="audio/completion.wav", duration=0.5, freq=880.0, sample_rate=44100):
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    n_samples = int(sample_rate * duration)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1) # Mono
        wav_file.setsampwidth(2) # 2 bytes per sample (16-bit)
        wav_file.setframerate(sample_rate)
        
        for i in range(n_samples):
            t = i / sample_rate
            # Add some harmonics for a "bell" like sound
            # Fundamental + 2nd harmonic (lighter) + exponential decay
            
            decay = math.exp(-6 * t)  # Fast decay
            
            value = math.sin(2 * math.pi * freq * t) * 0.6 + \
                    math.sin(2 * math.pi * (freq * 2) * t) * 0.3 + \
                    math.sin(2 * math.pi * (freq * 3) * t) * 0.1
            
            # Apply envelope
            sample = value * decay * 32767.0
            
            # Clipping
            sample = max(-32767, min(32767, sample))
            
            data = struct.pack('<h', int(sample))
            wav_file.writeframes(data)
            
    print(f"Generated {filename}")

def generate_click(filename="audio/click.wav", duration=0.03, freq=2000.0, sample_rate=44100):
    """Генерирует приятный короткий щелчок как в современных таск-менеджерах"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    n_samples = int(sample_rate * duration)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1) # Mono
        wav_file.setsampwidth(2) # 2 bytes per sample (16-bit)
        wav_file.setframerate(sample_rate)
        
        for i in range(n_samples):
            t = i / sample_rate
            
            # Быстрое затухание для короткого щелчка
            # Используем экспоненциальное затухание для мягкого звука
            decay = math.exp(-50 * t)  # Очень быстрое затухание
            
            # Основной тон с небольшой гармоникой для более приятного звука
            value = math.sin(2 * math.pi * freq * t) * 0.8 + \
                    math.sin(2 * math.pi * (freq * 1.5) * t) * 0.2
            
            # Применяем огибающую (envelope) для плавного начала и конца
            if t < duration * 0.1:  # Быстрый подъем в начале
                envelope = t / (duration * 0.1)
            else:  # Экспоненциальное затухание
                envelope = decay
            
            sample = value * envelope * 32767.0 * 0.6  # Немного тише для комфорта
            
            # Clipping
            sample = max(-32767, min(32767, sample))
            
            data = struct.pack('<h', int(sample))
            wav_file.writeframes(data)
            
    print(f"Generated {filename}")

if __name__ == "__main__":
    generate_click()  # Генерируем щелчок по умолчанию
