import os
#--with-coverage --cover-package=autosubmit --cover-inclusive --cover-xml --cover-xml-file=test/coverage.xml
os.system("python3 -m nose --verbosity=3 unit")

