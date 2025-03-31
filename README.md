# ALARM: Auth Log Analysis & Real-time Monitoring

## Using the Demo Site

There is live version of ALARM running at:

[alarm.sgt.me.uk](https://alarm.sgt.me.uk)


> 🔐 **Authentication**
>
> To access the site please login using your `@strath.ac.uk` email address.
> 
>A one-time access code will be emailed to you.


## Prerequisites

This project uses Docker Compose to start the server and run all necessary services.

- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose](https://docs.docker.com/compose/install/) installed

## Getting Started

1. Clone this repository:

```bash
git clone [https://gitlab.cis.strath.ac.uk/cmb21139/alarm.git](https://github.com/CallumSergeant/alarm.git)
cd alarm
```

2. Update configuration files:

- In `nginx/nginx.conf`, change the domain from `alarm.sgt.me.uk` to the domain you intent to host ALARM on. Change the IP address to the IP of your server.
- In `app/alarm/settings.py`, change `CSRF_TRUSTED_ORIGINS` to your domain, change `ALLOWED_HOSTS` to include your domain and server IP address. Change the `SECRET_KEY` of the application. Disable DEBUG when not developing.
- In `app/dashboard/views.py` change `generate_install_command` to your domain.

3. Start the server using Docker Compose:

```bash
docker-compose up
```

To run it in the background (detached mode):

```bash
docker-compose up -d
```

## Stopping the Server

To stop the server, press `Ctrl+C` if running in the foreground, or run:

```bash
docker-compose down
```
