import argparse
import json
import os

from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

FLEARN_API_KEY = os.environ.get("FLEARN_API_KEY", None)
FLEARN_DEBUG = False
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
	group_name = args.group
	database_path = FLEARN_FOLDER / f"{group_name}.json"

	if FLEARN_DEBUG:
		print(f"Looking up Group Name: {group_name}")
		print(f"Reading from Database Path: {database_path}")

	if not database_path.exists():
		print(f"Error: No flashcards found for group '{group_name}'.")
		print("Run 'flearn ls' to see avaliable groups.")
		return

	try:
		data = json.loads(database_path.read_text())
		cards = data.get("cards", [])

		print(f"\n--- Flashcards: {group_name} ---")
		for i, card in enumerate(cards, 1):
			print(f"\nCard {i}:")
			print(f"  Q: {card.get('front')}")
			print(f"  A: {card.get('back')}")
		print("\n" + "-" * 30)
	except json.JSONDecodeError:
		print(f"Error: The file {database_path} is corrupted or not valid JSON.")


def ls():
	if FLEARN_DEBUG:
		print(f"Scanning Database Folder: {FLEARN_FOLDER}")

	print("Available flashcard groups:")

	if not FLEARN_FOLDER.exists():
		print("  No groups found (database folder is empty).")
		return

	found = False
	for file in FLEARN_FOLDER.glob("*.json"):
		found = True
		print(f"  - {file.stem}")

	if not found:
		print("  No groups found.")


def study(args):
	group_name = args.group
	database_path = FLEARN_FOLDER / f"{group_name}.json"

	if FLEARN_DEBUG:
		print(f"Loading Study Session for Group: {group_name}")

	if not database_path.exists():
		print(f"Error: No flashcards found for group '{group_name}'.")
		print("Run 'flearn ls' to see available groups.")
		return

	try:
		data = json.loads(database_path.read_text())
		cards = data.get("cards", [])

		if not cards:
			print(f"No cards found in group '{group_name}'.")
			return

		print(f"\n--- Studying: {group_name} ---")
		print("Press [Enter] to reveal answers. Type 'q' and [Enter] to quit.\n")

		for i, card in enumerate(cards, 1):
			print(f"Card {i} of {len(cards)}")
			print(f"Q: {card.get('front')}")

			user_input = input("\n> Press Enter to reveal answer...")
			if user_input.strip().lower() == 'q':
				break

			print(f"A: {card.get('back')}")
			print("-" * 40)

			if i < len(cards):
				user_input = input("> Press Enter for next card...")
				if user_input.strip().lower() == 'q':
					break

		print("\nStudy session complete.")

	except json.JSONDecodeError:
		print(f"Error: The file {database_path} is corrupted or not valid JSON.")


def main():
	FLEARN_FOLDER.mkdir(parents=True, exist_ok=True)

	parser = argparse.ArgumentParser(prog="flearn", description="CLI AI-supported tool for quickly creating flashcards from materials you put in.")
	parser.add_argument("--debug", action="store_true", help="enable debug output")

	subparsers = parser.add_subparsers(dest="command", title="commands")

	# flearn gen <directory>
	parser_gen = subparsers.add_parser("gen", help="generates flashcards from new data in a given directory")
	parser_gen.add_argument("directory", type=str, help="target directory")

	# flearn regen <directory>
	parser_regen = subparsers.add_parser("regen", help="regenerates flashcards from all the data in a given directory")
	parser_regen.add_argument("directory", type=str, help="target directory")

	# flearn view <group>
	parser_view = subparsers.add_parser("view", help="views flashcards from a given group")
	parser_view.add_argument("group", type=str, help="name of the flashcard group to view")

	# flearn ls
	_ = subparsers.add_parser("ls", help="lists available flashcard groups")

	# flearn study <group>
	parser_study = subparsers.add_parser("study", help="interactively study flashcards from a given group")
	parser_study.add_argument("group", type=str, help="name of the flashcard group to study")

	args = parser.parse_args()

	if args.command is None:
		parser.print_help()
		return

	if args.debug:
		global FLEARN_DEBUG
		FLEARN_DEBUG = True
	else:
		FLEARN_DEBUG = False

	if args.command == "gen":
		gen(args)

	if args.command == "regen":
		regen(args)

	if args.command == "view":
		view(args)

	if args.command == "ls":
		ls()

	if args.command == "study":
		study(args)


if __name__ == "__main__":
	main()
