# Control PEP style
echo "*********  START PEP style tests  *********"
pylint ../lib/IO_utils/
pylint ../lib/Ner/
pylint ../views/*.py
pylint ../config.py
pylint ../models.py
echo "*********  END PEP style tests    *********"
# Launch unit tests
echo "*********  START Unit tests       *********"
pytest testProject.py
echo "*********  END Unit tests         *********"