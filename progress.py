import sys

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