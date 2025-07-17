import discord
from discord.ext import commands
from discord import app_commands, ui
import random
import threading
from flask import Flask
import os



# ==== CONFIGURATION ====
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1345400542540595270
SALON_ROUE_ID = 1395123963868479648
SALON_LOGS_ID = 1395125370608554064
SALON_LOGS_SERVICE_ID = 1365453600578605136
GIF_URL = "https://files.catbox.moe/xqs72u.mp4"

# ==== DISCORD BOT SETUP ====
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ==== FLASK SERVEUR POUR UPTIME ====
app = Flask("")

@app.route("/")
def home():
    return "Bot actif."

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# ==== RÉCOMPENSES PONDÉRÉES ====
rewards = [
    ("100€", 20),
    ("Verre d'eau", 20),
    ("200€", 20),
    ("500€", 15),
    ("Rien", 15),
    ("*2 sur la prochaine mise", 5),
    ("1000€", 3),
    ("Une photo avec le PDG", 1),
    ("Une visite du casino", 1),
]

def tirer_gain():
    pool = []
    for reward, chance in rewards:
        pool.extend([reward] * chance)
    return random.choice(pool)

# ==== VUE POUR LA ROUE ====
class VueRoue(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.joueurs_deja_passes = set()

    @discord.ui.button(label="🎰Tourner la roue", style=discord.ButtonStyle.green, custom_id="tourner_roue")
    async def tourner(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id

        if user_id in self.joueurs_deja_passes:
            await interaction.response.send_message("❌ Tu as déjà tourné la roue aujourd’hui !", ephemeral=True)
            return

        self.joueurs_deja_passes.add(user_id)
        gain = tirer_gain()

        embed = discord.Embed(title="🎁 Votre gain", color=discord.Color.gold())
        embed.add_field(name="Gain", value=gain, inline=False)
        embed.add_field(name="🎉", value="Félicitations ! Venez récupérer votre prix au casino.", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

        log_channel = bot.get_channel(SALON_LOGS_ID)
        if log_channel:
            await log_channel.send(f"🎡 {interaction.user.name} a tourné la roue et a gagné : **{gain}**")

# ==== COMMANDE POUR LANCER LA ROUE ====
@bot.tree.command(name="resetroue", description="Remet la roue à zéro", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(administrator=True)
async def resetroue(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title="🎡 Roue journalière",
        description="Clique sur le bouton ci-dessous pour tenter ta chance !",
        color=discord.Color.blue()
    )
    embed.set_image(url=GIF_URL)

    channel = bot.get_channel(SALON_ROUE_ID)
    if channel:
        await channel.send(embed=embed, view=VueRoue())
        await interaction.followup.send("✅ Roue relancée dans 🌡｜tourner-la-roue.", ephemeral=True)
    else:
        await interaction.followup.send("❌ Salon introuvable.", ephemeral=True)

# ==== COMMANDE POUR VOIR LE GAIN D’UN JOUEUR ====
@bot.tree.command(name="gains", description="Voir le gain d’un joueur", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(joueur="Le joueur à vérifier")
@app_commands.checks.has_permissions(administrator=True)
async def gains(interaction: discord.Interaction, joueur: discord.Member):
    await interaction.response.defer(ephemeral=True)

    log_channel = bot.get_channel(SALON_LOGS_ID)
    if log_channel:
        await interaction.followup.send(f"🔍 Regarde dans {log_channel.mention} pour les logs de {joueur.name}.", ephemeral=True)
    else:
        await interaction.followup.send("❌ Salon des logs introuvable.", ephemeral=True)

# ==== MODAL FIN DE SERVICE ====
class FinServiceModal(ui.Modal, title="📋 Rapport de fin de service"):
    nb_clients = ui.TextInput(label="👥 Nombre de clients", placeholder="Ex: 7", required=True)
    argent_depart = ui.TextInput(label="💸 Argent au départ", placeholder="Ex: 100K€", required=True)
    argent_fin = ui.TextInput(label="💰 Argent à la fin", placeholder="Ex: 360K€", required=True)
    temps_service = ui.TextInput(label="⏱️ Temps de service (HH:MM)", placeholder="Ex: 02:15", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = bot.get_channel(SALON_LOGS_ID)
        embed = discord.Embed(title="📝 Fin de service", color=discord.Color.green())
        embed.add_field(name="👤 Nom", value=interaction.user.name, inline=False)
        embed.add_field(name="👥 Nombre de clients", value=self.nb_clients.value, inline=True)
        embed.add_field(name="💸 Argent départ", value=self.argent_depart.value, inline=True)
        embed.add_field(name="💰 Argent fin", value=self.argent_fin.value, inline=True)
        embed.add_field(name="⏱️ Temps de service", value=self.temps_service.value, inline=True)

        await interaction.response.send_message("✅ Ton rapport a bien été envoyé !", ephemeral=True)
        await log_channel.send(embed=embed)

# ==== BOUTONS POUR SERVICE ====
class FinDeServiceView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="⛔ Fin de service", style=discord.ButtonStyle.danger, custom_id="fin_service_btn")
    async def fin_service(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FinServiceModal())

class PriseDeServiceView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="📢 Prise de service", style=discord.ButtonStyle.success, custom_id="prise_service_btn")
    async def prise_service(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = bot.get_channel(SALON_LOGS_SERVICE_ID)
        nom = interaction.user.name
        await log_channel.send(f"✅ Le joueur **{nom}** a pris son service.")
        await interaction.response.send_message(
            "🟢 Tu es maintenant en service.\nQuand tu veux terminer, clique sur le bouton ci-dessous.",
            view=FinDeServiceView(),
            ephemeral=True)

# ==== COMMANDE DE SERVICE ====
@bot.tree.command(name="service", description="Envoyer le bouton de prise de service")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def service(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Clique sur le bouton pour prendre ton service :", view=PriseDeServiceView())

# ==== ERREURS COMMANDES ====
@resetroue.error
@gains.error
async def permission_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("🚫 Tu n'as pas les permissions administrateur.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Une erreur est survenue.", ephemeral=True)

# ==== SYNCHRO DES COMMANDES ====
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    synced = await bot.tree.sync(guild=guild)
    print(f"✅ {bot.user} est connecté.")
    print(f"🔧 {len(synced)} commandes synchronisées pour la guilde {GUILD_ID}.")

# ==== LANCEMENT ====
keep_alive()
bot.run(TOKEN)
