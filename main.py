import configparser
import MySQLdb
from hashlib import sha1

import discord
from discord.ui import Button, InputText, Modal, Select, View
from discord.ext import commands

config = configparser.ConfigParser()
config.read('config.ini')

secret_config = configparser.ConfigParser()
secret_config.read('secret.ini')

server_name = config.get('Server', 'name')
discord.http.API_VERSION = '9' # necessary to read messages from the channel.

bot = commands.Bot(command_prefix=config.get('Bot', 'command_prefix'))

class MyModal(Modal):
    def __init__(self) -> None:
        super().__init__(title="Registration")
        self.add_item(InputText(label="Desired Account Username", placeholder="Type username here."))
        self.add_item(InputText(label="Desired Account Password", placeholder="Type password here.", min_length=4))

    async def callback(self, interaction: discord.Interaction):

        # Initialize database
        db = MySQLdb.connect(host=config.get('Database', 'host'),
                                user=config.get('Database', 'user'),
                                password=config.get('Database', 'password'),
                                port=int(config.get('Database', 'port')))

        username = self.children[0].value
        password = self.children[1].value

        cur = db.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM ' + config.get('Database', 'auth_db') + '.account WHERE username = %s', (username,)) 
        account = cur.fetchone()

        if account:
            response = 'Account already exists!'
        else:
            sha_pass_hash = sha1((username + ":" + password).upper().encode('utf-8')).hexdigest()
            cur.execute('INSERT INTO realmd.account (username, sha_pass_hash, expansion) VALUES (%s, %s, %s)', (username, sha_pass_hash, 4))
            db.commit()
            response = 'You have successfully registered!'
            
        # Close connection
        cur.close()

        await interaction.response.send_message(response, ephemeral=True)

@bot.command()
async def summon(ctx):
    embed = discord.Embed(description=f"Welcome to {server_name}'s Discord server. Click below to register! Or type '/register'!", color=0x00ff00)
    embed.set_image(url=config.get("Server", "banner_url"))
    embed.set_author(name=ctx.bot.user.name, icon_url=ctx.bot.user.display_avatar)

    button1 = Button(label="Register", style=discord.ButtonStyle.primary)
    button2 = Button(label="Our Website", url=config.get("Server", "website_url"))

    async def register(interaction):

        modal = MyModal()
        await interaction.response.send_modal(modal)
        

    button1.callback = register

    view = View()
    view.add_item(button1)
    view.add_item(button2)

    if config.getboolean("Bot", "purge_messages"):
        await ctx.message.channel.purge(limit=10000)

    await ctx.send(view=view, embed=embed)

@bot.slash_command(name="register")
async def register(ctx):
    modal = MyModal()
    await ctx.interaction.response.send_modal(modal)

bot.run(config.get('Bot', 'token'))