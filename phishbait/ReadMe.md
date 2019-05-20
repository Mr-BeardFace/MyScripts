# Phish Bait

Phish Bait

### Prerequisites

Phish Bait works best with an active Hunter.io account and API key. Hunter.io is a free to use email indexing website that has indexed over 200 million emails from tens of thousands of different domains. Phish Bait uses the API key to pull down the domain and/or email format (if not provided). It also uses the results within Hunter.io to start it's email list. Visit [Hunter.io](https://hunter.io/) to set up an account.

I plan on Phish Bait working with Bing API, however this is currently not set up. While this would not be needed for the program to work, it will likely be quicker and have better results than doing normal web requests.

## Python Modules
Uses python's requests and BeautifulSoup modules. 
If you're not familiar with requests, it's more lightweight and usable compared to urllib or urllib2. More about requests can be found [here](https://2.python-requests.org//en/master/).

BeautifulSoup (bs4) is used to pull data objects out of HTML and XML files. Also has a built in parser for pulling out specific objects or can be used with other parsers. More about BeautifulSoup can be found [here](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).

```
pip install bs4
pip install requests
```

### Additional Info

## TODO List

- [ ] Add a progress bar for LinkedIn searches
- [ ] Add Google and Yahoo searches
- [ ] Add aggressive scanner, will scrape domain's website to pull emails and try and figure out format
- [ ] Add Bing API option

## Known Issues

- Doesn't work well with company names that are also common surnames (Like Smith or Allen)
- Every so often Bing will fail to respond with full header, resulting in incorrect first/last names and email
