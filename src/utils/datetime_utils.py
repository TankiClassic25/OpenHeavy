"""
Datetime utility functions for OpenHeavy application.
Provides consistent datetime handling and formatting.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Union
import time


def get_current_datetime() -> datetime:
    """
    Get current datetime in UTC.
    
    Returns:
        Current datetime in UTC timezone
    """
    return datetime.now(timezone.utc)


def get_current_timestamp() -> float:
    """
    Get current timestamp as float.
    
    Returns:
        Current timestamp in seconds since epoch
    """
    return time.time()


def format_datetime(
    dt: datetime, 
    format_string: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime to format
        format_string: Format string (default: ISO-like format)
        
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_string)


def format_current_datetime(format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format current datetime to string.
    
    Args:
        format_string: Format string
        
    Returns:
        Formatted current datetime string
    """
    return format_datetime(get_current_datetime(), format_string)


def parse_datetime(
    datetime_string: str, 
    format_string: str = "%Y-%m-%d %H:%M:%S"
) -> datetime:
    """
    Parse datetime string to datetime object.
    
    Args:
        datetime_string: String to parse
        format_string: Expected format
        
    Returns:
        Parsed datetime object
        
    Raises:
        ValueError: If string doesn't match format
    """
    return datetime.strptime(datetime_string, format_string)


def timestamp_to_datetime(timestamp: float) -> datetime:
    """
    Convert timestamp to datetime.
    
    Args:
        timestamp: Timestamp in seconds since epoch
        
    Returns:
        Datetime object in UTC
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def datetime_to_timestamp(dt: datetime) -> float:
    """
    Convert datetime to timestamp.
    
    Args:
        dt: Datetime object
        
    Returns:
        Timestamp in seconds since epoch
    """
    return dt.timestamp()


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "2m 30s", "1h 15m")
    """
    if seconds < 0:
        return "0s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:  # Always show seconds if no other parts
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def format_duration_precise(seconds: float) -> str:
    """
    Format duration with millisecond precision.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string with milliseconds
    """
    if seconds < 1:
        ms = int(seconds * 1000)
        return f"{ms}ms"
    
    return format_duration(seconds)


def get_elapsed_time(start_time: float) -> float:
    """
    Get elapsed time since start time.
    
    Args:
        start_time: Start timestamp
        
    Returns:
        Elapsed time in seconds
    """
    return time.time() - start_time


def format_elapsed_time(start_time: float) -> str:
    """
    Format elapsed time since start time.
    
    Args:
        start_time: Start timestamp
        
    Returns:
        Formatted elapsed time string
    """
    elapsed = get_elapsed_time(start_time)
    return format_duration(elapsed)


def is_recent(dt: datetime, threshold_minutes: int = 5) -> bool:
    """
    Check if datetime is recent (within threshold).
    
    Args:
        dt: Datetime to check
        threshold_minutes: Threshold in minutes
        
    Returns:
        True if datetime is within threshold
    """
    now = get_current_datetime()
    threshold = timedelta(minutes=threshold_minutes)
    
    # Handle timezone-naive datetimes
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return (now - dt) <= threshold


def add_timezone(dt: datetime, tz: timezone = timezone.utc) -> datetime:
    """
    Add timezone to naive datetime.
    
    Args:
        dt: Naive datetime
        tz: Timezone to add
        
    Returns:
        Timezone-aware datetime
    """
    if dt.tzinfo is not None:
        return dt
    
    return dt.replace(tzinfo=tz)


def to_utc(dt: datetime) -> datetime:
    """
    Convert datetime to UTC.
    
    Args:
        dt: Datetime to convert
        
    Returns:
        Datetime in UTC timezone
    """
    if dt.tzinfo is None:
        # Assume local timezone for naive datetime
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.astimezone(timezone.utc)


def format_iso(dt: Optional[datetime] = None) -> str:
    """
    Format datetime as ISO string.
    
    Args:
        dt: Datetime to format (current time if None)
        
    Returns:
        ISO formatted datetime string
    """
    if dt is None:
        dt = get_current_datetime()
    
    return dt.isoformat()


def parse_iso(iso_string: str) -> datetime:
    """
    Parse ISO datetime string.
    
    Args:
        iso_string: ISO formatted datetime string
        
    Returns:
        Parsed datetime object
    """
    return datetime.fromisoformat(iso_string)


class Timer:
    """
    Simple timer class for measuring execution time.
    """
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def start(self) -> 'Timer':
        """Start the timer"""
        self.start_time = time.time()
        self.end_time = None
        return self
    
    def stop(self) -> float:
        """
        Stop the timer and return elapsed time.
        
        Returns:
            Elapsed time in seconds
        """
        if self.start_time is None:
            raise ValueError("Timer not started")
        
        self.end_time = time.time()
        return self.elapsed()
    
    def elapsed(self) -> float:
        """
        Get elapsed time.
        
        Returns:
            Elapsed time in seconds
        """
        if self.start_time is None:
            return 0.0
        
        end_time = self.end_time or time.time()
        return end_time - self.start_time
    
    def elapsed_formatted(self) -> str:
        """
        Get formatted elapsed time.
        
        Returns:
            Formatted elapsed time string
        """
        return format_duration_precise(self.elapsed())
    
    def __enter__(self) -> 'Timer':
        """Context manager entry"""
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        self.stop()


def measure_time(func):
    """
    Decorator to measure function execution time.
    
    Args:
        func: Function to measure
        
    Returns:
        Decorated function that logs execution time
    """
    def wrapper(*args, **kwargs):
        timer = Timer()
        timer.start()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = timer.stop()
            print(f"{func.__name__} executed in {format_duration_precise(elapsed)}")
    
    return wrapper