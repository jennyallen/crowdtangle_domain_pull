import requests
from requests import Request
import time
import csv
import json
import os
from datetime import date, timedelta, datetime
import sys
import itertools
import pandas as pd

from optparse import OptionParser
from config import API_KEY

# Usage: query_crowdtangle.py [options]

# Options:
#   -h, --help            show this help message and exit
#   -s START_DATE, --start_date=START_DATE
#                         Start date for querying, in the form \%Y-\%m-\%d
#   -e END_DATE, --end_date=END_DATE
#                         don't print status messages to stdout
#   -q QUERY, --query=QUERY
#                         Query string
#   -d DOMAINS, --domains=DOMAINS
#                         Comma separated list of domains (e.g.
#                         nytimes.com,breitbart.com
#   -f DOMAIN_FILE, --domain_file=DOMAIN_FILE
#                         File with list of domains, one domain per line
#   -o OUTPUT_FILE, --output_file=OUTPUT_FILE
#                         Name of the output file to output results
#   -p, --include_page_info
#                         Include page related info for query
#   -r PAGE_FILE, --page_file=PAGE_FILE
#                         Name of the page file to output page results
#   -c COUNT, --count=COUNT
#                         Number of posts to return
#   -l LIMIT, --limit=LIMIT
#                         Number of URLs per domain to return
#
# 
# Examples
#  python3 query_crowdtangle.py -f iffy_domains.txt -c 100 -l 5 -q "biden AND vote"
#  ==> Returns a TSV of top 100 posts by engagementwith unique URLs from domains in file "iffy_domains.txt" 
# 	that contain both "biden" and "vote". At most 5 URLs for domain for variety. 

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

class APIError(Exception):
	pass

def get_engagement_count(d):
	total = 0
	for x in d.values():
		total += x
	return total

def strip_newlines_and_tabs(s):
	if isinstance(s, str):
		return s.replace("\n", " ").replace("\t", " ")
	return s

def get_page_info(d):
	page_fields = get_pages_header()
	ret_d = {k:strip_newlines_and_tabs(v) for k, v in d.items() if k in page_fields}
	return ret_d

def get_match_domain(link, domains):
	for d in domains:
		if d in link:
			return d
	return False

def get_post_info(d, domains, page_info = True):
	top_level_fields = get_posts_header()
	post_d = {k:strip_newlines_and_tabs(v) for k,v in d.items() if k in top_level_fields}
	expanded_links = []
	if "expandedLinks" in d:
		expanded_links = [x["expanded"] for x in d["expandedLinks"]]
	potential_links = [x for x in [d.get("link", None)] if x] + expanded_links
	matching_links = [(x, get_match_domain(x, domains)) for x in potential_links]
	matching_links = [(x, y) for x, y in matching_links if y]
	if matching_links:
		post_d["link"], post_d["domain"] = matching_links[0]
	page_d = None
	if "account" in d:
		post_d["page_id"] = d["account"]["id"]
		if page_info:
			page_d = get_page_info(d["account"])		
	if "statistics" in d:
		post_d["engagement"] = get_engagement_count(d["statistics"]["actual"])
	return post_d, page_d

def create_search_url(start_date, end_date, search_term, count, platforms = "facebook"):
	url = "https://api.crowdtangle.com/posts/search"
	params = {
		"token" : API_KEY,
		"searchTerm" : search_term,
		"startDate" : start_date,
		"endDate" : end_date,
		"count" : 100,
		"language" : "en",
		"platforms" : platforms,
		"sortBy" : "total_interactions"
	}
	return Request('GET', url, params=params).prepare().url

def query_crowdtangle_posts_api(url, domains):
	res = requests.get(url)
	d = json.loads(res.text)
	if d["status"] == 429:
		raise APIError("Timeout")
	if d["status"] != 200 or "result" not in d:
		print(d)
		return None
	results = d["result"]
	pages_ids = set([])
	posts = []
	pages = []
	if "posts" in results:
		post_infos = [get_post_info(p, domains, page_info = True) for p in results["posts"]]
		posts = [post for post, _ in post_infos]
		for _, page in post_infos:
			if page["id"] not in pages_ids:
				pages_ids.add(page["id"])
				pages.append(page)					
	next_url = None
	if "pagination" in results and "nextPage" in results["pagination"]:
		next_url = results["pagination"]["nextPage"]
	return posts, pages, next_url

def write_posts(posts, filename = None):
	with open(filename, "w+") as f:
		post_writer = csv.DictWriter(f, fieldnames = get_posts_header(), delimiter = "\t")
		post_writer.writeheader()
		for p in posts:
			post_writer.writerow(p)

def write_pages(pages, filename = None):
	with open(filename, "w+") as f:
		page_writer = csv.DictWriter(f, fieldnames = get_pages_header(), delimiter = "\t")
		page_writer.writeheader()
		for p in pages:
			page_writer.writerow(p)

def get_posts_header():
	return ["id", "platformId", "platform", "date", "type", "message", "description", \
	 "link", "domain","postUrl", "score", "subscriberCount", "engagement", "page_id"]

def get_pages_header():
	return ["id", "platformId", "name","handle","subscriberCount","url","platform","platformId",\
		"accountType","pageAdminTopCountry","pageDescription","pageCreatedDate","pageCategory","verified"]

def get_posts_for_date(search_string, domains, start_date, end_date, count, include_page_info = False):
	url = create_search_url(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), search_string, count)
	posts = []
	pages = []
	while url and len(posts) < count * 3:
		print("Querying URL: " + url)
		try:
			new_posts, new_pages, url = query_crowdtangle_posts_api(url, domains)
			posts += new_posts
			if include_page_info:
				pages += new_pages
		except APIError:
			print("Hit rate limit, sleeping for a minute")
			time.sleep(60)
	return posts, pages

def create_query_string(query, domains):
	q = "(" + query + ") AND (" + " OR ".join(domains) + ")"
	return q

def grouper(iterable, n):
    iterable = iter(iterable)
    while True:
        tup = tuple(itertools.islice(iterable, 0, n))
        if tup:
            yield tup
        else:
            break

def get_posts_for_domains_and_date(query, domains, start_date, end_date, count, limit = None, include_page_info = False):
	posts = []
	pages = []
	for domain_group in grouper(domains, 100):
		query_string = create_query_string(query, domain_group)
		new_posts, new_pages = get_posts_for_date(query_string, domain_group, start_date, end_date, count, include_page_info)
		posts += new_posts
		if new_pages:
			pages += new_pages
	if posts:
		post_df = pd.DataFrame(posts)
		post_df = post_df.drop_duplicates(["link"])
		post_df = post_df.loc[post_df["type"] == "link", :]
		post_df = post_df.sort_values(by = "engagement", ascending = False)
		if len(post_df) > count:
			post_df = post_df.head(count)
		posts = post_df.to_dict('records')
	if pages:
		page_df = pd.DataFrame(pages)
		page_df = page_df[page_df["id"].isin(post_df["page_id"].tolist())]
		pages = page_df.to_dict('records')
	return posts, pages

def domain_limited_get_posts_for_domain_date(query, domains, start_date, end_date, count, limit = None, include_page_info = False):
	posts, pages = get_posts_for_domains_and_date(query, domains, start_date, \
												end_date, count, limit, include_page_info = False)
	if limit:
		final_posts = pd.DataFrame()
		final_post_id_list = []
		while domains and count > len(final_posts):
			posts_df = pd.DataFrame(posts)
			print(posts_df)
			posts_slice = posts_df.groupby("domain").head(limit)
			excluded_domains = posts_slice.groupby("domain")["link"].count().sort_values(ascending = False)
			excluded_domains = list(excluded_domains[excluded_domains >= limit].index)
			if excluded_domains:
				domains = [domain for domain in domains if domain not in excluded_domains]
				excluded_slice  = posts_slice.loc[posts_slice["domain"].isin(excluded_domains), :]
				posts_slice = posts_slice.loc[(posts_df["engagement"] >= min(excluded_slice["engagement"])) & \
										~posts_df["id"].isin(final_post_id_list)]
				final_posts = pd.concat([final_posts, posts_slice])
				final_post_id_list = list(final_posts["id"])
			else:
				final_posts = pd.concat([final_posts, posts_slice])
				print("break 1")
				break
			if len(posts) < count:
				print("break 2")
				break
			posts, pages = get_posts_for_domains_and_date(query, domains, start_date, \
								end_date, count, limit, include_page_info = False)
		final_posts = final_posts.sort_values(by = "engagement",ascending = False).head(count)
		if pages:
			page_df = pd.DataFrame(pages)
			pages = page_df[page_df["id"].isin(final_posts["page_id"].tolist())].todict('records')
		return final_posts.to_dict('records'), pages
	return posts, pages




# def get_posts_for_date_batched()

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-s", "--start_date", dest="start_date",
	                  help="Start date for querying, in the form \%Y-\%m-\%d, Defaults to Today - 1 week", default=None)
	parser.add_option("-e", "--end_date",
	                  dest="end_date", default=None,
	                  help="End date for querying, in the form \%Y-\%m-\%d, Defaults to Today")
	parser.add_option("-q", "--query",
	                  dest="query", default="",
	                  help="Query string, boolean style e.g. \"biden AND (vote OR ballot)\"")
	parser.add_option("-d", "--domains",
	                  dest="domains", default=None,
	                  help="Comma separated list of domains (e.g. nytimes.com,breitbart.com")
	parser.add_option("-f", "--domain_file",
	                  dest="domain_file", default=None,
	                  help="File with list of domains, one domain per line")
	parser.add_option("-o", "--output_file",
	                  dest="output_file", default=None,
	                  help="Name of the output file to output results")
	parser.add_option("-p", "--include_page_info",
	                  dest="include_page_info", action="store_true", default=False,
	                  help="Include page related info for query")
	parser.add_option("-r", "--page_file",
	                  dest="page_file", default=False,
	                  help="Name of the page file to output page results")
	parser.add_option("-c", "--count",
	                  dest="count", default=20,
	                  help="Number of posts to return")
	parser.add_option("-l", "--limit",
	                  dest="limit", default=None,
	                  help="Number of URLs per domain to return")
	(options, _) = parser.parse_args()
	(options, _) = parser.parse_args()

	# Default to 1 week 
	if not options.end_date:
		end_date = datetime.today()
	else:
		end_date = datetime.strptime(options.end_date, "%Y-%m-%d")
	if not options.start_date:
		start_date = datetime.today() - timedelta(7)
	else:
		start_date = datetime.strptime(options.start_date, "%Y-%m-%d")

	if end_date < start_date:
		raise Exception("End date before start date")
	domains = []
	if options.domains:
		domains = options.domains.split(",")
	if options.domain_file:
		domains += [x.strip() for x in open(options.domain_file, "r").readlines()]
	count = int(options.count)
	limit = None
	if options.limit:
		limit = int(options.limit)
	posts, pages = domain_limited_get_posts_for_domain_date(options.query, domains, start_date, \
				end_date, count, limit, options.include_page_info)
	
	time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
	post_file = "posts_{}_{}.tsv".format(options.query, time)
	if options.output_file:
		post_file = options.output_file
	write_posts(posts, post_file)
	if options.include_page_info:
		page_file = "pages_{}_{}.tsv".format(options.query, time)
		if options.page_file:
			page_file = options.page_file
		write_pages(pages, page_file)

