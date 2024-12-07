""" Provide cross-platform retval. """

import os

# noinspection DuplicatedCode
EX_CANTCREAT = getattr(os, "EX_CANTCREAT", 73)
EX_CONFIG = getattr(os, "EX_CONFIG", 78)
EX_DATAERR = getattr(os, "EX_DATAERR", 65)
EX_IOERR = getattr(os, "EX_IOERR", 74)
EX_NOHOST = getattr(os, "EX_NOHOST", 68)
EX_NOINPUT = getattr(os, "EX_NOINPUT", 66)
EX_NOPERM = getattr(os, "EX_NOPERM", 77)
EX_NOUSER = getattr(os, "EX_NOUSER", 67)
# noinspection DuplicatedCode
EX_OK = getattr(os, "EX_OK", 0)
EX_OSERR = getattr(os, "EX_OSERR", 71)
EX_OSFILE = getattr(os, "EX_OSFILE", 72)
EX_PROTOCOL = getattr(os, "EX_PROTOCOL", 76)
EX_SOFTWARE = getattr(os, "EX_SOFTWARE", 70)
EX_TEMPFAIL = getattr(os, "EX_TEMPFAIL", 75)
EX_UNAVAILABLE = getattr(os, "EX_UNAVAILABLE", 69)
EX_USAGE = getattr(os, "EX_USAGE", 64)
