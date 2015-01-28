#!/usr/bin/python
# pcgiwebnews.py - PCGI version of WebNews
# 1997.09.27 Jim.Tittsler@tpc.ml.org
# 1998.07.24 Jim.Tittsler@tpc.ml.org  converted to PCGI
"""Tokyo PC Users Group WebNews reader by Jim Tittsler"""

import sys, os, string, time, cgi, re
from nntplib import NNTP
from urllib import quote
from rfc822 import parseaddr, parsedate

print "Content-type: text/html"
print

NEWS_SERVER = 'news.tpc.ml.org'
#NEWS_SERVER = 'pengu.mww.dyn.ml.org'
default_show_articles = 30   # number of article headers to show on first entry
NewsError = "Error communicating with server"

logo_html = """<HTML><HEAD></HEAD><BODY BGCOLOR="#FFFFFF">
<A HREF="http://www.tpc.ml.org/" TARGET="_top"><IMG SRC="/tpc/images/tpcsml.gif" BORDER="0" ALT="TPC" ALIGN=LEFT></A>
<B><FONT SIZE=+1>Tokyo PC</FONT></B>
<B><FONT SIZE=+1>Users Group</FONT></B>
<BR CLEAR=LEFT>
<B><FONT SIZE="+1">%s</FONT></B><BR>
<EM>%s</EM><P>
<A HREF="mailto:%s@tpc.ml.org">Post new article</A><BR>
<A HREF="http://www.tpc.ml.org/" TARGET="_top">[Home]</A>&nbsp;
<A HREF="http://www.tpc.ml.org/tpc/newsgroups.html" TARGET="_top">[Newsgroups]</A>
</BODY></HTML>"""

ttalk_logo_html = """<HTML><HEAD></HEAD><BODY BGCOLOR="#FFFFFF">
<A HREF="http://www.ttalk.com/" TARGET="_top"><IMG SRC="http://ttalk.soholutions.com/images/tt.gif" BORDER="0" ALT="TTalk" ALIGN=LEFT WIDTH=59 HEIGHT=42></A>
<B><FONT SIZE=+1>TTalk</FONT></B>
<B>Broadcasting</B>
<BR CLEAR=LEFT>
<B><FONT SIZE="+1">%s</FONT></B><BR>
<EM>%s</EM><P>
<A HREF="mailto:%s@ttalk.soholutions.com">Post new article</A><BR>
<A HREF="http://www.ttalk.com/" TARGET="_top">[Home]</A>&nbsp;
<A HREF="http://ttalk.soholutions.com/%s" TARGET="_top">[Newsgroups]</A>
</BODY></HTML>"""

interesting_headers = re.compile(r"""
    ((?P<from>From:)
    |(?P<newsgroups>Newsgroups:\ tpc\.(?P<group>[-0-9a-zA-z\.]+)(?P<othergroups>.*))
    |(?P<subject>Subject:\ (?P<re>re:\s?)?(?P<real_subject>.*))
    |(?P<keep>Date:))""", re.X | re.I)

def logo(G="", D=""):
    """The logo pane for the TPC WebNews reader"""
    # turn the newsgroup name into a mailing list name by changing first . to -
    if string.find(G, "ttalk") >= 0:
        if string.find(G, "staff") >= 0:
	    return ttalk_logo_html % (G, D, string.replace(G, '.', '-'), "staff")
	else:
	    return ttalk_logo_html % (G, D, string.replace(G, '.', '-'), "")
    else:
        return logo_html % (G, D, string.replace(G, '.', '-'))

def show_article_and_kids(index, depth, lines, childof,
			  acc_string, pass_string, RESPONSE):
    art_nr, subject, poster, date, id, references, size, line_cnt = lines[index]
    name, email = parseaddr(poster)
    RESPONSE.write('<LI><A HREF="http:/cgi-bin/webnews/readnews?I=%s%s%s" TARGET="d">%s</A> (%s)  %s, %s' % (quote(id), acc_string, pass_string, cgi.escape(subject), line_cnt, name, time.strftime('%b %d, %H:%M', parsedate(date))))
    if index in childof:
	RESPONSE.write('<UL>')
	for i in range(len(lines)):
	    if childof[i] == index:
		show_article_and_kids(i, depth+1, lines, childof,
				      acc_string, pass_string, RESPONSE)
	RESPONSE.write('</UL>')

def newsgroup(G='', F='', C='', A=None, P=None, RESPONSE=None):
    """The article list for group G in framestyle F"""
    if G=='': return "Missing newsgroup name."
    group = G
    showframes = 1
    show_articles = default_show_articles
    if os.environ.has_key('HTTP_USER_AGENT'):
        browser = os.environ['HTTP_USER_AGENT']
    else:
        browser = "unknown"
    if string.find(browser, "Mozilla/") == 0:
        browser_version = string.atof(browser[8:string.index(browser, ' ')])
        if browser_version >= 2.00:
            showframes = 3
    if F != '':
	try:
	    showframes = string.atoi(F)
	except AttributeError:
	    showframes = 0
    if C != '':
        try:
            show_articles = string.atoi(C)
        except AttributeError:
            show_articles = default_show_articles

    user = A
    acc_string = ''
    if A: acc_string = '&A=' + A
    password = P
    pass_string = ''
    if P: pass_string = '&P=' + P
    
    lines = []
    RESPONSE.headers['expires'] = time.asctime(time.gmtime(time.time() + 60))
    RESPONSE.write( """<HTML><HEAD><TITLE>Tokyo PC Users Group: %s</TITLE></HEAD>""" % group)
    try:
        try:
	    news = NNTP(NEWS_SERVER)
        except:
	    RESPONSE.write( "<BODY><B>Can not connect to server:</B> ", NEWS_SERVER)
	    raise NewsError

        try:
	    resp = news.shortcmd('MODE READER')
        except:
	    RESPONSE.write( "<BODY><B>Can not communicate with server:</B> ", NEWS_SERVER)
	    raise NewsError

        if user:
            resp = news.shortcmd('authinfo user '+user)
            if resp[:3] == '381':
                if not password:
		    RESPONSE.write( "<BODY><B>Can not fetch newsgroup</B>")
		    raise NewsError
                else:
                    resp = news.shortcmd('authinfo pass '+password)
                    if resp[:3] != '281':
		        RESPONSE.write( "<BODY><B>Can not fetch newsgroup</B>")
			raise NewsError

        try:
	    resp, count, first, last, name = news.group(group)
        except:
            RESPONSE.write( "<BODY><B>No such newsgroup:</B> " + group )
            raise NewsError

	description = ""
	try:
	    resp, lines = news.xgtitle(group)
	except:
	    pass
	else:
	    for line in lines:
		name, description = line

	if showframes == 0:
	    RESPONSE.write( '<BODY BGCOLOR="#FFFFFF"><H1>%s</H1>' % group)
	    RESPONSE.write( "<EM>%s</EM><P>" % cgi.escape(description))
	elif showframes == 1 or showframes == 3:
	    if description:	description = "&D="+quote(description)
	    RESPONSE.write( '<FRAMESET ROWS="33%,*">')
	    RESPONSE.write( '  <FRAMESET COLS="220,*">')
	    RESPONSE.write( '    <FRAME SRC="/cgi-bin/webnews/logo?G=%s%s" scrolling="auto">' % (group, description))
	    RESPONSE.write( '    <FRAME SRC="/cgi-bin/webnews/newsgroup?G=%s&F=2%s%s#last" scrolling="yes"> ' % (group, acc_string, pass_string))
	    RESPONSE.write( '  </FRAMESET>')
            if string.find(G, "ttalk") >= 0:
                RESPONSE.write( '  <FRAME SRC="http://ttalk.soholutions.com/welcome.html" scrolling="auto" name="d">')
            else:
                RESPONSE.write( '  <FRAME SRC="/webnews/welcome.html" scrolling="auto" name="d">')
	    RESPONSE.write( '</FRAMESET><BODY BGCOLOR="#FFFFFF">')
	else:
	    RESPONSE.write( '<BODY BGCOLOR="#FFFFFF">')

	if showframes == 3:
	    raise NewsError

        if (show_articles > 0):
            ilast = string.atoi(last)
            ifirst = string.atoi(first)
            if ((ilast - ifirst + 1) > show_articles):
                first = "%d" % (ilast - show_articles + 1)
                RESPONSE.write( '<A HREF="/cgi-bin/webnews/newsgroup?G=%s&F=%d&C=0%s%s"><I>Retrieve earlier article headers</I></A> ' % (group, showframes, acc_string, pass_string))

	try:
	    resp, lines = news.xover(first, last)
	except:
	    RESPONSE.write( "<B>Unable to get article list for:</B> " + group)
	    raise NewsError

	RESPONSE.write( '<UL TYPE="none">')

	# pass 1: build a dictionary of message IDs
	ids = {}
	index = 0
	for line in lines:
	    art_nr, subject, poster, date, id, references, size, line_cnt = line
	    ids[id] = index
	    index = index + 1

	# pass 2: discover child articles
	childof = []
	subs = {}
#	subject_re_less = regex.symcomp("\([Rr]e:\)? *\(<real_subject>.*\)")
        subject_re_less = re.compile(r"(re:)?\s*(?P<real_subject>.*)")
	index = 0
	for line in lines:
	    art_nr, subject, poster, date, id, references, size, line_cnt = line
	    childof.append(-1)
#	    if subject_re_less.match(subject) > 0:
#		subject = subject_re_less.group('real_subject')
	    srl = subject_re_less.match(subject)
	    if srl: subject = srl.group('real_subject')
	    # if there are references, use them (most recent first)
	    if len(references) > 0:
		references.reverse()
		for ref in references:
		    if ids.has_key(ref):
			childof[index] = ids[ref]
			break
	    # if no references (or referee not found), use subject
	    if childof[index] == -1:
		if subs.has_key(subject) :
		    childof[index] = subs[subject]
		else:
		    subs[subject] = index
	    index = index + 1

#   index = 0
#   for line in lines:
#	art_nr, subject, poster, date, id, size, line_cnt, references = line
#	print index,childof[index],subject
#	index = index + 1

        index = 0
	for seq in childof:
	    if seq == -1:
		show_article_and_kids(index, 0, lines, childof,
				      acc_string, pass_string, RESPONSE)
	    index = index + 1

#	art_nr, subject, poster, date, id, size, line_cnt, references = line
#	name, email = parseaddr(poster)
#	print '<LI><A HREF="http:/cgi-bin/readnews.cgi?%s" TARGET="d">%s</A> (%s)  %s, %s' % (quote(id), subject, line_cnt, name, time.strftime('%b %d, %H:%M', parsedate(date)))

	RESPONSE.write('<A NAME="last">&nbsp</A></UL>')

    finally:
        if showframes != 2:
            if string.find(G, "ttalk") >= 0:
                RESPONSE.write( """<P><HR><P>A service of the
                <A HREF="http://www.soholutions.com/">SoHolutions</A>.""")
            else:
                RESPONSE.write( """<P><HR><P>A service of the
                <A HREF="http://www.tpc.ml.org/">Tokyo PC Users Group</A>.""")
        # print "<P><ADDRESS>",os.environ['HTTP_USER_AGENT'],"</ADDRESS>"
        RESPONSE.write( """</BODY></HTML>""")
    
def liven_url(matchobj):
    # if it was a URL-type match, but there is a zero length address part,
    # don't make it live (return the original string)
    if matchobj.group('uri') != None and matchobj.group('uri') == "":
	return matchobj.group(0)
    url = matchobj.group('url')
    text = url
    if matchobj.group('mailadr'):       # if an assumed Email address,
        if url[0] in string.digits:     #   and it starts with a digit
            return matchobj.group(0)    #     don't make it live (msg id?)
        url = "mailto:" + url           #   otherwise add mailto: tag
    if matchobj.group('web'):           # if a web link,
        url = url + '" target="fromtpc' #   put it into a new window
    return matchobj.group('opening') + \
           '<A HREF="'+url+'">'+text+'</A>' + \
           matchobj.group('closing')

def readnews(I="", A=None, P=None, RESPONSE=None):
    """Display article in HTML"""
    article = I
    user = A 
    password = P

    RESPONSE.write("""<HTML><HEAD><TITLE>Tokyo PC Users Group</TITLE></HEAD>
             <BODY BGCOLOR="#FFFFFF">""")

    try:
        news = NNTP(NEWS_SERVER)
    except:
        RESPONSE.write("Can not connect to server: " + NEWS_SERVER)
    resp = news.shortcmd('MODE READER')

    if user:
        resp = news.shortcmd('authinfo user '+user)
        if resp[:3] == '381':
            if not password:
	        RESPONSE.write("<B>Can not fetch article</B><P>")
            else:
                resp = news.shortcmd('authinfo pass '+password)
                if resp[:3] != '281':
	            RESPONSE.write("<B>Can not fetch article</B><P>")

    try:
        resp, nr, id, subs = news.head(article)
    except:
        RESPONSE.write("Article %s not available" % quote(article))

    RESPONSE.write('<TABLE WIDTH="100%" BGCOLOR="#CFCFCF"><TR><TD>')

    # build up the header (so we know Subject: by Newsgroups: output time)
    from_line = ""
    newsgroup_line = ""
    subject_line = ""
    keep_lines = ""
    mail_subject = ""
    for line in subs:
        ihdr = interesting_headers.match(line)
        if ihdr:
            if ihdr.group('from'):
	        name, email = parseaddr(line[6:])
	        if name:
		    from_line = 'From: <A HREF="mailto:%s%s">%s</A> &lt;%s&gt;<BR>' % (
		        email, "%s", name, email)
	        else:
		    from_line = 'From: <A HREF="mailto:%s%s">%s</A><BR>' % (
		        email, "%s", email)
	    elif ihdr.group('newsgroups'):
	        newsgroup_line = 'Newsgroups: <A HREF="mailto:tpc-%s@tpc.ml.org%s">tpc.%s</A>%s<BR>' % (
	        ihdr.group('group'), "%s",
		ihdr.group('group'), ihdr.group('othergroups'))
	    elif ihdr.group('subject'):
	        subject_line = 'Subject: <B>%s</B><BR>' % line[9:]
	        if ihdr.group('re'):
		    mail_subject = "?subject="+line[9:]
	        else:
		    mail_subject = "?subject=Re: "+line[9:]
	    elif ihdr.group('keep'):
	        keep_lines = keep_lines+line+"<BR>"

    if from_line:
        RESPONSE.write(from_line % mail_subject)
    if newsgroup_line:
        RESPONSE.write(newsgroup_line % mail_subject)
    RESPONSE.write(subject_line + keep_lines)

    RESPONSE.write('</TD></TR></TABLE><P>')

    try:
        resp, nr, id, subs = news.body(article)
    except:
        RESPONSE.write("Article %s body not available" % article)

    RESPONSE.write("<CODE>")
    for line in subs:
        RESPONSE.write(re.sub(r'''(?i)(?x)
           (?P<opening>[<(";]?)
           (?P<url>(((?P<web>http:)|(news:)|(mailto:)|(telnet:))(?P<uri>\S*?))
               # a mail address is some non-ws characters followed by @
               # followed by a domain name that has at least one . in it
              |(?P<mailadr>\S+@(\S+\.)+\S+?))
           # either a URL or a mail address will not contain [)">\s]
           # and will not end with punctuation just before the whitespace
           (?P<closing>([)"'>\s]|$|([&.?,:;]\s)+))''',
	    liven_url, line) + "<BR>")
    RESPONSE.write("</CODE>")

    RESPONSE.write("</BODY></HTML>")
    resp = news.quit()

if __name__ == '__main__':
    newsgroup('tpc.unix', '2')
#   readnews('<slrn6np315.g6.Jim.Tittsler@mon.dskk.co.jp>')
