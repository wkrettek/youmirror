'''
This module parses youtube urls, wraps them in pytube objects and 
pulls information from pytube objects
---
'''
from pytube import YouTube, Channel, Playlist, extract
from typing import Union, Any, Callable
import youmirror.filer as filer
from pytube.helpers import safe_filename
from pathlib import Path
import logging

def link_type(url: str) -> str:
    '''
    Really rough way to narrow down a link before creating a pytube object
    '''
    channel_strings = {'/user/', '/channel/', '/c/'}        # Possible strings for a channel
    if any(string in url for string in channel_strings):    # For some reason youtube has really inconsistent urls, so here we are
        return "channel"
    elif "playlist?list" in url:                            # String to check for a playlist
        return "playlist"
    elif "watch?v=" in url:                                 # String to check for a video
        return "single"
    else:
        logging.error(f"\'{url}\' is not a valid url")
        return None

def link_id(url: str, yt_string = None) -> str:
    '''
    Uses pytube's extract module to get the id from a url (more lightweight than creating an object)
    '''
    yt_string_to_func = {"channel": extract.channel_name, "playlist": extract.playlist_id, "single": extract.video_id}  # Translation dict from yt type to function

    if not yt_string:                   # Calculate the yt_string if not passed
        yt_string = link_type(url)
    func = yt_string_to_func[yt_string] # Extract the proper id from the url
    return func(url)
    
def yt_to_type_string(yt: Union[Channel, Playlist, YouTube]) -> str:
    '''
    Gets the type of the given pytube object and returns a string
    '''
    yt_type_to_string = {Channel: "channel", Playlist: "playlist", YouTube: "single"}    # Translation dict for convenience
    yt_type = type(yt)                      # Get type of pytube object
    if yt_type in yt_type_to_string:        # If it is a valid type
        return yt_type_to_string[yt_type]   # Return the translated string
    else:
        logging.error(f'Object {yt_type} is not a valid yt_type')


def get_metadata(yt: Union[Channel, Playlist, YouTube]) -> dict:
    '''
    Returns the metadata of a given pytube object as a dict
    '''
    meta = dict()
    meta["name"] = get_name(yt)             # Get the name
    meta["url"] = get_url(yt)
    if type(yt) in [Channel, Playlist]:     # Check if we have a channel or playlist
        children = get_children(yt)         # This will use pytube to get video_urls
        children_ids = set([link_id(child, "single") for child in children])    # We want the ids (not urls) for databasing purposes
        meta["children"] = children_ids     # Add the children ids to the metadata
        meta["available"] = True            # We will add a check later to determine this

    elif isinstance(yt, YouTube):
        meta["available"] = is_available(yt)    # Individual videos can be checked if they are available
    return meta

def is_available(yt: YouTube) -> bool:
    try:
        yt.check_availability()
    except Exception as e:
        logging.exception(f"Video {yt.title} is not available due to {e}")   # Need to report the url or the title if we can
    return True

def get_pytube(url: str, cache: dict[str: Union[YouTube, Channel, Playlist]]) -> Union[YouTube, Channel, Playlist]:
    '''
    Returns a new pytube object if not in the cache
    '''
    if url in cache:        # If the url is in the cache, return its object
        return cache[url]

    objects = {"channel": Channel, "playlist": Playlist, "single": YouTube}
    url_type = link_type(url)                       # Returns what type of link it is (as string)
    try:
        object = wrap_url(url, objects[url_type])   # Wrap the url in the proper pytube object
        cache[url] = object                         # Cache the object
        return object
    except Exception as e:
        logging.exception(f"Failed to parse Youtube link due to {e}")
        return None         # This indicates something went wrong, but we will handle it above

def new_pytube(url: str) -> Union[YouTube, Channel, Playlist]:
    '''
    This replaces get_pytube and returns a new pytube object from url
    '''
    objects = {"channel": Channel, "playlist": Playlist, "single": YouTube}
    url_type = link_type(url)                       # Returns what type of link it is (as string)
    try:
        object = wrap_url(url, objects[url_type])   # Wrap the url in the proper pytube object
        return object
    except Exception as e:
        logging.exception(f"Failed to parse Youtube link due to {e}")
        return None         # This indicates something went wrong, but we will handle it above

def wrap_url(url: str, object: Union[YouTube, Channel, Playlist]) -> Union[YouTube, Channel, Playlist]:
    '''
    Wraps the url in the proper pytube object
    '''
    return object(url)

def get_id(yt: Union[YouTube, Channel, Playlist]) -> str:
    """
    Returns the id of the pytube object
    """
    # funcs = {YouTube: get_id_from_video, Channel: get_id_from_channel, Playlist: get_id_from_playlist}
    # pytype = type(yt)
    # func = funcs[pytype]
    # return func(yt)
    type_to_id = {YouTube: "video_id", Channel: "channel_uri", Playlist: "playlist_id"}    # Translation dict from type to attribute
    t = type(yt)
    if t in type_to_id:
        return getattr(yt, type_to_id[t])
    else:
        logging.error(f"Failed to get id for {yt}")
        return None

def get_name(yt: Union[YouTube, Channel, Playlist]) -> str:
    """
    Returns the name of the pytube object
    """
    type_to_name = {YouTube: "title", Channel: "channel_name", Playlist: "title"}    # Translation dict from type to attribute
    t = type(yt)                         # Get the type of the object
    if t in type_to_name:                # If it is a valid type
        return getattr(yt, type_to_name[t])   # Return the attribute
    else:
        logging.error(f"Failed to get name for {yt}")
        return None

def get_url(yt: Union[YouTube, Channel, Playlist]) -> str:
    """
    Returns the url of the pytube object
    """
    type_to_url = {YouTube: "watch_url", Channel: "vanity_url", Playlist: "playlist_url"}    # Translation dict from type to property
    t = type(yt)                         # Get the type of the object
    if t in type_to_url:                # If it is a valid type
        return getattr(yt, type_to_url[t])   # Return the attribute
    else:
        logging.error(f"Failed to get url for {yt}")
        return None

def get_children(yt: Union[Channel, Playlist]) -> list[str]:
    '''
    Takes either a Channel or Playlist object and returns its video links as a list of strings
    '''
    try:
        logging.debug(f"Getting children for {get_name(yt)}")
        children = [url for url in yt.video_urls]   # Maybe we can async get this in the future?
        return children
    except Exception as e:
        logging.exception(f"Failed to get children for {get_name(yt)} due to {e}")
        return None

def get_files(path: str, yt_name: str, options: dict) -> dict:
    '''
    Returns a dict of filenames we want to download
    files = {filepath: {type: file_type, caption_type: caption_type}, filepath: {type: file_type, caption_type: caption_type}}
    '''
    to_download = { # Returns true/false if we want to download the video
        "video": options["dl_video"], 
        "audio": options["dl_audio"], 
        "caption": options["dl_captions"], 
        "thumbnail": options["dl_thumbnail"]
    }
    files = dict()
    for file_type in to_download:
        if to_download[file_type]:   # Check the boolean value matching the file_type
            if file_type == "caption":
                for caption_type in options["captions"]:    # We can download multiple caption types
                    filename = filer.calculate_filename(file_type, f'{yt_name}_{caption_type}')    # Add f'_{caption_type}'
                    filepath = str(Path(path)/filename)        # TODO THIS IS OVERKILL I WILL SIMPLIFY LATER
                    files[filepath] = {"type": file_type, "caption_type": caption_type}  # Add to files               
            else:
                filename = filer.calculate_filename(file_type, yt_name)    # Calculate the filename
                filepath = str(Path(path)/filename)                              # TODO THIS IS OVERKILL I WILL SIMPLIFY LATER
                files[filepath] = {"type": file_type}                            # Add to files

    return files

def is_available(yt: YouTube) -> bool:
    '''
    Returns whether a given pytube object is available
    '''
    try:
        yt.check_availability()
        return True
    except Exception as e:
        return False


def get_keys(yt: Union[Channel, Playlist, YouTube], keys: dict, options: dict, paths: dict) -> dict:
    '''
    Gets the keys that we want to put into the database and returns as a dictionary
            Channels/Playlists
                id
                name
                children
                available
                path
            Singles
                id          id from url
                name        Video title
                type        AKA parent type
                parent      Parent's id
                available   uses pytube's is_available()
                files       
    You can pass in a dict if you want to inject some values from above
    This is going to be a heavy function that calls from a lot of places. It's calculating a lot of things
    TODO I think I might move this to the databaser
    '''
    to_download = { # Returns true/false if we want to download the video
        "video": options["dl_video"], 
        "audio": options["dl_audio"], 
        "caption": options["dl_captions"], 
        "thumbnail": options["dl_thumbnail"]
    }
    yt_string = yt_to_type_string(yt)   # Get the type as a string
    metadata = get_metadata(yt)         # Strip the useful data off the pytube object
    keys.update(metadata)               # Add to our keys
    yt_id = get_id(yt)                  # We use this to resolve collisions

    if yt_string in ["channel", "playlist"]:    # Do the same stuff for channels and playlists
        path = filer.calculate_path(yt_string, keys["name"], "")
        keys["path"] = filer.resolve_collision(path, paths, yt_id)
        return keys

    elif yt_string == "single":
        if "parent_name" not in keys:           # Check if the parent name is already in the keys
            keys["parent_name"] = "None"            # Parent's name is empty if it's a single

        if "parent_type" not in keys:           # Check if the parent type is already in the keys
            keys["parent_type"] = "single"      # Parent's type is single if it's a single
        else:
            yt_string = keys["parent_type"]     # We are resetting the type to the parent type

        if "path" not in keys:                  # If no path was passed, calculate a new one
            temp = filer.calculate_path(yt_string, "", keys["name"])
            keys["path"] = filer.resolve_collision(temp, paths, yt_id)
        else:   # Take the path and add the name
            name = safe_filename(keys["name"]).replace(' ', '_')
            temp = str(Path(keys["path"])/Path(name))
            keys["path"] = filer.resolve_collision(temp, paths, yt_id)
            
        keys["files"] = get_files(keys["path"], keys["name"], options)  # Get the files for this video
        return keys
    else: 
        logging.error(f"Failed to get keys for {yt_string} {yt}")
        return None