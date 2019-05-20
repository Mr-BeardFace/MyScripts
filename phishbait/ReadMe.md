# PhishBait

PhishBait

### Prerequisites

Uses python's requests and BeautifulSoup modules. 
If you're not familiar with requests, it's more lightweight and usable compared to urllib or urllib2. More about requests can be found here: https://2.python-requests.org//en/master/.
BeautifulSoup (bs4) is used to pull data objects out of HTML and XML files. Also has a built in parser for pulling out specific objects or can be used with other parsers.

```
pip install bs4
pip install requests
```

## Additional Info

## TODO List

- [ ] Add a progress bar for LinkedIn searches
- [ ] Add Google and Yahoo searches
- [ ] Add aggressive scanner, will scrape domain's website to pull emails and try and figure out format
- [ ] Add Bing API option

## Known Issues

- Doesn't work well with company names that are also common surnames (Like Smith or Allen)
- Every so often Bing will fail to respond with full header, resulting in incorrect first/last names and email
