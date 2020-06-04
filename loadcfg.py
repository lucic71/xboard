import csv
import sys
from collections import defaultdict


def loadcfg():
    "Fill a dictionary with the fields [server], [port]"
    "[user] and [password]"

    # Default cfg file. Name cannot be changed
    filename = 'xboard.cfg'

    # Configure a dictionary of list with the following
    # fields

    config = defaultdict(list)
    config.fromkeys(['server', 'user', 'password', 'port'])

    try:
        with open(filename) as configFile:

            # Reader for the config file which is saved as csv
            reader = csv.DictReader(configFile)

            for row in reader:
                config['server'].append(row['server'])
                config['user'].append(row['user'])
                config['password'].append(row['password'])
                config['port'].append(row['port'])

    except EnvironmentError:
        print("Error while trying to open xboard.cfg file")
        print("Check if file xboard.cfg exists!")
        print("It should be a csv file with the following fields:")
        print("[server],[user],[password],[port]")

    # Return the filled dictionary
    return config

def main():
    print(loadcfg())

if __name__ == "__main__":
    main()
