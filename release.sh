( cd fanteam && celery -A fanteam worker -B -l INFO --concurrency 2  --max-memory-per-child=150000 )