import upnpclient
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib import parse

class DevialetPhantom:
    def __init__(self, u):
        self.name = u.friendly_name
        self.model = u.model_name
        self.instance_id = 0
        self.channel= 'Master'
        self.udn = u.udn
        self.upnp = u

    def getVolume(self):
        return self.upnp.RenderingControl.GetVolume(InstanceID=self.instance_id,Channel=self.channel)['CurrentVolume']

    def setVolume(self, volume):
        self.upnp.RenderingControl.SetVolume(InstanceID=self.instance_id,Channel=self.channel,DesiredVolume=volume)

    def volUp(self):
        volume = self.getVolume()
        self.setVolume(volume+1)

    def volDown(self):
        volume = self.getVolume()
        self.setVolume(volume-1)

class PhantomRemoteHandler(BaseHTTPRequestHandler):
    def __init__(self, phantomList):
        self.list = phantomList

    def __call__(self, *args):
        super().__init__(*args)

    def do_GET(self):
        if self.path.endswith('favicon.ico'):
            return
        parsed = parse.parse_qsl(parse.urlparse(self.path).query,keep_blank_values=True)
        if len(parsed)>=2:
            instruction = parsed[0][0]
            device = next(p for p in self.list if p.udn==parsed[1][1])
            if instruction == 'volUp':
                device.volUp()
            elif instruction == 'volDown':
                device.volDown()
            elif instruction == 'volume':
                device.setVolume(parsed[0][1])
            self.send_response(302)
            self.send_header("Cache-control", "no-cache")
            self.send_header("Location","/")
            self.end_headers()
            return
        html = "<html><head><title>Devialet Phantom UPNP remote</title></head>"
        html += "<h1>Devialet Phantom UPNP Remote</h1>"
        html += "<body>"
        html += "<ul>"
        for p in self.list:
            html+= "<li>%s: %s, Current Volume: %s." % (p.name, p.model, p.getVolume())
            html+= "<br/>"
            html+= "<button type='button' onclick=\"location.href='/?volUp&udn=%s'\">+</button>" % p.udn
            html+= "<button type='button' onclick=\"location.href='/?volDown&udn=%s'\">-</button>" % p.udn
            html+= "<button type='button' onclick=\"location.href='/?volume=50&udn=%s'\">50</button>" % p.udn
            html+= "<button type='button' onclick=\"location.href='/?volume=55&udn=%s'\">55</button>" % p.udn
            html+= "<button type='button' onclick=\"location.href='/?volume=60&udn=%s'\">60</button>" % p.udn
            html+= "</li>"
        html+= "</ul></body></html>"
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

devices = upnpclient.discover()
phantomList = [DevialetPhantom(d) for d in devices if d.manufacturer=='Devialet' and 'Phantom' in d.model_name]

print("Found %s Phantom device%s" % (len(phantomList), "s" if len(phantomList)>2 else ""))

with HTTPServer(("", 8888), PhantomRemoteHandler(phantomList)) as httpd:
    print("Starting http server on port 8888")
    httpd.serve_forever()
