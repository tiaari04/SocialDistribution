[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/etkNZkSE)
CMPUT404-project-socialdistribution
===================================

CMPUT404-project-socialdistribution

See [the web page](https://uofa-cmput404.github.io/general/project.html) for a description of the project.

Make a distributed social network!

## Documentation
* There is a `docs` folder which includes `api.md`, `endpoints.md`, and `user-stories.md`
* There is a OpenAPI ("Swagger") specification hosted on [Github Pages](https://uofa-cmput404.github.io/f25-project-red/swagger.html)

## License

* This project is licensed under the MIT License.

## Copyright

The authors claiming copyright, if they wish to be known, can list their names here...

## Team Members

1. Danielle Guloien, dguloien
2. Kaustav Sikder, ksikder
3. Sam Fritz, fritz1
4. Evelyn Chiew, echiew
5. Ervin Lanada, elanada
6. Tiandra Wallace, tiandra

       

## Heroku

https://cmput404-project-red-9e98d52591b5.herokuapp.com/


## Testing

### 1. Create and Activate a Virtual Environment

```bash
python -m venv .venv

# On macOS/Linux:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate
```

### 2. Install Project Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run Database Migrations

```bash
python manage.py migrate
```

### 4. Run Tests

Run all tests:
```bash
python manage.py test
```

Run tests for a specific app:
```bash
python manage.py test <app_name>
```