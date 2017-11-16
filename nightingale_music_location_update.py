# -*- coding: utf-8 -*-
"""
Usage:
  1. Run the script.
  2. Supply the path to the main@library.songbirdnest.com.db when asked.
  3. When prompted, provide the "existing" part of a file path which you'd like
     to replace.
  4. When prompted, provide the replacement part of a file path which you'd like
     to substitute for the existing bit you specified a moment before.

I wrote this module to help me preserve the ratings and collected mass of
pasted-in-and-saved song lyrics that I had amassed over years of using
Nightingale <https://getnightingale.com/>, a desktop music player, on another
computer.

Replacing the contents of the profile folder inside the new install's
AppData/Roamin/Nightingale/Profiles directory with the contents of my old
profile was simple enough. Nightingale only asked me to update my "watch" folder
and I did that easily through the Nightingale UI. I had also migrated all of the
actual music files, but they were going to be in a different location on the new
system.

There didn't seem to be any way of handling this through the Nightingale UI, so
I had a look at the SQLite databases stored in the 'db' subdirectory of the
profile folder.

The database named <main@library.songbirdnest.com.db>[1] is where the music file
locations were stored.

[1] Nightingale is a fork of Songbird, which halted development in 2013.
    <https://en.wikipedia.org/wiki/Songbird_(software)>
"""

from pathlib import Path
import sqlite3

def dict_factory(cursor, one_row):
    """
    Turns db rows into dictionaries.
    """
    dict_this_row = {}
    for idx, col in enumerate(cursor.description):
        dict_this_row[col[0]] = one_row[idx]
    return dict_this_row

def commit_close_and_quit(connection):
    """
    Commits changes, closes db connection, and quits this script.
    """
    connection.commit()
    connection.close()
    quit()

def from_user_get_db_path():
    """
    Prompts user to provide path to their main@library.songbirdnest.com.db.
    """
    str_msg = "Please enter the path to your main@library.songbirdnest.com.db: "
    str_ng_sqlite_db_location = input(str_msg).strip()
    file_ng_db = Path(str_ng_sqlite_db_location)
    if not file_ng_db.is_file():
        print("There doesn't seem to be any SQLite database there. Quitting")
        quit()
    else:
        return str_ng_sqlite_db_location

def rtn_int_total_songs(conn_db, curs_db):
    """
    Checks whether the db contains any songs. Functions as a sanity check.
    """
    str_query = "SELECT COUNT(*) FROM media_items"
    int_songs = int(curs_db.execute(str_query).fetchone()['COUNT(*)'])
    if int_songs == 0:
        str_msg = ("There don't seem to be any songs (media_items). Are you"
                   "sure that you specified the correct database file?")
        print(str_msg)
        commit_close_and_quit(conn_db)
    else:
        return int_songs


def get_file_path_frag_to_replace():
    """
    Prompts user to specify the part of file paths which they want to replace.
    """
    str_msg = ("Please enter the path prefix (i.e. the 'front' of the path, "
               "starting from the beginning) to your music files location which"
               "you want to replace:")
    str_file_path_frag_to_replace = input(str_msg).strip()
    if not str_file_path_frag_to_replace:
        print("You didn't provide a path prefix to replace. Quitting")
        quit()
    else:
        return str_file_path_frag_to_replace

def get_replacement_file_path_frag(str_old_path_frag):
    """
    Prompts user to specify the (partial) file paths they want to substitute in.
    """
    str_msg = ("Please enter the replacement path prefix (i.e. the value you "
               "want to substitute for the one you provided a moment ago)")
    str_replacement_file_path_frag = input(str_msg).strip()
    if not str_replacement_file_path_frag:
        print("You didn't provide a new path prefix to substitute for the"
              "old. Quitting")
        quit()
    if str_replacement_file_path_frag == str_old_path_frag:
        print("You provided the same value for the old and path prefix."
              "Nothing to do here. Quitting")
        quit()
    else:
        return str_replacement_file_path_frag

def rtn_int_num_paths_to_modify(str_target, int_num_songs, conn_db, curs_db):
    """
    How many file paths will be modified?
    """
    str_query = "SELECT COUNT(*) FROM media_items WHERE content_url LIKE ?"
    int_affected = int(curs_db.execute(str_query, ('%' + str_target + '%',)).fetchone()['COUNT(*)'])
    if int_affected == 0:
        print("No songs appear to be associated with the file path location"
              "prefix you specified.")
        commit_close_and_quit(conn_db)
    else:
        print(str(int_affected) + ' songs (of a total of ' + str(int_num_songs) +
              ') appear to be associated with the old location you have specified.')
        return int_affected

def rtn_int_paths_changed(str_target, str_replacement, curs_db):
    """
    Do the substitution and return the number of paths modified.
    """
    int_rows_selected = 0
    int_rows_changed = 0
    for row in curs_db.execute("SELECT * FROM media_items").fetchall():
        int_rows_selected += 1
        if row['content_url'].startswith(str_target):
            str_new_path = row['content_url'].replace(str_target, str_replacement)
            str_query = "UPDATE media_items SET content_url=? WHERE media_item_id=?"
            curs_db.execute(str_query, (str_new_path, row['media_item_id'],))
            int_rows_changed += 1
    if int_rows_changed > 0:
        str_msg = ('This script changed the content_url value for ' +
                   str(int_rows_changed) + ' of ' + str(int_rows_selected) + ' songs.')
        print(str_msg)
    else:
        print('Something went wrong. No changes were made.')
    return int_rows_changed

if __name__ == "__main__":
    conn = sqlite3.connect(from_user_get_db_path())
    conn.row_factory = dict_factory
    c = conn.cursor()
    int_total_songs = rtn_int_total_songs(conn, c)
    str_old_frag = get_file_path_frag_to_replace()
    str_new_frag = get_replacement_file_path_frag(str_old_frag)
    int_changes_needed = rtn_int_num_paths_to_modify(str_old_frag, int_total_songs, conn, c)
    int_changes_made = rtn_int_paths_changed(str_old_frag, str_new_frag, c)
    commit_close_and_quit(conn)

