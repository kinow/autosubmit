import os

os.system("nosetests --with-coverage --cover-erase --cover-package=autosubmit --cover-html test/unit")
# os.system("nosetests --exclude=regression --with-coverage --cover-package=autosubmit --cover-inclusive --cover-xml --cover-xml-file=test/coverage.xml test")
