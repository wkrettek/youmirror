
'''
This module handles all of the downloading to disk, and parses whatever 
filters were passed down from the config 

My first priority is finding the best matching resolution when the user specifies it. Then, the container (mp4/webm) has to match the audio codec so we can combine them. The absolute basic default is to download the highest resolution video and audio. If we download by resolution we can use stream.includes_audio_track to decide if we have to find a matching audio track.

I could maybe make other types of downloads available. I think a possible one is like a metadata and another one is like the js. Could be useful

'''
from pytube import YouTube, StreamQuery, Stream, Caption, request
import logging
from pathlib import Path
import subprocess
from urllib.request import urlretrieve  # Using this to download thumbnails

file_types = {"video", "caption", "audio", "thumbnail"} # TODO download js and raw html?
# Order resolutions from highest to lowest in a list
resolutions = ["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"] # Stored as a list because order is important
sub_types = ["mp4", "webm"]    # Prefer mp4 over webm

def get_stream(yt: YouTube, file_type: str, options: dict) -> Stream:
    '''
    Applies all the filters and gets a stream object
    '''
    subtype = "mp4" # This is the subtype we're gonna go with
    if "resolution" in options: resolution = options["resolution"]  # Get the resolution from the options
    if file_type == "audio":
        stream = yt.streams.filter(only_audio=True, subtype=subtype).order_by("abr").desc()
    else:
        stream = yt.streams.get_highest_resolution()
    return stream

def get_video_stream(yt: YouTube, options: dict) -> Stream:
    '''
    Gets the video stream from the video
    '''
    if "resolution" in options:             # If resolution is specified
        resolution = options["resolution"]  # Get the resolution from the options
    else:
        return yt.streams.filter(progressive=True, subtype="mp4").order_by("resolution").last()  # Else, get the highest res progressive stream (usually 720p)
    stream = None       # Initialize the stream
    find_res = iter(resolutions[resolutions.index(resolution):]) # Iterate through the resolutions
    while not stream:   # Until we find a good one
        streams = yt.streams.filter(subtype="mp4", resolution=resolution) # Filter streams by resolution
        stream = next(iter(streams), None)  # Get the first stream or none if there is no stream
        resolution = next(find_res) # Get the next resolution
    return stream

def get_audio_stream(yt: YouTube, options: dict) -> Stream:
    '''
    Gets the audio stream from the video
    '''
    return yt.streams.get_audio_only()  # This returns the highest bitrate audio stream by default (mp4)

def combine_video_audio(video_file: str, audio_file: str) -> str:
    '''
    Combines the video and audio files
    '''
    temp = Path(f'{video_file}.temp')   # Create temp file
    temp.touch()                        # Create the file   
    Path(video_file).rename(temp)       # Rename the video file to the temp file
    temp = str(temp)                    # Convert to string
    subprocess.run(["ffmpeg", "-y", "-i", f"{temp}", "-i", f"{audio_file}", "-c:v", "copy", "-c:a", "copy", f"{video_file}"])               # Use ffmpeg to combine the video and audio
    Path(audio_file).unlink()     # Delete the temp audio file
    Path(temp).unlink()           # Delete the temp video file
    return video_file


def get_filesize(yt: YouTube, file_type: str, options: dict) -> int:
    '''
    Gets the filesize of the video
    '''
    video_stream = get_video_stream(yt, options)        # Get the video stream
    filesize = video_stream.filesize                    # Determine the video filesize
    if not video_stream.includes_audio_track:           # If it doesn't include an audio track
        audio_stream = get_audio_stream(yt, options)    # Get the audio stream
        filesize += audio_stream.filesize               # Add the audio_stream filesize
    return filesize

def download_stream(stream: Stream, path: str, filename: str, options: dict) -> bool:
    '''
    Downloads to the given filepath and returns if a new file was downloaded or not
    '''
    stream.download(output_path=path, filename=filename) # Download to the appropriate path and name
    return True

def download_video(yt: YouTube, path: str, filename: str, options: dict) -> None:
    '''
    Gets the proper stream for video and downloads it
    '''
    try:

        video_stream = get_video_stream(yt, options)                # Get the video stream
        download_stream(video_stream, path, filename, options)      # Download the video stream
        if not video_stream.includes_audio_track:                   # If no audio track
            audio_stream = get_audio_stream(yt, options)            # Get the audio streamm
            download_stream(audio_stream, path, "temp_audio.mp4", options)  # Download the audio stream
            combine_video_audio(f"{path}{filename}", f"{path}temp_audio.mp4") # Combine the video and audio
    except Exception as e:
        logging.exception(f'Could not download video at {str(path) + filename}')

def download_caption(yt: YouTube, path: str, filename: str, options: dict) -> str:
    '''
    Gets the captions from the video and downloads them
    # TODO This implements a uses a fix that is not in pytube right now so it is in my wkrettek repo
    Probably should just implement it in this library until pytube is updated
    '''
    # TODO handle for different languages
    captions_types = ["a.en, en"]
    captions = yt.caption_tracks
    for c_type in captions_types:
        if c_type in filename:
            if c_type in captions:
                caption = captions[c_type]
                caption.download(output_path=path, title=filename) # Adding the index to the filename for now
                return filename
    return None

def download_audio(yt: YouTube, path: str, filename: str, options: dict) -> str:
    '''
    Gets the audio from a video and downloads it
    -----
    Stream looks like yt.streams.filter(only_audio=True, subtype="mp4").desc()
    Audio files are coming out too long, so we want to trim it to the reported length if it is longer
    '''
    try:
        length = yt.length                                  # Get the length of the video
        stream = get_stream(yt, "audio", options)           # Get the audio stream
        download_stream(stream, path, filename, options)    # Download the audio stream
        if options["has_ffmpeg"]:                           # TODO If they have ffmpeg, trim the audio
            pass
            # subprocess.run(["ffmpeg", "-y", "-i", f"{path}{filename}", "-ss", "00:00:00", "-t", f"{length}", f"{path}{filename}"])
    except Exception as e:
        logging.exception(f'Could not download video {filename}')


def download_thumbnail(yt: YouTube, path: str, filename: str, options: dict) -> str:
    '''
    Gets the thumbnail from the video and downloads it
    '''
    try:
        url = yt.thumbnail_url  # For now, pytube can only get the url for a thumbnail
        path = Path(path)       # Wrap the path
        path.mkdir(parents=True, exist_ok=True)    # Make the directory if it doesn't exist
        filepath = path/Path(filename)            # Add the path and filename
        filename: Path = filepath.with_suffix(".jpg")   # Add the extension for the thumbnail
        filename.touch()                                # Create the file if it doesn't already exist
        urlretrieve(url, filename=filename)             # Download to filename
    except Exception as e:
        logging.exception(f'Could not download thumbnail at {filename}')
    # TODO implement a way to download the url, probably copy however pytube manages to do it without dependencies

def download_single(yt: YouTube, file_type: str, filepath: str, options: dict) -> None:
    '''
    Takes a single YouTube object and handles the downloading based on configs
    '''

    file_type_to_do = {         # Translation from file type to func
        "video": download_video, 
        "audio": download_audio, 
        "caption": download_caption, 
        "thumbnail": download_thumbnail}

    filepath = Path(filepath)       # Convert to Path
    path = filepath.parent          # Get the path
    filename = filepath.stem        # Get the filename

    print(f"Downloading {filepath}")

    func = file_type_to_do[file_type]               # Figure out what to do
    func(yt, path, filename, options)               # Call the function