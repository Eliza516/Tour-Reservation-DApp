from PIL import Image, ImageDraw, ImageFont
W,H=1700,860
im=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(im)
F=lambda s,b=False: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'%('-Bold' if b else ''),s)
blue=((227,242,253),(21,101,192)); green=((232,245,233),(46,125,50))
bw,bh=420,170
pos={'user':(80,520),'fe':(80,140),'mm':(640,140),'net':(1200,140),'remix':(640,520),'sc':(1200,520)}
txt={'user':('Người dùng','Điều hành / Khách hàng',blue),
'fe':('Frontend','React + Vite + web3.js',blue),
'mm':('MetaMask','window.ethereum · ký giao dịch',blue),
'net':('Sepolia Testnet','nút RPC',green),
'remix':('Remix IDE','biên dịch & deploy',blue),
'sc':('Smart Contract','TourReservation (Solidity)',green)}
for k,(x,y) in pos.items():
    t,s,(fill,line)=txt[k]
    d.rounded_rectangle([x,y,x+bw,y+bh],radius=22,fill=fill,outline=line,width=4)
    for txtl,f,dy in ((t,F(34,True),38),(s,F(24),95)):
        w=d.textlength(txtl,font=f); d.text((x+(bw-w)/2,y+dy),txtl,font=f,fill=(13,33,55))
def c(k,side):
    x,y=pos[k]
    return {'r':(x+bw,y+bh//2),'l':(x,y+bh//2),'t':(x+bw//2,y),'b':(x+bw//2,y+bh)}[side]
def arrow(p,q,both=True,label=None):
    d.line([p,q],fill=(55,71,79),width=5)
    import math
    def head(a,b):
        ang=math.atan2(b[1]-a[1],b[0]-a[0]); L=24
        pts=[b,(b[0]-L*math.cos(ang-0.4),b[1]-L*math.sin(ang-0.4)),(b[0]-L*math.cos(ang+0.4),b[1]-L*math.sin(ang+0.4))]
        d.polygon(pts,fill=(55,71,79))
    head(p,q)
    if both: head(q,p)
    if label:
        mx,my=(p[0]+q[0])/2,(p[1]+q[1])/2; r=26
        d.ellipse([mx-r,my-r,mx+r,my+r],fill='white',outline=(55,71,79),width=3)
        f=F(28,True); w=d.textlength(label,font=f); d.text((mx-w/2,my-17),label,font=f,fill=(13,33,55))
arrow(c('user','t'),c('fe','b'),False,'1')
arrow(c('fe','r'),c('mm','l'),True,'2')
arrow(c('mm','r'),c('net','l'),True,'3')
arrow(c('net','b'),c('sc','t'),True,'4')
arrow(c('remix','r'),c('sc','l'),False,'A')
im.save('arch.png')
