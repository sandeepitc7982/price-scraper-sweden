# Developer Guidelines

## Usage

You can make use of the [poetry](https://python-poetry.org/) environment and run the scraper using its CLI interface.
If you don't want to interact with poetry and set up a python environment, you can make use of the Docker support and Makefile
to run the script on any machine that can run docker containers.

### Environment variables

- `LOGURU_LEVEL`: Control the verbosity of the output logs (`TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`).
- `PM_GCP_LOGGING`: Set to `true` to push the logs to GCP.
- `PM_FILE_LOGGING`: Set to `true` to enable file based logging. When enabled, generate logs in logs directory by default with filename `price-monitor-{date}.log`.

### Pre-requisites

- Pycharm community version or any other IDE is installed on the system, if not installed
- Install git on the system and ensure if installation is completed by verifying the version - [Link](https://github.com/git-guides/install-git)
  - Go to target folder location and clone the git-hub repository branch - [Link](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
- Open pycharm or the preferred IDE and go to the folder where you cloned the repository and set up the virtual environment
  - Complete the virtual environment setup and activate the virtual environment - [Link](https://docs.python.org/3/library/venv.html)
- Go to `Makefile` and install the packages as mentioned in "bootstrap_local"
- A local `config.json` file to be passed as a CLI argument.
  - Steps to Create a local 'config.json'
    1. Create a new folder named `local` inside `config` folder
    2. Create a file `config.json` in `local` folder and copy the script from `production` folder `config.json`
    3. Modify the `config.json` in local folder - change the `environment` key value from "Production" to "local"
    4. The config file setup for local is ready
- Chrome installation is required on the machine where the price scraper will be executed.
  - Steps to setup chrome in Linux system.
    - Download the Google Chrome binary using this command line ` wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb`
    - Install the binary
      - For yum package manager : `yum install -y ./google-chrome-stable_current_amd64.deb`
      - For apt package manager : `apt install -y ./google-chrome-stable_current_amd64.deb`