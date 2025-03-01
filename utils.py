#!/usr/bin/env python3
"""
Utility functions for dejavu2-cli.

This module contains helper functions for:
- Logging setup
- String processing
- Date/time utilities
"""
import logging
import warnings
import os
import re
import unicodedata
from datetime import datetime
import tzlocal

# Setup logging
def setup_logging(verbose=False, log_file=None, quiet=False):
    """
    Configure logging for the application with proper formatting and filters.
    
    Args:
        verbose: Whether to use DEBUG level logging (default: False)
        log_file: Path to a log file to write logs to (default: None)
        quiet: Whether to suppress console output (default: False)
    
    Returns:
        The configured root logger instance
    """
    # Configure root logger
    root_logger = logging.getLogger()
    
    # Clear any existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set log level based on verbosity
    if verbose:
        root_level = logging.DEBUG
    else:
        root_level = logging.INFO
        
    root_logger.setLevel(root_level)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter('%(levelname)s - %(name)s: %(message)s')
    
    # Set up console handler unless quiet mode is enabled
    if not quiet:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(root_level)
        root_logger.addHandler(console_handler)
    
    # Set up file handler if a log file is specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(detailed_formatter)
            file_handler.setLevel(logging.DEBUG)  # Always log everything to file
            root_logger.addHandler(file_handler)
        except Exception as e:
            logging.error(f"Failed to set up log file: {str(e)}")
    
    # Get the utils logger (this module)
    logger = logging.getLogger(__name__)
    
    # Configure third-party library loggers
    # Suppress warnings from specific modules
    warnings.filterwarnings("ignore", category=UserWarning, module=r"^anthropic\..*")
    warnings.filterwarnings("ignore", category=UserWarning, module=r"^openai\..*")
    
    # Set conservative logging levels for noisy libraries
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Log the logging configuration
    logger.debug(f"Logging initialized (verbose={verbose}, log_file={log_file}, quiet={quiet})")
    
    return root_logger

# String manipulation utilities
def post_slug(input_str: str, sep_char: str = '-',
    preserve_case: bool = False, max_len: int = 0) -> str:
    """
    Create a URL/filename-friendly slug from a given string.
    
    Converts a string to a URL-friendly format by:
    1. Replacing special characters with ASCII equivalents
    2. Removing accents and unusual characters
    3. Converting spaces and punctuation to separator characters
    4. Lowercasing (unless preserve_case=True)
    5. Limiting length (if max_len is provided)
    
    Args:
        input_str: The string to convert to a slug
        sep_char: Character to use as a separator (default: '-')
        preserve_case: If False, converts to lowercase (default: False)
        max_len: Maximum length of the slug (default: 0, no limit)
        
    Returns:
        A clean, URL-friendly slug string
        
    Example:
        >>> post_slug("Hello World!")
        'hello-world'
        >>> post_slug("Café & Restaurant", max_len=10)
        'cafe-resta'
    """
    # Handle edge cases
    if not input_str:
        return ''
        
    try:
        # Character replacement mapping
        translation_table = str.maketrans({
            '–': '-',  # en dash
            '—': '-',  # em dash
            '½': '-',
            '¼': '-',
            'ı': 'i',
            '•': 'o',
            'ł': 'l',
            'ø': 'o',
            'Đ': 'D',
            'ð': 'd',
            'đ': 'd',
            'Ł': 'L',
            '´': '',
            '★': ' ',
        })
        
        # Multi-character replacements
        multi_char_replacements = {
            ' & ': ' and ',
            'œ': 'oe',
            '™': '-TM',
            'Œ': 'OE',
            'ß': 'ss',
            'æ': 'ae',
            'â�¹': 'Rs',
            '�': '-',
        }
        
        # Regular expressions for cleaning
        ps_html_entity_re = re.compile(r'&[^ \t]*;')
        ps_non_alnum_re = re.compile(r'[^a-zA-Z0-9]+')
        ps_quotes_re = re.compile(r"[\"'`'´]")
        
        # Ensure separator is valid
        if not sep_char:
            sep_char = '-'
        sep_char = sep_char[0]  # Use just the first character
        
        # Process the string
        # 1. Apply character translations
        input_str = input_str.translate(translation_table)
        
        # 2. Apply multi-character replacements
        input_str = re.sub('|'.join(re.escape(key) for key in multi_char_replacements.keys()),
                          lambda m: multi_char_replacements[m.group(0)], input_str)
        
        # 3. Replace HTML entities
        input_str = ps_html_entity_re.sub(sep_char, input_str)
        
        # 4. Normalize unicode and convert to ASCII
        input_str = unicodedata.normalize('NFKD', input_str).encode('ASCII', 'ignore').decode()
        
        # 5. Remove quotes
        input_str = ps_quotes_re.sub('', input_str)
        
        # 6. Convert to lowercase if not preserving case
        if not preserve_case:
            input_str = input_str.lower()
        
        # 7. Replace non-alphanumeric with separator and trim
        input_str = ps_non_alnum_re.sub(sep_char, input_str).strip(sep_char)
        
        # 8. Handle maximum length if specified
        if max_len and len(input_str) > max_len:
            input_str = input_str[:max_len]
            # Try to cut at a separator for cleaner slugs
            last_sep_char_pos = input_str.rfind(sep_char)
            if last_sep_char_pos != -1:
                input_str = input_str[:last_sep_char_pos]
        
        return input_str
    except Exception as e:
        logging.warning(f"Error generating slug: {str(e)}")
        # Return a simple sanitized version if there was an error
        return re.sub(r'[^a-zA-Z0-9-]', '', str(input_str).lower())

def spacetime_placeholders(text: str) -> str:
    """
    Replace date/time placeholders in a text string with current values.
    
    Supported placeholders:
    - {date}: Current date in YYYY-MM-DD format
    - {time}: Current time in HH:MM:SS format
    - {datetime}: Combined date and time (YYYY-MM-DD HH:MM:SS)
    - {year}: Current year (YYYY)
    - {month}: Current month (MM)
    - {day}: Current day (DD)
    - {hour}: Current hour (HH)
    - {minute}: Current minute (MM)
    - {second}: Current second (SS)
    - {dow}: Current day of week name (e.g., "Monday")
    - {tz}: Current timezone name
    - {spacetime}: Complete string with day, date, time, and timezone
    
    Args:
        text: The string containing placeholders to replace
        
    Returns:
        String with placeholders replaced by current values
    
    Example:
        >>> spacetime_placeholders("Today is {date} at {time}")
        'Today is 2025-01-03 at 12:30:45'
    """
    if not text or not isinstance(text, str):
        return text
    
    if '{' not in text:
        return text
        
    try:
        now = datetime.now()
        
        # Create map of placeholders to their values
        replacements = {
            "{date}": now.strftime("%Y-%m-%d"),
            "{time}": now.strftime("%H:%M:%S"),
            "{datetime}": now.strftime("%Y-%m-%d %H:%M:%S"),
            "{year}": now.strftime("%Y"),
            "{month}": now.strftime("%m"),
            "{day}": now.strftime("%d"),
            "{hour}": now.strftime("%H"),
            "{minute}": now.strftime("%M"),
            "{second}": now.strftime("%S"),
            "{dow}": now.strftime("%A"),  # Full day name
            "{tz}": str(tzlocal.get_localzone().key)
        }
        
        # Add spacetime after we have all the other values
        replacements["{spacetime}"] = f"{replacements['{dow}']} {replacements['{date}']} {replacements['{time}']} {replacements['{tz}']}"
        
        # Replace each placeholder in the text
        result = text
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
            
            # Also handle double-brace format for backward compatibility
            double_brace = placeholder.replace('{', '{{').replace('}', '}}')
            result = result.replace(double_brace, value)
            
        return result
    except Exception as e:
        # Log but don't crash on date/time errors
        logging.warning(f"Error processing date/time placeholders: {str(e)}")
        return text