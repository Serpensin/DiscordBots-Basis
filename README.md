# This is a basic setup for a Bot with slash-commands using discord.py with Python >= 3.11.


## Features

- **Feature 1:** Feature 1 description.
- **Feature 2:** Feature 2 description.

## Setup

### Classic Method

1. Ensure Python >=3.11 is installed. Download it [here](https://www.python.org/downloads/).
2. Clone this repository or download the zip file.
3. Open a terminal in the folder where you cloned the repository or extracted the zip file.
4. Run `pip install -r requirements.txt` to install the dependencies.
5. Open the file ".env.template" and complete all variables:
   - `TOKEN`: The token of your bot. Obtain it from the [Discord Developer Portal](https://discord.com/developers/applications).
   - `OWNER_ID`: Your Discord ID.
   - `SUPPORT_SERVER`: The ID of your support server. The bot must be a member of this server to create an invite if someone requires support.
6. Rename the file ".env.template" to ".env".
7. Run `python3 main.py` or `python main.py` to start the bot.

### Docker Method
Ensure Docker is installed. Download it from the [Docker website](https://docs.docker.com/get-docker/).

#### Docker Compose Method

1. Open the `docker-compose.yml` file and update the environment variables as needed (such as `TOKEN`, `OWNER_ID`, and `SUPPORT_SERVER`).
2. In the terminal, run the following command from the cloned folder to start the bot: `docker-compose up -d`.

#### Build the image yourself

1. Clone this repository or download the zip file.
2. Open a terminal in the cloned or extracted zip file.
2. Run `docker build -t basis .` to build the Docker image.

#### Use the pre-built image

1. Open a terminal.
2. Run the bot with the command below:
   - Modify the variables according to your requirements.
   - Set the `TOKEN`, and `OWNER_ID`.

#### Run the bot
You only need to expose the port `-p 5000:5000`, if you want to use an external tool, to test, if the bot is running.
In this case, you need to call the `/health` endpoint.
```bash
docker run -d \
-e SUPPORT_SERVER=ID_OF_SUPPORTSERVER \
-e TOKEN=BOT_TOKEN \
-e OWNER_ID=DISCORD_ID_OF_OWNER \
--name Hercules \
--restart any \
--health-cmd="curl -f http://localhost:5000/health || exit 1" \
--health-interval=30s \
--health-timeout=10s \
--health-retries=3 \
--health-start-period=40s \
-p 5000:5000 \
-v hercules_log:/app/Hercules/Logs \
ghcr.io/serpensin/discordbots-hercules:latest
```