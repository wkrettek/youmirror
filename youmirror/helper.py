__all__ = [""]

'''
This module manages the filetree
------
This is the second most important module in the project, it must be able to 
generate the paths and filenames that make up the project with the given options
and resolve any naming conflicts. Thankfully, we can do most of our work with just
pathlib and some crafty organization
# TODO
I am deciding between two filetree implementations
Let's call this the 'tall' implementation
   Root
    | -- channels
            | -- channel name
                    | -- videos
                    | -- captions
                    | -- audio
                    | -- thumbnails
    | -- playlists
            | -- playlist name
                    | -- videos
                    | -- captions
                    | -- audio
                    | -- thumbnails
    | -- singles
            | -- videos
            | -- captions
            | -- audio
            | -- thumbnails

----- or -----
Lets' call this the 'wide' implementation
   Root
    | -- videos
            | -- channels
                    | -- channel name
            | -- playlists
                    | -- playlist name
            | -- singles
    | -- captions
            | -- channels
            | -- playlists
            | -- singles
    | -- audio
            | -- channels
            | -- playlists
            | -- singles
    | -- thumbnails
            | -- channels
            | -- playlists
            | -- singles
------------------
The second one is better for the stuff I want to do with this project later on (files of the same type are all under one tree),
but the first one is better for keeping things more condensed. And if you just download videos, like most people do, you'll just see one folder inside the root, which is always annoying AF to me
------------------
I think I can implement an "export" command later on to use the db to export things that are grouped together. Sucks if your db gets corrupted, but oh well
'''
from pathlib import Path
import logging

valid_file_types = {"videos", "captions", "audio", "thumbnails"}  # Valid file types

def file_exists(filepath: Path) -> bool:
    '''
    Checks if the config exists in the current working directory
    '''
    try:
        return filepath.is_file()              # Check if the file exists
    except Exception as e:
        logging.info(f"Could not check file {filepath} due to {e}")
        return False

def create_file(filepath: Path) -> None:
    '''
    Creates a file given a path and filename
    '''
    try:
        if not filepath.is_file():
            filepath.open(mode = "w")
    except Exception as e:
        print(e)

def create_path(path: Path) -> None:
    '''
    Creates the path 
    '''
    try:
        if not path.is_dir():
            path.mkdir(parents = True, exist_ok = True)     
    except Exception as e:
        print(e)

def calculate_path(file_type: str, yt_type: str, parent_name) -> str:
    '''
    Calculates 
    wide formula = /file_type/yt_type/parent_name
    tall formula = /yt_type/parent_name/file_type
    '''
    # File type comes from options
    # Parent type comes from yt type
    # Parent name comes from yt name

    yt_types = {"channel": "channels","playlist": "playlists", "single": "singles"}         # Valid parent types
    if yt_type in yt_types:             # Check the yt_type is valid
        yt_type = yt_types[yt_type] # Yes I know this is dumb but I need to make it plural for formatting reasons
    
    path = Path(file_type)/Path(yt_type)/Path(parent_name)  # Build the filepath
    return  str(path)

def calculate_filename(file_type: str, yt_name: str) -> str:
    '''
    Calculates the filename from the given database settings and returns a string
    '''
    # File type comes from options
    # Parent type comes from yt type
    # Parent name comes from yt name
    file_type_to_extension = {"videos": ".mp4", "captions": ".srt", "audio": ".mp3", "thumbnails": ".jpg"}
    if file_type in valid_file_types:
        extension = file_type_to_extension[file_type]
        filename = f"{yt_name}.{extension}"
        return filename
    else:
        logging.error(f"Invalid file type {file_type} passed") 

def calculate_filepath(file_type: str, yt_type: str, parent_name: str,  yt_name: str,) -> str:
    '''
    Calculates what filepaths apply to a given 
    '''
    path = calculate_path(file_type, yt_type, parent_name)
    filename = calculate_filename(file_type, yt_name)
    filepath = Path(path)/Path(filename)
    return str(filepath)

# TODO
def resolve_collision(path: str, filetree: dict, yt_id: str) -> Path:
    '''
    Appends the yt_id if the path already exists
    '''
    if path in filetree:                           # If the path already exists
        path = Path(str(path) + f'_ym{yt_id}' ) # Append "_ym{yt_id}" to the end of the name 
    return path

def verify_installation(filepath: Path) -> bool:
    '''
    Take a database entry and verify that it is fully installed
    '''
    logging.info(f"Checking if file {filepath}")
    if filepath.is_file():
        logging.info(f"File {filepath} is installed")
        return True
    else:
        logging.info(f"File {filepath} is not installed")
    return False

