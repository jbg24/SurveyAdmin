#Create list of random login codes in format [az]### or ###[az]
#Use: generate_login.py -n [number of codes] [-l if you want the letter portion at the end]

import sys
import random
import getopt
import string
import csv
def id_generator(size=4, letter_last=False):
    '''
    Generate random combination of 1 letter and 3 digits
    '''
	
	#remove ambiguous o and l characters
    replace_chars = ["o", "l"]
    chars = string.ascii_lowercase
	
    for char in replace_chars:
        chars = chars.replace(char, "")
		
	#remove 0
    nums =  string.digits.replace("0","")

	#create code: e.g. b452
    rand_nums = ''.join(random.choice(nums) for _ in range(size-1))

    if letter_last:
        return rand_nums + random.choice(chars) 
    else:
        return random.choice(chars) + rand_nums
	

def main(args):
    '''
    Parses command-line arguments and creates panel from first argument
	args: (iterable )profiled school file and, if included, argument to indicate that classes with fewer than 5 should not be removed
    '''
    letter_last = False
    count = 100

    try:
        opts, args = getopt.getopt(args, "n:l")
    except getopt.GetoptError:
        print("Use: generate_login.py -n [number of codes] [-l if you want the letter portion at the end]")    
    for opt, optarg in opts:
        if opt in ("-n"):
            count = int(optarg)
        elif opt in ("-l"):
            letter_last = True
        
    #random and unique login codes - use a set
    random_list = set()
		
	#create the same number of login codes as the number of enrolled or what we set above as enrollment
    while (len(random_list) < count):
        random_list.add(id_generator(4,letter_last))
	
    with open('codelist{}.csv'.format(count), 'wb') as f:
        writer = csv.writer(f)
        for val in random_list:
            writer.writerow([val])
		
		
# Pass all params after program name to our main
if __name__ == "__main__":
    main(sys.argv[1:])		

