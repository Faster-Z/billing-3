from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json, os, hashlib, time, re, hmac as hmac_lib, requests as req_lib

app = Flask(__name__)
app.secret_key = 'strengthcloud_ultra_v3_secret_key_2024'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # set True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7  # 7 days
DATA_FILE = 'data.json'

DEFAULT_DATA = {
    "plans": [
        {"id":1,"name":"Dirt","ram":"2GB","cpu":"80%","storage":"8GB NVMe","price_monthly":59,"price_yearly":590,"price_lifetime":1499,"color":"#ff6b35","popular":False,"sold_out":False,"emoji":"🪨","description":"Perfect for small servers with a few friends."},
        {"id":2,"name":"Wooden","ram":"4GB","cpu":"100%","storage":"10GB NVMe","price_monthly":99,"price_yearly":990,"price_lifetime":2499,"color":"#c8864e","popular":False,"sold_out":False,"emoji":"🌲","description":"Great starter plan for growing communities."},
        {"id":3,"name":"Stone","ram":"6GB","cpu":"150%","storage":"15GB NVMe","price_monthly":199,"price_yearly":1990,"price_lifetime":4999,"color":"#94a3b8","popular":False,"sold_out":False,"emoji":"🪨","description":"Ideal for modded servers up to 20 players."},
        {"id":4,"name":"Iron","ram":"8GB","cpu":"200%","storage":"20GB NVMe","price_monthly":299,"price_yearly":2990,"price_lifetime":7499,"color":"#7c9eb2","popular":True,"sold_out":False,"emoji":"⚔️","description":"Our most popular plan for SMP servers."},
        {"id":5,"name":"Emerald","ram":"12GB","cpu":"250%","storage":"25GB NVMe","price_monthly":399,"price_yearly":3990,"price_lifetime":9999,"color":"#10b981","popular":False,"sold_out":False,"emoji":"💎","description":"Serious performance for large communities."},
        {"id":6,"name":"Diamond","ram":"16GB","cpu":"300%","storage":"30GB NVMe","price_monthly":499,"price_yearly":4990,"price_lifetime":12499,"color":"#38bdf8","popular":False,"sold_out":False,"emoji":"💠","description":"High-end power for busy multiplayer worlds."},
        {"id":7,"name":"Netherite","ram":"20GB","cpu":"300%","storage":"40GB NVMe","price_monthly":599,"price_yearly":5990,"price_lifetime":14999,"color":"#8b5cf6","popular":False,"sold_out":False,"emoji":"🔮","description":"Ultimate performance for large networks."},
        {"id":8,"name":"Titanium","ram":"32GB","cpu":"400%","storage":"50GB NVMe","price_monthly":999,"price_yearly":9990,"price_lifetime":24999,"color":"#f59e0b","popular":False,"sold_out":False,"emoji":"👑","description":"Unmatched power for massive server networks."},
    ],
    "vps_plans": [
        {"id":1,"name":"VPS Starter","cpu_cores":1,"ram":"1GB","storage":"20GB NVMe","bandwidth":"1TB","price_monthly":149,"price_yearly":1490,"color":"#06b6d4","popular":False,"sold_out":False,"emoji":"🌱","description":"Entry-level VPS for dev environments and small apps.","os":["Ubuntu 25.10 (Latest)","Ubuntu 24.04 LTS","Ubuntu 22.04 LTS","Debian 13","Debian 12","CentOS 9"]},
        {"id":2,"name":"VPS Basic","cpu_cores":2,"ram":"2GB","storage":"40GB NVMe","bandwidth":"2TB","price_monthly":299,"price_yearly":2990,"color":"#3b82f6","popular":False,"sold_out":False,"emoji":"💻","description":"Reliable VPS for small business websites and apps.","os":["Ubuntu 25.10 (Latest)","Ubuntu 24.04 LTS","Ubuntu 22.04 LTS","Debian 13","Debian 12","Windows Server 2025","Windows Server 2022"]},
        {"id":3,"name":"VPS Pro","cpu_cores":4,"ram":"4GB","storage":"80GB NVMe","bandwidth":"4TB","price_monthly":599,"price_yearly":5990,"color":"#8b5cf6","popular":True,"sold_out":False,"emoji":"🚀","description":"Professional VPS for production workloads.","os":["Ubuntu 25.10 (Latest)","Ubuntu 24.04 LTS","Ubuntu 22.04 LTS","Debian 13","Debian 12","CentOS 9","Windows Server 2025","Windows Server 2022"]},
        {"id":4,"name":"VPS Business","cpu_cores":6,"ram":"8GB","storage":"160GB NVMe","bandwidth":"8TB","price_monthly":999,"price_yearly":9990,"color":"#10b981","popular":False,"sold_out":False,"emoji":"🏢","description":"Business-grade for high-traffic applications.","os":["Ubuntu 25.10 (Latest)","Ubuntu 24.04 LTS","Ubuntu 22.04 LTS","Debian 13","Debian 12","Windows Server 2025","Windows Server 2022"]},
        {"id":5,"name":"VPS Enterprise","cpu_cores":8,"ram":"16GB","storage":"320GB NVMe","bandwidth":"Unlimited","price_monthly":1999,"price_yearly":19990,"color":"#f59e0b","popular":False,"sold_out":False,"emoji":"⚡","description":"Enterprise power for demanding workloads.","os":["Ubuntu 25.10 (Latest)","Ubuntu 24.04 LTS","Ubuntu 22.04 LTS","Debian 13","Debian 12","CentOS 9","Windows Server 2025","Windows Server 2022"]},
        {"id":6,"name":"VPS Titan","cpu_cores":16,"ram":"32GB","storage":"640GB NVMe","bandwidth":"Unlimited","price_monthly":3999,"price_yearly":39990,"color":"#ef4444","popular":False,"sold_out":False,"emoji":"👑","description":"Maximum performance dedicated VPS resources.","os":["Ubuntu 25.10 (Latest)","Ubuntu 24.04 LTS","Ubuntu 22.04 LTS","Debian 13","Debian 12","Windows Server 2025","Windows Server 2022"]},
    ],
    "stats":{"servers":"500+","uptime":"99.9%","support":"24/7","gamers":"10,000+"},
    "site":{"name":"StrengthCloud","discord":"https://discord.gg/strengthcloud","tagline":"Premium Minecraft Hosting"},
    "admin":{"username":"admin","password": hashlib.sha256(b"admin123").hexdigest()},
    "features":[
        {"icon":"⚡","title":"Instant Setup","desc":"Live within seconds of purchase."},
        {"icon":"💾","title":"NVMe SSD","desc":"Ultra-fast zero-lag storage."},
        {"icon":"🛡️","title":"DDoS Protection","desc":"Enterprise-grade, always free."},
        {"icon":"🎧","title":"24/7 Support","desc":"Always here to help you."},
        {"icon":"🔧","title":"1-Click Modpacks","desc":"Install any modpack instantly."},
        {"icon":"🗄️","title":"Unlimited DBs","desc":"No MySQL database limits."},
        {"icon":"🖥️","title":"Control Panel","desc":"Manage from one dashboard."},
        {"icon":"📡","title":"99.9% Uptime","desc":"Guaranteed infrastructure."},
    ],
    "faqs":[
        {"q":"How quickly is my server set up?","a":"Instantly after payment — Pterodactyl auto-provisions your server in seconds."},
        {"q":"What Minecraft versions do you support?","a":"We support all versions from 1.8 to the latest, including Bedrock."},
        {"q":"Is DDoS protection really free?","a":"Yes! All plans include enterprise-grade DDoS protection at no extra cost."},
        {"q":"What payment methods do you accept?","a":"Razorpay (UPI, Cards, NetBanking, Wallets), UPI QR, and Bank Transfer."},
        {"q":"Can I upgrade my plan later?","a":"Absolutely! You can upgrade anytime from your client panel."},
        {"q":"Do you offer refunds?","a":"We offer a 3-day money-back guarantee on all plans."},
    ],
    "testimonials":[
        {"name":"Alex_MC","role":"Server Owner","stars":5,"text":"StrengthCloud is incredible! Lag-free with 50+ players."},
        {"name":"CraftKing","role":"Modpack Dev","stars":5,"text":"Server went live instantly after payment. Amazing!"},
        {"name":"PixelStudio","role":"Gaming Community","stars":5,"text":"Switched from another host — night and day difference."},
        {"name":"BlockMaster99","role":"SMP Owner","stars":4,"text":"Great uptime and the control panel is super easy."},
        {"name":"RedstoneWiz","role":"Technical Player","stars":5,"text":"DDoS protection saved our server multiple times."},
        {"name":"BuilderPro","role":"Creative Server","stars":5,"text":"Affordable + premium performance. Real deal."},
    ],
    "users":[], "orders":[],
    "announcements":[{"id":1,"title":"Welcome!","message":"Enjoy 20% off with code LAUNCH20","type":"info","active":True}],
    "coupons":[
        {"code":"LAUNCH20","discount":20,"type":"percent","active":True},
        {"code":"FLAT100","discount":100,"type":"flat","active":True},
    ],
    "sale":{"active":False,"percent":30,"label":"MEGA SALE","subtitle":"Limited time offer!","expires":""},
    "payment":{
        "razorpay_key_id":"",
        "razorpay_key_secret":"",
        "upi_id":"",
        "upi_name":"",
        "upi_qr":"",
        "bank_name":"",
        "bank_account":"",
        "bank_ifsc":"",
        "bank_holder":"",
        "methods_enabled":["razorpay","upi","bank"],
        "currency":"INR"
    },
    "pterodactyl":{
        "enabled":False,
        "panel_url":"",
        "api_key":"",
        "location_id":1,
        "nest_id":1,
        "egg_id":1,
        "docker_image":"ghcr.io/pterodactyl/yolks:java_17",
        "startup":"java -Xms128M -XX:MaxRAMPercentage=95.0 -jar {{SERVER_JARFILE}}",
        "default_variables":{"SERVER_JARFILE":"server.jar","MINECRAFT_VERSION":"latest"}
    },
    "cpanel":{
        "enabled":False,
        "whm_url":"",
        "api_token":"",
        "default_package":"default",
        "nameserver1":"ns1.strengthcloud.xyz",
        "nameserver2":"ns2.strengthcloud.xyz",
        "ip_address":"",
        "auto_provision":True
    },
    "discord":{
        "bot_token":"",
        "owner_id":"",
        "webhook_url":"",
        "bot_secret":"",
        "site_url":"http://localhost:5000",
        "notify_orders":True,
        "notify_provisions":True
    }
}

# ── DATA ──────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f: d = json.load(f)
        for k in DEFAULT_DATA:
            if k not in d: d[k] = DEFAULT_DATA[k]
        for p in d.get('vps_plans',[]):
            for key,dv in [("emoji","🖥️"),("description",""),("os",[]),("sold_out",False),("popular",False)]:
                if key not in p: p[key]=dv
        for p in d.get('plans',[]):
            for key,dv in [("emoji","⛏️"),("description",""),("sold_out",False),("popular",False)]:
                if key not in p: p[key]=dv
        for k in DEFAULT_DATA['payment']:
            d.setdefault('payment',{}); d['payment'].setdefault(k, DEFAULT_DATA['payment'][k])
        for k in DEFAULT_DATA['pterodactyl']:
            d.setdefault('pterodactyl',{}); d['pterodactyl'].setdefault(k, DEFAULT_DATA['pterodactyl'][k])
        for k in DEFAULT_DATA['cpanel']:
            d.setdefault('cpanel',{}); d['cpanel'].setdefault(k, DEFAULT_DATA['cpanel'][k])
        for k in DEFAULT_DATA['discord']:
            d.setdefault('discord',{}); d['discord'].setdefault(k, DEFAULT_DATA['discord'][k])
        return d
    save_data(DEFAULT_DATA); return DEFAULT_DATA

def save_data(data):
    with open(DATA_FILE,'w') as f: json.dump(data,f,indent=2)

def discord_notify(order):
    """Send order notification via Discord webhook (instant, no bot needed)."""
    try:
        data = load_data()
        cfg = data.get('discord', {})
        webhook_url = cfg.get('webhook_url', '').strip()
        if not webhook_url or not cfg.get('notify_orders', True):
            return
        items = order.get('items', [])
        item_lines = []
        for it in items:
            plan = it.get('plan', {})
            pname = plan.get('name', it.get('name','Item')) if isinstance(plan, dict) else it.get('name','Item')
            ptype = '🖥️ VPS' if it.get('type')=='vps' else '⛏️ MC'
            billing = it.get('billing','monthly').capitalize()
            egg = it.get('egg_type',''); mc_v = it.get('mc_version',''); vos = it.get('vps_os','')
            detail = f' `{egg} {mc_v}`' if egg else (f' `{vos}`' if vos else '')
            item_lines.append(f'{ptype} **{pname}** ({billing}){detail}')
        status = order.get('status','pending')
        method = order.get('payment_method','?').upper()
        color_map = {'paid':0x10b981,'active':0x8b5cf6,'pending_verification':0xf59e0b,'pending':0x6b7280}
        color = color_map.get(status, 0x6b7280)
        utr = order.get('utr_number',''); pid = order.get('payment_id','')
        ref_line = f"\n🔖 UTR: `{utr}`" if utr else (f"\n💳 Pay ID: `{pid}`" if pid else '')
        embed = {
            "title": f"🛒 New Order #{order.get('id','')}",
            "description": f"**{status.replace('_',' ').upper()}** via **{method}**",
            "color": color,
            "fields": [
                {"name":"👤 Customer","value":f"`{order.get('username','?')}`","inline":True},
                {"name":"💰 Amount","value":f"**₹{order.get('final',order.get('total',0))}**","inline":True},
                {"name":"📅 Date","value":order.get('date',''),"inline":True},
                {"name":"📦 Items","value":'\n'.join(item_lines) or '—',"inline":False},
            ],
            "footer":{"text":"StrengthCloud Order Alert"},
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }
        if utr: embed['fields'].append({"name":"🔖 UTR / Ref","value":f"`{utr}`","inline":True})
        if pid: embed['fields'].append({"name":"💳 Payment ID","value":f"`{pid}`","inline":True})
        req_lib.post(webhook_url, json={"embeds":[embed],"username":"StrengthCloud","avatar_url":"https://cdn.discordapp.com/icons/1416472559104299210/6299f0c15609e8680791202bfa89df74.webp"}, timeout=8)
    except Exception as e:
        print(f'Discord notify error: {e}')

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()
def get_cart(): return session.get('cart',[])
def cart_count(): return len(get_cart())

# ── PTERODACTYL ──────────────────────────────────────────────────
def parse_ram_mb(s):
    s=s.strip().upper()
    if 'GB' in s: return int(float(s.replace('GB','').strip())*1024)
    if 'MB' in s: return int(s.replace('MB','').strip())
    return 1024

def parse_disk_mb(s):
    m=re.search(r'(\d+)',s)
    if m:
        v=int(m.group(1))
        return v*1024*1024 if 'TB' in s.upper() else v*1024
    return 10240

def ptero_headers(cfg):
    return {'Authorization':f'Bearer {cfg["api_key"]}','Content-Type':'application/json','Accept':'Application/vnd.pterodactyl.v1+json'}

def ptero_create_user(cfg, email, username, password):
    url = cfg['panel_url'].rstrip('/')+'/api/application/users'
    try:
        r = req_lib.post(url, json={'email':email,'username':username,'first_name':username,'last_name':'User','password':password}, headers=ptero_headers(cfg), timeout=15)
        if r.status_code in [200,201]: return r.json()['attributes']['id'], None
        if r.status_code==422:
            s = req_lib.get(f"{url}?filter[email]={email}", headers=ptero_headers(cfg), timeout=10)
            if s.status_code==200:
                users=s.json().get('data',[])
                if users: return users[0]['attributes']['id'], None
        return None, r.text
    except Exception as e: return None, str(e)

def ptero_get_egg_variables(cfg, nest_id, egg_id):
    """Fetch required variables for an egg from Pterodactyl"""
    url = cfg['panel_url'].rstrip('/')+f'/api/application/nests/{nest_id}/eggs/{egg_id}?include=variables'
    try:
        r = req_lib.get(url, headers=ptero_headers(cfg), timeout=10)
        if r.status_code == 200:
            variables = r.json().get('attributes',{}).get('relationships',{}).get('variables',{}).get('data',[])
            env = {}
            for v in variables:
                attr = v.get('attributes',{})
                env_var = attr.get('env_variable','')
                default = attr.get('default_value','')
                if env_var:
                    env[env_var] = default
            return env
    except:
        pass
    return {}

def ptero_create_server(cfg, plan, order, ptero_uid):
    url = cfg['panel_url'].rstrip('/')+'/api/application/servers'
    name = f"SC-{order['username']}-{plan['name'].replace(' ','-')}-{order['id']%10000}"
    cpu_val = int(str(plan.get('cpu','100%')).replace('%','')) if plan.get('cpu') else 100

    # Start with egg's own default variables
    nest_id = cfg.get('nest_id', 1)
    egg_id = cfg.get('egg_id', 1)
    env = ptero_get_egg_variables(cfg, nest_id, egg_id)

    # Override with admin-configured defaults
    admin_vars = cfg.get('default_variables', {})
    env.update(admin_vars)

    # Always ensure these common ones are set
    env.setdefault('SERVER_JARFILE', 'server.jar')
    env.setdefault('MINECRAFT_VERSION', 'latest')
    env.setdefault('BUILD_TYPE', 'recommended')
    env.setdefault('FORGE_VERSION', '')
    env.setdefault('MC_VERSION', 'latest')

    payload = {
        'name': name, 'user': ptero_uid, 'egg': egg_id,
        'docker_image': cfg.get('docker_image', 'ghcr.io/pterodactyl/yolks:java_17'),
        'startup': cfg.get('startup', 'java -Xms128M -XX:MaxRAMPercentage=95.0 -jar {{SERVER_JARFILE}}'),
        'environment': env,
        'limits': {
            'memory': parse_ram_mb(plan.get('ram','1GB')),
            'swap': 0,
            'disk': parse_disk_mb(plan.get('storage','10GB')),
            'io': 500,
            'cpu': cpu_val
        },
        'feature_limits': {'databases':5,'backups':3,'allocations':1},
        'deploy': {'locations':[cfg.get('location_id',1)],'dedicated_ip':False,'port_range':[]}
    }
    try:
        r = req_lib.post(url, json=payload, headers=ptero_headers(cfg), timeout=20)
        if r.status_code in [200,201]:
            a=r.json()['attributes']
            return a.get('id'), a.get('uuid'), a.get('identifier'), None
        return None, None, None, r.text
    except Exception as e: return None, None, None, str(e)

def auto_provision(order):
    data=load_data(); cfg=data.get('pterodactyl',{})
    if not cfg.get('enabled') or not cfg.get('panel_url') or not cfg.get('api_key'):
        return {'provisioned':False,'reason':'Pterodactyl not configured'}

    # Strip trailing slash from panel URL
    cfg['panel_url'] = cfg['panel_url'].rstrip('/')

    uid = order.get('user_id')
    username = order.get('username','')

    # Find user by id first, then fallback to username
    user = next((u for u in data['users'] if u['id']==uid), None)
    if not user and username:
        user = next((u for u in data['users'] if u['username']==username), None)

    # If still not found, create a synthetic user from order data
    if not user:
        user = {
            'id': uid,
            'username': username or f'user{uid}',
            'email': f'{username or "user"}@strengthcloud.local',
            'fname': username or 'User',
            'lname': ''
        }

    # Generate deterministic password
    ptero_pw = f"SC@{hash_pw(str(uid) + cfg['api_key'])[:12]}"

    ptero_uid, err = ptero_create_user(cfg, user['email'], user['username'], ptero_pw)
    if not ptero_uid:
        return {'provisioned':False,'reason':f'Pterodactyl user creation failed: {err}'}

    mc_plans = {p['id']:p for p in data['plans']}
    vps_plans = {p['id']:p for p in data['vps_plans']}
    results = []

    for item in order.get('items',[]):
        plan = (vps_plans if item.get('type')=='vps' else mc_plans).get(item.get('plan_id'))
        if not plan:
            plan = item.get('plan') or {'name': item.get('name','Server'), 'ram':'1GB','cpu':'100%','storage':'10GB NVMe'}
        if not plan: continue

        # Use item-level config if present (set during cart add)
        item_cfg = dict(cfg)
        if item.get('docker_image'):
            item_cfg['docker_image'] = item['docker_image']
        if item.get('mc_version'):
            item_cfg['default_variables'] = dict(cfg.get('default_variables',{}))
            item_cfg['default_variables']['MINECRAFT_VERSION'] = item['mc_version']
            item_cfg['default_variables']['MC_VERSION'] = item['mc_version']

        sid, suuid, sidentifier, err = ptero_create_server(item_cfg, plan, order, ptero_uid)
        results.append({'plan': plan.get('name','Server'), 'server_id':sid, 'identifier':sidentifier, 'error':err, 'success':sid is not None, 'egg_type':item.get('egg_type','vanilla'), 'mc_version':item.get('mc_version','latest')})

    # Save provision result back to order
    for o in data['orders']:
        if o['id'] == order['id']:
            o['ptero_provisioned'] = True
            o['ptero_user_id'] = ptero_uid
            o['ptero_servers'] = results
            o['ptero_password'] = ptero_pw
            o['status'] = 'active' if any(r['success'] for r in results) else o.get('status','pending')
            break
    save_data(data)

    return {
        'provisioned': True,
        'panel_url': cfg['panel_url'],
        'username': user['username'],
        'password': ptero_pw,
        'servers': results
    }

# ── CPANEL / WHM AUTO-PROVISION ───────────────────────────────────
def cpanel_headers(cfg):
    return {'Authorization': f'whm root:{cfg["api_token"]}', 'Content-Type': 'application/json'}

def cpanel_api(cfg, func, params={}):
    """Call WHM API2"""
    base = cfg['whm_url'].rstrip('/')
    url = f"{base}:2087/json-api/{func}?api.version=1"
    try:
        r = req_lib.get(url, params=params, headers=cpanel_headers(cfg), verify=False, timeout=15)
        if r.status_code == 200:
            return r.json(), None
        return None, f"WHM {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return None, str(e)

def cpanel_create_account(cfg, username, domain, password, plan=None):
    """Create a cPanel account via WHM"""
    base = cfg['whm_url'].rstrip('/')
    params = {
        'username': username[:16],  # cPanel max 16 chars
        'domain': domain,
        'password': password,
        'plan': plan or cfg.get('default_package', 'default'),
        'contactemail': '',
        'ip': 'n',
        'cgi': 1,
        'frontpage': 0,
        'hasshell': 0,
    }
    try:
        r = req_lib.post(f"{base}:2087/json-api/createacct?api.version=1",
            params=params, headers=cpanel_headers(cfg), verify=False, timeout=20)
        if r.status_code == 200:
            result = r.json()
            if result.get('metadata',{}).get('result') == 1 or result.get('data',{}).get('success',0):
                return True, None
            return False, result.get('metadata',{}).get('reason', str(result)[:200])
        return False, f"WHM {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)

def cpanel_suspend(cfg, username, suspend=True, reason=""):
    """Suspend or unsuspend a cPanel account"""
    func = 'suspendacct' if suspend else 'unsuspendacct'
    params = {'user': username}
    if suspend and reason: params['reason'] = reason
    return cpanel_api(cfg, func, params)

def cpanel_change_password(cfg, username, password):
    """Change cPanel account password"""
    base = cfg['whm_url'].rstrip('/')
    params = {'user': username, 'password': password, 'db_pass_update': 1}
    try:
        r = req_lib.post(f"{base}:2087/json-api/passwd?api.version=1",
            params=params, headers=cpanel_headers(cfg), verify=False, timeout=15)
        return r.status_code == 200, r.text[:200] if r.status_code != 200 else None
    except Exception as e:
        return False, str(e)

def cpanel_get_accounts(cfg):
    """List all cPanel accounts"""
    result, err = cpanel_api(cfg, 'listaccts', {'searchtype': 'user', 'search': '', 'want': 'user,domain,ip,diskused,disklimit,suspended'})
    if result:
        return result.get('data', {}).get('acct', []), None
    return [], err

def generate_cpanel_details(order, cfg):
    """Generate username, domain, password for a VPS order"""
    uname = order.get('username', 'user')
    # cPanel username: max 16 chars, alphanumeric only
    cp_user = re.sub(r'[^a-z0-9]', '', uname.lower())[:12] + str(order['id'] % 1000)
    cp_user = cp_user[:16]
    domain = f"{cp_user}.strengthcloud.xyz"
    password = f"SC#{hashlib.sha256((cp_user + str(order['id'])).encode()).hexdigest()[:10]}@1"
    return cp_user, domain, password

def auto_provision_vps(order):
    """Auto-provision VPS order via cPanel WHM"""
    data = load_data()
    cfg = data.get('cpanel', {})
    if not cfg.get('enabled') or not cfg.get('whm_url') or not cfg.get('api_token'):
        return {'provisioned': False, 'reason': 'cPanel WHM not configured'}

    cp_user, domain, password = generate_cpanel_details(order, cfg)

    # Use customer-chosen password if provided
    vps_item = next((i for i in order.get('items',[]) if i.get('type')=='vps'), None)
    if vps_item and vps_item.get('vps_password'):
        password = vps_item['vps_password']
    selected_os = (vps_item.get('vps_os') or 'Ubuntu 22.04') if vps_item else 'Ubuntu 22.04'

    # Find VPS plan for package selection
    vps_plans = {p['id']: p for p in data.get('vps_plans', [])}
    plan = None
    for item in order.get('items', []):
        if item.get('type') == 'vps':
            plan = vps_plans.get(item.get('plan_id'))
            break

    package = cfg.get('default_package', 'default')
    if plan and plan.get('cpanel_package'):
        package = plan['cpanel_package']

    ok, err = cpanel_create_account(cfg, cp_user, domain, password, package)

    result = {
        'provisioned': ok,
        'cp_username': cp_user,
        'cp_domain': domain,
        'cp_password': password,
        'cp_url': f"https://{domain}:2083",
        'whm_url': cfg['whm_url'],
        'nameserver1': cfg.get('nameserver1', ''),
        'nameserver2': cfg.get('nameserver2', ''),
        'ip': cfg.get('ip_address', ''),
        'os': selected_os,
        'error': err,
        'plan': plan.get('name', 'VPS') if plan else 'VPS'
    }

    # Save to order
    for o in data['orders']:
        if o['id'] == order['id']:
            o['cpanel_provisioned'] = ok
            o['cpanel_details'] = result
            if ok: o['status'] = 'active'
            break
    save_data(data)
    return result

# ── RAZORPAY ──────────────────────────────────────────────────────
def rz_create_order(key_id, key_secret, amount_inr, receipt):
    import base64 as b64
    try:
        creds=b64.b64encode(f"{key_id}:{key_secret}".encode()).decode()
        r=req_lib.post('https://api.razorpay.com/v1/orders',
            json={'amount':amount_inr*100,'currency':'INR','receipt':str(receipt)},
            headers={'Authorization':f'Basic {creds}','Content-Type':'application/json'},timeout=10)
        if r.status_code==200: return r.json().get('id'),None
        return None,r.text
    except Exception as e: return None,str(e)

def rz_verify(key_secret, order_id, payment_id, signature):
    msg=f"{order_id}|{payment_id}"
    expected=hmac_lib.new(key_secret.encode(),msg.encode(),hashlib.sha256).hexdigest()
    return hmac_lib.compare_digest(expected,signature)

# ── DOMAIN ────────────────────────────────────────────────────────
DOMAIN_PRICES={'.fun':499,'.xyz':549,'.in':799,'.online':849,'.site':899,'.shop':1199,'.host':1299,'.com':1399,'.org':1499,'.net':1499,'.io':2499,'.co':1799,'.dev':1899,'.app':1699,'.gg':2999,'.me':899,'.info':749,'.biz':699,'.store':999,'.tech':1099}

@app.route('/api/domain-search')
def domain_search():
    if not session.get('user'): return jsonify({'error':'login_required'}),401
    q=re.sub(r'[^a-z0-9\-]','',request.args.get('q','').strip().lower())
    if not q or len(q)<2: return jsonify({'error':'Too short'})
    taken=['google','facebook','youtube','minecraft','amazon','microsoft']
    results=[{'domain':q+ext,'ext':ext,'price':price,'available':q.lower() not in taken and (len(q)%2==1 or len(q)>8)} for ext,price in DOMAIN_PRICES.items()]
    results.sort(key=lambda x:(not x['available'],x['price']))
    return jsonify({'results':results,'query':q})

# ── PUBLIC ────────────────────────────────────────────────────────
@app.route('/') 
def index(): return render_template('loading.html')
@app.route('/home')
def home(): return render_template('home.html',data=load_data(),cart_count=cart_count(),user=session.get('user'))
@app.route('/minecraft-hosting')
def hosting(): return render_template('hosting.html',data=load_data(),cart_count=cart_count(),user=session.get('user'))
@app.route('/vps')
def vps(): return render_template('vps.html',data=load_data(),cart_count=cart_count(),user=session.get('user'))
@app.route('/domains')
def domains(): return render_template('domains.html',data=load_data(),cart_count=cart_count(),user=session.get('user'))
@app.route('/support')
def support(): return render_template('support.html',data=load_data(),cart_count=cart_count(),user=session.get('user'))

# ── CART ──────────────────────────────────────────────────────────
@app.route('/api/cart')
def api_cart():
    data=load_data(); mc={p['id']:p for p in data['plans']}; vp={p['id']:p for p in data['vps_plans']}
    enriched=[]
    for item in get_cart():
        ptype=item.get('type','mc'); p=(vp if ptype=='vps' else mc).get(item['plan_id'])
        if p:
            k=f"price_{item['billing']}"
            entry={'name':p['name'],'billing':item['billing'],'price':p.get(k,p['price_monthly']),'type':ptype}
            if ptype=='mc':
                entry['mc_version']=item.get('mc_version','latest')
                entry['egg_type']=item.get('egg_type','vanilla')
            if ptype=='vps':
                entry['vps_os']=item.get('vps_os','Ubuntu 22.04')
            enriched.append(entry)
    return jsonify({'items':enriched,'total':sum(i['price'] for i in enriched),'count':len(enriched)})

@app.route('/cart')
def cart():
    data=load_data(); mc={p['id']:p for p in data['plans']}; vp={p['id']:p for p in data['vps_plans']}
    enriched=[]
    for item in get_cart():
        ptype=item.get('type','mc'); p=(vp if ptype=='vps' else mc).get(item['plan_id'])
        if p:
            k=f"price_{item['billing']}"; enriched.append({**item,'plan':p,'price':p.get(k,p['price_monthly'])})
    total=sum(i['price'] for i in enriched)
    return render_template('cart.html',data=data,cart_items=enriched,total=total,user=session.get('user'),cart_count=cart_count())

@app.route('/cart/add',methods=['POST'])
def cart_add():
    session.permanent = True
    payload=request.json; cart=session.get('cart',[])
    for item in cart:
        if item['plan_id']==payload['plan_id'] and item['billing']==payload['billing'] and item.get('type')==payload.get('type','mc'):
            return jsonify({'count':len(cart),'msg':'Already in cart'})
    entry={'plan_id':payload['plan_id'],'billing':payload['billing'],'name':payload.get('name',''),'type':payload.get('type','mc')}
    # Store Minecraft config
    if payload.get('type','mc')=='mc':
        entry['mc_version']=payload.get('mc_version','latest')
        entry['egg_type']=payload.get('egg_type','vanilla')
        entry['docker_image']=payload.get('docker_image','')
    # Store VPS config
    if payload.get('type')=='vps':
        entry['vps_os']=payload.get('vps_os','Ubuntu 22.04')
        entry['vps_password']=payload.get('vps_password','')
    cart.append(entry)
    session['cart']=cart; session.modified=True
    return jsonify({'count':len(cart),'msg':'Added!'})

@app.route('/cart/remove',methods=['POST'])
def cart_remove():
    idx=request.json.get('index',-1); cart=session.get('cart',[])
    if 0<=idx<len(cart): cart.pop(idx)
    session['cart']=cart; session.modified=True; return jsonify({'count':len(cart)})

@app.route('/cart/clear',methods=['POST'])
def cart_clear(): session['cart']=[]; return jsonify({'ok':True})

# ── AUTH ──────────────────────────────────────────────────────────
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        data=load_data(); uname=request.form.get('username','').strip(); pw=request.form.get('password','')
        if uname==data['admin']['username'] and hash_pw(pw)==data['admin']['password']:
            session['admin']=True; session.permanent=True; session['user']={'username':uname,'role':'admin','id':0,'email':'admin@strengthcloud.com'}; return redirect(url_for('admin'))
        for u in data.get('users',[]):
            if u['username']==uname and u['password']==hash_pw(pw):
                if not u.get('active',True): return render_template('login.html',error='Account suspended.',data=data,cart_count=cart_count())
                session.permanent = True
                session['user']={'username':u['username'],'email':u['email'],'role':u.get('role','user'),'id':u['id']}
                # Grant admin panel access if user has admin role
                if u.get('role')=='admin':
                    session['admin']=True
                    return redirect(url_for('admin'))
                return redirect(url_for('dashboard'))
        return render_template('login.html',error='Invalid credentials.',data=data,cart_count=cart_count())
    return render_template('login.html',data=load_data(),cart_count=cart_count())

@app.route('/signup',methods=['GET','POST'])
def signup():
    data=load_data()
    if request.method=='POST':
        uname=request.form.get('username','').strip(); email=request.form.get('email','').strip()
        pw=request.form.get('password',''); fname=request.form.get('fname','').strip(); lname=request.form.get('lname','').strip()
        for u in data.get('users',[]):
            if u['username']==uname: return render_template('signup.html',error='Username taken.',data=data,cart_count=cart_count())
            if u['email']==email: return render_template('signup.html',error='Email registered.',data=data,cart_count=cart_count())
        nu={'id':int(time.time()),'username':uname,'email':email,'password':hash_pw(pw),'fname':fname,'lname':lname,'active':True,'role':'user','joined':time.strftime('%Y-%m-%d'),'orders':[]}
        data['users'].append(nu); save_data(data)
        session['user']={'username':uname,'email':email,'role':'user','id':nu['id']}; return redirect(url_for('dashboard'))
    return render_template('signup.html',data=data,cart_count=cart_count())

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))

# ── DASHBOARD ─────────────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    if not session.get('user'): return redirect(url_for('login'))
    data=load_data(); uid=session['user'].get('id')
    user_data=next((u for u in data['users'] if u['id']==uid),None)
    orders=[o for o in data.get('orders',[]) if o.get('user_id')==uid]
    return render_template('dashboard.html',data=data,user=session['user'],user_data=user_data,orders=orders,cart_count=cart_count())

@app.route('/dashboard/change-ptero-password',methods=['POST'])
def change_ptero_password():
    if not session.get('user'): return jsonify({'error':'Not logged in'}),401
    data=load_data(); cfg=data.get('pterodactyl',{})
    new_pw=request.json.get('password','').strip()
    if len(new_pw)<8: return jsonify({'error':'Min 8 characters'})
    uid=session['user'].get('id'); username=session['user'].get('username','')
    # Find user
    user=next((u for u in data['users'] if u['id']==uid or u['username']==username),None)
    if not user: return jsonify({'error':'User not found'})
    # Find ptero user id from orders
    ptero_uid=None
    for o in data['orders']:
        if o.get('user_id')==uid or o.get('username')==username:
            if o.get('ptero_user_id'):
                ptero_uid=o['ptero_user_id']; break
    if not ptero_uid: return jsonify({'error':'No Pterodactyl account found'})
    if not cfg.get('panel_url') or not cfg.get('api_key'):
        return jsonify({'error':'Pterodactyl not configured'})
    try:
        r=req_lib.patch(f"{cfg['panel_url'].rstrip('/')}/api/application/users/{ptero_uid}",
            json={'email':user['email'],'username':user['username'],'first_name':user.get('fname',username),'last_name':user.get('lname','User'),'password':new_pw},
            headers=ptero_headers(cfg),timeout=10)
        if r.status_code in [200,201]:
            # Update stored password in all orders
            for o in data['orders']:
                if (o.get('user_id')==uid or o.get('username')==username) and o.get('ptero_user_id')==ptero_uid:
                    o['ptero_password']=new_pw
            save_data(data)
            return jsonify({'success':True})
        return jsonify({'error':f'Panel error {r.status_code}: {r.text[:200]}'})
    except Exception as e: return jsonify({'error':str(e)})

@app.route('/dashboard/change-password',methods=['POST'])
def change_password():
    if not session.get('user'): return jsonify({'error':'Not logged in'}),401
    data=load_data(); uid=session['user'].get('id')
    for u in data['users']:
        if u['id']==uid:
            if u['password']!=hash_pw(request.json.get('current','')): return jsonify({'error':'Current password incorrect'})
            if len(request.json.get('new',''))<6: return jsonify({'error':'Min 6 chars'})
            u['password']=hash_pw(request.json.get('new','')); save_data(data); return jsonify({'success':True})
    return jsonify({'error':'Not found'})

@app.route('/dashboard/update-profile',methods=['POST'])
def update_profile():
    if not session.get('user'): return jsonify({'error':'Not logged in'}),401
    data=load_data(); uid=session['user'].get('id')
    for u in data['users']:
        if u['id']==uid:
            u['fname']=request.json.get('fname',''); u['lname']=request.json.get('lname',''); u['email']=request.json.get('email','')
            save_data(data); return jsonify({'success':True})
    return jsonify({'error':'Not found'})

# ── CHECKOUT ──────────────────────────────────────────────────────
def _enrich_cart(data):
    mc={p['id']:p for p in data['plans']}; vp={p['id']:p for p in data['vps_plans']}
    enriched=[]
    for item in get_cart():
        p=(vp if item.get('type')=='vps' else mc).get(item['plan_id'])
        if p:
            k=f"price_{item['billing']}"; enriched.append({**item,'plan':p,'price':p.get(k,p['price_monthly'])})
    return enriched

@app.route('/checkout',methods=['GET'])
def checkout():
    if not session.get('user'): return redirect(url_for('login'))
    data=load_data(); items=_enrich_cart(data)
    if not items: return redirect(url_for('cart'))
    total=sum(i['price'] for i in items)
    pmethods=data.get('payment',{}); ptero=data.get('pterodactyl',{})
    return render_template('checkout.html',data=data,cart_items=items,total=total,
        user=session.get('user'),cart_count=cart_count(),payment=pmethods,
        ptero_enabled=ptero.get('enabled',False),razorpay_key=pmethods.get('razorpay_key_id',''))

@app.route('/checkout/apply-coupon',methods=['POST'])
def apply_coupon():
    code=request.json.get('code','').strip().upper(); data=load_data()
    for c in data.get('coupons',[]):
        if c['code']==code and c['active']: return jsonify({'success':True,'type':c['type'],'discount':c['discount']})
    return jsonify({'success':False,'error':'Invalid or expired coupon'})

@app.route('/checkout/razorpay-create',methods=['POST'])
def razorpay_create():
    if not session.get('user'): return jsonify({'error':'Login required'}),401
    data=load_data(); pm=data.get('payment',{})
    if not pm.get('razorpay_key_id') or not pm.get('razorpay_key_secret'):
        return jsonify({'error':'Razorpay not configured. Please use UPI or Bank Transfer.'}),400
    items=_enrich_cart(data)
    if not items: return jsonify({'error':'Cart empty'}),400
    total=sum(i['price'] for i in items)
    coupon=request.json.get('coupon','').strip().upper(); discount=0
    for c in data.get('coupons',[]):
        if c['code']==coupon and c['active']:
            discount=int(total*c['discount']/100) if c['type']=='percent' else c['discount']; break
    final=max(1,total-discount)
    receipt=f"SC{int(time.time())}"
    rz_id,err=rz_create_order(pm['razorpay_key_id'],pm['razorpay_key_secret'],final,receipt)
    if not rz_id: return jsonify({'error':f'Gateway error: {err}'}),500
    session['pending_order']={'items':items,'total':total,'discount':discount,'final':final,'coupon':coupon,'rz_order_id':rz_id}
    return jsonify({'order_id':rz_id,'amount':final*100,'currency':'INR','key':pm['razorpay_key_id'],
        'name':data['site']['name'],'email':session['user'].get('email',''),'contact':''})

@app.route('/checkout/razorpay-verify',methods=['POST'])
def razorpay_verify():
    if not session.get('user'): return jsonify({'error':'Login required'}),401
    data=load_data(); pm=data.get('payment',{})
    rz_oid=request.json.get('razorpay_order_id',''); rz_pid=request.json.get('razorpay_payment_id',''); rz_sig=request.json.get('razorpay_signature','')
    if not rz_verify(pm.get('razorpay_key_secret',''),rz_oid,rz_pid,rz_sig):
        return jsonify({'error':'Payment verification failed. Contact support.'}),400
    pending=session.pop('pending_order',None)
    if not pending: return jsonify({'error':'Order session expired'}),400
    order={'id':int(time.time()),'user_id':session['user'].get('id',0),'username':session['user'].get('username','unknown'),
        'items':pending['items'],'total':pending['total'],'discount':pending['discount'],'final':pending['final'],
        'coupon':pending['coupon'],'status':'paid','payment_method':'razorpay','payment_id':rz_pid,
        'rz_order_id':rz_oid,'date':time.strftime('%Y-%m-%d %H:%M')}
    data['orders'].append(order); save_data(data); session['cart']=[]
    provision=auto_provision(order)
    discord_notify(order)
    return jsonify({'success':True,'order_id':order['id'],'provision':provision})

@app.route('/checkout/manual-order',methods=['POST'])
def manual_order():
    # Must be logged in
    if not session.get('user'):
        return jsonify({'error':'Session expired. Please log in again.'}),401

    data=load_data()

    # Try to get cart from session
    cart=session.get('cart',[])

    # Build enriched cart
    items=_enrich_cart(data)

    # If session cart is empty, try to get from request body as fallback
    if not items:
        return jsonify({'error':'Your cart is empty. Please go back and add items.'}),400

    total=sum(i['price'] for i in items)
    body = request.json or {}
    coupon=body.get('coupon','').strip().upper()
    method=body.get('method','upi')
    utr=body.get('utr','').strip()

    discount=0
    for c in data.get('coupons',[]):
        if c['code']==coupon and c['active']:
            discount=int(total*c['discount']/100) if c['type']=='percent' else c['discount']; break
    final=max(0,total-discount)

    order={
        'id':int(time.time()),
        'user_id':session['user'].get('id', session['user'].get('username', 0)),
        'username':session['user'].get('username','unknown'),
        'items':items,
        'total':total,
        'discount':discount,
        'final':final,
        'coupon':coupon,
        'status':'pending_verification',
        'payment_method':method,
        'utr_number':utr,
        'date':time.strftime('%Y-%m-%d %H:%M')
    }
    data['orders'].append(order)
    save_data(data)
    session['cart']=[]
    session.modified=True
    discord_notify(order)
    return jsonify({'success':True,'order_id':order['id']})

@app.route('/order-success/<int:oid>')
def order_success(oid):
    if not session.get('user'): return redirect(url_for('login'))
    data=load_data()
    order=next((o for o in data['orders'] if o['id']==oid and o['user_id']==session['user'].get('id',0)),None)
    if not order: return redirect(url_for('dashboard'))
    # Pass items separately to avoid dict .items() method conflict in Jinja
    order_items = order.get('items', [])
    return render_template('order_success.html',order=order,order_items=order_items,data=data,user=session.get('user'),cart_count=0,ptero=data.get('pterodactyl',{}))

# ── ADMIN ─────────────────────────────────────────────────────────
@app.route('/admin')
def admin():
    if not session.get('admin'): return redirect(url_for('admin_login'))
    data=load_data()
    stats={'total_users':len(data.get('users',[])),'total_orders':len(data.get('orders',[])),'total_plans':len(data.get('plans',[])),'total_vps':len(data.get('vps_plans',[])),'revenue':sum(o.get('final',0) for o in data.get('orders',[])),'pending_orders':len([o for o in data.get('orders',[]) if o.get('status') in ['pending','pending_verification']]),'active_users':len([u for u in data.get('users',[]) if u.get('active',True)])}
    return render_template('admin.html',data=data,stats=stats)

@app.route('/admin/login',methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        data=load_data(); uname=request.form.get('username',''); pw=request.form.get('password','')
        if uname==data['admin']['username'] and hash_pw(pw)==data['admin']['password']:
            session['admin']=True; session.permanent=True; session['user']={'username':uname,'role':'admin','id':0,'email':'admin@strengthcloud.com'}; return redirect(url_for('admin'))
        return render_template('admin_login.html',error='Invalid admin credentials')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout(): session.pop('admin',None); return redirect(url_for('admin_login'))

@app.route('/admin/save',methods=['POST'])
def admin_save():
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    payload=request.json; data=load_data()
    for k in ['plans','vps_plans','stats','site','features','faqs','announcements','coupons','sale','payment','pterodactyl','cpanel','discord']:
        if k in payload: data[k]=payload[k]
    # Strip trailing slash from panel URL
    if 'pterodactyl' in payload and data['pterodactyl'].get('panel_url'):
        data['pterodactyl']['panel_url'] = data['pterodactyl']['panel_url'].rstrip('/')
    if 'admin' in payload:
        a=payload['admin']; data['admin']['username']=a['username']
        if a.get('password'): data['admin']['password']=hash_pw(a['password'])
    save_data(data); return jsonify({'success':True})

@app.route('/admin/ptero-servers')
def ptero_servers():
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data(); cfg=data.get('pterodactyl',{})
    if not cfg.get('panel_url') or not cfg.get('api_key'):
        return jsonify({'error':'Pterodactyl not configured. Go to Admin → Pterodactyl tab.'})
    base = cfg['panel_url'].rstrip('/')
    hdrs = ptero_headers(cfg)
    try:
        # Fetch all servers
        servers=[]; page=1
        while True:
            r=req_lib.get(f"{base}/api/application/servers?per_page=100&page={page}",headers=hdrs,timeout=12)
            if r.status_code!=200: return jsonify({'error':f'Panel error {r.status_code}: {r.text[:200]}'})
            j=r.json(); servers+=j.get('data',[]); 
            if j.get('meta',{}).get('pagination',{}).get('current_page',1)>=j.get('meta',{}).get('pagination',{}).get('total_pages',1): break
            page+=1

        # Fetch users count
        ur=req_lib.get(f"{base}/api/application/users?per_page=1",headers=hdrs,timeout=8)
        user_count=ur.json().get('meta',{}).get('pagination',{}).get('total',0) if ur.status_code==200 else 0

        # Fetch nodes for name mapping
        nr=req_lib.get(f"{base}/api/application/nodes",headers=hdrs,timeout=8)
        nodes={n['attributes']['id']:n['attributes']['name'] for n in nr.json().get('data',[])} if nr.status_code==200 else {}

        result=[]
        for s in servers:
            a=s.get('attributes',{})
            result.append({
                'id': a.get('id'),
                'uuid': a.get('uuid'),
                'identifier': a.get('identifier'),
                'name': a.get('name'),
                'suspended': a.get('suspended',False),
                'limits': a.get('limits',{}),
                'node': nodes.get(a.get('node'),'Node '+str(a.get('node','?'))),
                'user_id': a.get('user'),
                'user_email': '',
                'user_username': '',
            })

        # Enrich with user details (batch by unique user ids)
        user_ids = list({s['user_id'] for s in result if s['user_id']})
        user_map={}
        for uid in user_ids[:50]:  # limit to avoid too many requests
            try:
                uresp=req_lib.get(f"{base}/api/application/users/{uid}",headers=hdrs,timeout=6)
                if uresp.status_code==200:
                    ua=uresp.json()['attributes']
                    user_map[uid]={'email':ua.get('email',''),'username':ua.get('username','')}
            except: pass
        for s in result:
            u=user_map.get(s['user_id'],{})
            s['user_email']=u.get('email',''); s['user_username']=u.get('username','')

        return jsonify({'servers':result,'panel_url':base,'user_count':user_count})
    except Exception as e:
        return jsonify({'error':str(e)})

@app.route('/admin/ptero-suspend',methods=['POST'])
def ptero_suspend():
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data(); cfg=data.get('pterodactyl',{})
    if not cfg.get('panel_url') or not cfg.get('api_key'): return jsonify({'error':'Not configured'})
    sid=request.json.get('server_id'); suspend=request.json.get('suspend',True)
    action='suspend' if suspend else 'unsuspend'
    try:
        r=req_lib.post(f"{cfg['panel_url'].rstrip('/')}/api/application/servers/{sid}/{action}",
            headers=ptero_headers(cfg),timeout=10)
        if r.status_code in [200,201,204]: return jsonify({'success':True})
        return jsonify({'error':f'Panel returned {r.status_code}: {r.text[:200]}'})
    except Exception as e: return jsonify({'error':str(e)})

@app.route('/admin/ptero-edit-resources',methods=['POST'])
def ptero_edit_resources():
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data(); cfg=data.get('pterodactyl',{})
    if not cfg.get('panel_url') or not cfg.get('api_key'): return jsonify({'error':'Not configured'})
    sid=request.json.get('server_id')
    memory=request.json.get('memory',1024)
    cpu=request.json.get('cpu',100)
    disk=request.json.get('disk',10240)
    try:
        # First get current server build config
        r=req_lib.get(f"{cfg['panel_url'].rstrip('/')}/api/application/servers/{sid}",
            headers=ptero_headers(cfg),timeout=10)
        if r.status_code!=200: return jsonify({'error':f'Server not found: {r.status_code}'})
        current=r.json()['attributes']
        # Update limits
        payload={
            'allocation': current.get('allocation',0),
            'memory':memory,'swap':0,'disk':disk,'io':500,'cpu':cpu,
            'threads': None,
            'feature_limits':current.get('feature_limits',{'databases':5,'backups':3,'allocations':1})
        }
        r2=req_lib.patch(f"{cfg['panel_url'].rstrip('/')}/api/application/servers/{sid}/build",
            json=payload,headers=ptero_headers(cfg),timeout=10)
        if r2.status_code in [200,201]: return jsonify({'success':True})
        return jsonify({'error':f'Panel returned {r2.status_code}: {r2.text[:300]}'})
    except Exception as e: return jsonify({'error':str(e)})

@app.route('/admin/ptero-delete',methods=['POST'])
def ptero_delete():
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data(); cfg=data.get('pterodactyl',{})
    if not cfg.get('panel_url') or not cfg.get('api_key'): return jsonify({'error':'Not configured'})
    sid=request.json.get('server_id')
    try:
        r=req_lib.delete(f"{cfg['panel_url'].rstrip('/')}/api/application/servers/{sid}",
            headers=ptero_headers(cfg),timeout=10)
        if r.status_code in [200,201,204]: return jsonify({'success':True})
        # Force delete option if normal delete fails
        r2=req_lib.delete(f"{cfg['panel_url'].rstrip('/')}/api/application/servers/{sid}/force",
            headers=ptero_headers(cfg),timeout=10)
        if r2.status_code in [200,201,204]: return jsonify({'success':True})
        return jsonify({'error':f'Panel returned {r.status_code}: {r.text[:200]}'})
    except Exception as e: return jsonify({'error':str(e)})


def test_cpanel():
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data(); cfg=data.get('cpanel',{})
    if not cfg.get('whm_url') or not cfg.get('api_token'):
        return jsonify({'success':False,'error':'WHM URL and API token required'})
    result, err = cpanel_api(cfg, 'listaccts', {'searchtype':'user','search':'','want':'user'})
    if result:
        count = len(result.get('data',{}).get('acct',[]))
        return jsonify({'success':True,'message':f'✅ Connected! {count} cPanel accounts found.'})
    return jsonify({'success':False,'error':f'❌ {err}'})

@app.route('/admin/cpanel-accounts')
def cpanel_accounts():
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data(); cfg=data.get('cpanel',{})
    if not cfg.get('whm_url') or not cfg.get('api_token'):
        return jsonify({'error':'cPanel not configured'})
    accounts, err = cpanel_get_accounts(cfg)
    if err: return jsonify({'error':err})
    return jsonify({'accounts':accounts,'whm_url':cfg.get('whm_url','')})

@app.route('/admin/cpanel-suspend', methods=['POST'])
def admin_cpanel_suspend():
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data(); cfg=data.get('cpanel',{})
    username = request.json.get('username')
    suspend  = request.json.get('suspend', True)
    reason   = request.json.get('reason', 'Suspended by admin')
    result, err = cpanel_suspend(cfg, username, suspend, reason)
    if err: return jsonify({'success':False,'error':err})
    return jsonify({'success':True})

@app.route('/admin/cpanel-provision-order/<int:oid>', methods=['POST'])
def cpanel_provision_order(oid):
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data()
    order=next((o for o in data['orders'] if o['id']==oid),None)
    if not order: return jsonify({'error':'Not found'}),404
    result = auto_provision_vps(order)
    return jsonify(result)

@app.route('/dashboard/change-cpanel-password', methods=['POST'])
def change_cpanel_password():
    if not session.get('user'): return jsonify({'error':'Not logged in'}),401
    data=load_data(); cfg=data.get('cpanel',{})
    new_pw = request.json.get('password','').strip()
    if len(new_pw) < 8: return jsonify({'error':'Min 8 characters'})
    uid = session['user'].get('id'); uname = session['user'].get('username','')
    # Find order with cpanel details
    order = next((o for o in data['orders'] if (o.get('user_id')==uid or o.get('username')==uname) and o.get('cpanel_provisioned')), None)
    if not order: return jsonify({'error':'No cPanel account found'})
    cp_user = order.get('cpanel_details',{}).get('cp_username','')
    if not cp_user: return jsonify({'error':'cPanel username not found'})
    ok, err = cpanel_change_password(cfg, cp_user, new_pw)
    if ok:
        order['cpanel_details']['cp_password'] = new_pw
        save_data(data)
        return jsonify({'success':True})
    return jsonify({'error':err or 'Failed to change password'})

@app.route('/admin/test-discord-webhook', methods=['POST'])
def test_discord_webhook():
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    url = request.json.get('webhook_url','').strip()
    if not url: return jsonify({'error':'No webhook URL provided'})
    try:
        embed = {
            "title": "✅ StrengthCloud Bot Connected!",
            "description": "Order notifications are working. You'll receive a message like this for every new order.",
            "color": 0x8b5cf6,
            "fields": [
                {"name":"👤 Customer","value":"`testuser`","inline":True},
                {"name":"💰 Amount","value":"**₹99**","inline":True},
                {"name":"📦 Items","value":"⛏️ MC **Dirt** (Monthly) `vanilla 1.21.11 (Latest)`","inline":False},
            ],
            "footer":{"text":"StrengthCloud Order Alert — Test Message"},
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }
        r = req_lib.post(url, json={"embeds":[embed],"username":"StrengthCloud","avatar_url":"https://cdn.discordapp.com/icons/1416472559104299210/6299f0c15609e8680791202bfa89df74.webp"}, timeout=8)
        if r.status_code in [200,201,204]:
            return jsonify({'success':True})
        return jsonify({'error':f'Discord returned {r.status_code}: {r.text[:200]}'})
    except Exception as e:
        return jsonify({'error':str(e)})


@app.route('/admin/test-pterodactyl', methods=['POST'])
def test_pterodactyl():
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data(); cfg=data.get('pterodactyl',{})
    if not cfg.get('panel_url') or not cfg.get('api_key'): return jsonify({'error':'Panel URL and API key required'})
    try:
        r=req_lib.get(cfg['panel_url'].rstrip('/')+'/api/application/nodes',headers=ptero_headers(cfg),timeout=8)
        if r.status_code==200: return jsonify({'success':True,'message':f"Connected! {len(r.json().get('data',[]))} node(s) found."})
        elif r.status_code==401: return jsonify({'success':False,'error':'❌ Invalid API key — check permissions'})
        elif r.status_code==403: return jsonify({'success':False,'error':'❌ API key missing Read permissions'})
        return jsonify({'error':f"Panel returned {r.status_code}: {r.text[:200]}"})
    except Exception as e: return jsonify({'error':str(e)})

@app.route('/admin/provision-order/<int:oid>',methods=['POST'])
def admin_provision_order(oid):
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data()
    order=next((o for o in data['orders'] if o['id']==oid),None)
    if not order: return jsonify({'error':'Order not found'}),404
    return jsonify(auto_provision(order))

@app.route('/admin/user/<int:uid>/toggle',methods=['POST'])
def admin_toggle_user(uid):
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data()
    for u in data['users']:
        if u['id']==uid: u['active']=not u.get('active',True); save_data(data); return jsonify({'active':u['active']})
    return jsonify({'error':'Not found'}),404

@app.route('/admin/user/<int:uid>/set-role',methods=['POST'])
def admin_set_role(uid):
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data()
    role=request.json.get('role','user')
    if role not in ['admin','user']: return jsonify({'error':'Invalid role'}),400
    for u in data['users']:
        if u['id']==uid:
            u['role']=role
            save_data(data)
            return jsonify({'success':True,'role':role,'username':u['username']})
    return jsonify({'error':'User not found'}),404

@app.route('/admin/user/<int:uid>/delete',methods=['POST'])
def admin_delete_user(uid):
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data(); data['users']=[u for u in data['users'] if u['id']!=uid]; save_data(data); return jsonify({'success':True})

@app.route('/admin/order/<int:oid>/status',methods=['POST'])
def admin_order_status(oid):
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data(); status=request.json.get('status')
    for o in data['orders']:
        if o['id']==oid:
            o['status']=status; save_data(data)
            if status=='active' and not o.get('ptero_provisioned'):
                auto_provision(o)
            return jsonify({'success':True})
    return jsonify({'error':'Not found'}),404

@app.route('/admin/order/<int:oid>/accept',methods=['POST'])
def admin_accept_order(oid):
    if not session.get('admin'): return jsonify({'error':'Unauthorized'}),401
    data=load_data()
    order=next((o for o in data['orders'] if o['id']==oid),None)
    if not order: return jsonify({'error':'Order not found'}),404
    order['status']='active'; save_data(data)

    # Detect order type — if any item is VPS, use cPanel
    has_vps = any(i.get('type')=='vps' for i in order.get('items',[]))
    has_mc  = any(i.get('type')!='vps' for i in order.get('items',[]))

    provision_ptero = None
    provision_cpanel = None
    if has_mc:
        provision_ptero = auto_provision(order)
    if has_vps:
        provision_cpanel = auto_provision_vps(order)

    return jsonify({'success':True,'provision_ptero':provision_ptero,'provision_cpanel':provision_cpanel})

# ── BOT API — called by bot.py directly using secret key ──────────
def _bot_auth():
    """Verify bot secret key from request header or JSON body."""
    data = load_data()
    secret = data.get('discord', {}).get('bot_secret', '')
    if not secret:
        return False
    provided = request.headers.get('X-Bot-Secret') or (request.json or {}).get('secret', '')
    return provided == secret

@app.route('/bot/order/<int:oid>/accept', methods=['POST'])
def bot_accept_order(oid):
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    data = load_data()
    order = next((o for o in data['orders'] if o['id'] == oid), None)
    if not order: return jsonify({'error': 'Order not found'}), 404
    if order.get('status') == 'active':
        return jsonify({'success': True, 'already': True, 'status': 'active'})
    order['status'] = 'active'
    save_data(data)
    has_vps = any(i.get('type') == 'vps' for i in order.get('items', []))
    has_mc  = any(i.get('type') != 'vps' for i in order.get('items', []))
    provision_ptero = auto_provision(order) if has_mc else None
    provision_cpanel = auto_provision_vps(order) if has_vps else None
    return jsonify({'success': True, 'status': 'active',
                    'provision_ptero': provision_ptero,
                    'provision_cpanel': provision_cpanel})

@app.route('/bot/order/<int:oid>/reject', methods=['POST'])
def bot_reject_order(oid):
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    data = load_data()
    order = next((o for o in data['orders'] if o['id'] == oid), None)
    if not order: return jsonify({'error': 'Order not found'}), 404
    order['status'] = 'rejected'
    reason = (request.json or {}).get('reason', 'Rejected by admin')
    order['reject_reason'] = reason
    save_data(data)
    return jsonify({'success': True, 'status': 'rejected'})

@app.route('/bot/order/<int:oid>/provision', methods=['POST'])
def bot_provision_order(oid):
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    data = load_data()
    order = next((o for o in data['orders'] if o['id'] == oid), None)
    if not order: return jsonify({'error': 'Order not found'}), 404
    has_vps = any(i.get('type') == 'vps' for i in order.get('items', []))
    has_mc  = any(i.get('type') != 'vps' for i in order.get('items', []))
    result = {}
    if has_mc:  result['ptero']  = auto_provision(order)
    if has_vps: result['cpanel'] = auto_provision_vps(order)
    return jsonify({'success': True, 'result': result})

@app.route('/bot/order/<int:oid>/info', methods=['GET'])
def bot_order_info(oid):
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    data = load_data()
    order = next((o for o in data['orders'] if o['id'] == oid), None)
    if not order: return jsonify({'error': 'Order not found'}), 404
    return jsonify({'order': order})

@app.route('/bot/orders', methods=['GET'])
def bot_orders():
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    data   = load_data()
    status = request.args.get('status','')
    limit  = int(request.args.get('limit', 10))
    orders = data.get('orders', [])
    if status: orders = [o for o in orders if o.get('status') == status]
    orders = list(reversed(orders))[:limit]
    return jsonify({'orders': orders, 'total': len(data.get('orders', []))})

@app.route('/bot/users', methods=['GET'])
def bot_users():
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    data  = load_data()
    q     = request.args.get('q','').lower()
    users = data.get('users', [])
    if q: users = [u for u in users if q in u.get('username','').lower() or q in u.get('email','').lower()]
    safe  = [{'id':u['id'],'username':u['username'],'email':u['email'],
              'fname':u.get('fname',''),'lname':u.get('lname',''),
              'active':u.get('active',True),'role':u.get('role','user'),
              'joined':u.get('joined','')} for u in users]
    return jsonify({'users': safe, 'total': len(data.get('users', []))})

@app.route('/bot/user/<int:uid>/toggle', methods=['POST'])
def bot_toggle_user(uid):
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    data = load_data()
    for u in data['users']:
        if u['id'] == uid:
            u['active'] = not u.get('active', True)
            save_data(data)
            return jsonify({'success': True, 'active': u['active'], 'username': u['username']})
    return jsonify({'error': 'User not found'}), 404

@app.route('/bot/user/<int:uid>/delete', methods=['POST'])
def bot_delete_user(uid):
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    data = load_data()
    user = next((u for u in data['users'] if u['id'] == uid), None)
    if not user: return jsonify({'error': 'User not found'}), 404
    data['users'] = [u for u in data['users'] if u['id'] != uid]
    save_data(data)
    return jsonify({'success': True, 'username': user['username']})

@app.route('/bot/user/<int:uid>/role', methods=['POST'])
def bot_set_user_role(uid):
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    role = (request.json or {}).get('role', 'user')
    data = load_data()
    for u in data['users']:
        if u['id'] == uid:
            u['role'] = role
            save_data(data)
            return jsonify({'success': True, 'username': u['username'], 'role': role})
    return jsonify({'error': 'User not found'}), 404

@app.route('/bot/stats', methods=['GET'])
def bot_stats():
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    data    = load_data()
    orders  = data.get('orders', [])
    users   = data.get('users', [])
    revenue = sum(o.get('final', 0) for o in orders)
    pending = len([o for o in orders if o.get('status') in ['pending','pending_verification']])
    active  = len([o for o in orders if o.get('status') == 'active'])
    return jsonify({
        'total_users':   len(users),
        'active_users':  len([u for u in users if u.get('active', True)]),
        'total_orders':  len(orders),
        'pending_orders': pending,
        'active_orders': active,
        'total_revenue': revenue,
        'site_name':     data.get('site', {}).get('name', 'StrengthCloud'),
    })

@app.route('/bot/servers', methods=['GET'])
def bot_servers():
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    data = load_data()
    cfg  = data.get('pterodactyl', {})
    if not cfg.get('panel_url') or not cfg.get('api_key'):
        return jsonify({'error': 'Pterodactyl not configured'})
    try:
        base = cfg['panel_url'].rstrip('/')
        hdrs = ptero_headers(cfg)
        r    = req_lib.get(f'{base}/api/application/servers?per_page=50', headers=hdrs, timeout=12)
        if r.status_code != 200:
            return jsonify({'error': f'Panel {r.status_code}'})
        servers = [{'id':s['attributes']['id'],'name':s['attributes']['name'],
                    'identifier':s['attributes']['identifier'],
                    'suspended':s['attributes'].get('suspended',False),
                    'memory':s['attributes'].get('limits',{}).get('memory',0)}
                   for s in r.json().get('data',[])]
        return jsonify({'servers': servers, 'panel_url': base})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/bot/server/<string:sid>/suspend', methods=['POST'])
def bot_suspend_server(sid):
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    data    = load_data()
    cfg     = data.get('pterodactyl', {})
    if not cfg.get('panel_url') or not cfg.get('api_key'):
        return jsonify({'error':'Pterodactyl not configured'})
    suspend = (request.json or {}).get('suspend', True)
    action  = 'suspend' if suspend else 'unsuspend'
    base    = cfg['panel_url'].rstrip('/')
    hdrs    = ptero_headers(cfg)
    # If sid is not numeric, try to find numeric id by identifier
    numeric_id = sid
    if not str(sid).isdigit():
        try:
            r = req_lib.get(f'{base}/api/application/servers?per_page=100', headers=hdrs, timeout=10)
            if r.status_code == 200:
                for s in r.json().get('data', []):
                    if s['attributes'].get('identifier') == sid:
                        numeric_id = str(s['attributes']['id'])
                        break
        except: pass
    try:
        r = req_lib.post(f'{base}/api/application/servers/{numeric_id}/{action}',
                         headers=hdrs, timeout=10)
        if r.status_code in [200,201,204]:
            return jsonify({'success': True, 'action': action, 'server_id': numeric_id})
        return jsonify({'error': f'Panel returned {r.status_code} — Make sure you used the numeric ID from .servers, not the short identifier'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/bot/server/<string:sid>/delete', methods=['POST'])
def bot_delete_server(sid):
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    data = load_data()
    cfg  = data.get('pterodactyl', {})
    if not cfg.get('panel_url') or not cfg.get('api_key'):
        return jsonify({'error':'Pterodactyl not configured'})
    base = cfg['panel_url'].rstrip('/')
    hdrs = ptero_headers(cfg)
    numeric_id = sid
    if not str(sid).isdigit():
        try:
            r = req_lib.get(f'{base}/api/application/servers?per_page=100', headers=hdrs, timeout=10)
            if r.status_code == 200:
                for s in r.json().get('data', []):
                    if s['attributes'].get('identifier') == sid:
                        numeric_id = str(s['attributes']['id'])
                        break
        except: pass
    try:
        r = req_lib.delete(f'{base}/api/application/servers/{numeric_id}',
                           headers=hdrs, timeout=10)
        if r.status_code in [200,201,204]:
            return jsonify({'success': True})
        r2 = req_lib.delete(f'{base}/api/application/servers/{numeric_id}/force',
                            headers=hdrs, timeout=10)
        if r2.status_code in [200,201,204]:
            return jsonify({'success': True})
        return jsonify({'error': f'Panel returned {r.status_code} — Use numeric ID from .servers'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/bot/coupon/add', methods=['POST'])
def bot_add_coupon():
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    body = request.json or {}
    code     = body.get('code','').upper().strip()
    discount = int(body.get('discount', 10))
    ctype    = body.get('type', 'percent')
    if not code: return jsonify({'error': 'Code required'})
    data = load_data()
    data.setdefault('coupons', [])
    for c in data['coupons']:
        if c['code'] == code:
            return jsonify({'error': f'Coupon {code} already exists'})
    data['coupons'].append({'code': code, 'discount': discount, 'type': ctype, 'active': True})
    save_data(data)
    return jsonify({'success': True, 'code': code, 'discount': discount, 'type': ctype})

@app.route('/bot/coupon/delete', methods=['POST'])
def bot_delete_coupon():
    if not _bot_auth(): return jsonify({'error':'Unauthorized'}), 401
    code = (request.json or {}).get('code','').upper().strip()
    data = load_data()
    before = len(data.get('coupons', []))
    data['coupons'] = [c for c in data.get('coupons', []) if c['code'] != code]
    if len(data['coupons']) == before:
        return jsonify({'error': f'Coupon {code} not found'})
    save_data(data)
    return jsonify({'success': True, 'code': code})



if __name__=='__main__':
    if not os.path.exists(DATA_FILE): save_data(DEFAULT_DATA)
    app.run(debug=True,port=5000)
