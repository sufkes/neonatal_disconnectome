# Libraries used

1. Eel
2. [Picnic css](https://picnicss.com/)

# Setup instructions

## Setup using docker

1. Install Docker on your machine
2. Add the controls template and example_input_data folders with appropriate subfolders and files
3. run `docker compose up -d` in same directory as docker compose file
4. Get the running container id using `docker ps`
5. exec into the docker container using command `docker exec --it CONTAINER_ID bash`
6. run the command inside the container to start the application `python main.py`
7. open in a browser the following url [localhost:8000/templates/main.html](localhost:8000/templates/main.html)
8. to gracefully shutdown the container in a new terminal run `docker compose down --rmi all`
9. since docker takes up a lot of space run `docker system prune -a` to remove unused docker images

## Troubleshooting

### if you run into this issue

```
Authorization required, but no authorization protocol specified

Traceback (most recent call last):
  File "/home/disconnectome/.local/lib/python3.11/site-packages/eel/__init__.py", line 537, in _process_message
    return_val = _exposed_functions[message['name']](*message['args'])
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/main.py", line 23, in getFolder
    root = Tk()
           ^^^^
  File "/usr/local/lib/python3.11/tkinter/__init__.py", line 2345, in __init__
    self.tk = _tkinter.create(screenName, baseName, className, interactive, wantobjects, useTk, sync, use)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_tkinter.TclError: couldn't connect to display "unix:0"
```

just run `xhost +local:docker` from your main terminal

### setting up Tkinter on Mac

install tkinter with homebrew

## Setup using venv instead of docker

1. Create a python virtual environment: `python -m venv disconnectomeEnv`
2. Activate the environment in your terminal:
   1. MacOS: `source disconnectomeEnv/bin/activate`
   2. Window: `disconnectomeEnv\Scripts\activate`
3. Install package: `pip install --no-cache-dir -r requirements.txt`
4. When you are done deactivate: `Deactivate`

# Build instructions

python -m eel main.py web --windowed --noupx --add-data="./controls:controls" --add-data="./template:template" --hidden-import PIL._tkinter_finder --hidden-import PIL._imagingtk

add --onefile --noconsole when happy with result
