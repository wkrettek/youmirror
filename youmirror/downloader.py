
'''
This module handles all of the downloading to disk, and parses whatever 
filters were passed down from the config 

My first priority is finding the best matching resolution when the user specifies it. Then, the container (mp4/webm) has to match the audio codec so we can combine them. The absolute basic default is to download the highest resolution video and audio. If we download by resolution we can use stream.includes_audio_track to decide if we have to find a matching audio track.

I could maybe make other types of downloads available. I think a possible one is like a metadata and another one is like the js. Could be useful

'''
from pytube import YouTube, StreamQuery, Stream, Caption, request
import logging
from pathlib import Path
from urllib.request import urlretrieve  # Using this to download thumbnails

file_types = {"video", "caption", "audio", "thumbnail"} # TODO download js and raw html?
resolutions = ["highest", "lowest", "144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p", "4320p"] # Stored as a list because order is important
sub_types = ["mp4", "webm"]    # Prefer mp4 over webm
resolution_to_itags = {
    "144p": {}, "240p": {}, "360p": {}, "480p": {}, "720p": {},
    "1080":{}, "1440":{}, "2160":{}, "4320":{},
}

def get_stream(yt: YouTube, file_type: str, options: dict) -> Stream:
    '''
    Applies all the filters and gets a stream object
    # TODO this implements a fix that is not in pytube right now so it is in my wkrettek repo,
    Need to implement myself until pytube is updated
    '''
    subtype = "mp4" # This is the subtype we're gonna go with
    if file_type == "audio":
        stream = yt.streams.filter(only_audio=True, subtype=subtype).order_by("abr").desc()
    else:
        stream = yt.streams.get_highest_resolution()
    return stream

def download_stream(stream: Stream, path: str, filename: str, options: dict) -> bool:
    '''
    Downloads to the given filepath and returns if a new file was downloaded or not
    '''
    filename = filename + ".mp4"
    stream.download(output_path=path, filename=filename) # Download to the appropriate path and name
    return True

def download_video(yt: YouTube, path: str, filename: str, options: dict) -> None:
    '''
    Gets the proper stream for video and downloads it
    '''
    try:
        stream = get_stream(yt, "video", options)     # Get stream with applied filters
        download_stream(stream, path, filename, options)
    except Exception as e:
        logging.exception(f'Could not download video at {str(path) + filename}')

def download_caption(yt: YouTube, path: str, filename: str, options: dict) -> str:
    '''
    Gets the captions from the video and downloads them
    # TODO This implements a uses a fix that is not in pytube right now so it is in my wkrettek repo
    Probably should just implement it in this library until pytube is updated
    '''
    # TODO handle for different languages
    captions = yt.caption_tracks
    for i, c in enumerate(captions):
        c.download(output_path=path, title=filename+str(i)) # Adding the index to the filename for now
    return filename

def download_audio(yt: YouTube, path: str, filename: str, options: dict) -> str:
    '''
    Gets the audio from a video and downloads it
    -----
    Stream looks like yt.streams.filter(only_audio=True, subtype="mp4").desc()
    Audio files are coming out too long, so we want to trim it to the reported length if it is longer
    '''
    options["dl_audio"] = True
    try:
        stream = get_stream(yt, "audio", options)
        download_stream(stream, path, filename, options)
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

def download_single(yt: YouTube, filepath: str, options: dict) -> None:
    '''
    Takes a single YouTube object and handles the downloading based on configs
    '''
    extension_to_file_type = {  # Translation from file extension to file type
        ".mp4":"video", ".mp3": "audio", 
        ".srt": "caption", ".jpg": "thumbnail"}

    file_type_to_do = {         # Translation from file type to func
        "video": download_video, 
        "audio": download_audio, 
        "caption": download_caption, 
        "thumbnail": download_thumbnail}

    filepath = Path(filepath)       # Convert to Path
    path = filepath.parent          # Get the path
    filename = filepath.stem        # Get the filename

    print(f"Downloading {filepath}")

    extension = Path(filepath).suffix   # Get the extension
    file_type = extension_to_file_type[extension]   # Convert to file type
    func = file_type_to_do[file_type]   # Figure out what to do
    func(yt, path, filename, options)         # Call the function