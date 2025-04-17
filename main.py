import streamlit as st
import yt_dlp
import os
import time
from datetime import datetime
from pathlib import Path
import requests
from PIL import Image
from io import BytesIO
import re

# Page configuration with custom theme
st.set_page_config(
    page_title="YouTube to MP3 Converter",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to enhance UI
def load_css():
    css = """
    <style>
    .main {
        background: linear-gradient(to right, #1a1a2e, #16213e, #1a1a2e);
        color: white;
    }
    .stButton button {
        background-color: #ff2e63;
        color: white;
        border-radius: 20px;
        padding: 10px 20px;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #ff5c8d;
        transform: scale(1.05);
    }
    .download-card {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0px;
        animation: fadeIn 0.5s;
    }
    .title-text {
        font-size: 3.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #ff2e63, #08d9d6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 20px;
    }
    .subtitle-text {
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 30px;
        color: #eaeaea;
    }
    .url-input {
        border-radius: 10px;
        border: 2px solid #08d9d6;
        padding: 10px;
    }
    .success-box {
        background-color: rgba(8, 217, 214, 0.2);
        border-left: 5px solid #08d9d6;
        padding: 20px;
        border-radius: 5px;
        animation: pulse 2s infinite;
    }
    .download-btn {
        border-radius: 20px;
        padding: 10px 25px;
        background-color: #08d9d6;
        color: #1a1a2e;
        font-weight: bold;
        border: none;
        width: 100%;
        transition: all 0.3s ease;
    }
    .download-btn:hover {
        background-color: #0cffe9;
        transform: scale(1.05);
    }
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(8, 217, 214, 0.4);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(8, 217, 214, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(8, 217, 214, 0);
        }
    }
    @keyframes fadeIn {
        from {opacity: 0;}
        to {opacity: 1;}
    }
    .stProgress > div > div {
        background-color: #ff2e63;
    }
    .stDownloadButton button {
        background-color: #08d9d6;
        color: #1a1a2e;
        border-radius: 20px;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    .stDownloadButton button:hover {
        background-color: #0cffe9;
        transform: scale(1.05);
    }
    div[data-testid="stHorizontalBlock"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0px;
    }
    .stExpander {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

load_css()

# Create directories if they don't exist
downloads_dir = Path("downloads")
downloads_dir.mkdir(exist_ok=True)

# Function to extract video ID from YouTube URL
def extract_video_id(url):
    # Regular YouTube URL
    youtube_regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(youtube_regex, url)
    if match:
        return match.group(1)
    return None

# Function to fetch video thumbnail
def get_thumbnail(video_id):
    if not video_id:
        return None
    try:
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        response = requests.get(thumbnail_url)
        img = Image.open(BytesIO(response.content))
        return img
    except:
        try:
            # Try another resolution if maxresdefault is not available
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            response = requests.get(thumbnail_url)
            img = Image.open(BytesIO(response.content))
            return img
        except:
            return None

# Function to get video info without downloading
def get_video_info(youtube_url):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return {
                'title': info.get('title', 'Unknown Title'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown Uploader'),
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date', '')
            }
    except Exception as e:
        return None

# Function to download audio
def download_audio(youtube_url, progress_callback=None, output_path="downloads"):
    """
    Download audio from YouTube URL and convert to MP3
    """
    try:
        def progress_hook(d):
            if d['status'] == 'downloading':
                # Calculate progress percentage
                if 'total_bytes' in d and d['total_bytes'] > 0:
                    percentage = d['downloaded_bytes'] / d['total_bytes']
                    if progress_callback:
                        progress_callback(percentage)
                elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                    percentage = d['downloaded_bytes'] / d['total_bytes_estimate']
                    if progress_callback:
                        progress_callback(percentage)

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f"{output_path}/%(title)s.%(ext)s",
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [progress_hook],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            filename = ydl.prepare_filename(info)
            filename = filename.replace(f".{info['ext']}", ".mp3")
            
            if os.path.exists(filename):
                return filename, True, "File already exists", info
            
            # Download the file
            ydl.download([youtube_url])
            
            return filename, True, "Success", info
    except Exception as e:
        return None, False, str(e), None

# Initialize session states
if 'download_complete' not in st.session_state:
    st.session_state.download_complete = False
if 'filename' not in st.session_state:
    st.session_state.filename = None
if 'info' not in st.session_state:
    st.session_state.info = None
if 'show_extra' not in st.session_state:
    st.session_state.show_extra = False

# Custom HTML title
st.markdown('<div class="title-text">YouTube to MP3 Converter</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Download and convert any YouTube video to MP3 with our sleek, powerful tool</div>', unsafe_allow_html=True)

# URL input with columns for better layout
col1, col2 = st.columns([3, 1])
with col1:
    youtube_url = st.text_input("YouTube URL", placeholder="Paste YouTube URL here...", label_visibility="collapsed")
with col2:
    download_button = st.button("Convert to MP3 🔄", use_container_width=True)

# Preview area
if youtube_url and not st.session_state.download_complete:
    video_id = extract_video_id(youtube_url)
    thumbnail = get_thumbnail(video_id)
    video_info = get_video_info(youtube_url)
    
    if video_info:
        preview_col1, preview_col2 = st.columns([1, 2])
        
        with preview_col1:
            if thumbnail:
                st.image(thumbnail, use_column_width=True)
            else:
                st.image("https://via.placeholder.com/480x360?text=No+Preview+Available", use_column_width=True)
        
        with preview_col2:
            st.markdown(f"### {video_info['title']}")
            
            # Format duration to minutes:seconds
            minutes = video_info['duration'] // 60
            seconds = video_info['duration'] % 60
            duration_str = f"{minutes}:{seconds:02d}"
            
            # Format date to readable format
            if video_info['upload_date']:
                try:
                    date_obj = datetime.strptime(video_info['upload_date'], '%Y%m%d')
                    upload_date = date_obj.strftime('%B %d, %Y')
                except:
                    upload_date = video_info['upload_date']
            else:
                upload_date = 'Unknown'
            
            st.markdown(f"**Uploader:** {video_info['uploader']}")
            st.markdown(f"**Duration:** {duration_str}")
            st.markdown(f"**Upload Date:** {upload_date}")
            st.markdown(f"**Views:** {video_info['view_count']:,}")

# Download process
if download_button and youtube_url:
    # Check if the URL is valid
    if not (youtube_url.startswith('http://') or youtube_url.startswith('https://') or 'youtube.com' in youtube_url or 'youtu.be' in youtube_url):
        st.error("Please enter a valid YouTube URL")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(progress):
            progress_bar.progress(progress)
            status_text.text(f"Downloading... {int(progress * 100)}%")
        
        try:
            status_text.text("Starting download...")
            filename, success, message, info = download_audio(youtube_url, update_progress)
            
            if success:
                # Update session state
                st.session_state.download_complete = True
                st.session_state.filename = filename
                st.session_state.info = info
                
                # Complete the progress bar
                progress_bar.progress(1.0)
                status_text.empty()
                
                # Force a rerun using st.rerun() instead of st.experimental_rerun()
                st.rerun()
            else:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Error: {message}")
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ An error occurred: {str(e)}")

# Download complete section
if st.session_state.download_complete and st.session_state.filename:
    filename = st.session_state.filename
    file_size = os.path.getsize(filename) / (1024 * 1024)  # Convert to MB
    
    # Success area with animation
    st.markdown("""
    <div class="success-box">
        <h2>✅ Conversion completed successfully!</h2>
        <p>Your audio file is ready to download. Click the button below to save it to your device.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### {os.path.basename(filename)}")
        st.markdown(f"**File Size:** {file_size:.2f} MB")
        
        # Show audio player
        with open(filename, "rb") as file:
            audio_bytes = file.read()
            st.audio(audio_bytes, format="audio/mp3")
    
    with col2:
        # Create download button
        with open(filename, "rb") as file:
            btn = st.download_button(
                label="Download MP3 📥",
                data=file,
                file_name=os.path.basename(filename),
                mime="audio/mpeg",
                use_container_width=True
            )
    
    # Reset button
    if st.button("Convert Another Video 🔄"):
        st.session_state.download_complete = False
        st.session_state.filename = None
        st.session_state.info = None
        # Use st.rerun() instead of st.experimental_rerun()
        st.rerun()

# Display recent downloads
with st.expander("Recent Downloads"):
    mp3_files = list(downloads_dir.glob("*.mp3"))
    
    if not mp3_files:
        st.info("No recent downloads found.")
    else:
        # Sort files by modification time (newest first)
        mp3_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Display the 5 most recent files
        for i, mp3_file in enumerate(mp3_files[:5]):
            file_size = os.path.getsize(mp3_file) / (1024 * 1024)  # Convert to MB
            
            # Format the modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(mp3_file))
            mod_time_str = mod_time.strftime("%b %d, %Y at %I:%M %p")
            
            st.markdown(f"""
            <div class="download-card">
                <h4>{mp3_file.name}</h4>
                <p>Size: {file_size:.2f} MB • Downloaded: {mod_time_str}</p>
            </div>
            """, unsafe_allow_html=True)
            
            with open(mp3_file, "rb") as file:
                st.download_button(
                    label="Download",
                    data=file,
                    file_name=mp3_file.name,
                    mime="audio/mpeg",
                    key=f"download_{i}"
                )

# Footer with features
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🚀 Features
    - High-quality audio (192kbps)
    - Fast conversions
    - All YouTube formats supported
    """)

with col2:
    st.markdown("""
    ### 📋 Supported URLs
    - Regular YouTube videos
    - YouTube Shorts
    - YouTube Music
    - Age-restricted videos
    """)

with col3:
    st.markdown("""
    ### 🛠️ How to Use
    1. Paste any YouTube URL
    2. Click "Convert to MP3"
    3. Download and enjoy!
    """)

# Add instructions
with st.expander("Troubleshooting & FAQs"):
    st.markdown("""
    ### Common Issues
    
    **Error: This video is unavailable**
    - Make sure the video exists and is not private
    - Try copying the URL again from YouTube
    
    **Download is slow**
    - This depends on your internet connection and the video length
    - Longer videos take more time to process
    
    **File not downloading**
    - Try using a different browser
    - Check your download settings
    
    ### Frequently Asked Questions
    
    **Is there a limit to how many videos I can convert?**
    No, you can convert as many videos as you want.
    
    **What's the maximum video length supported?**
    There's no strict limit, but very long videos (over several hours) might take a long time to process.
    
    **Is this legal?**
    This tool is for personal use only. You should only download content that you have the right to access and use according to YouTube's terms of service.
    """)

# Hidden footer with credits
st.markdown("""
<div style='text-align: center; color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 50px;'>
Made with ❤️ using Streamlit and yt-dlp | © 2025
</div>
""", unsafe_allow_html=True)