# -*- coding: utf-8 -*-
import re
import logging
import argparse
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)
if not logger.handlers:
	handler = logging.StreamHandler()
	handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
	logger.addHandler(handler)
	logger.setLevel(logging.INFO)
	logger.propagate = False


def find_closing_brace(text, start_index):
	open_braces = 0
	i = start_index
	length = len(text)
	in_quote = False

	while i < length:
		char = text[i]
		if char == '"':
			in_quote = not in_quote
		elif not in_quote:
			if char == '#': # Simple comment skipping
				eol = text.find('\n', i)
				if eol == -1: return -1
				i = eol
			elif char == '{':
				open_braces += 1
			elif char == '}':
				open_braces -= 1
				if open_braces == 0:
					return i
		i += 1
	return -1


def check_civic_conflicts(mod_path):
	civics_path = mod_path / "common/governments/civics"
	if not civics_path.is_dir():
		logger.error("Civics directory not found: %s" % civics_path)
		return

	logger.info("Checking for civic conflicts in %s..." % civics_path)

	civic_conflicts = defaultdict(set)
	civic_files = {}
	neg_re = re.compile(r'\b(NOT|NOR)\s*=\s*\{')
	possible_re = re.compile(r"\bpossible\s*=\s*\{")
	has_civic_re = re.compile(r'\bhas_civic\s*=\s*"?([\w\.\-\:]+)"?')
	value_re = re.compile(r'\bvalue\s*=\s*"?([\w\.\-\:]+)"?')
	block_start_re = re.compile(r"^([@\w\.\-\:]+)\s*=\s*\{", re.M)
	sub_block_re = re.compile(r"\b(possible|potential)\s*=\s*\{")

	# 1. Parse all civics
	for filepath in civics_path.glob("*.txt"):
		with filepath.open("r", encoding="utf-8", errors="ignore") as f:
			content = f.read()

		for match in block_start_re.finditer(content):
			civic_name = match.group(1)
			civic_files[civic_name] = filepath

			start_idx = match.end() - 1  # Points to '{'
			end_idx = find_closing_brace(content, start_idx)

			if end_idx == -1:
				continue

			civic_block = content[start_idx + 1 : end_idx]

			for sub_match in sub_block_re.finditer(civic_block):
				# Check if commented
				line_start = civic_block.rfind("\n", 0, sub_match.start()) + 1
				if "#" in civic_block[line_start : sub_match.start()]:
					continue

				sub_start_idx = sub_match.end() - 1
				sub_end_idx = find_closing_brace(civic_block, sub_start_idx)

				if sub_end_idx == -1:
					continue

				condition_block = civic_block[sub_start_idx + 1 : sub_end_idx]

				for neg_match in neg_re.finditer(condition_block):
					# Check if commented
					line_start_neg = (
						condition_block.rfind("\n", 0, neg_match.start()) + 1
					)
					if "#" in condition_block[line_start_neg : neg_match.start()]:
						continue

					neg_start = neg_match.end() - 1
					neg_end = find_closing_brace(condition_block, neg_start)
					if neg_end == -1:
						continue
					neg_content = condition_block[neg_start + 1 : neg_end]

					# Find all has_civic = X
					for hc_match in has_civic_re.finditer(neg_content):
						ls = neg_content.rfind("\n", 0, hc_match.start()) + 1
						if "#" in neg_content[ls : hc_match.start()]:
							continue
						target_civic = hc_match.group(1)
						civic_conflicts[civic_name].add(target_civic)

					# Find value = X
					for v_match in value_re.finditer(neg_content):
						ls = neg_content.rfind("\n", 0, v_match.start()) + 1
						if "#" in neg_content[ls : v_match.start()]:
							continue
						val = v_match.group(1)
						civic_conflicts[civic_name].add(val)

	# 2. Check and group conflicts
	fixes = defaultdict(set)
	for civic, conflicts in civic_conflicts.items():
		if civic.startswith("origin_"):
			continue

		for target in conflicts:
			if target.startswith("origin_"):
				continue

			# Ignore if target is not a known civic (e.g. ethic, authority)
			if target not in civic_files:
				continue

			# Check if target excludes civic
			if civic not in civic_conflicts.get(target, set()):
				logger.warning(
					f"Civic Conflict Out of Sync: '{civic}' excludes '{target}', but '{target}' does not exclude '{civic}'. Queuing fix..."
				)
				fixes[target].add(civic)

	if not fixes:
		logger.info("No civic conflicts found.")
		return

	civics_re = re.compile(r'\bcivics\s*=\s*\{')

	# 3. Apply fixes
	for target, missing_civics in fixes.items():
		if not missing_civics:
			continue

		target_file = civic_files.get(target)
		if not target_file:
			continue

		with target_file.open("r", encoding="utf-8") as f:
			target_content = f.read()

		civic_re = re.compile(rf"^{re.escape(target)} = \{{", re.M)
		m_civic = civic_re.search(target_content)
		if not m_civic:
			logger.error(
				f"Could not find definition for '{target}' in {target_file}"
			)
			continue

		civic_start = m_civic.end() - 1
		civic_end = find_closing_brace(target_content, civic_start)

		civic_body = target_content[civic_start : civic_end + 1]

		# Find 'possible = {'
		m_possible = None
		for m in possible_re.finditer(civic_body):
			line_start = civic_body.rfind('\n', 0, m.start()) + 1
			if '#' not in civic_body[line_start:m.start()]:
				m_possible = m
				break

		insertion_str = ""
		for mc in sorted(missing_civics):
			insertion_str += f"\n\t\t\t\tvalue = {mc}"

		is_single_civic = "T" if len(missing_civics) == 1 else "R"

		if m_possible:
			poss_start_rel = m_possible.end() - 1
			poss_end_rel = find_closing_brace(civic_body, poss_start_rel)

			possible_body = civic_body[poss_start_rel:poss_end_rel+1]

			# Find 'civics = {' inside possible
			m_civics = None
			for m in civics_re.finditer(possible_body):
				line_start = possible_body.rfind('\n', 0, m.start()) + 1
				if '#' not in possible_body[line_start:m.start()]:
					m_civics = m
					break

			if m_civics:
				c_start_rel = m_civics.end() - 1
				c_end_rel = find_closing_brace(possible_body, c_start_rel)

				civics_body_inner = possible_body[c_start_rel+1:c_end_rel]

				# Check for existing NOR/NOT blocks
				found_suitable_nor = False

				for m_neg in neg_re.finditer(civics_body_inner):
					line_start = civics_body_inner.rfind('\n', 0, m_neg.start()) + 1
					if '#' in civics_body_inner[line_start:m_neg.start()]: continue

					nor_start_inner = m_neg.end() - 1
					nor_end_inner = find_closing_brace(civics_body_inner, nor_start_inner)

					nor_content = civics_body_inner[nor_start_inner+1:nor_end_inner]

					# Check if this NOR has a 'text =' property (tooltip) — skip if so
					if "text =" not in nor_content:
						# Extract existing values and merge
						for v_match in value_re.finditer(nor_content):
							missing_civics.add(v_match.group(1))
						for hc_match in has_civic_re.finditer(nor_content):
							missing_civics.add(hc_match.group(1))

						# Re-create insertion string with merged set
						insertion_str = ""
						for mc in sorted(missing_civics):
							insertion_str += f"\n\t\t\t\tvalue = {mc}"

						is_single_civic = "T" if len(missing_civics) == 1 else "R"
						prefix = ""
						suffix = ""

						# Handle inline block (no newlines)
						if '\n' not in civics_body_inner:
							prefix = "\n\t\t\t"
							suffix = "\n\t\t"
							c_start_rel -= 1
							nor_end_inner += 2

						new_block = f"{prefix}NO{is_single_civic} = {{{insertion_str}\n\t\t\t}}{suffix}"

						# Calculate absolute positions
						abs_civics_inner_start = civic_start + poss_start_rel + c_start_rel + 1
						not_block_start_abs = abs_civics_inner_start + m_neg.start()
						not_block_end_abs = abs_civics_inner_start + nor_end_inner + 1

						target_content = target_content[:not_block_start_abs] + new_block + target_content[not_block_end_abs:]

						found_suitable_nor = True
						break

				if not found_suitable_nor:
					# Insert a new NOR block inside existing civics = {}
					insert_pos = civic_start + poss_start_rel + c_end_rel
					block_insert = f"\tNO{is_single_civic} = {{{insertion_str}\n\t\t\t}}\n\t\t"
					target_content = target_content[:insert_pos] + block_insert + target_content[insert_pos:]
			else:
				# Insert civics = { NOR = {} } inside existing possible = {}
				insert_pos = civic_start + poss_end_rel
				block_insert = f"\tcivics = {{\n\t\t\tNO{is_single_civic} = {{{insertion_str}\n\t\t\t}}\n\t\t}}\n\t"
				target_content = target_content[:insert_pos] + block_insert + target_content[insert_pos:]
		else:
			# No possible block at all — insert full possible = { civics = { NOR = {} } }
			insert_pos = civic_end
			block_insert = f"\tpossible = {{\n\t\tcivics = {{\n\t\t\tNO{is_single_civic} = {{{insertion_str}\n\t\t\t}}\n\t\t}}\n\t}}\n"
			target_content = target_content[:insert_pos] + block_insert + target_content[insert_pos:]

		with target_file.open("w", encoding="utf-8") as f:
			f.write(target_content)

		logger.info(f"Fixed: Added {len(missing_civics)} exclusions to '{target}'.")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Check and fix asymmetric civic exclusion conflicts in a Stellaris mod."
	)
	parser.add_argument(
		"-input", "--mod_path",
		type=str,
		required=True,
		help="Path to the mod root directory (must contain common/governments/civics/)"
	)
	args = parser.parse_args()

	mod_path = Path(args.mod_path)
	if not mod_path.is_dir():
		logger.error(f"Mod path does not exist or is not a directory: {mod_path}")
		raise SystemExit(1)

	check_civic_conflicts(mod_path)
