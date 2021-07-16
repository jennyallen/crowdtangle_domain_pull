# Instructions
1. Download python3 (see https://www.python.org/downloads/)

2. Install requirements using pip
`pip3 install -r requirements.txt`

3. Create a CrowdTangle API Key (see: https://authority.site/a-beginners-guide-to-the-crowdtangle-api-565/)

4. Add API key to config.py (see `example_config.py` for template)
	`mv example_config.py config.py`
	Add API key

5. Run script using instructions below, e.g. 
	`python3 query_crowdtangle.py -f iffy_domains.txt`

# To use script
Usage: `query_crowdtangle.py` [options]
```
Options:
  -h, --help            show this help message and exit
  -s START_DATE, --start_date=START_DATE
                        Start date for querying, in the form \%Y-\%m-\%d
  -e END_DATE, --end_date=END_DATE
                        don't print status messages to stdout
  -q QUERY, --query=QUERY
                        Query string
  -d DOMAINS, --domains=DOMAINS
                        Comma separated list of domains (e.g.
                        nytimes.com,breitbart.com
  -f DOMAIN_FILE, --domain_file=DOMAIN_FILE
                        File with list of domains, one domain per line
  -o OUTPUT_FILE, --output_file=OUTPUT_FILE
                        Name of the output file to output results
  -p, --include_page_info
                        Include page related info for query
  -r PAGE_FILE, --page_file=PAGE_FILE
                        Name of the page file to output page results
  -c COUNT, --count=COUNT
                        Number of posts to return
  -l LIMIT, --limit=LIMIT
                        Number of URLs per domain to return
```

Example:
`python3 query_crowdtangle.py -f iffy_domains.txt -c 100 -l 5 -q "biden AND vote"`
 ==> Returns a TSV in the "output" folfer of top 100 posts by engagementwith unique URLs from domains in file "iffy_domains.txt" that contain both "biden" and "vote". At most 5 URLs for domain for variety. 