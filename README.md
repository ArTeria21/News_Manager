Command for creating docker container with postgresql:
```bash
docker run --name news_pg_base -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=admin -e POSTGRES_DB=base -p 5124:5432 -d postgres
```