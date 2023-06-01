import difflib
from io import BytesIO
import sys
import time
from typing import List
import os, requests
import re
import pexpect
from PIL import Image
import warnings
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, _base

warnings.filterwarnings("ignore")

args = sys.argv[1:]

if ("-v" in args):
	verbose = True
else:
	verbose = False

if ("-l" in args):
	log = True
else:
	log = False

games = "/mnt/g/Games"
os.chdir(games)
non_steam_games_yml = ["league-of-legends", "overwatch 2"]
non_steam_games = ["AAGL", "LoL", "Overwatch", "HSRL"]

headers = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Methods': 'GET',
	'Access-Control-Allow-Headers': 'Content-Type',
	'Access-Control-Max-Age': '3600',
	'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
	}



def write(p):
	sys.stdout.write("\rProgress: ")
	l = len(p)
	for i in p:
		match i:
			case 0:
				sys.stdout.write("\033[97mN")
				l -= 1
			case 1:
				sys.stdout.write("\033[92mS")
			case 2:
				sys.stdout.write("\033[93mP")
				l -= 1
			case -1:
				sys.stdout.write("\033[91mE")

	
	sys.stdout.write(f"\033[0m {round(l / len(p) * 100, 2)}%")
	sys.stdout.flush()


l : List[os.DirEntry[str]] = []
def fc(e : os.DirEntry):
	with open("/home/rc/.config/lutris/games/" + e.name, "r") as f:
		lines = "".join(f.readlines())
		try:
			name_match = re.search('name\s*: (.+)\\n', lines)
			name = name_match.group(1)
			return name.lower()
		except:
			name = e.name[0:e.name.rfind("-")]
			return name.lower()

def cond(e : os.DirEntry):
	if e.name[0] == ".":
		return False

	for i in non_steam_games_yml:
		if difflib.SequenceMatcher(None, i.lower(), e.name.lower()).ratio() > 0.5 or difflib.SequenceMatcher(None, i.lower(), fc(e)).ratio() > 0.55:
			return False
	
	return True




config_files = sorted([(e.name, fc(e)) for e in os.scandir("/home/rc/.config/lutris/games") if cond(e)], reverse = True)

matches : List[tuple[os.DirEntry[str], tuple[str, str]]] = []


g = sorted(os.scandir(games), key = lambda x : x.name)

for entry in g:
	if entry.is_dir() and (entry.name not in non_steam_games):
		l.append(entry)
		if config_files:
			config_files = sorted(config_files, key = lambda x : difflib.SequenceMatcher(None, x[1].lower(), entry.name.lower()).ratio(), reverse = True)
			matches.append((entry.name, config_files[0]))
			config_files = config_files[1:]

l = sorted(l, key = lambda x : x.name, reverse = True)
config_files = sorted([(e.name, fc(e)) for e in os.scandir("/home/rc/.config/lutris/games") if cond(e)], reverse = True)

assert(len(l) == len(config_files))


def get_name(yml : str) -> str:
	words = yml[0:yml.rfind(".")].split("-")
	words = words[:-1]
	if (words[-1] == "setup" or words[-1] == "standard"):
		words = words[:-1]
	
	return "-".join(words)
	



matches = [(e[0], (e[1][0], get_name(e[1][0]))) for e in matches]


matches = sorted(matches, key = lambda x : x[0])

matches_numbered = []

k = 1
for m in matches:
	matches_numbered.append((k, m))
	k += 1



def mod(e : tuple[int, tuple[str, tuple[str, str]]], lock):
	(k, (i, j)) = e
	with lock:
		progress[k - 1] = 2
		write(progress)
	name = i
	link = f"http://store.steampowered.com/api/storesearch/?term={name}&l=english&cc=US&include_appinfo=true"
	req = requests.get(link, headers)
	game_id = dict(req.json()['items'][0])['id']
	if verbose:
		print("\n------------------------------------------------------------------")
		print(f"({k}) Name : {name}")
		print(f"({k}) ID : {game_id}")
		print(f"({k}) Requesting App Icon Info from SteamCMD")
	child = pexpect.spawn("steamcmd", encoding="utf-8", timeout = None)
	# child.logfile_read = sys.stdout
	child.expect("Loading Steam API...OK")
	child.sendline("login anonymous")
	child.expect("Waiting for user info...OK")
	child.sendline(f"app_info_request {game_id}")
	child.expect("App info request sent.")
	time.sleep(1.5)
	child.sendline(f"app_info_print {game_id}")
	child.expect("\r\n\}")
	child.sendline("quit")
	data = child.before
	child.close()
	if verbose:
		print("------------------------------------------------------------------")
		print(f"({k}) Terminating SteamCMD for {game_id}")
		print(f"({k}) Searching for Client Icon Link")
	icon_match = re.search('"clienticon"(\\t)+"(\w+)"', data)
	try:
		icon_link = icon_match.group(2)
	except:
		if verbose:
			print(f"({k}) Error on {game_id}")

		with lock:
			progress[k - 1] = -1
			write(progress)
		fails.append(e)

		return

	
	game_icon_link = f"http://media.steampowered.com/steamcommunity/public/images/apps/{game_id}/{icon_link}.ico"
	if verbose:
		print(f"({k}) Client Icon Link : {game_icon_link}")
	
	req = requests.get(game_icon_link, headers)
	
	im = Image.open(BytesIO(req.content))
	with open(games + "/" + name + "/client_icon.ico", "w"):
		im.save(games + "/" + name + "/client_icon.ico")
	
	img = Image.open(games + "/" + name + "/client_icon.ico")
	img.save(games + "/" + name + "/client_icon.png")
	img.save(f"/home/rc/.local/share/icons/hicolor/128x128/apps/lutris_{j[1]}.png")

	with lock:
		progress[k - 1] = 1
		write(progress)



def mod_seq(e : tuple[int, tuple[str, tuple[str, str]]]):
	(k, (i, j)) = e
	progress[k - 1] = 2
	write(progress)
	name = i
	link = f"http://store.steampowered.com/api/storesearch/?term={name}&l=english&cc=US&include_appinfo=true"
	req = requests.get(link, headers)
	game_id = dict(req.json()['items'][0])['id']
	if verbose:
		print("\n------------------------------------------------------------------")
		print(f"({k}) Name : {name}")
		print(f"({k}) ID : {game_id}")
		print(f"({k}) Requesting App Icon Info from SteamCMD")
	child = pexpect.spawn("steamcmd", encoding="utf-8", timeout = None)

	if log:
		child.logfile_read = sys.stdout
	
	child.expect("Loading Steam API...OK")
	child.sendline("login anonymous")
	child.expect("Waiting for user info...OK")
	child.sendline(f"app_info_request {game_id}")
	child.expect("App info request sent.")
	time.sleep(1.5)
	child.sendline(f"app_info_print {game_id}")
	child.expect("\r\n\}")
	child.sendline("quit")
	data = child.before
	child.close()
	if verbose:
		print("------------------------------------------------------------------")
		print(f"({k}) Terminating SteamCMD for {game_id}")
		print(f"({k}) Searching for Client Icon Link")
	icon_match = re.search('"clienticon"(\\t)+"(\w+)"', data)
	try:
		icon_link = icon_match.group(2)
	except:
		if verbose:
			print(f"({k}) Error on {game_id}")

		fails.append(e)
		return

	
	game_icon_link = f"http://media.steampowered.com/steamcommunity/public/images/apps/{game_id}/{icon_link}.ico"
	if verbose:
		print(f"({k}) Client Icon Link : {game_icon_link}")
	
	req = requests.get(game_icon_link, headers)
	
	im = Image.open(BytesIO(req.content))
	with open(games + "/" + name + "/client_icon.ico", "w"):
		im.save(games + "/" + name + "/client_icon.ico")
	
	img = Image.open(games + "/" + name + "/client_icon.ico")
	img.save(games + "/" + name + "/client_icon.png")
	img.save(f"/home/rc/.local/share/icons/hicolor/128x128/apps/lutris_{j[1]}.png")
	progress[k - 1] = 1
	write(progress)

start = time.time()

lock = Lock()
global progress
global fails


progress = [0] * len(matches_numbered)
fails = []

write(progress)

with ThreadPoolExecutor(max_workers = len(matches_numbered)) as e:
	fs = [e.submit(mod, m, lock) for m in matches_numbered]
	def result_iter():
		try:
			# reverse to keep finishing order
			fs.reverse()
			while fs:
				# Careful not to keep a reference to the popped future
				yield _base._result_or_cancel(fs.pop())
		finally:
			for future in fs:
				future.cancel()
	result_iter()

sys.stdout.write("\033[0m")
if verbose:
	print("\n" + fails)


for f in fails:
	mod_seq(f)

end = time.time()
print(f"\nExec time : {end - start}")
