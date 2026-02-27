import os
import sqlite3
import shutil
import tempfile
import sys
import logging
from datetime import datetime, timedelta
import glob
import subprocess
import json

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AdharshBrowserAuditor")

def chrome_time_to_datetime(chrome_time):
    """Converts a Chrome/Chromium Windows FileTime (microseconds since 1601) to a readable datetime string.

    Args:
        chrome_time (int): The timestamp in microseconds.

    Returns:
        str: A formatted datetime string or "Unknown" if conversion fails.
    """
    if chrome_time <= 0:
        return "Unknown"
    try:
        return (datetime(1601, 1, 1) + timedelta(microseconds=chrome_time)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Failed to convert Chrome time {chrome_time}: {e}")
        return "Unknown"

def firefox_time_to_datetime(firefox_time):
    """Converts a Firefox/Mozilla Unix Epoch Microseconds timestamp to a readable datetime string.

    Args:
        firefox_time (int): The timestamp in microseconds.

    Returns:
        str: A formatted datetime string or "Unknown" if conversion fails.
    """
    if firefox_time <= 0:
        return "Unknown"
    try:
        return datetime.fromtimestamp(firefox_time / 1000000).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Failed to convert Firefox time {firefox_time}: {e}")
        return "Unknown"

def is_browser_running(browser_name):
    """Checks if a browser process is currently active on the system.

    This prevents file lock errors when attempting to read or delete SQLite databases.

    Args:
        browser_name (str): The common name of the browser (e.g., 'Chrome').

    Returns:
        bool: True if the browser process is running, False otherwise.
    """
    process_names = {
        "Chrome": "chrome.exe",
        "Edge": "msedge.exe",
        "Firefox": "firefox.exe",
        "Comet": "comet.exe",
        "Brave": "brave.exe",
        "Atlas": "atlas.exe"
    }

    target = ""
    for b_name, exe in process_names.items():
        if browser_name.startswith(b_name):
            target = exe
            break

    if not target:
        return False
    
    try:
        output = subprocess.check_output('tasklist', shell=True).decode('utf-8', errors='ignore')
        return target in output.lower()
    except Exception as e:
        logger.error(f"Error checking if {browser_name} is running: {e}")
        return False

def clear_browser_history(browser_name, base_path, browser_type='chromium', time_range="All Time"):
    """Clears history entries from the browser database based on a specified time range.

    Args:
        browser_name (str): Name of the browser.
        base_path (str): Path to the browser profile directory.
        browser_type (str, optional): 'chromium' or 'firefox'. Defaults to 'chromium'.
        time_range (str, optional): Range to clear ("Last Hour", "Last 24 Hours", "All Time"). Defaults to "All Time".

    Returns:
        tuple (bool, str): (Success status, Result message).
    """
    if is_browser_running(browser_name):
        logger.warning(f"Attempted to clear history for {browser_name} while it was running.")
        return False, f"Please close {browser_name} before clearing history."

    logger.info(f"Clearing {time_range} history for {browser_name} at {base_path}")

    # Calculate cutoff time
    now = datetime.now()
    if time_range == "Last Hour":
        cutoff_dt = now - timedelta(hours=1)
    elif time_range == "Last 24 Hours":
        cutoff_dt = now - timedelta(days=1)
    else:
        cutoff_dt = None

    if browser_type == 'chromium':
        db_path = os.path.join(base_path, 'History')
        if not os.path.exists(db_path):
            logger.error(f"Chromium history not found at {db_path}")
            return False, "History file not found."
        
        cutoff_timestamp = 0
        if cutoff_dt:
            cutoff_timestamp = int((cutoff_dt - datetime(1601, 1, 1)).total_seconds() * 1000000)

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if not cutoff_dt:
                tables = ['urls', 'visits', 'downloads', 'keyword_search_terms', 'segments', 'visit_source']
                for table in tables:
                    try: cursor.execute(f"DELETE FROM {table}")
                    except sqlite3.OperationalError: pass
            else:
                cursor.execute("DELETE FROM visits WHERE visit_time > ?", (cutoff_timestamp,))
                cursor.execute("DELETE FROM downloads WHERE start_time > ?", (cutoff_timestamp,))
                cursor.execute("DELETE FROM urls WHERE last_visit_time > ?", (cutoff_timestamp,))
                
            conn.commit()
            conn.close()
            logger.info(f"Successfully cleared {time_range} Chromium history for {browser_name}")
            return True, f"Successfully cleared {browser_name} history ({time_range})."
        except Exception as e:
            logger.error(f"Error clearing Chromium history for {browser_name}: {e}")
            return False, f"Error clearing history: {str(e)}"

    elif browser_type == 'firefox':
        db_path = os.path.join(base_path, 'places.sqlite')
        if not os.path.exists(db_path):
            logger.error(f"Firefox history not found at {db_path}")
            return False, "History file not found."
            
        cutoff_timestamp = 0
        if cutoff_dt:
            cutoff_timestamp = int(cutoff_dt.timestamp() * 1000000)

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if not cutoff_dt:
                tables = ['moz_places', 'moz_historyvisits', 'moz_inputhistory']
                for table in tables:
                    try: cursor.execute(f"DELETE FROM {table}")
                    except sqlite3.OperationalError: pass
            else:
                cursor.execute("DELETE FROM moz_historyvisits WHERE visit_date > ?", (cutoff_timestamp,))
            
            conn.commit()
            conn.close()
            logger.info(f"Successfully cleared {time_range} Firefox history for {browser_name}")
            return True, f"Successfully cleared {browser_name} history ({time_range})."
        except Exception as e:
            logger.error(f"Error clearing Firefox history for {browser_name}: {e}")
            return False, f"Error clearing history: {str(e)}"
            
    return False, "This app does not store local history in a clearable format."

def clear_browser_cache(browser_name, base_path, browser_type='chromium'):
    """Clears cache directories for a specific browser.

    Args:
        browser_name (str): Name of the browser.
        base_path (str): Path to the browser profile directory.
        browser_type (str, optional): 'chromium', 'firefox', or 'electron'. Defaults to 'chromium'.

    Returns:
        tuple (bool, str): (Success status, Result message).
    """
    if is_browser_running(browser_name):
        logger.warning(f"Attempted to clear cache for {browser_name} while it was running.")
        return False, f"Please close {browser_name} before clearing cache."

    logger.info(f"Clearing cache for {browser_name} at {base_path}")
    cache_dirs = []
    if browser_type == 'chromium':
        cache_dirs = [
            os.path.join(base_path, 'Cache'),
            os.path.join(base_path, 'Code Cache'),
            os.path.join(base_path, 'GPUCache')
        ]
    elif browser_type == 'firefox':
        local_app_data = os.environ.get('LOCALAPPDATA')
        if local_app_data:
            profile_name = os.path.basename(base_path)
            cache_dirs = [os.path.join(local_app_data, 'Mozilla', 'Firefox', 'Profiles', profile_name, 'cache2')]
    elif browser_type == 'electron':
        cache_dirs = [
            os.path.join(base_path, 'Cache'),
            os.path.join(base_path, 'Code Cache'),
            os.path.join(base_path, 'GPUCache'),
            os.path.join(base_path, 'Local Storage')
        ]

    cleared_count = 0
    errors = []
    
    for cdir in cache_dirs:
        if os.path.exists(cdir):
            try:
                for root, dirs, files in os.walk(cdir, topdown=False):
                    for name in files:
                        try: os.remove(os.path.join(root, name))
                        except: pass
                    for name in dirs:
                        try: shutil.rmtree(os.path.join(root, name))
                        except: pass
                cleared_count += 1
            except Exception as e:
                logger.error(f"Error clearing cache dir {cdir}: {e}")
                errors.append(str(e))
    
    if cleared_count > 0:
        logger.info(f"Successfully cleared {cleared_count} cache directories for {browser_name}")
        return True, f"Cleared {cleared_count} cache directories for {browser_name}."
    return False, f"No cache directories found or cleared for {browser_name}."

def get_history(db_path, browser_type='chromium'):
    """Extracts browsing history from a browser's SQLite database.

    Args:
        db_path (str): Path to the history SQLite file.
        browser_type (str, optional): 'chromium' or 'firefox'. Defaults to 'chromium'.

    Returns:
        list: A list of dicts containing 'url', 'title', and 'time'.
    """
    if not os.path.exists(db_path):
        logger.debug(f"History database not found at {db_path}")
        return []
    
    temp_db = os.path.join(tempfile.gettempdir(), f'browser_history_{browser_type}')
    try:
        shutil.copy2(db_path, temp_db)
    except Exception as e:
        logger.error(f"Failed to copy history database for {browser_type}: {e}")
        return []
    
    history = []
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        if browser_type == 'chromium':
            cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC")
            for row in cursor.fetchall():
                history.append({
                    'url': row[0],
                    'title': row[1] or "No Title",
                    'time': chrome_time_to_datetime(row[2])
                })
        elif browser_type == 'firefox':
            cursor.execute("SELECT url, title, last_visit_date FROM moz_places WHERE last_visit_date IS NOT NULL ORDER BY last_visit_date DESC")
            for row in cursor.fetchall():
                history.append({
                    'url': row[0],
                    'title': row[1] or "No Title",
                    'time': firefox_time_to_datetime(row[2])
                })
        conn.close()
    except Exception as e:
        logger.error(f"Error reading {browser_type} history: {e}")
    finally:
        if os.path.exists(temp_db):
            try: os.remove(temp_db)
            except: pass
    return history

def get_downloads(db_path, browser_type='chromium'):
    """Extracts download history from a browser's SQLite database.

    Args:
        db_path (str): Path to the history/places SQLite file.
        browser_type (str, optional): 'chromium' or 'firefox'. Defaults to 'chromium'.

    Returns:
        list: A list of dicts containing 'path', 'size', and 'time'.
    """
    if not os.path.exists(db_path):
        logger.debug(f"Downloads database not found at {db_path}")
        return []
    
    temp_db = os.path.join(tempfile.gettempdir(), f'browser_downloads_{browser_type}')
    try:
        shutil.copy2(db_path, temp_db)
    except Exception as e:
        logger.error(f"Failed to copy downloads database for {browser_type}: {e}")
        return []
    
    downloads = []
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        if browser_type == 'chromium':
            cursor.execute("SELECT target_path, start_time, total_bytes FROM downloads ORDER BY start_time DESC")
            for row in cursor.fetchall():
                downloads.append({
                    'path': row[0],
                    'time': chrome_time_to_datetime(row[1]),
                    'size': f"{row[2] / 1024 / 1024:.2f} MB" if row[2] > 0 else "Unknown"
                })
        elif browser_type == 'firefox':
            # Firefox downloads are complex to extract; this is a simplified version
            cursor.execute("SELECT content, dateAdded FROM moz_annos INNER JOIN moz_places ON moz_annos.place_id = moz_places.id WHERE anno_attribute_id = (SELECT id FROM moz_anno_attributes WHERE name = 'downloads/destinationFileURI') ORDER BY dateAdded DESC")
            for row in cursor.fetchall():
                downloads.append({
                    'path': row[0],
                    'size': "N/A",
                    'time': firefox_time_to_datetime(row[1])
                })
        conn.close()
    except Exception as e:
        logger.error(f"Error reading {browser_type} downloads: {e}")
    finally:
        if os.path.exists(temp_db):
            try: os.remove(temp_db)
            except: pass
    return downloads

def get_extensions(base_path, browser_type='chromium'):
    """Lists installed extensions for the browser.

    Args:
        base_path (str): Path to the browser profile directory.
        browser_type (str, optional): 'chromium' or 'firefox'. Defaults to 'chromium'.

    Returns:
        list: A list of extension names/IDs.
    """
    extensions = []
    try:
        if browser_type == 'chromium':
            ext_path = os.path.join(base_path, 'Extensions')
            if os.path.exists(ext_path):
                for ext_id in os.listdir(ext_path):
                    ext_dir = os.path.join(ext_path, ext_id)
                    if not os.path.isdir(ext_dir): continue
                    
                    resolved_name = ext_id
                    versions = [d for d in os.listdir(ext_dir) if os.path.isdir(os.path.join(ext_dir, d))]
                    if versions:
                        manifest_path = os.path.join(ext_dir, versions[0], 'manifest.json')
                        if os.path.exists(manifest_path):
                            try:
                                with open(manifest_path, 'r', encoding='utf-8') as f:
                                    manifest = json.load(f)
                                    resolved_name = manifest.get('name', ext_id)
                                    if resolved_name.startswith('__MSG_'):
                                        resolved_name = f"{ext_id} (Localized)"
                            except: pass
                    extensions.append(f"{resolved_name} [{ext_id}]")
        elif browser_type == 'firefox':
            ext_json_path = os.path.join(base_path, 'extensions.json')
            if os.path.exists(ext_json_path):
                with open(ext_json_path, 'r', encoding='utf-8') as f:
                    ext_data = json.load(f)
                    for addon in ext_data.get('addons', []):
                        name = addon.get('defaultLocale', {}).get('name') or addon.get('name')
                        if name: extensions.append(f"{name} [{addon.get('id')}]")
    except Exception as e:
        logger.error(f"Error extracting extensions for {browser_type}: {e}")
    return extensions

def get_cache_info(cache_path):
    """Calculates total size and file count of a cache directory.

    Args:
        cache_path (str): Path to the cache directory.

    Returns:
        tuple (str, int): (Human-readable size, File count).
    """
    if not os.path.exists(cache_path):
        return "0 MB", 0
    
    total_size = 0
    file_count = 0
    try:
        for root, _, files in os.walk(cache_path):
            file_count += len(files)
            for f in files:
                try: total_size += os.path.getsize(os.path.join(root, f))
                except OSError: pass
    except Exception as e:
        logger.debug(f"Error calculating cache info for {cache_path}: {e}")
    return f"{total_size / 1024 / 1024:.2f} MB", file_count

def get_browser_data(name, base_path, browser_type='chromium'):
    """Aggregates all relevant data for a single browser profile.

    Args:
        name (str): Human-readable name of the browser.
        base_path (str): Path to the profile directory.
        browser_type (str, optional): 'chromium', 'firefox', or 'electron'. Defaults to 'chromium'.

    Returns:
        dict: A dictionary containing status, history, downloads, extensions, and cache info.
    """
    logger.info(f"Aggregating data for {name} ({browser_type})")
    data = {
        'name': name,
        'history': [],
        'downloads': [],
        'extensions': [],
        'cache_size': "0 MB",
        'cache_files': 0,
        'status': 'Not Found',
        'base_path': base_path,
        'browser_type': browser_type
    }
    
    if not base_path or not os.path.exists(base_path):
        logger.debug(f"{name} profile path not found: {base_path}")
        return data

    data['status'] = 'Active'
    
    if browser_type == 'chromium':
        history_file = os.path.join(base_path, 'History')
        data['history'] = get_history(history_file, 'chromium')
        data['downloads'] = get_downloads(history_file, 'chromium')
        data['extensions'] = get_extensions(base_path, 'chromium')
        cache_dir = os.path.join(base_path, 'Cache')
        data['cache_size'], data['cache_files'] = get_cache_info(cache_dir)
        
    elif browser_type == 'firefox':
        history_file = os.path.join(base_path, 'places.sqlite')
        data['history'] = get_history(history_file, 'firefox')
        data['downloads'] = get_downloads(history_file, 'firefox')
        data['extensions'] = get_extensions(base_path, 'firefox')
        
    elif browser_type == 'electron':
        data['cache_size'], data['cache_files'] = get_cache_info(os.path.join(base_path, 'Cache'))
        data['history'] = [{'url': 'N/A', 'title': 'Electron apps do not store history in standard format', 'time': 'N/A'}]
        
    return data

def discover_profiles(base_user_data_path, browser_type='chromium'):
    """Discovers all available user profiles for a given browser path.

    Args:
        base_user_data_path (str): The root 'User Data' or profiles directory.
        browser_type (str): 'chromium' or 'firefox'.

    Returns:
        list: A list of tuples (profile_id, full_path)
    """
    profiles = []
    if not os.path.exists(base_user_data_path):
        return profiles

    if browser_type == 'chromium':
        # Chromium profiles are directories in the base path.
        # 'Default' is the first, then 'Profile 1', 'Profile 2', etc.
        # They usually contain a 'Preferences' file.
        potential_profiles = ['Default'] + [f'Profile {i}' for i in range(1, 20)]
        for p_id in potential_profiles:
            p_path = os.path.join(base_user_data_path, p_id)
            if os.path.exists(p_path) and (os.path.exists(os.path.join(p_path, 'Preferences')) or os.path.exists(os.path.join(p_path, 'History'))):
                profiles.append((p_id, p_path))
    
    elif browser_type == 'firefox':
        # Firefox profiles are subdirectories in the base path.
        # They often have names like 'xxxxxxxx.default-release'.
        for entry in os.listdir(base_user_data_path):
            p_path = os.path.join(base_user_data_path, entry)
            if os.path.isdir(p_path) and os.path.exists(os.path.join(p_path, 'places.sqlite')):
                # Clean up the name for the UI by removing the random 8-char prefix
                clean_name = entry.split('.')[-1] if '.' in entry else entry
                # Capitalize it nicely (e.g. 'default-release' -> 'Default-Release')
                clean_name = clean_name.replace('-', ' ').title()
                profiles.append((clean_name, p_path))
    
    return profiles

def get_all_browsers_data():
    """Scans all supported browsers and all their profiles.

    Returns:
        dict: A nested dictionary mapping 'Browser (Profile)' to their data dicts.
    """
    logger.info("Initializing comprehensive global browser and profile scan...")
    
    # Mapping of Browser Name to their Base User Data Path
    browser_bases = [
        ("Chrome", os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data'), 'chromium'),
        ("Edge", os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data'), 'chromium'),
        ("Firefox", os.path.expandvars(r'%APPDATA%\Mozilla\Firefox\Profiles'), 'firefox'),
        ("Comet", os.path.expandvars(r'%LOCALAPPDATA%\Comet\User Data'), 'chromium'),
        ("Brave", os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data'), 'chromium'),
        ("Atlas", os.path.expandvars(r'%LOCALAPPDATA%\AtlasBrowser\User Data'), 'chromium')
    ]
    
    results = {}
    for browser_name, base_path, btype in browser_bases:
        try:
            discovered = discover_profiles(base_path, btype)
            if not discovered:
                # Add placeholder if browser is not installed
                display_name = f"{browser_name} (Unconfigured)"
                results[display_name] = {
                    'name': display_name,
                    'history': [],
                    'downloads': [],
                    'extensions': [],
                    'cache_size': "0 MB",
                    'cache_files': 0,
                    'status': 'Not Installed',
                    'base_path': '',
                    'browser_type': btype
                }
                continue
                
            for p_id, p_path in discovered:
                display_name = f"{browser_name} ({p_id})"
                results[display_name] = get_browser_data(display_name, p_path, btype)
        except Exception as e:
            logger.error(f"Unexpected error during {browser_name} multi-profile scan: {e}")
            
    return results

if __name__ == "__main__":
    logging.info("Adharsh Browser Auditor CLI Diagnostics Started.")
    results = get_all_browsers_data()
    for name, data in results.items():
        print(f"\n[{name}] {data.get('status', 'Unknown')}")
        if data.get('status') == 'Active':
            print(f" -> History entries: {len(data.get('history', []))}")
            print(f" -> Extensions: {len(data.get('extensions', []))}")
            print(f" -> Cache size: {data.get('cache_size', '0 MB')}")
