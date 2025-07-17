import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
import threading

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Keep-alive via Flask (nécessaire pour Render ou UptimeRobot)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Discord actif 🚀"

def run():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run).start()

# === Slash Commande : 🎡｜roue-de-la-fortune ===

class RouletteButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎡 Tourner la roue", style=discord.ButtonStyle.green, custom_id="spin_wheel")
    async def spin(self, interaction: discord.Interaction, button: discord.ui.Button):
        import random
        multiplicateur = random.choice([0, 0.5, 1, 1.5, 2, 3, 5, 10])
        await interaction.response.send_message(
            f"🎰 La roue a tourné... **x{multiplicateur}** !", ephemeral=True
        )

@tree.command(name="roue", description="🎡 Jouer à la roue de la fortune")
async def roulette(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎡｜Roue de la Fortune",
        description="Clique sur **🎡 Tourner la roue** pour gagner un multiplicateur !\n"
                    "__Disponible une fois par jour.__\n"
                    "Toute tentative de triche sera sanctionnée d'une amende de 1000€ 💸",
        color=0xFFD700
    )
    await interaction.response.send_message(embed=embed, view=RouletteButton())

# === Slash Commande : ✅｜service ===

class ServiceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Prendre son service", style=discord.ButtonStyle.green, custom_id="start_service")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"{interaction.user.mention} est maintenant en service ✅", ephemeral=False)

@tree.command(name="service", description="✅ Prendre son service")
async def service(interaction: discord.Interaction):
    embed = discord.Embed(
        title="✅｜Prise de Service",
        description="Clique sur **Prendre son service** pour commencer ta journée !",
        color=0x00FF00
    )
    await interaction.response.send_message(embed=embed, view=ServiceView())

# === Slash Commande : ❌｜fin ===

class FinServiceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="❌ Fin de service", style=discord.ButtonStyle.red, custom_id="end_service")
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"{interaction.user.mention} a terminé son service ❌", ephemeral=False)

@tree.command(name="fin", description="❌ Fin de service")
async def fin(interaction: discord.Interaction):
    embed = discord.Embed(
        title="❌｜Fin de Service",
        description="Clique sur **Fin de service** pour arrêter ton travail !",
        color=0xFF0000
    )
    await interaction.response.send_message(embed=embed, view=FinServiceView())

# === Événement de synchronisation ===

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Connecté en tant que {bot.user}")

# === Token ===

bot.run("TON_TOKEN_ICI")
