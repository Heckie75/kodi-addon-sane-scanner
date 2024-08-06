import sys
import urllib.parse

from resources.lib import directory, executer, printer, scanner

if __name__ == '__main__':

    if sys.argv[1] == "find_scanner":
        scanner.find_scanner()

    elif sys.argv[1] == "find_printer":
        printer.find_printer()

    else:
        path = urllib.parse.urlparse(sys.argv[0]).path
        url_params = urllib.parse.parse_qs(sys.argv[2][1:])

        if "exec" in url_params:
            executer.execute(path, url_params)

        else:
            directory.browse(path=path, handle=int(sys.argv[1]))
