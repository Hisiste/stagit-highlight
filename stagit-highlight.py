#!/usr/bin/env python3

import fileinput
import html
import os
import os.path
import re
import sys

import pygments
import pygments.lexers
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

SUCCESS = 0
FAILURE = 1


def highlight_file(pathname: str) -> int:
	"""
	Syntax highlight the given file. If no lexer can be found for the given file, i.e. the file
	is a plaintext file or the language isn't supported, then this function simply returns
	SUCCESS and does nothing. If the file can be highlighted then first the file is opened and
	it's contents saved. If this opening of the file throws an error than the function returns
	FAILURE and the program moves on to the next file. No CSS is provided with the highlighted
	HTML, you must write that yourself.
	"""
	try:
		lexer = pygments.lexers.get_lexer_for_filename(pathname.removesuffix(".html"))
	except ClassNotFound:
		return SUCCESS

	try:
		with open(pathname, "r", encoding="utf-8") as f:
			data = f.readlines()
	except IOError as e:
		print("%s: Failed to open file '%s': %s", (sys.argv[0], pathname, e), file=sys.stderr)
		return FAILURE

	code = ""
	in_content = False
	for line in fileinput.FileInput(pathname, inplace=True):
		# Collect all of the raw code into a string buffer
		if (
			m := re.match(r'<a href="#l[0-9]+" class="line" id="l[0-9]+"> *[0-9]+</a> (.*)', line)
		) :
			code += m.group(1) + "\n"

		# Link to the syntax stylesheet
		if re.match(r'<link rel="stylesheet" type="text/css" href="(../)*style.css"/>$', line):
			print(line + line.replace("style.css", "syntax.css"), end="")
		# Set the in_content flag if we entered the content div, this is where the code is
		elif line == '<div id="content">\n':
			in_content = True
			print(line, end="")
		# If we aren't in it then don't modify the current line
		elif not in_content:
			print(line, end="")
		# We need to add a second closing div tag
		elif line == "</div>\n":
			print(line + "</div>", end="")
		# Add a div with class "highlight"
		elif re.match(r'<p> .* <a href="(../)*raw/.*">raw</a></p><hr/><pre id=blob">$', line):
			print(line.replace("<hr/>", '<hr/><div class="highlight">'), end="")
		else:
			print(line, end="")

	# Syntax highlight the code and save it as an array of lines
	codelines = (
		pygments.highlight(html.unescape(code), lexer, HtmlFormatter())
		.removeprefix('<div class="highlight"><pre>')
		.split("\n")
	)

	# Write the syntax highlighted code to the file
	j = 0
	for line in fileinput.FileInput(pathname, inplace=True):
		if (m := re.match(r'(<a href="#l[0-9]+" class="line" id="l[0-9]+"> *[0-9]+</a> )', line)) :
			print(m.group(1) + codelines[j])
			j += 1
		else:
			print(line, end="")

	return SUCCESS


def traverse_repository(pathname: str) -> int:
	"""
	Recursively traverse the directory `pathname`. If all goes well, then SUCCESS is returned.
	If something goes wrong at any point of the traversal (which includes the actual syntax
	highlighting) then FAILURE is returned.
	"""
	retval = SUCCESS

	for i in os.listdir(pathname):
		newpath = os.path.join(pathname, i)
		if os.path.isdir(newpath):
			retval = traverse_repository(newpath)
		# My fork of stagit(1) has a .html file for each directory so that you can navigate
		# directories in a non-retarded way
		elif not os.path.isdir(newpath.removesuffix(".html")):
			retval = highlight_file(newpath)

	return retval


def main() -> int:
	if len(sys.argv) != 2:
		print("Usage: %s filedir" % sys.argv[0], file=sys.stderr)
		return FAILURE

	# Make sure that the passed directory is infact a real directory that we can interact with
	if not os.path.isdir(sys.argv[1]):
		print("%s: Pathname '%s' is not a directory" % (sys.argv[0], sys.argv[1]), file=sys.stderr)
		return FAILURE

	return traverse_repository(sys.argv[1])


if __name__ == "__main__":
	sys.exit(main())
