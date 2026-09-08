from typing import Union

def format_timestamp(seconds: Union[int, float], include_ms: bool = True) -> str:
    """Formats float seconds into HH:MM:SS or HH:MM:SS.mmm"""
    if seconds is None or seconds < 0:
        seconds = 0.0
    
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))

    if hrs > 0:
        if include_ms:
            return f"{hrs:02d}:{mins:02d}:{secs:02d}.{ms:03d}"
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    else:
        if include_ms:
            return f"{mins:02d}:{secs:02d}.{ms:03d}"
        return f"{mins:02d}:{secs:02d}"

def parse_timestamp(timestamp_str: str) -> float:
    """Parses HH:MM:SS or MM:SS or HH:MM:SS.mmm string into float seconds"""
    parts = timestamp_str.strip().split(":")
    if len(parts) == 3:
        hrs = float(parts[0])
        mins = float(parts[1])
        secs = float(parts[2])
        return hrs * 3600 + mins * 60 + secs
    elif len(parts) == 2:
        mins = float(parts[0])
        secs = float(parts[1])
        return mins * 60 + secs
    elif len(parts) == 1:
        return float(parts[0])
    return 0.0
