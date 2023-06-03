import os
import re
import difflib

def get_name(e : os.DirEntry) -> str:
	with open("/home/rc/.config/lutris/games/" + e.name, "r") as f:
		lines = "".join(f.readlines())
		try:
			name_match = re.search('name\s*: (.+)\\n', lines)
			name = name_match.group(1)
			return name.lower()
		except:
			name : str = e.name[0:e.name.rfind("-")]
			return name.lower()

def check(e : os.DirEntry, games):
	if e.name[0] == ".":
		return False

	for i in games:
		if difflib.SequenceMatcher(None, i.lower(), e.name.lower()).ratio() > 0.5 or difflib.SequenceMatcher(None, i.lower(), get_name(e)).ratio() > 0.55:
			return False
	
	return True

def config_name(yml : str) -> str:
	words = yml[0:yml.rfind(".")].split("-")
	words = words[:-1]
	if (words[-1] == "setup" or words[-1] == "standard"):
		words = words[:-1]
	
	return "-".join(words)