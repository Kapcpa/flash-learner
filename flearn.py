import argparse
import os

from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

FLEARN_API_KEY = os.environ.get("FLEARN_API_KEY", None)
FLEARN_DEBUG = os.environ.get("FLEARN_DEBUG", False)
FLEARN_FOLDER = Path(os.environ.get('FLEARN_FOLDER', '~/.flearn')).expanduser()

client: Groq | None = None


def get_client() -> Groq:
	global client

	if client is None:
		if not FLEARN_API_KEY:
			print("Error: FLEARN_API_KEY is not set. Please check your .env file.")
			exit(1)
		client = Groq(api_key=FLEARN_API_KEY)

	return client


def gen(args):
	target_dir = Path(args.directory).resolve()
	group_name = target_dir.name

	database_path = FLEARN_FOLDER / f"{group_name}.json"

	if FLEARN_DEBUG:
		print(f"Target Directiory: {target_dir}")
		print(f"Group Name: {group_name}")
		print(f"Saving to Database Path: {database_path}")

	if not target_dir.exists() or not target_dir.is_dir():
		print(f"Error: Directory '{args.directory}' does not exist.")
		return

	print(f"Generating new flashcards for group '{group_name}' from {target_dir}...")

	# TODO: pass content to llm here
	mock_data = {
		"group": group_name,
		"source_dir": str(target_dir),
		"cards": [
			{"front": "What does flearn do?", "back": "Generates flashcards using AI!"}
		]
	}

	database_path.write_text(json.dumps(mock_data, indent=4))
	print(f"New flashcards saved to group '{group_name}'.")


def regen(args):
	target_dir = Path(args.directory).resolve()
	group_name = target_dir.name
	print(f"Regenerating all flashcards for group '{group_name}' from {target_dir}...")
	# TODO: Implement full overwrite logic


def view(args):
	target_dir = Path(args.directory)
	print(f"Viewing flashcards in {target_dir}...")


def ls(args):
	print("Listing directories and flashcard counts...")


def main():
	parser = argparse.ArgumentParser(prog="flearn", description="CLI AI-supported tool for quickly creating flashcards from materials you put in.")
	parser.add_argument("--debug", action="store_true", help="enable debug output")

	subparsers = parser.add_subparsers(dest="command", title="commands")

	# flearn gen
	parser_gen = subparsers.add_parser("gen", help="generates flashcards from new data in a given directory")
	parser_gen.add_argument("directory", type=str, help="target directory")

	# flearn regen
	parser_regen = subparsers.add_parser("regen", help="regenerates flashcards from all the data in a given directory")
	parser_regen.add_argument("directory", type=str, help="target directory")

	# flearn view
	parser_view = subparsers.add_parser("view", help="views flashcards from a given directory")
	parser_view.add_argument("directory", type=str, help="target directory")

	# flearn ls
	parser_ls = subparsers.add_parser("ls", help="lists directories and their state")
	parser_ls.add_argument("directory", type=str, nargs='?', default=".", help="target directory (optional)")

	args = parser.parse_args()

	FLEARN_FOLDER.mkdir(parents=True, exist_ok=True)

	if args.debug:
		global FLEARN_DEBUG
		FLEARN_DEBUG = True

	if args.command == "gen":
		gen(args)

	if args.command == "regen":
		regen(args)

	if args.command == "view":
		view(args)

	if args.command == "ls":
		ls(args)


if __name__ == "__main__":
	main()