from argparse import RawTextHelpFormatter
from random import choices
from string import punctuation

import argparse
import json
import os
import re
import sys
import time
import urllib.parse

try:
    from bs4 import BeautifulSoup
except:
    print('Please install BeautifulSoup before running again with "pip install bs4"...')
    sys.exit()
 try:
    import requests
except:
    print('Please install requests before running again with "pip install requests"...')
    sys.exit()

## I like to use random UA Strings with my requests
def UA_pull():
    UA_list = ['Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
            'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9a1) Gecko/20070308 Minefield/3.0a1',
            'Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Thunderbird/45.8.0',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0',
            'Mozilla/5.0 (X11; U; Linux i686; pt-BR; rv:1.9.0.15) Gecko/2009102815 Ubuntu/9.04 (jaunty) Firefox/3.0.15',
            'Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0',
            'Mozilla/5.0 (X11; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0',
            'Mozilla/5.0 (X11; Datanyze; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
            'Mozilla/5.0 (Windows NT 5.1; rv:7.0.1) Gecko/20100101 Firefox/7.0.1',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)']
    ua = choices(UA_list)[0]
    return ua

def hunter(company,domain=None,api=None):
   
    if domain == None:
        print('\nAttempting to find domain via Hunter.io...')
        try:
            ua = UA_pull()
            headers = {'User-Agent': ua}
            response = requests.get("https://hunter.io/v2/domains-suggestion?query={}".format(company[:19]),headers=headers).text
            data = json.loads(response)
            domain = data['data'][0]['domain']
            print('Domain: {}'.format(domain))
            return domain
        except:
            print('Could not find domain for {} in Hunter.io. Restart and provide domain.'.format(company))
            sys.exit()
    else:
        print('\nAttempting to identify format via Hunter.io...')
        
        ## If an API key is not provided, it will ask again
        while api == None or len(api) != 40:
            api = input('Hunter.io API Key> ')
            if api.lower() == 'q' or api.lower() == 'e' or api.lower() == 'quit' or api.lower() == 'exit':
                print('\nIn order to create emails a Hunter.io API key or email format must be given...')
                sys.exit()
        email_list = {}
        offset = 0
        results = 0
        ua = UA_pull()
        headers = {'User-Agent': ua}
       
        response = requests.get("https://hunter.io/v2/domain-search?limit=100&offset={}&domain={}&api_key={}&format=json".format(offset,domain,api),headers=headers).text
        data = json.loads(response)
        
        if 'errors' in response:
            print('\nHunter.io Error: {}'.format(data['errors'][0]['details']))
            sys.exit()
        
        ## If no results were found for that domain, try to find it via Hunter.io
        if data['meta']['results'] == 0:
            print('\nCould not find {} within Hunter.io...'.format(domain))
            time.sleep(3)
            domain = hunter(company)
            proceed = input('\nContinue with discovered domain?\n')
            [sys.exit() if proceed.lower() != 'y' or proceed.lower() !='yes' else True]
        
        ## If Hunter.io already has a lot of emails, ask if user wants to proceed with Phish Bait
        if data['meta']['results'] > 1000:
            print("\n{} emails exist within Hunter.io...".format(data['meta']['results']))
            proceed = input('Continue with Phish Bait anyway?\n')
            [sys.exit() if proceed.lower() != 'y' or proceed.lower() !='yes' else True]
            
        format = data['data']['pattern']
        print('Format: {}'.format(format))
        
        ## Pulling emails that are already stored in Hunter.io
        for record in data['data']['emails']:
            email = record['value']
            firstname = record['first_name']
            lastname = record['last_name']
            try:
                email_list.update({email:firstname+' '+lastname})
            except:
                pass
            results = data['meta']['results']
            offset += 100
       
        ## If there are multiple pages to pull from, iterates through
        while results >= offset:
            ua = UA_pull()
            headers = {'User-Agent': ua}
            response = requests.get("https://hunter.io/v2/domain-search?limit=100&offset={}&domain={}&api_key={}&format=json".format(offset,domain,api),headers=headers).text
            data = json.loads(response)

            format = data['data']['pattern']
            for record in data['data']['emails']:
                email = record['value']
                firstname = record['first_name']
                lastname = record['last_name']
                try:
                    email_list.update({email:firstname+' '+lastname})
                except:
                    pass
        return format,email_list
   
def pull_names(args):
    print("\nBeginning to scrape search engine for valid names...\nThis may take a while...\n")
    
    linkedin_address = dict()
    company = args.company
    limit = args.r
    
    if limit == None:
        limit = 10000
    ua = UA_pull()
    headers = {'User-Agent': ua}

    start = 1

    while start < int(limit):

        content = requests.get('https://www.bing.com/search?q=site%3alinkedin.com%2fin+%22{}%22&qs=n&sp=-1&pq=site%3alinkedin.com%2fin+%22{}%22&sc=1-29&sk=&cvid=7235D443925049369236729AA53EF430&first={}&FORM=PERE'.format(company,company,start),headers=headers).content
       
        soup = BeautifulSoup(content,"html.parser")
        
        ol = soup.findAll('ol')[0]
        for li in ol.findAll('li',attrs={'class':'b_algo'}):
            
            ## Getting rid of bad characters
            text = li.text.replace('\u2013','-')
            text = text.replace('|','-')
            text = text.replace(',','-')
            text = text.replace('[','-')
            
            ## Pulling name
            name = text.split('-')[0][:-1]
            
            ## LinkedIn Address is unique, using it to rid duplicates
            for a in li.findAll('a',href=True):
                address = a['href']
                [linkedin_address.update({address:''}) if address not in linkedin_address.keys() else True]
            
            ## Looking for Users whos name has Company name in it but doesn't work for Company
            if company in name:
                result = '-'.join(text.split('-')[1:])
                if name in result:
                    result = result.replace(name,'')
                if result.count(name) == 0:
                    break
            
            ## If "first name" is a title, like Dr., skip it
            name = name.split(' ')              
            if '.' in name[0]:
                firstname = name[1]
            else:
                firstname = name[0]
            
            ## First name is easy, now it's time to find the appropriate last name
            index = -1
            lastname = None
            
            ## Steps through name list, going backwards, looking for an appropriate last name
            while lastname == None:
                try:
                    lastname = re.search("^[A-Za-z]+$",name[index])
                    index -= 1
                except:
                    lastname = name[-1]
            
            ## If the first name was identified as the last name (ie, no last name was found
            ## just give a blank last name
            if lastname == firstname:
                lastname = ''
                
            try:
                lastname = lastname.string
            except:
                pass
            
            #Update the dictionary
            linkedin_address.update({address:firstname+' '+lastname})
        
        #Increase search results
        start += 12
        if start < int(limit):
            print(" [+] Bing - {} of {} completed".format(start,limit),end="\r")
        else:
            print(" [+] Bing - {} of {} completed".format(limit,limit),end="\r")
        
    name_list = list(filter(None,linkedin_address.values()))

    return name_list

def create_emails(name_list,format,domain,email_list=None):
    test = []
    if email_list == None:
        email_list = dict()
   
    ## Getting rid of brackets in punc, will mess with the indexing
    punc = punctuation.replace('}','')
    punc = punc.replace('{','')
   
    ## Format is defined within brackets, splitting format to be used as separate indexes
    indexing = re.findall('{(.*?)}',format)
    
    ## Seperating first and last names into a new list
    split_name = [name.split(' ') for name in name_list]
   
    for names in split_name:
        
        firstname = names[0]
        lastname = names[1]       
       
        ## If first name is first
        if 'f' in indexing[0]:
            
            ## If it's the first name, use the full name or the length given within index
            ## ie f = 1, fi = 2, fir = 3
            if len(indexing[0]) == 5:
                index1 = firstname
            else:
                index1 = firstname[:len(indexing[0])]
            
            ## Doing same for last name
            if len(indexing[1]) == 4:
                index2 = lastname
            else:
                index2 = lastname[:len(indexing[1])]
        
        ## If lastname is first, do the exact same as above
        else:
            if len(indexing[0]) == 4:
                index1 = lastname
            else:
                index1 = lastname[:len(indexing[0])]
            if len(indexing[1]) == 5:
                index2 = firstname
            else:
                index2 = firstname[:len(indexing[1])]
       
        ## Searching for symbols within the email, like a . or -
        for symbol in re.findall('[{}]'.format(punc),format):
            start = re.search(symbol,format).start()
            if format[:start-1] == '':
                index1 = symbol+index1
            elif format[start+1:] == '':
                index2 = index2+symbol
            else:
                index1 = index1+symbol
               
        email = "{}{}@{}".format(index1,index2,domain)
        
        ## Adding a digit to the end of duplicate emails
        num = 2
        count = 2
        while email.lower() in email_list.keys():
            if num == 2:
                atindex = re.search('@',email).start()
                email = email[:atindex]+str(num)+email[atindex:]         
            else:
                email = email.replace(str(num-1),str(count))
            count+=1
            num +=1
           
        email_list.update({email.lower():firstname+' '+lastname})

    return email_list

if __name__ == "__main__":
    try:
        os.system('cls')
    except:
        os.system('clear')
    
    banner  = "           ___                        ___         ___                      ___     \n"
    banner += "          (   )       .-.            (   )       (   )               .-.  (   )    \n"
    banner += "    .-..   | | .-.   ( __)    .--.    | | .-.     | |.-.     .---.  ( __)  | |_    \n"
    banner += "   /    \  | |/   \  (''')  /  _  \   | |/   \    | /   \   / .-, \ (''') (   __)  \n"
    banner += "  ' .-,  ; |  .-. .   | |  . .' `. ;  |  .-. .    |  .-. | (__) ; |  | |   | |     \n"
    banner += "  | |  . | | |  | |   | |  | '   | |  | |  | |    | |  | |   .'`  |  | |   | | ___ \n"
    banner += "  | |  | | | |  | |   | |  _\_`.(___) | |  | |    | |  | |  / .'| |  | |   | |(   )\n"
    banner += "  | |  | | | |  | |   | | (   ). '.   | |  | |    | |  | | | /  | |  | |   | | | | \n"
    banner += "  | |  ' | | |  | |   | |  | |  `\ |  | |  | |    | '  | | ; |  ; |  | |   | ' | | \n"
    banner += "  | `-'  ' | |  | |   | |  ; '._,' '  | |  | |    ' `-' ;  ' `-'  |  | |   ' `-' ; \n"
    banner += "  | \__.' (___)(___) (___)  '.___.'  (___)(___)    `.__.   `.__.'_. (___)   `.__.  \n"
    banner += "  | |                                                                              \n"
    banner += " (___)                                                                             \n"
    print(banner)
    
    parser = argparse.ArgumentParser(description = 
            " Creates emails for a phishing campaign by pulling names of LinkedIn accounts associated with \n"
            " target organization. Bing/Google is used to find LinkedIn accounts and Hunter.io is used to \n"
            " get the email format for target organization, if one is not provided.\n",
            epilog=" Example: phishbait.py Microsoft -d microsoft.com -f {f}-{last} -r 20000 -o /home/beard/out.csv",
            formatter_class=RawTextHelpFormatter)
    parser.add_argument("company",help="Company name of target")
    parser.add_argument("-d",metavar="domain",help="Domain name of target")
    parser.add_argument("-f",metavar="format",help="Format of email address if known. ie {f}{last}")
    parser.add_argument("-a",metavar="api_key",help="Hunter.io API Key for pulling email format/domain. Can also be used to pull existing list")
    parser.add_argument("-r",metavar="results",help="Number of Bing results to search through (default is 10000)")
    parser.add_argument("-o",metavar="outfile",help="File to output results as csv")    
    
    args = parser.parse_args()
    
    if args.d == None:
        args.d = hunter(args.company)
    
    if args.f == None:
        args.f,email_list = hunter(args.company,args.d,args.a)
        
    name_list = pull_names(args)
    email_list = create_emails(name_list,args.f,args.d,email_list=None)
    
    total = len(email_list)
    print("\nFound {} unique emails for {}\n".format(total,args.company))   
    
    if args.o:
        print("\nWriting results to {}...".format(args.o))
        the_file = open(args.o,'a')
        for item in email_list.items():
            the_file.write('{},{}'.format(item[0],item[1]))
        the_file.close()
   else:
        for item in sorted(email_list.items()):
            print('Email: {:<35}{:>30}'.format(item[0],item[1]))
