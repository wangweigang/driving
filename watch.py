# watch a file change. modified based on https://stackoverflow.com/questions/182197/how-do-i-watch-a-file-for-changes/4690739#4690739

import os
import win32file
import win32con

path_to_watch = "." # look at the current directory
file_to_watch = "test.txt" # look for changes to a file called test.txt

def ProcessNewData( newData ):
    print ("Text added: %s"%newData)

# Set up the bits we'll need for output
ACTIONS = {
  1 : "Created",
  2 : "Deleted",
  3 : "Updated",
  4 : "Renamed from something",
  5 : "Renamed to something"
}

FILE_LIST_DIRECTORY = 0x0001
hDir = win32file.CreateFile (
  path_to_watch,
  FILE_LIST_DIRECTORY,
  win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
  None,
  win32con.OPEN_EXISTING,
  win32con.FILE_FLAG_BACKUP_SEMANTICS,
  None
)

# Open the file we're interested in
a = open(file_to_watch, "r")

# Throw away any exising log data
a.read()

# Wait for new data and call ProcessNewData for each new chunk that's written
while 1:
  # Wait for a change to occur
  results = win32file.ReadDirectoryChangesW (
    hDir,
    1024,
    False,
    win32con.FILE_NOTIFY_CHANGE_LAST_WRITE,
    None,
    None
  )

  # For each change, check to see if it's updating the file we're interested in
  for action, file in results:
    #full_filename = os.path.join (path_to_watch, file)
    print (file, ACTIONS.get (action, "Unknown"))
    if file == file_to_watch:
        newText = a.read()
        if newText != "":
            ProcessNewData( newText )
            
            