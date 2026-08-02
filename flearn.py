import argparse
import hashlib
import json
import os

from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

FLEARN_API_KEY = os.environ.get("FLEARN_API_KEY", None)
FLEARN_FOLDER = Path(os.environ.get('FLEARN_FOLDER', '~/.flearn')).expanduser()
FLEARN_DEBUG = False
FLEARN_FLASHCARD_GEN_PROMPT = """
You are a precise flashcard generator. Read the provided study materials and extract the most important concepts.
Output ONLY valid JSON in the following exact format:
{
  "cards": [
	{"front": "Question or concept?", "back": "Answer or definition."}
  ]
}
"""

client: Groq | None = None


def get_client() -> Groq:
	global client

	if client is None:
		if not FLEARN_API_KEY:
			print("Error: FLEARN_API_KEY is not set. Please check your .env file.")
			exit(1)
		client = Groq(api_key=FLEARN_API_KEY)

	return client


def get_file_hash(filepath: Path) -> str:
	hasher = hashlib.md5()
	hasher.update(filepath.read_bytes())
	return hasher.hexdigest()


def load_database(database_path: Path) -> dict:
	if not database_path.exists():
		return {}

	try:
		return json.loads(database_path.read_text())
	except json.JSONDecodeError:
		print(f"Warning: Database file '{database_path.name}' is corrupted. Starting fresh.")
		return {}


def get_all_cards(data: dict) -> list[dict]:
	cards_by_file = data.get("cards_by_file", {})

	if cards_by_file:
		cards = []

		for file_cards in cards_by_file.values():
			cards.extend(file_cards)

		return cards

	return data.get("cards", [])


def get_text_files(target_dir: Path, file_states: dict) -> tuple[str, dict]:
	content = []
	new_file_states = file_states.copy()

	for file_path in target_dir.glob("*"):
		if file_path.suffix.lower() in ['.txt', '.md']:
			try:
				current_hash = get_file_hash(file_path)
				filename = file_path.name

				if file_states.get(filename) != current_hash:
					if FLEARN_DEBUG:
						print(f"New or modified file detected: {filename}")

					text = file_path.read_text(encoding='utf-8')
					content.append(f"--- Document: {filename} ---\n{text}\n")
					new_file_states[filename] = current_hash
				else:
					if FLEARN_DEBUG:
						print(f"Unchanged, skipping: {filename}")
			except Exception as e:
				print(f"Warning: Could not read {file_path.name}: {e}")

	return "\n".join(content), new_file_states


def get_llm_flashcards(content: str) -> list[dict]:
	try:
		response = get_client().chat.completions.create(
			model="llama-3.3-70b-versatile",
			messages=[
				{"role": "system", "content": FLEARN_FLASHCARD_GEN_PROMPT},
				{"role": "user", "content": content}
			],
			response_format={"type": "json_object"},
			temperature=0.3
		)

		result = json.loads(response.choices[0].message.content)
		return result.get("cards", [])
	except Exception as e:
		print(f"Error communicating with Groq: {e}")
		return []


def sync_files(target_dir: Path, file_states: dict, cards_by_file: dict, force_regen: bool) -> bool:
	has_changes = False
	current_files = set()

	for file_path in target_dir.glob("*"):
		if file_path.suffix.lower() not in ['.txt', '.md']:
			continue

		filename = file_path.name
		current_files.add(filename)

		try:
			current_hash = get_file_hash(file_path)
			is_modified = file_states.get(filename) != current_hash

			if force_regen or is_modified:
				if FLEARN_DEBUG:
					status = "Regenerating" if force_regen else ("New" if filename not in file_states else "Modified")
					print(f"[DEBUG] {status} file detected: {filename}")

				print(f"Processing: {filename}...")
				text = file_path.read_text(encoding='utf-8')
				generated_cards = get_llm_flashcards(text)

				if generated_cards:
					cards_by_file[filename] = generated_cards
					file_states[filename] = current_hash
					has_changes = True
				else:
					print(f"Warning: Failed to generate cards for {filename}")
			else:
				if FLEARN_DEBUG:
					print(f"[DEBUG] Unchanged, skipping: {filename}")

		except Exception as e:
			print(f"Warning: Could not process {filename}: {e}")

	deleted_files = [file for file in file_states.keys() if file not in current_files]

	for deleted_file in deleted_files:
		if FLEARN_DEBUG:
			print(f"[DEBUG] Removing deleted file from state: {deleted_file}")

		file_states.pop(deleted_file, None)
		cards_by_file.pop(deleted_file, None)
		has_changes = True

	return has_changes


def gen(args, force_regen: bool = False):
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

	database_data = load_database(database_path)
	file_states = {} if force_regen else database_data.get("file_states", {})
	cards_by_file = {} if force_regen else database_data.get("cards_by_file", {})

	action_str = "Regenerating all" if force_regen else "Scanning for new or modified"
	print(f"{action_str} files in group '{group_name}'...")

	has_changes = sync_files(target_dir, file_states, cards_by_file, force_regen)

	if not has_changes:
		print("No new or modified files found. Everything is up to date!")
		return

	save_data = {
		"group": group_name,
		"source_dir": str(target_dir),
		"file_states": file_states,
		"cards_by_file": cards_by_file
	}

	database_path.write_text(json.dumps(save_data, indent=4))
	print(f"New flashcards saved to group '{group_name}'.")


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

	database_data = load_database(database_path)
	cards = get_all_cards(database_data)

	if not cards:
		print(f"No cards in group '{group_name}'")
		return

	print(f"\n--- Flashcards: {group_name} ---")
	for i, card in enumerate(cards, 1):
		print(f"\nCard {i}:")
		print(f"  Q: {card.get('front')}")
		print(f"  A: {card.get('back')}")
	print("\n" + "-" * 30)


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

	database_data = load_database(database_path)
	cards = get_all_cards(database_data)

	if not cards:
		print(f"No cards in group '{group_name}'")
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

	global FLEARN_DEBUG
	FLEARN_DEBUG = args.debug

	if args.command == "gen":
		gen(args, False)

	if args.command == "regen":
		gen(args, True)

	if args.command == "view":
		view(args)

	if args.command == "ls":
		ls()

	if args.command == "study":
		study(args)


if __name__ == "__main__":
	main()
