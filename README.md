# Wayne

## Installation

Using `virtualenvwrapper`, the process is pretty straightforward:

```shell
git clone git@github.com:anthonygelibert/road_to_billions.git
cd road_to_billions
mkvirtualenv -p python3.12 -a . -r requirements.txt --prompt "Road to Billions" road_to_billions
```

## Usage

**WARNING: `wayne.py` expects that `API_KEY` and `API_SECRET` are available in the process environment.**

The IDEA run configurations load `${PROJECT_DIR}/.env` file before running the commands.
It allows an `.env` file to contain these values (without being tracked by `git`).


