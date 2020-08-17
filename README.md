# mangadex-download
serach for and downloads manga chapters from [mangadex.org](mangadex.org) as pdf and (optionally) sends the files to the an email.

---

## Installation

### Clone
- Clonse this repo first using
```shell
git clonse https://github.com/howard-yen/mangadex-download
```

### Setup
- All the required python packages are listed in the requirements.txt
- It is highly recommended to use a virtual environment
- You can install them with:
```shell
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```
- You should also put your USER_AGENT in the `.env`, not required but recommended.
- `.env` should look something like this
```
USER_AGENT=Mozilla/5.0 (X11; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0
```
- You should be logged onto mangadex on your browser in order to search for title, this program uses cookies from your browser (If you don't want to search for title and just want to download, that'd be possible but I just haven't implemented the prompts)
- if you want to email the chapter, the only supported emails currently is gmail, and you have to Turn [Allow less secure apps to ON](https://myaccount.google.com/lesssecureapps). Be aware that this makes it easier for others to gain access to your account. Future plans include using the more secure Gmail API instead of this work around.
---

## Usage
- Simply run 
```
python download.py
```
- follow the prompt and you'll be able to search for a manga and select the chapters to download, they will be in a new folder with the title as the name. 
- if you want to email the chapters, you can just follow the prompts as well. 

---

## Future Plans
- Add support for selecting languages. This is mostly implemented, but need to find out the lang-id for different lanuages. 
- Add sleep timers between requests
- Add support for sending emails to multiple addresses (using bcc)
