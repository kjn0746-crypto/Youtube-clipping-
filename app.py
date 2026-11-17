
import streamlit as st
import yt_dlp
import subprocess
import os
import re
import zipfile
import tempfile

st.set_page_config(page_title="AI YouTube Shorts Clipper", page_icon="🎬")

st.title("AI YouTube Shorts Clipper")
st.write("Turn long videos into vertical short clips.")

url = st.text_input("Paste your YouTube video URL")

duration = st.slider("Clip duration (seconds)", 15, 60, 30)
number = st.slider("Number of clips", 1, 10, 5)

if st.button("Generate Shorts", type="primary"):
    if not re.match(r"https?://(www\.)?(youtube\.com|youtu\.be)/", url):
        st.error("Enter a valid YouTube URL.")
        st.stop()

    with st.spinner("Downloading video..."):
        try:
            with tempfile.TemporaryDirectory() as folder:
                output = os.path.join(folder, "video.mp4")

                options = {
                    "format": "best[height<=720][ext=mp4]/best[height<=720]",
                    "outtmpl": output,
                    "merge_output_format": "mp4",
                    "noplaylist": True,
                    "quiet": True,
                }

                with yt_dlp.YoutubeDL(options) as ydl:
                    info = ydl.extract_info(url, download=True)

                source = output
                if not os.path.exists(source):
                    files = [
                        os.path.join(folder, f)
                        for f in os.listdir(folder)
                        if f.endswith(".mp4")
                    ]
                    if not files:
                        raise Exception("Video download failed.")
                    source = files[0]

                total = info.get("duration", 0)
                if not total or total < duration:
                    raise Exception("Video is shorter than selected clip duration.")

                st.success("Video downloaded!")

                clips = []
                step = max(duration, int(total / number))

                for i in range(number):
                    start = i * step
                    if start + duration > total:
                        break

                    target = os.path.join(folder, f"short_{i+1}.mp4")

                    command = [
                        "ffmpeg", "-y", "-ss", str(start),
                        "-i", source, "-t", str(duration),
                        "-vf",
                        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                        "-c:v", "libx264", "-preset", "ultrafast",
                        "-c:a", "aac", "-movflags", "+faststart",
                        target
                    ]

                    subprocess.run(
                        command, check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE
                    )
                    clips.append(target)

                if not clips:
                    raise Exception("No clips could be generated.")

                zip_path = os.path.join(folder, "shorts.zip")
                with zipfile.ZipFile(zip_path, "w") as archive:
                    for clip in clips:
                        archive.write(clip, os.path.basename(clip))

                st.success(f"Created {len(clips)} vertical clips!")

                for clip in clips:
                    st.video(clip)
                    with open(clip, "rb") as f:
                        st.download_button(
                            f"Download {os.path.basename(clip)}",
                            f.read(),
                            file_name=os.path.basename(clip),
                            mime="video/mp4"
                        )

                with open(zip_path, "rb") as f:
                    st.download_button(
                        "Download all Shorts",
                        f.read(),
                        file_name="YouTube_Shorts.zip"
                    )

        except Exception as error:
            st.error(f"Processing failed: {error}")
            st.info("Some YouTube videos block automated downloads. Try a video you own or upload an authorized video.")
                                      
