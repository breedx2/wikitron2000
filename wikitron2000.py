#
# Convert wiki markup drupal entries to html
#

import sys
import argparse
import MySQLdb
import creds
import urllib
import json
import time
import re
import uuid

parser = argparse.ArgumentParser(description='Some drupal Mediawiki -> HTML conversion')
parser.add_argument('--nid', metavar='<nid>', type=int, help='Specify the node id to munge')
parser.add_argument('--update', dest='update', action='store_const', const=True, default=False, help='Go all the way and update the database')

args = parser.parse_args()
node_id = args.nid
print("Limiting selection to just node = %s" %(node_id))
if args.update:
	print("We will update the database.")

def wiki_to_html(wiki):
	input_data = { 'action': 'parse', 'format': 'json', 'text': wiki, 'disablepp': 'true' }
	data = urllib.urlencode(input_data)
	response = urllib.urlopen("http://en.wikipedia.org/w/api.php", data=data)
	if response.getcode() != 200:
		raise Exception("CONVERTOTRON FAIL!! code = %d" %(response.getcode()))
	result = response.read()
	json_result = json.loads(result)
	text = json_result['parse']['text']['*']
	return text

def fetch_body(cur, nid):
	print("Fetching body...")
	cur.execute("SELECT vid,uid,teaser,body from node_revisions where nid = %(nid)s order by vid desc limit 1;", {'nid': nid})
	row = cur.fetchall()[0]
	return (row[0], row[1], row[2], row[3])

def get_html_filter_format_id(cur):
	cur.execute("select format from filter_formats where name = 'Full HTML';")
	row = cur.fetchall()[0]
	return int(row[0])

def get_max_vid_for_nid(cur, nid):
	cur.execute("select max(vid) from node_revisions where nid = %(nid)s", {'nid': nid})
	row = cur.fetchall()[0]
	return int(row[0])

def update_vid_for_nid(cur, nid):
	vid = get_max_vid_for_nid(cur, nid)
	print("New version vid = %s" %(vid))
	cur.execute("update node set vid = %s where nid = %s", (vid, nid))

def update_attachments(cur, nid, old_vid):
	vid = get_max_vid_for_nid(cur, nid)
	cur.execute("""insert into upload (fid, vid, description, list, nid, weight)
				select fid, %(newvid)s, description, list, nid, weight 
				from upload
				where nid = %(nid)s and vid = %(vid)s""", {'newvid': vid, 'nid': nid, 'vid': old_vid})

def update_format(cur, nid, uid, title, teaser, html):
	format_id = get_html_filter_format_id(cur)
	old_vid = get_max_vid_for_nid(cur, nid)
	print("Inserting new node revision...")
	log = "Magic wiki -> html convertotron 2000"
	timestamp = int(time.time())
	cur.execute("""INSERT into node_revisions (nid, uid, title, body, teaser, log, timestamp, format) 
				values 
				(%s, %s, %s, %s, %s, %s, %s, %s);""", 
				(nid, uid, title, html, teaser, log, timestamp, format_id))
	# Not threadsafe, but we assume we're the only ones editing at this time.  Thanks for your patience.
	update_vid_for_nid(cur, nid)
	update_attachments(cur, nid, old_vid)

def magic_pre_mungify(body):
	""" Replace stuff that the wiki parse fails for us, instead substitute some magic that we can 
	later substitute."""
	mappings = dict()
	result = body
	imgwads = re.findall(r'\[http://.*?\]', body)
	for wad in imgwads:
		if re.search(r'\.(JPG|jpg|PNG|png|GIF|gif)\]$', wad) is not None:
			link = wad.strip('[]')
			imghtml = "<img alt='img' src='%s'/>" %(link)
			magic = uuid.uuid4().hex
			mappings[magic] = imghtml
			result = result.replace(wad, magic)
	linkwads = re.findall(r'\[\[\w+\|.+?\]\]', result)
	for wad in linkwads:
		link = wad.strip('[[').strip(']]')
		wiki, text = link.split('|')
		linkhtml = "<a href='/wiki/%s'>%s</a>" %(wiki, text)
		magic = uuid.uuid4().hex
		mappings[magic] = linkhtml
		result = result.replace(wad, magic)
	linkwads = re.findall("\[http://[\w|\.]+ .*?\]", result)
	for wad in linkwads:
		link = wad.strip('[]')
		url, text = link.split(' ', 1)
		linkhtml = "<a href='%s'>%s</a>" %(url, text)
		magic = uuid.uuid4().hex
		mappings[magic] = linkhtml
		result = result.replace(wad, magic)
	return result, mappings

def magic_post_mungify(body, mappings):
	result = body
	for k,v in mappings.iteritems():
		result = result.replace(k, v)
	return result

db = MySQLdb.connect(host="127.0.0.1", port=3306, user=creds.mysql_user, passwd=creds.mysql_pass, db="dorkbotpdx")
cur = db.cursor() 
cur.execute("""SELECT n.nid, n.title, ff.name FROM node n 
			JOIN node_revisions nr ON n.nid = nr.nid AND n.vid = nr.vid 
			JOIN filter_formats ff ON nr.format = ff.format 
			WHERE ff.name = "Mediawiki" 
			ORDER BY n.nid;""")

# Could have just filtered in the query, but oh wells
rows = filter(lambda x: x[0] == int(node_id), cur.fetchall())

# TODO: There should only be one row anyway, why bother looping
for row in rows:
	(nid, title) = (row[0], row[1])
	print("Processing node %s:  %s" %(nid, title))
	(vid, uid, teaser, body) = fetch_body(cur, nid)
	body, mappings = magic_pre_mungify(body)
	print body
	print "------------------------------------------------------------"
	html = wiki_to_html(body)
	html = magic_post_mungify(html, mappings)
	teaser = wiki_to_html(teaser)
	print html
	if args.update:
		update_format(cur, nid, uid, title, teaser, html)
		db.commit()
