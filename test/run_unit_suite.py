import os

os.system("python3 -m 'nose' --exclude=regression --with-coverage --cover-package=autosubmit --cover-inclusive --cover-xml --cover-xml-file=test/coverage.xml test")

