# CMPUT404 Project: Social Distribution
A distributed social network built with Django. Authors on different nodes can follow each other, share entries, like and comment on posts, and exchange content across nodes via a RESTful API.

See [the web page](https://uofa-cmput404.github.io/general/project.html) for a description of the project.

## Live Demo
https://cmput404-project-red-tiandra-994713c1815d.herokuapp.com/<br>
Username: github_user<br>
Password: iamauser123

## Team Members
| Name | GitHub Username |
|---|---|
| Danielle Guloien | dguloien |
| Kaustav Sikder | ksikder |
| Sam Fritz | fritz1 |
| Evelyn Chiew | echiew |
| Ervin Lanada | elanada |
| Tiandra Wallace | tiandra |

## Features
* **Author Profiles**: Public profile pages with bio, picture, and GitHub activity integration
* **Entries**: Create, edit, and delete posts in plain text, CommonMark (Markdown), or image format
* **Visibility Controls**: Public, unlisted, and friends-only entry visibility
* **Stream / Timeline**: Date-sorted feed of entries from followed authors and public content
* **Following & Friends**: Follow requests with approval/denial; mutual follows create friendships
* **Likes & Comments**: Like and comment on any accessible entry or comment
* **Node-to-Node Networking**: Distributed inbox system; nodes push entries, likes, and comments to remote followers
* **Admin Controls**: Node admins can manage authors, approve sign-ups, and connect/disconnect remote nodes

## Documentation
* There is a `docs` folder which includes `api.md`, `endpoints.md`, and `user-stories.md`
* There is a OpenAPI ("Swagger") specification hosted on [Github Pages](https://uofa-cmput404.github.io/f25-project-red/swagger.html)

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### 1. Clone the Repository
```bash
git clone https://github.com/tiaari04/SocialDistribution.git
cd SocialDistribution
```

### 2. Create and Activate a Virtual Environment
```bash
python -m venv .venv

# macOS/Linux:
source .venv/bin/activate

# Windows (PowerShell):
.venv\Scripts\Activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run Database Migrations
```bash
python manage.py migrate
```

### 5. Start the Development Server
```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## Running Tests

Run all tests:
```bash
python manage.py test
```

Run tests for a specific app:
```bash
python manage.py test <app_name>
```

> **Note:** The project uses SQLite for local testing and PostgreSQL (via Heroku) for production.

## Tech Stack

* **Backend**: Django (Python)
* **Database:** PostgreSQL (production) / SQLite (local/testing)
* **Deployment**: Heroku
* **API**: RESTful, with HTTP Basic Auth for node-to-node connections

## License

* This project is licensed under the MIT License.

## Copyright

The authors claiming copyright, if they wish to be known, can list their names here...
