# Setup instructions

1. Install Docker on your machine
2. Add the controls template and example_input_data folders with appropriate subfolders and files
3. run `docker compose up -d` in same directory as docker compose file
4. Get the running container id using `docker ps`
5. exec into the docker container using command `docker exec --it CONTAINER_ID bash`
6. run the command inside the container to start the application `python main.py`
7. open in a browser the following url [localhost:8000/templates/001.html](localhost:8000/templates/001.html)
8. to gracefully shutdown the container in a new terminal run `docker compose down --rmi all`
9. since docker takes up a lot of space run `docker system prune -a` to remove unused docker images


## Build instructions
python -m eel main.py web --windowed --add-data="./controls:controls" --add-data="./template:template"
