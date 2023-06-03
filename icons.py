from typing import List
import warnings
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, _base
from mod import *

warnings.filterwarnings("ignore")

args = sys.argv[1:]

verbose = True if "-v" in args else False
log = True if "-l" in args else False

l : List[os.DirEntry[str]] = []
config_files = sorted([(e.name, get_name(e)) for e in os.scandir("/home/rc/.config/lutris/games") if check(e, non_steam_games_yml)], reverse = True)

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
config_files = sorted([(e.name, get_name(e)) for e in os.scandir("/home/rc/.config/lutris/games") if check(e, non_steam_games_yml)], reverse = True)

matches_numbered = list(zip(range(1, len(matches) + 1), sorted([(e[0], (e[1][0], config_name(e[1][0]))) for e in matches], key = lambda x : x[0])))

start = time.time()

lock = Lock()

write(progress)

with ThreadPoolExecutor(max_workers = len(matches_numbered)) as e:
	fs = [e.submit(mod, m, lock, verbose, log) for m in matches_numbered]
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

sys.stdout.write("\033[0m\n")
if verbose:
	print("Failed: " + fails)

for f in fails:
	mod_seq(f, verbose, log)

end = time.time()
print(f"Exec time : {end - start}")
