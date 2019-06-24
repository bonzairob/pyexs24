# PyEXS24 - reading EXS24 files in Python

This tool allows reading of Apple's EXS24 software instrument format (used in GarageBand and Logic) in Python.

## Usage
You can run `python pyexs24.py [exs file]` to print a file's details on the command line.

You can also import pyexs24 into your own project, where `pyexs24.load_exs( file_path )` will return a dict object containing `zones` and `samples`.

## Credits
The file was ported from a lua project, **EXS24 for Renoise**, by matt-allan, which can be found [here](https://github.com/matt-allan/renoise-exs24).