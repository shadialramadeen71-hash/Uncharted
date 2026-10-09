import sys, math, cairo
sys.argv=[sys.argv[0]]
import render as R
from render import *
W2,H2=1280,720
def make(variant,out):
    surf=cairo.ImageSurface(cairo.FORMAT_ARGB32,W2,H2); cr=cairo.Context(surf)
    cr.scale(W2/1920,H2/1080)
    # background photo
    R.kenburns(cr,"00.jpeg" if variant==1 else "01.jpeg",0,1,1.05,1.05,px=(0.6,0.6),dark=0.62)
    # red gradient on right behind face
    g=cairo.RadialGradient(1420,560,50,1420,560,700); g.add_color_stop_rgba(0,0.75,0.08,0.06,0.55); g.add_color_stop_rgba(1,0,0,0,0)
    cr.set_source(g); cr.paint()
    # left dark gradient for text
    g=cairo.LinearGradient(0,0,1100,0); g.add_color_stop_rgba(0,0,0,0,0.92); g.add_color_stop_rgba(1,0,0,0,0)
    cr.set_source(g); cr.rectangle(0,0,1100,1080); cr.fill()
    # mugshot with white border, slight tilt
    s=R.load("mug_up.png"); iw,ih=s.get_width(),s.get_height(); sc=860/ih
    cr.save(); cr.translate(1430,560); cr.rotate(math.radians(3 if variant==1 else -3))
    cr.set_source_rgba(0,0,0,0.6); cr.rectangle(-iw*sc/2+18,-ih*sc/2+22,iw*sc,ih*sc); cr.fill()
    cr.set_source_rgb(1,1,1); cr.rectangle(-iw*sc/2-12,-ih*sc/2-12,iw*sc+24,ih*sc+24); cr.fill()
    cr.translate(-iw*sc/2,-ih*sc/2); cr.scale(sc,sc); cr.set_source_surface(s,0,0); cr.get_source().set_filter(cairo.FILTER_BEST); cr.paint()
    cr.restore()
    def stroke_text(s_,x,y,size,col,outline=8):
        cr.select_font_face("Inter",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD); cr.set_font_size(size)
        cr.move_to(x,y); cr.text_path(s_); cr.set_source_rgb(0,0,0); cr.set_line_width(outline); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve(); cr.set_source_rgb(*col); cr.fill()
    if variant==1:
        # red tag
        cr.set_source_rgb(*R.RED); cr.rectangle(80,90,560,92); cr.fill()
        R.bold(cr,"FORT HOOD 2009",105,155,52,(1,1,1),spacing=2)
        stroke_text("13 KILLED.",80,370,150,(1,1,1),10)
        stroke_text("10 MINUTES.",80,530,150,(1,1,1),10)
        stroke_text("HOW HE WAS",80,700,110,R.AMBER,8)
        stroke_text("STOPPED",80,830,110,R.AMBER,8)
        cr.set_source_rgba(0,0,0,0.75); cr.rectangle(80,890,780,90); cr.fill()
        cr.set_source_rgb(*R.RED); cr.rectangle(80,890,10,90); cr.fill()
        R.bold(cr,"EXECUTION SET: DEC 3, 2026",110,950,44,(1,1,1))
    else:
        stroke_text("THE ARMY",80,260,112,(1,1,1),10)
        stroke_text("PSYCHIATRIST",80,390,112,(1,1,1),10)
        stroke_text("WHO TURNED",80,560,130,R.RED,10)
        stroke_text("ON HIS OWN",80,700,130,R.RED,10)
        cr.set_source_rgba(0,0,0,0.75); cr.rectangle(80,800,800,150); cr.fill()
        cr.set_source_rgb(*R.AMBER); cr.rectangle(80,800,10,150); cr.fill()
        R.bold(cr,"FORT HOOD · NOV 5, 2009",110,860,42,R.AMBER,spacing=2)
        R.bold(cr,"Firing squad set for Dec 3, 2026",110,920,38,(1,1,1))
    surf.write_to_png(out)
make(1,"thumb_v1.png"); make(2,"thumb_v2.png")
