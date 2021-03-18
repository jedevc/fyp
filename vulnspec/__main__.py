import sys

from . import vulnspec

if __name__ == "__main__":
    result = vulnspec.main()
    sys.exit(result)
