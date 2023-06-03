from io import BytesIO
import requests
import pexpect
from PIL import Image
from progress import *
import time
import re
from clean import *


headers = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Methods': 'GET',
	'Access-Control-Allow-Headers': 'Content-Type',
	'Access-Control-Max-Age': '3600',
	'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
	}

global progress
global fails

games = "/mnt/g/Games"
non_steam_games_yml = ["league-of-legends", "overwatch 2"]
non_steam_games = ["AAGL", "LoL", "Overwatch", "HSRL"]

progress = [0] * (len(list(os.scandir(games))) - len(non_steam_games))
fails = []


def mod(e : tuple[int, tuple[str, tuple[str, str]]], lock, verbose, log):
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



def mod_seq(e : tuple[int, tuple[str, tuple[str, str]]], verbose, log):
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
	except:
		if verbose:
			print(f"({k}) Error on {game_id}")

		fails.append(e)
		return

	
	
