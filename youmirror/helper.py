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

import youmirror.parser as parser
from pathlib import Path
import logging
from pytube import Channel, Playlist, YouTube
from typing import Union


def get_path(path : str, filename : str) -> Path:
    '''
    Wraps a path and filename into a Path object
    '''
    path = Path(path)   # Wrap the path
    filepath = path/Path(filename)
    return filepath

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

def path_exists(path: Path) -> bool:
    '''
    Checks if a path exists
    '''
    return path.is_dir()

def create_path(path: Path) -> None:
    '''
    Creates the path 
    '''
    try:
        if not path.is_dir():
            path.mkdir(parents = True, exist_ok = True)     
    except Exception as e:
        print(e)

def verify_config(filepath: Path) -> Path:
    '''
    Find the config file in the current working directory
    '''
    if  filepath.exists():
        return filepath
    else:
        return None

def calculate_path(yt: Union[Channel, Playlist, YouTube]) -> str:
    '''
    Calculates the filepath for the given database settings
    wide formula = /file_type/parent_type/parent_name
    tall formula = /parent_type/parent_name/file_type
    '''
    file_types = {"videos", "captions", "audio", "thumbnails"}  # Valid file types
    parent_types = {"channels", "playlists", "singles"}
    path_dict = {Channel: "channels", Playlist: "playlists", YouTube: "singles"}    # Dict to sort from object to path
    object_type = type(yt)                          # Get the type of pytube object
    pathname = Path(path_dict[object_type])         # The object type will inform us where to sort it
    if isinstance(yt, YouTube):                     # If it's a single, stop here
        return str(pathname)
    pathname = pathname/Path(parser.get_name(yt))   # Add the channel/playlist's name to the path
    # Resolve collision, need to add some handling here in case it sees a duplicate and that's okay
    # I guess if we only do this while adding then it will always be okay, because we catch duplicates before getting to this stage? We won't be calculating the filepath, we'll be checking it against the 
    return  str(pathname)

# TODO
def resolve_collision(yt: YouTube, filename: Path) -> Path:
    '''
    Changes the filename if one already exists with the same name
    '''
    return ''

# This can either get the filename from the pytube stream object, or it can generate
# It itself from the title
# RESOLUTION: For now we will just use the title until this breaks things
def calculate_filename(yt: YouTube) -> str:
    '''
    Determines the filename from the youtube object
    Must handle collision
    '''
    try:
        filename = yt.title
        # filename = resolve_collision()
        return filename
    except Exception as e:
        return None

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

