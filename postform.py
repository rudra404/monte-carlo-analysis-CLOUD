#!/usr/bin/python3

import os
import html
import cgi
import cgitb
cgitb.enable()

print("Content-type: text/html\r\n\r\n")
print("<font size=+1>Environment</font><br /><br />")
for param in os.environ.keys():
  print("<b>", param, "</b>: ", os.environ[param], " <br /> ")

form = cgi.FieldStorage()
message = form.getvalue("message", "(no message)")

print("<p>Previous message: ", html.escape(message), "</p>")
print("""

<p>Simple Form

<form method="post" action="postform.py">
  <p>message: <input type="text" name="message"/></p>
</form>


</body>
</html>
""")
