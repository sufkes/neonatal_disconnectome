python -m eel main.py web --windowed --noupx ^
  --add-data="./controls:controls" ^
  --add-data="./template:template" ^
  --hidden-import PIL._tkinter_finder ^
  --hidden-import PIL._imagingtk
