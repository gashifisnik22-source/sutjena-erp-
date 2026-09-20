import os, sqlite3, hashlib
from datetime import datetime
from flask import (Flask, request, redirect, render_template_string, session, flash)

app = Flask(__name__)
app.secret_key = "sutjena_mobile_2026"
DB = "sutjena.db"
conn = sqlite3.connect(DB, check_same_thread=False)
conn.row_factory = sqlite3.Row
c = conn.cursor()

def h(p): return hashlib.sha256(p.encode()).hexdigest()

c.executescript("""
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, user TEXT UNIQUE, pin TEXT, role TEXT);
CREATE TABLE IF NOT EXISTS ngjyra(id INTEGER PRIMARY KEY, emri TEXT);
CREATE TABLE IF NOT EXISTS madhesia(id INTEGER PRIMARY KEY, emri TEXT);
CREATE TABLE IF NOT EXISTS produkt(id INTEGER PRIMARY KEY, modeli TEXT);
CREATE TABLE IF NOT EXISTS variant(id INTEGER PRIMARY KEY, pid INT, ngj INT, madh INT, sku TEXT, blerje REAL, shitje REAL, sasia INT, foto TEXT);
CREATE TABLE IF NOT EXISTS klient(id INTEGER PRIMARY KEY, emri TEXT, tel TEXT, pike INT DEFAULT 0, borxh REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS bon(id INTEGER PRIMARY KEY, klient INT, data TEXT, total REAL, rabat REAL, paguar REAL, borxh REAL, menyra TEXT, nr TEXT);
CREATE TABLE IF NOT EXISTS bon_det(id INTEGER PRIMARY KEY, bon INT, vid INT, sasi INT, cmim REAL);
CREATE TABLE IF NOT EXISTS num(id INTEGER PRIMARY KEY, vit INT, nr INT);
""")

if not c.execute("SELECT id FROM users WHERE user='seller'").fetchone():
    c.execute("INSERT INTO users(user,pin,role) VALUES(?,?,?)", ("seller","1234","seller"))
    c.execute("INSERT INTO users(user,pin,role) VALUES(?,?,?)", ("admin","482913","admin"))
    for n in ["Bardhë","Zi","Rozë","Bebe","Saten","Dantellë"]:
        c.execute("INSERT INTO ngjyra(emri) VALUES(?)", (n,))
    for m in ["XS","S","M","L","XL","XXL","Universal"]:
        c.execute("INSERT INTO madhesia(emri) VALUES(?)", (m,))
    conn.commit()

def auth(f):
    def d(*a,**k):
        return f(*a,**k) if "uid" in session else redirect("/login")
    return d

LOGIN = """
<!doctype html><meta name=viewport content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>body{font-family:system-ui;background:#111;color:#fff;height:100vh;display:flex;flex-direction:column}
.top{padding:26px;color:#e83e8c;font-size:22px;text-align:center}
.box{flex:1;display:flex;flex-direction:column;justify-content:center;padding:24px}
input{font-size:30px;text-align:center;padding:16px;border-radius:16px;letter-spacing:10px;background:#000;color:#0f0;border:1px solid #333}
button{margin-top:20px;background:#e83e8c;color:#fff;border:0;padding:18px;border-radius:16px;font-size:22px}
</style>
<div class=top>🌸 SUTJENA SHOP</div>
<div class=box>
<form method=post><input name=pin type=password inputmode=numeric maxlength=6 placeholder="PIN">
<button>HYR</button></form>
{% with m=get_flashed_messages() %}{% for x in m %}<div style=color:red;text-align:center>{{x}}</div>{% endfor %}{% endwith %}
</div>
"""

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=c.execute("SELECT * FROM users WHERE pin=?", (request.form["pin"],)).fetchone()
        if u:
            session.update(uid=u["id"], emri=u["user"], roli=u["role"])
            return redirect("/x9admin" if u["role"]=="admin" else "/mobile")
        flash("PIN gabim")
    return render_template_string(LOGIN)

@app.route("/logout")
def logout():
    session.clear(); return redirect("/login")

@app.route("/x9admin")
@auth
def x9():
    if session["roli"]!="admin": return redirect("/mobile")
    return render_template_string("""
    <!doctype html><meta name=viewport content=width=device-width>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/bootstrap.min.css" rel="stylesheet">
    <div class=container mt-3><h3>🔐 Admin</h3>
    <a href="/stok" class="btn btn-primary w-100 mb-2">📦 Stok</a>
    <a href="/klientet" class="btn btn-info w-100 mb-2">👥 Klientët</a>
    <a href="/raport" class="btn btn-danger w-100 mb-2">📊 Raport</a>
    <a href="/mobile" class="btn btn-success w-100 mb-2">📱 Shitje</a>
    <a href="/logout" class="btn btn-light w-100">Dil</a></div>
    """)

@app.route("/mobile")
@auth
def mobile():
    q=request.args.get("q","")
    r=c.execute("""SELECT v.id,p.modeli,n.emri,m.emri,v.shitje,v.sasia,v.foto
                   FROM variant v JOIN produkt p ON v.pid=p.id
                   JOIN ngjyra n ON v.ngj=n.id JOIN madhesia m ON v.madh=m.id
                   WHERE v.sasia>0 AND p.modeli LIKE ?""", (f"%{q}%",)).fetchall()
    cards=""
    for x in r:
        cards+=f"""<div class=card p-2><b>{x['modeli']}</b><br>{x['emri']}/{x[2]} | {x['shitje']}€ | stok {x['sasia']}
        <a href="/add/{x['id']}" class="btn btn-sm btn-success float-end">+</a><div class=clearfix></div></div>"""
    return render_template_string("""
    <!doctype html><meta name=viewport content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/bootstrap.min.css" rel="stylesheet">
    <style>.top{position:sticky;top:0;background:#e83e8c;color:#fff;padding:16px;font-size:20px}
    .card{border-radius:16px;box-shadow:0 2px 8px #0001;margin:10px}</style>
    <div class=top>🌸 Sutjena — {{session.emri}}</div>
    <form class=px-2 method=get><input name=q class=form-control placeholder="basic bh zi m"></form>
    <div style="padding-bottom:80px">{{cards|safe}}</div>
    <div class="fixed-bottom d-flex gap-2 p-2 bg-white border-top">
      <a href="/cart" class="btn btn-success flex-fill">🧾 Boni</a>
      <a href="/klientet" class="btn btn-info flex-fill">👥</a>
      <a href="/alarm" class="btn btn-danger flex-fill">⚠️</a>
    </div>
    """, cards=cards)

@app.route("/add/<int:vid>")
@auth
def add(vid):
    cart=session.get("cart",{}); cart[str(vid)]=cart.get(str(vid),0)+1; session["cart"]=cart
    return redirect(request.referrer or "/mobile")

@app.route("/cart")
@auth
def cart():
    cart=session.get("cart",{}); total=0; rows=""
    for vid,sasi in cart.items():
        v=c.execute("SELECT p.modeli,n.emri,m.emri,v.shitje FROM variant v JOIN produkt p ON v.pid=p.id JOIN ngjyra n ON v.ngj=n.id JOIN madhesia m ON v.madh=m.id WHERE v.id=?",(vid,)).fetchone()
        if v:
            total+=sasi*v["shitje"]; rows+=f"<div class='border p-2'>{v['modeli']} {v['emri']}/{v[2]} x{sasi} = {sasi*v['shitje']}€</div>"
    return render_template_string("""
    <!doctype html><meta name=viewport content=width=device-width>
    <div class=container mt-3><h4>🧾 Karroca</h4>{{rows}}
    <p><b>Total: {{total}}€</b></p>
    <form method=post action=/mbyll><button class="btn btn-success w-100">Mbyll bonin</button></form>
    <a href=/mobile class="btn btn-outline-dark w-100 mt-2">Kthehu</a></div>
    """, rows=rows, total=total)

@app.route("/mbyll", methods=["POST"])
@auth
def mbyll():
    cart=session.get("cart",{}); total_pa=0; art=[]
    for vid,sasi in cart.items():
        v=c.execute("SELECT * FROM variant WHERE id=?",(vid,)).fetchone()
        if v and sasi<=v["sasia"]:
            art.append((v,sasi)); total_pa+=sasi*v["shitje"]
            c.execute("UPDATE variant SET sasia=sasia-? WHERE id=?",(sasi,vid))
    vit=datetime.now().year
    nr=c.execute("SELECT nr FROM num WHERE vit=?",(vit,)).fetchone()
    if not nr: c.execute("INSERT INTO num(vit,nr) VALUES(?,1)",(vit,)); nr={"nr":1}
    nr_f=f"VF-{vit}-{nr['nr']:04d}"; c.execute("UPDATE num SET nr=nr+1 WHERE vit=?",(vit,))
    c.execute("INSERT INTO bon(klient,data,total,rabat,paguar,borxh,menyra,nr) VALUES(?,?,?,0,0,?, 'Cash', ?)",
              (None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total_pa, total_pa, nr_f))
    bid=c.lastrowid
    for v,sasi in art:
        c.execute("INSERT INTO bon_det(bon,vid,sasi,cmim) VALUES(?,?,?,?)",(bid,v["id"],sasi,v["shitje"]))
    conn.commit(); session["cart"]={}
    return f"<meta name=viewport content=width=device-width><div class=container mt-4><h3>Bon {nr_f}</h3>Total: {total_pa}€<br><a href=/mobile class='btn btn-success mt-3'>Bon tjetër</a></div>"

@app.route("/klientet")
@auth
def klientet():
    ks=c.execute("SELECT * FROM klient").fetchall()
    return render_template_string("<!doctype html><meta name=viewport content=width=device><div class=container mt-3><h4>Klientët</h4>{% for k in ks %}<div class='border p-2'>{k['emri']} · {k['tel']} · pikë {k['pike']} · borxh {k['borxh']}</div>{% endfor %}<a href=/mobile class='btn btn-outline-dark w-100 mt-3'>Kthehu</a></div>", ks=ks)

@app.route("/alarm")
@auth
def alarm():
    r=c.execute("SELECT p.modeli,n.emri,m.emri,v.sasia FROM variant v JOIN produkt p ON v.pid=p.id JOIN ngjyra n ON v.ngj=n.id JOIN madhesia m ON v.madh=m.id WHERE v.sasia<=3").fetchall()
    return render_template_string("<!doctype html><meta name=viewport content=width=device><div class=container mt-3><h4>⚠️ Stok ulët</h4>{% for x in r %}<div class='alert alert-danger'>{x['modeli']} {x['emri']}/{x[2]} — {x['sasia']}</div>{% else %}<div class='alert alert-success'>OK</div>{% endfor %}<a href=/mobile class='btn btn-outline-dark w-100'>Kthehu</a></div>", r=r)

@app.route("/stok")
@auth
def stok():
    r=c.execute("SELECT p.modeli,n.emri,m.emri,v.shitje,v.sasia FROM variant v JOIN produkt p ON v.pid=p.id JOIN ngjyra n ON v.ngj=n.id JOIN madhesia m ON v.madh=m.id").fetchall()
    return render_template_string("<!doctype html><meta name=viewport content=width=device><div class=container mt-3><h4>📦 Stok</h4>{% for x in r %}<div class='border p-2'>{x['modeli']} {x['emri']}/{x[2]} | {x['shitje']}€ | stok {x['sasia']}</div>{% endfor %}<a href=/x9admin class='btn btn-outline-dark w-100 mt-3'>Panel</a></div>", r=r)

@app.route("/raport")
@auth
def raport():
    tot=c.execute("SELECT COALESCE(SUM(total),0) FROM bon").fetchone()[0]
    return f"<meta name=viewport content=width=device><div class=container mt-4><h3>Raport</h3>Shitje totale: {tot}€<br><a href=/x9admin class='btn btn-outline-dark mt-3'>Kthehu</a></div>"

@app.route("/")
def index():
    return redirect("/login")

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
