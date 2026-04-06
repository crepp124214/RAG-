import os
os.environ['DATABASE_URL'] = 'sqlite:///./data/phase29-acceptance.db'
from worker.main import main
main()
