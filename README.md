# flash-learner

A fast CLI tool that automatically lets you generate, manage and study flashcards directly from your local notes, lectures and documents, with the use of AI.


## Features

- **Multiple Format Support:** Extracts text from .txt, .md, .pdf, .docx, .pptx, .png and .jpg.
- **Flashcard Generation:** Uses Llama 3 via Groq to extract strict definitions and concepts.
- **State Tracking:** Modifying a document only updates the flashcards for that specific file without duplicating your deck.
- **Command Line Interface:** A terminal UI for flipping cards and reviewing materials.


## Installation

### Prerequisites

Tesseract is required to run flearn if you want to extract text from images

### Build from source

```
git clone https://github.com/Kapcpa/flash-learner.git
cd flash-learner
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile flearn.py
```

### First run

Running the binary first time will detect that it has not been set up and will launch the setup wizard.

`./flearn`

It will prompt for the Groq API key and ask if you want to install flearn globally. Once installed you can use it from any directory

## Usage

Flash-learner organizes flashcards into groups. Group name is set autmatically to the name of the folder containing the source files.

```
flearn --help
usage: flearn [-h] [--debug] {gen,regen,rm,view,ls,study} ...

CLI AI-supported tool for quickly creating flashcards from materials you put in.

options:
  -h, --help            show this help message and exit
  --debug               enable debug output

commands:
  {gen,regen,rm,view,ls,study}
    gen                 generates flashcards from new data in a given directory
    regen               regenerates flashcards from all the data in a given directory
    rm                  removes specific flashcards by their numbers
    view                views flashcards from a given group
    ls                  lists available flashcard groups
    study               interactively study flashcards from a given group
```

## Commands

### gen
`flearn gen path/to/notes`

Scans the files, generates flashcards and ask for approval before saving them to the database. Running this command again later will result in only processing the files that have been added or modified.

### regen
`flearn regen path/to/notes`

Ignores the cache and completely rebuiulds a deck of flashcards based on the current state of the folder.

### rm
`flearn rm group-name flashcard-indices`

Removes flashcards from a given group by their index number.

### ls
`flearn ls`

Lists all the groups currently stored in local database.

### view
`flearn view group-name`

Shows the entire Q&A list for a given group

### study
`flearn study group-name`

Goes over flashcards of a given group one by one.

## Debugging

Appending the `--debug` flag to any command shows exactly what the app is doing under the hood.
