"""
StrengthCloud Discord Bot — Full Command System
────────────────────────────────────────────────
Prefix: .  (dot)   |   Type .help to see all commands

Install:   pip install "discord.py>=2.3.0" requests
Run:       python bot.py
"""

import discord
from discord.ext import tasks
from discord import ui
import json, os, time, asyncio, requests

DATA_FILE     = 'data.json'
NOTIFIED_FILE = 'notified_orders.json'
POLL_INTERVAL = 8
PREFIX        = '.'

# ── Helpers ───────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f: return json.load(f)
    return {}

def load_notified():
    if os.path.exists(NOTIFIED_FILE):
        with open(NOTIFIED_FILE) as f: return set(json.load(f))
    return set()

def save_notified(ids):
    with open(NOTIFIED_FILE, 'w') as f: json.dump(list(ids), f)

def get_cfg():
    return load_data().get('discord', {})

def api(method, path, **kwargs):
    cfg    = get_cfg()
    base   = cfg.get('site_url', 'http://localhost:5000').rstrip('/')
    secret = cfg.get('bot_secret', '')
    headers = {'X-Bot-Secret': secret, 'Content-Type': 'application/json'}
    try:
        r = requests.request(method, f'{base}{path}', headers=headers, timeout=15, **kwargs)
        return r.json()
    except Exception as e:
        return {'error': str(e)}

def is_owner(user_id):
    return str(user_id) == str(get_cfg().get('owner_id', ''))

def fmt_items(items):
    lines = []
    for it in items:
        plan  = it.get('plan', {})
        pname = plan.get('name', it.get('name','Item')) if isinstance(plan, dict) else it.get('name','Item')
        ptype = '🖥️ VPS' if it.get('type') == 'vps' else '⛏️ MC'
        bill  = it.get('billing','monthly').capitalize()
        egg   = it.get('egg_type',''); mc_v = it.get('mc_version',''); vos = it.get('vps_os','')
        detail = f' `{egg} {mc_v}`' if egg else (f' `{vos}`' if vos else '')
        lines.append(f'{ptype} **{pname}** ({bill}){detail}')
    return '\n'.join(lines) or '—'

STATUS_COLOR = {'paid':0x10b981,'active':0x8b5cf6,'pending_verification':0xf59e0b,'pending':0x6b7280,'rejected':0xef4444}
STATUS_EMOJI = {'paid':'✅','active':'🚀','pending_verification':'⏳','pending':'🕐','rejected':'❌'}

def order_embed(order, title=None, color=None):
    oid    = order.get('id','')
    status = order.get('status','pending')
    method = order.get('payment_method','?').upper()
    uname  = order.get('username','?')
    final  = order.get('final', order.get('total', 0))
    date   = order.get('date','')
    utr    = order.get('utr_number','')
    pid    = order.get('payment_id','')
    em     = STATUS_EMOJI.get(status, '📦')
    embed  = discord.Embed(
        title=title or f'🛒 Order #{oid}',
        description=f'{em} **{status.replace("_"," ").upper()}** via **{method}**',
        color=color or STATUS_COLOR.get(status, 0x6b7280),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name='👤 Customer', value=f'`{uname}`', inline=True)
    embed.add_field(name='💰 Amount',   value=f'**₹{final}**', inline=True)
    embed.add_field(name='📅 Date',     value=date or '—', inline=True)
    embed.add_field(name='📦 Items',    value=fmt_items(order.get('items',[])), inline=False)
    if utr: embed.add_field(name='🔖 UTR',        value=f'`{utr}`', inline=True)
    if pid: embed.add_field(name='💳 Payment ID', value=f'`{pid}`', inline=True)
    ptero = order.get('ptero_provisioned', False)
    cp    = order.get('cpanel_provisioned', False)
    embed.add_field(name='⚙️ Provision', value='✅ Done' if (ptero or cp) else '⏳ Pending', inline=True)
    embed.set_footer(text='StrengthCloud Bot')
    return embed

# ── UI Buttons (attached to DM notifications) ─────────────────────
class OrderButtons(ui.View):
    def __init__(self, order_id: int):
        super().__init__(timeout=None)
        self.order_id = order_id

    async def _disable(self, interaction):
        for c in self.children: c.disabled = True
        await interaction.message.edit(view=self)

    @ui.button(label='✅ Accept & Provision', style=discord.ButtonStyle.success, custom_id='btn_accept')
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        if not is_owner(interaction.user.id):
            await interaction.response.send_message('❌ Not authorized.', ephemeral=True); return
        await interaction.response.defer()
        msg = await interaction.followup.send('⏳ Accepting and provisioning...')
        res = api('POST', f'/bot/order/{self.order_id}/accept')
        if res.get('success'):
            lines  = []
            ptero  = res.get('provision_ptero') or {}
            cpanel = res.get('provision_cpanel') or {}
            if ptero:
                if ptero.get('provisioned'):
                    lines.append(f"⛏️ **MC Server Created**\n> 🔗 `{ptero.get('panel_url','')}`\n> 👤 `{ptero.get('username','')}` 🔑 `{ptero.get('password','')}`")
                else:
                    lines.append(f"⛏️ MC Failed: {ptero.get('reason','?')}")
            if cpanel:
                if cpanel.get('provisioned'):
                    lines.append(f"🖥️ **VPS Created**\n> 🌐 `{cpanel.get('cp_url','')}`\n> 👤 `{cpanel.get('cp_username','')}` 🔑 `{cpanel.get('cp_password','')}`\n> 💻 OS: `{cpanel.get('os','')}`")
                else:
                    lines.append(f"🖥️ VPS Failed: {cpanel.get('error','?')}")
            embed = discord.Embed(title=f'✅ Order #{self.order_id} Accepted',
                                  description='\n\n'.join(lines) or 'Active (no auto-provision configured)',
                                  color=0x10b981, timestamp=discord.utils.utcnow())
            await msg.edit(content='', embed=embed)
            await self._disable(interaction)
        else:
            await msg.edit(content=f'❌ {res.get("error","Failed")}')

    @ui.button(label='❌ Reject', style=discord.ButtonStyle.danger, custom_id='btn_reject')
    async def reject(self, interaction: discord.Interaction, button: ui.Button):
        if not is_owner(interaction.user.id):
            await interaction.response.send_message('❌ Not authorized.', ephemeral=True); return
        await interaction.response.send_modal(RejectModal(self.order_id, self))

    @ui.button(label='⚙️ Provision Only', style=discord.ButtonStyle.primary, custom_id='btn_prov')
    async def provision(self, interaction: discord.Interaction, button: ui.Button):
        if not is_owner(interaction.user.id):
            await interaction.response.send_message('❌ Not authorized.', ephemeral=True); return
        await interaction.response.defer()
        msg = await interaction.followup.send('⏳ Provisioning...')
        res = api('POST', f'/bot/order/{self.order_id}/provision')
        if res.get('success'):
            r = res.get('result', {}); lines = []
            p = r.get('ptero',{}); c = r.get('cpanel',{})
            if p: lines.append(f"⛏️ MC: {'✅ `'+p.get('panel_url','')+'`' if p.get('provisioned') else '❌ '+p.get('reason','?')}")
            if c: lines.append(f"🖥️ VPS: {'✅ `'+c.get('cp_url','')+'`' if c.get('provisioned') else '❌ '+c.get('error','?')}")
            embed = discord.Embed(title=f'⚙️ Order #{self.order_id} Provisioned',
                                  description='\n'.join(lines) or 'Done', color=0x8b5cf6,
                                  timestamp=discord.utils.utcnow())
            await msg.edit(content='', embed=embed)
        else:
            await msg.edit(content=f'❌ {res.get("error","?")}')

    @ui.button(label='📋 Details', style=discord.ButtonStyle.secondary, custom_id='btn_detail')
    async def details(self, interaction: discord.Interaction, button: ui.Button):
        if not is_owner(interaction.user.id):
            await interaction.response.send_message('❌ Not authorized.', ephemeral=True); return
        await interaction.response.defer(ephemeral=True)
        res = api('GET', f'/bot/order/{self.order_id}/info')
        if 'order' in res:
            embed = order_embed(res['order'], title=f'📋 Full Details — Order #{self.order_id}')
            pp = res['order'].get('ptero_password','')
            if pp: embed.add_field(name='🔑 Ptero Pass', value=f'`{pp}`', inline=True)
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(f'❌ {res.get("error","?")}', ephemeral=True)


class RejectModal(ui.Modal, title='Reject Order'):
    reason = ui.TextInput(label='Reason', placeholder='Payment not received...', required=False, max_length=200)
    def __init__(self, oid, view):
        super().__init__(); self.oid = oid; self.pview = view
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        res = api('POST', f'/bot/order/{self.oid}/reject', json={'reason': self.reason.value or 'Rejected'})
        if res.get('success'):
            embed = discord.Embed(title=f'❌ Order #{self.oid} Rejected',
                                  description=f'Reason: {self.reason.value or "No reason given"}',
                                  color=0xef4444, timestamp=discord.utils.utcnow())
            await interaction.followup.send(embed=embed)
            for c in self.pview.children: c.disabled = True
            await interaction.message.edit(view=self.pview)
        else:
            await interaction.followup.send(f'❌ {res.get("error","?")}')


# ── Bot ───────────────────────────────────────────────────────────
intents                 = discord.Intents.default()
intents.message_content = True
client                  = discord.Client(intents=intents)


async def handle_command(message):
    content = message.content.strip()
    if not content.startswith(PREFIX): return
    if not is_owner(message.author.id):
        await message.reply('❌ Only the site owner can use bot commands.'); return

    parts = content[len(PREFIX):].split()
    if not parts: return
    cmd  = parts[0].lower()
    args = parts[1:]

    # ══════════════════════════════════════════════════════════════
    # .help
    # ══════════════════════════════════════════════════════════════
    if cmd == 'help':
        embed = discord.Embed(
            title='🤖 StrengthCloud Bot — Command List',
            description='**Prefix:** `.` (dot)  |  Only the owner can run these',
            color=0x8b5cf6,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name='​', value='━━━━━━━━━━━━━━━━━━━━━━━', inline=False)

        embed.add_field(name='📦  ORDERS', value=(
            '`  .orders                ` — last 10 orders\n'
            '`  .orders pending        ` — filter by status\n'
            '`  .orders active         ` — only active\n'
            '`  .order <id>            ` — full order details\n'
            '`  .accept <id>           ` — ✅ accept + provision\n'
            '`  .reject <id> [reason]  ` — ❌ reject order\n'
            '`  .provision <id>        ` — ⚙️ provision only'
        ), inline=False)

        embed.add_field(name='​', value='━━━━━━━━━━━━━━━━━━━━━━━', inline=False)

        embed.add_field(name='👥  USERS', value=(
            '`  .users                 ` — list all users\n'
            '`  .users <search>        ` — search by name/email\n'
            '`  .user <id>             ` — user details + orders\n'
            '`  .suspend <id>          ` — 🔴/🟢 toggle suspend\n'
            '`  .makeadmin <id>        ` — 👑 give admin role\n'
            '`  .revokeadmin <id>      ` — remove admin role\n'
            '`  .deluser <id>          ` — 🗑️ delete user'
        ), inline=False)

        embed.add_field(name='​', value='━━━━━━━━━━━━━━━━━━━━━━━', inline=False)

        embed.add_field(name='🖥️  SERVERS (Pterodactyl)', value=(
            '`  .servers               ` — list all servers\n'
            '`  .susserver <id>        ` — ⛔ suspend server\n'
            '`  .unsusserver <id>      ` — ▶️  unsuspend server\n'
            '`  .delserver <id>        ` — 🗑️ delete server'
        ), inline=False)

        embed.add_field(name='​', value='━━━━━━━━━━━━━━━━━━━━━━━', inline=False)

        embed.add_field(name='🎟️  COUPONS', value=(
            '`  .coupons                        ` — list all\n'
            '`  .addcoupon <CODE> <amt> percent  ` — % discount\n'
            '`  .addcoupon <CODE> <amt> flat     ` — ₹ flat off\n'
            '`  .delcoupon <CODE>                ` — delete coupon'
        ), inline=False)

        embed.add_field(name='​', value='━━━━━━━━━━━━━━━━━━━━━━━', inline=False)

        embed.add_field(name='📊  STATS', value=(
            '`  .stats                 ` — revenue + overview\n'
            '`  .help                  ` — show this menu'
        ), inline=False)

        embed.add_field(name='​', value='━━━━━━━━━━━━━━━━━━━━━━━', inline=False)

        embed.add_field(name='💡  Examples', value=(
            '`.accept 73438`\n'
            '`.reject 73438 Payment not received`\n'
            '`.addcoupon SAVE20 20 percent`\n'
            '`.users blackgaming`\n'
            '`.order 73438`'
        ), inline=False)

        embed.set_footer(text='StrengthCloud Bot • All actions directly from Discord')
        await message.reply(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # .stats
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'stats':
        res = api('GET', '/bot/stats')
        if 'error' in res:
            await message.reply(f'❌ {res["error"]}'); return
        embed = discord.Embed(title='📊 StrengthCloud Stats', color=0x8b5cf6, timestamp=discord.utils.utcnow())
        embed.add_field(name='👥 Users',    value=f'`{res["total_users"]}` total / `{res["active_users"]}` active', inline=True)
        embed.add_field(name='📦 Orders',   value=f'`{res["total_orders"]}` total', inline=True)
        embed.add_field(name='⏳ Pending',  value=f'`{res["pending_orders"]}`', inline=True)
        embed.add_field(name='🚀 Active',   value=f'`{res["active_orders"]}`', inline=True)
        embed.add_field(name='💰 Revenue',  value=f'**₹{res["total_revenue"]}**', inline=True)
        await message.reply(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # .orders [status]
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'orders':
        status = args[0] if args else ''
        path   = '/bot/orders?limit=10' + (f'&status={status}' if status else '')
        res    = api('GET', path)
        if 'error' in res:
            await message.reply(f'❌ {res["error"]}'); return
        orders = res.get('orders', [])
        if not orders:
            await message.reply('📭 No orders found.'); return
        embed = discord.Embed(
            title=f'📦 Orders {("("+status+")") if status else "— Latest 10"}',
            color=0x8b5cf6, timestamp=discord.utils.utcnow()
        )
        for o in orders:
            em = STATUS_EMOJI.get(o.get('status',''), '📦')
            embed.add_field(
                name=f'{em} #{o["id"]} — {o.get("username","?")} — ₹{o.get("final",0)}',
                value=f'`{o.get("status","?")}` via `{o.get("payment_method","?").upper()}` | {o.get("date","")}',
                inline=False
            )
        embed.set_footer(text=f'Total orders in DB: {res.get("total",0)}')
        await message.reply(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # .order <id>
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'order':
        if not args:
            await message.reply('Usage: `.order <id>`'); return
        res = api('GET', f'/bot/order/{args[0]}/info')
        if 'error' in res:
            await message.reply(f'❌ {res["error"]}'); return
        embed = order_embed(res['order'])
        pp = res['order'].get('ptero_password','')
        if pp: embed.add_field(name='🔑 Ptero Pass', value=f'`{pp}`', inline=True)
        await message.reply(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # .accept <id>
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'accept':
        if not args:
            await message.reply('Usage: `.accept <order_id>`'); return
        msg = await message.reply('⏳ Accepting and provisioning...')
        res = api('POST', f'/bot/order/{args[0]}/accept')
        if res.get('success'):
            lines  = []
            ptero  = res.get('provision_ptero') or {}
            cpanel = res.get('provision_cpanel') or {}
            if ptero:
                if ptero.get('provisioned'):
                    lines.append(f"⛏️ **MC Server**\n> Panel: `{ptero.get('panel_url','')}`\n> User: `{ptero.get('username','')}` Pass: `{ptero.get('password','')}`")
                else:
                    lines.append(f"⛏️ MC Failed: {ptero.get('reason','?')}")
            if cpanel:
                if cpanel.get('provisioned'):
                    lines.append(f"🖥️ **VPS**\n> URL: `{cpanel.get('cp_url','')}`\n> User: `{cpanel.get('cp_username','')}` Pass: `{cpanel.get('cp_password','')}`\n> OS: `{cpanel.get('os','')}`")
                else:
                    lines.append(f"🖥️ VPS Failed: {cpanel.get('error','?')}")
            embed = discord.Embed(
                title=f'✅ Order #{args[0]} Accepted & Provisioned',
                description='\n\n'.join(lines) or 'Status set to Active (no auto-provision configured)',
                color=0x10b981, timestamp=discord.utils.utcnow()
            )
            await msg.edit(content='', embed=embed)
        else:
            await msg.edit(content=f'❌ {res.get("error","Failed")}')

    # ══════════════════════════════════════════════════════════════
    # .reject <id> [reason]
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'reject':
        if not args:
            await message.reply('Usage: `.reject <order_id> [reason]`'); return
        reason = ' '.join(args[1:]) or 'Rejected by admin'
        res    = api('POST', f'/bot/order/{args[0]}/reject', json={'reason': reason})
        if res.get('success'):
            embed = discord.Embed(title=f'❌ Order #{args[0]} Rejected',
                                  description=f'Reason: {reason}', color=0xef4444,
                                  timestamp=discord.utils.utcnow())
            await message.reply(embed=embed)
        else:
            await message.reply(f'❌ {res.get("error","Failed")}')

    # ══════════════════════════════════════════════════════════════
    # .provision <id>
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'provision':
        if not args:
            await message.reply('Usage: `.provision <order_id>`'); return
        msg = await message.reply('⏳ Provisioning...')
        res = api('POST', f'/bot/order/{args[0]}/provision')
        if res.get('success'):
            r = res.get('result', {}); lines = []
            p = r.get('ptero',{}); c = r.get('cpanel',{})
            if p: lines.append(f"⛏️ MC: {'✅ `'+p.get('panel_url','')+'`' if p.get('provisioned') else '❌ '+p.get('reason','?')}")
            if c: lines.append(f"🖥️ VPS: {'✅ `'+c.get('cp_url','')+'`' if c.get('provisioned') else '❌ '+c.get('error','?')}")
            embed = discord.Embed(title=f'⚙️ Order #{args[0]} Provisioned',
                                  description='\n'.join(lines) or 'Done', color=0x8b5cf6,
                                  timestamp=discord.utils.utcnow())
            await msg.edit(content='', embed=embed)
        else:
            await msg.edit(content=f'❌ {res.get("error","?")}')

    # ══════════════════════════════════════════════════════════════
    # .users [search]
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'users':
        q   = args[0] if args else ''
        res = api('GET', f'/bot/users' + (f'?q={q}' if q else ''))
        if 'error' in res:
            await message.reply(f'❌ {res["error"]}'); return
        users = res.get('users', [])
        if not users:
            await message.reply('📭 No users found.'); return
        embed = discord.Embed(title=f'👥 Users {("— search: "+q) if q else ""}',
                              color=0x8b5cf6, timestamp=discord.utils.utcnow())
        for u in users[:15]:
            role_tag = ' 👑' if u.get('role') == 'admin' else ''
            status   = '🟢' if u.get('active', True) else '🔴'
            embed.add_field(
                name=f'{status} [{u["id"]}] {u["username"]}{role_tag}',
                value=f'`{u["email"]}` | Joined: {u.get("joined","?")}',
                inline=False
            )
        embed.set_footer(text=f'Total: {res.get("total",0)} users | Use ID in commands')
        await message.reply(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # .user <id>
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'user':
        if not args:
            await message.reply('Usage: `.user <user_id>`'); return
        res   = api('GET', f'/bot/users?q={args[0]}')
        users = res.get('users', [])
        user  = next((u for u in users if str(u['id']) == args[0]), None)
        if not user:
            await message.reply(f'❌ User `{args[0]}` not found'); return
        ores   = api('GET', '/bot/orders?limit=50')
        orders = [o for o in ores.get('orders', []) if str(o.get('user_id','')) == args[0] or o.get('username','') == user['username']]
        embed  = discord.Embed(title=f'👤 {user["username"]}',
                               color=0x8b5cf6 if user.get('active',True) else 0xef4444,
                               timestamp=discord.utils.utcnow())
        embed.add_field(name='ID',     value=f'`{user["id"]}`', inline=True)
        embed.add_field(name='Email',  value=f'`{user["email"]}`', inline=True)
        embed.add_field(name='Role',   value=f'`{user.get("role","user")}`', inline=True)
        embed.add_field(name='Status', value='🟢 Active' if user.get('active',True) else '🔴 Suspended', inline=True)
        embed.add_field(name='Joined', value=user.get('joined','?'), inline=True)
        embed.add_field(name='Name',   value=f'{user.get("fname","")} {user.get("lname","")}', inline=True)
        if orders:
            ol = '\n'.join([f"`#{o['id']}` {STATUS_EMOJI.get(o.get('status',''),'📦')} ₹{o.get('final',0)}" for o in orders[:8]])
            embed.add_field(name=f'📦 Orders ({len(orders)})', value=ol, inline=False)
        await message.reply(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # .suspend <id>
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'suspend':
        if not args:
            await message.reply('Usage: `.suspend <user_id>`'); return
        res = api('POST', f'/bot/user/{args[0]}/toggle')
        if res.get('success'):
            st = '🟢 Activated' if res.get('active') else '🔴 Suspended'
            await message.reply(f'{st} user **{res.get("username","?")}** `#{args[0]}`')
        else:
            await message.reply(f'❌ {res.get("error","Failed")}')

    # ══════════════════════════════════════════════════════════════
    # .makeadmin / .revokeadmin <id>
    # ══════════════════════════════════════════════════════════════
    elif cmd in ('makeadmin', 'revokeadmin'):
        if not args:
            await message.reply(f'Usage: `.{cmd} <user_id>`'); return
        role = 'admin' if cmd == 'makeadmin' else 'user'
        res  = api('POST', f'/bot/user/{args[0]}/role', json={'role': role})
        if res.get('success'):
            emoji = '👑' if role == 'admin' else '👤'
            await message.reply(f'{emoji} **{res.get("username","?")}** is now `{role}`')
        else:
            await message.reply(f'❌ {res.get("error","Failed")}')

    # ══════════════════════════════════════════════════════════════
    # .deluser <id>
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'deluser':
        if not args:
            await message.reply('Usage: `.deluser <user_id>`'); return
        client._pending_del_user = args[0]
        await message.reply(f'⚠️ Delete user `#{args[0]}`? Send `.confirmuser {args[0]}` within 15s to confirm.')
        await asyncio.sleep(15)
        client._pending_del_user = None

    elif cmd == 'confirmuser':
        uid = getattr(client, '_pending_del_user', None)
        if uid and args and args[0] == uid:
            res = api('POST', f'/bot/user/{uid}/delete')
            if res.get('success'):
                await message.reply(f'🗑️ User **{res.get("username","?")}** `#{uid}` deleted.')
            else:
                await message.reply(f'❌ {res.get("error","Failed")}')
            client._pending_del_user = None
        else:
            await message.reply('⚠️ No pending delete or wrong ID.')

    # ══════════════════════════════════════════════════════════════
    # .servers
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'servers':
        msg = await message.reply('⏳ Fetching from panel...')
        res = api('GET', '/bot/servers')
        if 'error' in res:
            await msg.edit(content=f'❌ {res["error"]}'); return
        servers = res.get('servers', [])
        if not servers:
            await msg.edit(content='📭 No servers found.'); return
        embed = discord.Embed(
            title=f'🖥️ Pterodactyl Servers ({len(servers)})',
            description='Use the **numeric ID** (left column) with `.susserver`, `.unsusserver`, `.delserver`',
            color=0x8b5cf6, timestamp=discord.utils.utcnow()
        )
        for s in servers[:20]:
            ram  = f'{s["memory"]//1024}GB' if s.get('memory',0) >= 1024 else f'{s.get("memory",0)}MB'
            susp = '⛔ SUSPENDED' if s.get('suspended') else '✅ RUNNING'
            embed.add_field(
                name=f'{susp}  •  ID: **{s["id"]}**',
                value=f'📛 {s["name"]}\n🔑 Identifier: `{s.get("identifier","?")}`\n💾 RAM: `{ram}`',
                inline=True
            )
        embed.set_footer(text=f'✅ Use numeric ID e.g. .susserver {servers[0]["id"] if servers else "123"}')
        await msg.edit(content='', embed=embed)

    # ══════════════════════════════════════════════════════════════
    # .susserver / .unsusserver <id>
    # ══════════════════════════════════════════════════════════════
    elif cmd in ('susserver', 'unsusserver'):
        if not args:
            await message.reply(f'Usage: `.{cmd} <server_id>`'); return
        suspend = cmd == 'susserver'
        res     = api('POST', f'/bot/server/{args[0]}/suspend', json={'suspend': suspend})
        if res.get('success'):
            emoji = '⛔' if suspend else '✅'
            await message.reply(f'{emoji} Server `#{args[0]}` {"suspended" if suspend else "unsuspended"}.')
        else:
            await message.reply(f'❌ {res.get("error","Failed")}')

    # ══════════════════════════════════════════════════════════════
    # .delserver <id>
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'delserver':
        if not args:
            await message.reply('Usage: `.delserver <server_id>`'); return
        client._pending_del_srv = args[0]
        await message.reply(f'⚠️ Delete server `#{args[0]}`? Send `.confirmserver {args[0]}` within 15s.')
        await asyncio.sleep(15)
        client._pending_del_srv = None

    elif cmd == 'confirmserver':
        sid = getattr(client, '_pending_del_srv', None)
        if sid and args and args[0] == sid:
            res = api('POST', f'/bot/server/{sid}/delete')
            if res.get('success'):
                await message.reply(f'🗑️ Server `#{sid}` deleted from panel.')
            else:
                await message.reply(f'❌ {res.get("error","Failed")}')
            client._pending_del_srv = None
        else:
            await message.reply('⚠️ No pending delete or wrong ID.')

    # ══════════════════════════════════════════════════════════════
    # .coupons
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'coupons':
        data    = load_data()
        coupons = data.get('coupons', [])
        if not coupons:
            await message.reply('📭 No coupons yet.'); return
        embed = discord.Embed(title='🎟️ Active Coupons', color=0x8b5cf6)
        for c in coupons:
            sym = '%' if c['type'] == 'percent' else '₹'
            val = f'**{sym}{c["discount"]}** off | {"🟢 Active" if c.get("active") else "🔴 Disabled"}'
            embed.add_field(name=f'`{c["code"]}`', value=val, inline=True)
        await message.reply(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # .addcoupon <CODE> <amount> [percent|flat]
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'addcoupon':
        if len(args) < 2:
            await message.reply('Usage: `.addcoupon <CODE> <amount> [percent|flat]`'); return
        code  = args[0].upper()
        try:    amount = int(args[1])
        except: await message.reply('❌ Amount must be a number'); return
        ctype = args[2].lower() if len(args) > 2 else 'percent'
        if ctype not in ('percent', 'flat'):
            await message.reply('❌ Type must be `percent` or `flat`'); return
        res = api('POST', '/bot/coupon/add', json={'code': code, 'discount': amount, 'type': ctype})
        if res.get('success'):
            sym = '%' if ctype == 'percent' else '₹'
            await message.reply(f'✅ Coupon **{code}** created — **{sym}{amount}** {ctype}')
        else:
            await message.reply(f'❌ {res.get("error","Failed")}')

    # ══════════════════════════════════════════════════════════════
    # .delcoupon <CODE>
    # ══════════════════════════════════════════════════════════════
    elif cmd == 'delcoupon':
        if not args:
            await message.reply('Usage: `.delcoupon <CODE>`'); return
        res = api('POST', '/bot/coupon/delete', json={'code': args[0].upper()})
        if res.get('success'):
            await message.reply(f'🗑️ Coupon **{args[0].upper()}** deleted.')
        else:
            await message.reply(f'❌ {res.get("error","Failed")}')

    # ══════════════════════════════════════════════════════════════
    # Unknown command
    # ══════════════════════════════════════════════════════════════
    else:
        await message.reply(f'❓ Unknown command `.{cmd}`\nType `.help` to see all available commands.')


# ── Events ────────────────────────────────────────────────────────
@client.event
async def on_ready():
    cfg = get_cfg()
    print(f'✅ Bot online: {client.user}')
    print(f'   Owner ID : {cfg.get("owner_id","NOT SET — set in Admin Panel")}')
    print(f'   Site URL : {cfg.get("site_url","http://localhost:5000")}')
    print(f'   Prefix   : {PREFIX}  (type .help in DM)')
    check_orders.start()

@client.event
async def on_message(message):
    if message.author.bot: return
    if message.content.startswith(PREFIX):
        await handle_command(message)

@tasks.loop(seconds=POLL_INTERVAL)
async def check_orders():
    try:
        cfg      = get_cfg()
        owner_id = cfg.get('owner_id', '')
        if not owner_id: return
        owner    = await client.fetch_user(int(owner_id))
        data     = load_data()
        notified = load_notified()
        for order in data.get('orders', []):
            oid = str(order.get('id', ''))
            if oid in notified: continue
            embed = order_embed(order)
            view  = OrderButtons(order_id=int(oid))
            try:
                await owner.send(embed=embed, view=view)
                notified.add(oid)
                save_notified(notified)
                print(f'📨 DM sent: order #{oid}')
            except discord.Forbidden:
                print(f'❌ Cannot DM owner (order #{oid})')
            except Exception as e:
                print(f'❌ DM error #{oid}: {e}')
    except Exception as e:
        print(f'⚠️ check_orders: {e}')

@check_orders.before_loop
async def before_check():
    await client.wait_until_ready()

# ── Entry ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    cfg   = get_cfg()
    token = cfg.get('bot_token', '')
    if not token:
        print('❌ No bot_token — set it in Admin Panel → Discord Bot')
        exit(1)
    print('🤖 StrengthCloud Bot starting...')
    print(f'   Type .help in DM to see all commands')
    client.run(token)
