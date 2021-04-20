# Vulnspec server

This example provides a live server which can be used to host a survey for
evaluating the project's success.

The general structure is just a lightweight wrapper surrounding the vulnspec
library, with some web frontend powered by flask.

Here are the individual software components used:

- Caddy, used as a reverse proxy server
- Flask application, used to create challenges, as well as collect responses to
  the survey
- Postgres database, used to store survey responses
- Directus server, used to provide a visual interface to the database to easily
  view responses, and later export them as a CSV

## Running

Navigate to the right directory:

    $ cd examples/server/

Download and build all container images:

    $ docker-compose pull && docker-compose build

Create an environment using the provided template (make sure to modify it with
your domain, secrets, keys, etc):

    $ cp .env.example .env

Finally, run the server:

    $ docker-compose up -d

You can follow along with the logs:

    $ docker-compose logs -f

