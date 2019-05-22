# Phish Bait

Phish Bait is meant to be used for engagements where a Phishing Campaign falls within the ROE however no emails are provided. It will use common search engines to identify LinkedIn accounts asociated with a target company. The names of the LinkedIn accounts will be used to create an email list for the campaign. 

Honestly, I decided to create this script because a friend showed me [EmailGen](https://github.com/navisecdelta/EmailGen) created by @pry0cc, which I liked a lot, but thought there could be something added to make it more intuitive. Plus, I'm still new to scripting so I'm using it as practice. So if the people at NaviSec Delta see this, I hope they don't mind.

### Prerequisites

Phish Bait works best with an active Hunter.io account and API key. Hunter.io is a free to use email indexing website that has indexed over 200 million emails from tens of thousands of different domains. Phish Bait uses the API key to pull down the domain and/or email format (if not provided). It also uses the results within Hunter.io to start it's email list. Visit [Hunter.io](https://hunter.io/) to set up an account.

I plan on Phish Bait working with Bing API, however this is currently not set up. While this would not be needed for the program to work, it will likely be quicker and have better results than doing normal web requests.

#### Python Modules
Uses python's requests and BeautifulSoup modules. 
If you're not familiar with requests, it's more lightweight and usable compared to urllib or urllib2. More about requests can be found [here](https://2.python-requests.org//en/master/).

BeautifulSoup (bs4) is used to pull data objects out of HTML and XML files. Also has a built in parser for pulling out specific objects or can be used with other parsers. More about BeautifulSoup can be found [here](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).

```
pip install bs4
pip install requests
```

### Additional Info

#### TODO List

- [X] Add error handler if domain wasn't found in Hunter.io.
- [X] Add a progress bar for LinkedIn searches
- [X] Add Google and Yahoo searches
- [ ] Finish this ReadMe
- [ ] Add aggressive scanner, will scrape domain's website to pull emails and try and figure out format
- [ ] Add Bing and Google API option

#### Known Issues

- Doesn't work well with company names that are also common surnames (Like Smith or Allen)
- Every so often Bing will fail to respond with full header, resulting in incorrect first/last names and email
