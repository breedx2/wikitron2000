#
# Convert wiki markup drupal entries to html
#

import sys
import argparse
import MySQLdb
import creds
import urllib
import json

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
	cur.execute("SELECT vid,uid,body from node_revisions where nid = %(nid)s order by vid desc limit 1;", {'nid': nid})
	row = cur.fetchall()[0]
	return (row[0], row[1], row[2])

def update_format(cur, nid):
	pass


db = MySQLdb.connect(host="127.0.0.1", port=3306, user=creds.mysql_user, passwd=creds.mysql_pass, db="dorkbotpdx")
cur = db.cursor() 
cur.execute("""SELECT n.nid, n.title, ff.name FROM node n 
			JOIN node_revisions nr ON n.nid = nr.nid AND n.vid = nr.vid 
			JOIN filter_formats ff ON nr.format = ff.format 
			WHERE ff.name = "Mediawiki" 
			ORDER BY n.nid;""")

# Could have just filtered in the query, but oh wells
rows = filter(lambda x: x[0] == int(node_id), cur.fetchall())

for row in rows:
	(nid, title) = (row[0], row[1])
	print("Processing node %s:  %s" %(nid, title))
	(vid, uid, body) = fetch_body(cur, nid)
	print body
	print "------------------------------------------------------------"
	print wiki_to_html(body)
