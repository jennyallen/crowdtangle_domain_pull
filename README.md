# Instructions
1. [Clone](https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository-from-github/cloning-a-repository) this github repository

2. Download python3 (see https://www.python.org/downloads/)

3. Install requirements using pip

`pip3 install -r requirements.txt`

4. Create a CrowdTangle API Key (see: https://authority.site/a-beginners-guide-to-the-crowdtangle-api-565/)

5. Add API key to config.py, e.g. by:

	`mv example_config.py config.py`

	Adding API key to `config.py`

6. Run script using instructions below, e.g. 
	`python3 query_crowdtangle.py -f iffy_domains.txt`

# To use script
Usage: `query_crowdtangle.py [options]`
```
Options:
  -h, --help            show this help message and exit
  -s START_DATE, --start_date=START_DATE
                        Optional. Start date for querying, in the form \%Y-\%m-\%d,
                        Defaults to Today - 1 week
  -e END_DATE, --end_date=END_DATE
                        Optional. End date for querying, in the form \%Y-\%m-\%d,
                        Defaults to Today
  -q QUERY, --query=QUERY
                        Optional. Query string, boolean style e.g. "biden AND (vote OR
                        ballot)". Defaults to the empty string. 
  -d DOMAINS, --domains=DOMAINS
                        Optional. Comma separated list of domains (e.g.
                        nytimes.com,breitbart.com. Need either -d or -f flag to run.  
  -f DOMAIN_FILE, --domain_file=DOMAIN_FILE
                        Optional. File with list of domains, one domain per line. Need either -f or -d to run. 
  -o OUTPUT_FILE, --output_file=OUTPUT_FILE
                        Optional. Name of the output file to output results (defaults to
                        output/posts_<query>_<datetime>.tsv)
  -p, --include_page_info
                        Optional. Include page related info for query. Defaults to False. 
  -r PAGE_FILE, --page_file=PAGE_FILE
                        Optional. Name of the page file to output page results. Defaults
                        to output/pages_<query>_<datetime>.tsv. 
  -c COUNT, --count=COUNT
                        Optional. Number of posts to return. Defaults to 20. 
  -l LIMIT, --limit=LIMIT
                        Optional. Number of URLs per domain to return (for variety). Defaults to no limit.  
```

Example:

`python3 query_crowdtangle.py -f iffy_domains.txt -c 100 -l 5 -q "biden AND vote"`

 ==> Returns a TSV in the "output" folfer of top 100 posts by engagementwith unique URLs from domains in file "iffy_domains.txt" that contain both "biden" and "vote". At most 5 URLs for domain for variety. 