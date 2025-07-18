import discord
from discord.ext import commands
from discord import app_commands, ui
from discord.ui import View, Button, Select # Import manquant corrigé
import random
import threading
from flask import Flask
import os

# ==== CONFIGURATION ====
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1345400542540595270

ANNONCE_CHANNEL_ID = 1345408288618971217  # Salon clients (aussi utilisé pour /sonnette)
SALON_CLIENTS_ID = 1345408288618971217    # Même salon pour la commande sonnette
SALON_CROUPIERS_ID = 1395596646754160671
ROLE_CROUPIER_ID = 1395597067967139983
SALON_BOUTON_ID = 1366439389005348875
STAFF_ROLE_ID = 1345412431278772294
CATEGORY_ID = 1352313661212983417

ROLE_CASINO_ID = 1345597978051739788
ROLE_PAUSE_ID = 1345598189574815754
SALON_ROUE_ID = 1395123963868479648
SALON_LOGS_ID = 1395125370608554064
SALON_LOGS_gains_ID = 1395607093121388586
SALON_LOGS_SERVICE_ID = 1365453600578605136

#GIF_URL = "https://freeimage.host/i/Fj3hfBn"
GIF_URL = "https://raw.githubusercontent.com/Rallou80/Casino/main/royal.png"

# ==== INTENTS & BOT SETUP ====
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==== FLASK KEEP ALIVE ====
app = Flask("")

@app.route("/")
def home():
    return "Bot actif."

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# ==== CLASSE : CasinoControlView (anciennement CasinoView, renommée) ====
class CasinoControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def remove_pause_role(self, interaction):
        pause_role = interaction.guild.get_role(ROLE_PAUSE_ID)
        if pause_role and pause_role in interaction.guild.me.roles:
            await interaction.guild.me.remove_roles(pause_role)

    async def delete_last_royal_announcement(self, channel: discord.TextChannel):
        async for message in channel.history(limit=10):
            if message.author == channel.guild.me and message.embeds:
                embed = message.embeds[0]
                if embed.description and "ROYAL Casino" in embed.description:
                    await message.delete()
                    break

    @discord.ui.button(label="Ouvrir", style=discord.ButtonStyle.success, custom_id="casino_ouvrir")
    async def open_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.remove_pause_role(interaction)
        role = interaction.guild.get_role(ROLE_CASINO_ID)
        if role:
            await interaction.guild.me.add_roles(role)

        embed = discord.Embed(
            title="✅ Annonce d'Ouverture",
            description="Le **ROYAL Casino** ouvre ses portes !\n\nVenez tenter votre chance et décrocher le jackpot ! 🌀💎\n\nLes jeux sont prêts, il ne manque plus que vous. 🍀🔥\n\n**ROYAL Casino.**",
            color=discord.Color.green()
        )
        channel = interaction.guild.get_channel(ANNONCE_CHANNEL_ID)
        if channel:
            await self.delete_last_royal_announcement(channel)
            await channel.send(embed=embed)

        await interaction.response.send_message("✅ Casino ouvert et annonce envoyée.", ephemeral=True)

    @discord.ui.button(label="Fermer", style=discord.ButtonStyle.danger, custom_id="casino_fermer")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.remove_pause_role(interaction)
        role = interaction.guild.get_role(ROLE_CASINO_ID)
        if role:
            await interaction.guild.me.remove_roles(role)

        embed = discord.Embed(
            title="🚫 Annonce de Fermeture",
            description="Le **ROYAL Casino** ferme ses portes pour le moment.\n\nRevenez bientôt pour de nouvelles sensations fortes ! 🌫️🎭\n\nLe repos est nécessaire pour mieux gagner demain ! 🛌💤\n\n**ROYAL Casino.**",
            color=discord.Color.red()
        )
        channel = interaction.guild.get_channel(ANNONCE_CHANNEL_ID)
        if channel:
            await self.delete_last_royal_announcement(channel)
            await channel.send(embed=embed)

        await interaction.response.send_message("🚫 Casino fermé et annonce envoyée.", ephemeral=True)

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.primary, custom_id="casino_pause")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(ROLE_PAUSE_ID)
        if role:
            await interaction.guild.me.add_roles(role)

        embed = discord.Embed(
            title="⏸️ Annonce de Pause",
            description="Le **ROYAL Casino** fait une courte **pause**.\n\nUne petite coupure avant de relancer les machines à fond ! ☕️🎮\n\nRestez à l’écoute, nous reviendrons très bientôt. 💬⏱️\n\n**ROYAL Casino.**",
            color=discord.Color.blurple()
        )
        channel = interaction.guild.get_channel(ANNONCE_CHANNEL_ID)
        if channel:
            await self.delete_last_royal_announcement(channel)
            await channel.send(embed=embed)

        await interaction.response.send_message("⏸️ Pause activée et annonce envoyée.", ephemeral=True)




# =========== Blackjack Game ============
cards = [str(n) for n in range(2, 11)] + ["J", "Q", "K", "A"]
class BlackjackView(discord.ui.View):
    def __init__(self, player, dealer, message, user):
        super().__init__(timeout=None)
        self.player = player
        self.dealer = dealer
        self.message = message
        self.user = user
        self.stopped = False

    def calculate_total(self, hand):
        total, aces = 0, 0
        for card in hand:
            if card in ["J", "Q", "K"]:
                total += 10
            elif card == "A":
                aces += 1
                total += 11
            else:
                total += int(card)
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def blackjack_embed(self):
        return discord.Embed(
            title="🃏 Partie de Blackjack",
            description=(
                f"**Vos cartes :** {' '.join(self.player)}\n"
                f"**Total :** {self.calculate_total(self.player)}\n\n"
                f"**Cartes du croupier :** {' '.join(self.dealer[:1])} ❓"
            ),
            color=discord.Color.gold()
        )

    @discord.ui.button(label="🟢 Tirer", style=discord.ButtonStyle.success)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return await interaction.response.send_message("Tu ne joues pas cette partie.", ephemeral=True)

        self.player.append(random.choice(cards))
        total = self.calculate_total(self.player)
        if total > 21:
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="💥 Vous avez dépassé 21 !",
                    description=(
                        f"**Vos cartes :** {' '.join(self.player)}\nTotal : {total}\n\n"
                        f"Croupier : {' '.join(self.dealer)} ({self.calculate_total(self.dealer)})\n\n**❌ Vous avez perdu !**"
                    ),
                    color=discord.Color.red()
                ),
                view=self.replay_view()
            )
            self.stopped = True
            return
        await interaction.response.edit_message(embed=self.blackjack_embed())

    @discord.ui.button(label="🟡 Rester", style=discord.ButtonStyle.secondary)
    async def stay(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return await interaction.response.send_message("Tu ne joues pas cette partie.", ephemeral=True)

        while self.calculate_total(self.dealer) < 17:
            self.dealer.append(random.choice(cards))

        player_total = self.calculate_total(self.player)
        dealer_total = self.calculate_total(self.dealer)

        if player_total > dealer_total or dealer_total > 21:
            result = "🏆 **Vous avez gagné !**"
            color = discord.Color.green()
        elif player_total < dealer_total:
            result = "❌ **Vous avez perdu !**"
            color = discord.Color.red()
        else:
            result = "🤝 **Égalité !**"
            color = discord.Color.blurple()

        embed = discord.Embed(
            title="🎲 Résultat de la Partie",
            description=(
                f"**Vos cartes :** {' '.join(self.player)} ({player_total})\n"
                f"**Cartes du croupier :** {' '.join(self.dealer)} ({dealer_total})\n\n{result}"
            ),
            color=color
        )
        await interaction.response.edit_message(embed=embed, view=self.replay_view())
        self.stopped = True

    def replay_view(self):
        view = View()
        view.add_item(Button(label="🔁 Rejouer", style=discord.ButtonStyle.primary, custom_id="replay_blackjack"))
        return view

class RetryButton(Button):
    def __init__(self, user):
        super().__init__(label="🔁 Rejouer", style=discord.ButtonStyle.success)
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return await interaction.response.send_message("Ce n’est pas ta partie.", ephemeral=True)

        new_view = RouletteEuropeenneView(self.user)
        embed = discord.Embed(
            title="🎡 Nouvelle Partie de Roulette Européenne",
            description="Choisissez un numéro **ou** une couleur, puis cliquez sur **Lancer la roulette**.",
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed, view=new_view)


class RouletteEuropeenneView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user
        self.bet_number = None
        self.bet_color = None

        # Sélecteurs plages de numéros
        options_1_12 = [discord.SelectOption(label=str(n), description=f"Parier sur le numéro {n}") for n in range(1, 13)]
        options_13_24 = [discord.SelectOption(label=str(n), description=f"Parier sur le numéro {n}") for n in range(13, 25)]
        options_25_36 = [discord.SelectOption(label=str(n), description=f"Parier sur le numéro {n}") for n in range(25, 37)]

        self.select_number_1 = Select(
            placeholder="1-12",
            options=options_1_12,
            max_values=1,
            custom_id="roulette_num_1"
        )
        self.select_number_2 = Select(
            placeholder="13-24",
            options=options_13_24,
            max_values=1,
            custom_id="roulette_num_2"
        )
        self.select_number_3 = Select(
            placeholder="25-36",
            options=options_25_36,
            max_values=1,
            custom_id="roulette_num_3"
        )
        # Select couleur
        color_options = [
            discord.SelectOption(label="Rouge", description="Parier sur la couleur Rouge", emoji="🔴"),
            discord.SelectOption(label="Noir", description="Parier sur la couleur Noir", emoji="⚫")
        ]
        self.select_color = Select(
            placeholder="Choisissez une couleur",
            options=color_options,
            max_values=1,
            custom_id="roulette_color"
        )

        # Ajouter les sélecteurs
        self.add_item(self.select_number_1)
        self.add_item(self.select_number_2)
        self.add_item(self.select_number_3)
        self.add_item(self.select_color)

        # Bouton Lancer roulette
        self.spin_button = Button(label="🎡 Lancer la roulette", style=discord.ButtonStyle.primary, disabled=True)
        self.add_item(self.spin_button)

        # Assign callbacks
        self.select_number_1.callback = self.number_select_callback
        self.select_number_2.callback = self.number_select_callback
        self.select_number_3.callback = self.number_select_callback
        self.select_color.callback = self.color_select_callback
        self.spin_button.callback = self.spin_callback

    async def number_select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return await interaction.response.send_message("Ce n’est pas ta partie.", ephemeral=True)

        # Récupérer le numéro choisi
        selected_value = None
        for select in [self.select_number_1, self.select_number_2, self.select_number_3]:
            if interaction.data["custom_id"] == select.custom_id:
                selected_value = int(select.values[0])
                break

        if selected_value is None:
            return await interaction.response.send_message("Erreur de sélection.", ephemeral=True)

        # Désactiver les autres sélects et la couleur
        self.bet_number = selected_value
        self.bet_color = None

        # Clear toutes les sélections sauf celle qui vient d'être choisie
        for select in [self.select_number_1, self.select_number_2, self.select_number_3, self.select_color]:
            if select.custom_id != interaction.data["custom_id"]:
                select.disabled = True
            else:
                # Fixe la sélection actuelle pour garder le visuel
                select.disabled = False
                select.options = [
                    discord.SelectOption(label=opt.label, value=opt.value, default=(int(opt.value) == selected_value if opt.value.isdigit() else False))
                    for opt in select.options
                ]

        self.spin_button.disabled = False

        await interaction.response.edit_message(content=f"Tu as parié sur le numéro {self.bet_number}. Lance la roulette !", view=self)

    async def color_select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return await interaction.response.send_message("Ce n’est pas ta partie.", ephemeral=True)

        chosen_color = self.select_color.values[0]
        self.bet_color = chosen_color.lower()
        self.bet_number = None

        # Désactiver tous les selects de numéro
        for select in [self.select_number_1, self.select_number_2, self.select_number_3]:
            select.disabled = True
            # Reset leurs options par défaut
            select.options = [discord.SelectOption(label=opt.label, value=opt.value, default=False) for opt in select.options]

        # Fixer la sélection couleur (pour garder le visuel)
        self.select_color.options = [
            discord.SelectOption(label=opt.label, value=opt.value, default=(opt.label.lower() == self.bet_color))
            for opt in self.select_color.options
        ]

        self.spin_button.disabled = False

        await interaction.response.edit_message(content=f"Tu as parié sur la couleur {self.bet_color.capitalize()}. Lance la roulette !", view=self)

    def get_color(self, number):
        # 0 est vert, pas rouge ni noir
        if number == 0:
            return "vert"
        # Rouge (nombres rouges sur roulette européenne)
        rouges = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
        return "rouge" if number in rouges else "noir"

    async def spin_callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return await interaction.response.send_message("Ce n’est pas ta partie.", ephemeral=True)

        result = random.randint(0, 36)
        result_color = self.get_color(result)

        if self.bet_number is not None:
            win = (result == self.bet_number)
        elif self.bet_color is not None:
            win = (result_color == self.bet_color)
        else:
            win = False

        description = f"🎰 La bille est tombée sur **{result} ({result_color.upper()})**.\n"
        if win:
            description += "🏆 Félicitations, tu as **gagné** ton pari !"
            color = discord.Color.green()
        else:
            if self.bet_number is not None:
                lost = f"ton numéro **{self.bet_number}**"
            else:
                lost = f"la couleur **{self.bet_color.capitalize()}**"
            description += f"❌ Dommage, tu as perdu {lost}."
            color = discord.Color.red()

        embed = discord.Embed(
            title="🎡 Résultat de la Roulette",
            description=description,
            color=color
        )

        # Désactiver tout
        for item in self.children:
            item.disabled = True

        # On enlève tout et on ajoute juste le bouton rejouer
        self.clear_items()
        self.add_item(RetryButton(self.user))

        await interaction.response.edit_message(embed=embed, view=self)

# ============ Vue de lancement de jeu ============

class StartGameView(discord.ui.View):
    @discord.ui.button(label="🎰 Blackjack", style=discord.ButtonStyle.success, custom_id="start_blackjack")
    async def start_blackjack(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = [random.choice(cards), random.choice(cards)]
        dealer = [random.choice(cards), random.choice(cards)]
        embed = discord.Embed(
            title="🃏 Partie de Blackjack",
            description=(
                f"**Vos cartes :** {' '.join(player)}\n"
                f"**Total :** {BlackjackView(player, dealer, None, interaction.user).calculate_total(player)}\n\n"
                f"**Cartes du croupier :** {' '.join(dealer[:1])} ❓"
            ),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, view=BlackjackView(player, dealer, None, interaction.user))

    @discord.ui.button(label="🎡 Roulette Européenne", style=discord.ButtonStyle.primary, custom_id="start_roulette")
    async def start_roulette(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎡 Roulette Européenne",
            description="Choisissez un numéro (1-36) **ou** une couleur, puis cliquez sur **Lancer la roulette**.",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=RouletteEuropeenneView(interaction.user))

# ============ Vue après /sonnette ============
class CasinoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def create_private_game_channel(self, interaction: discord.Interaction, game_name: str):
        guild = interaction.guild
        member = interaction.user
        croupier_channel = guild.get_channel(SALON_CROUPIERS_ID)
        croupier_role = guild.get_role(ROLE_CROUPIER_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        private_channel = await guild.create_text_channel(
            name=f"🎰・jeu-{member.display_name}".lower().replace(" ", "-"),
            overwrites=overwrites,
            category=guild.get_channel(CATEGORY_ID)
        )

        await croupier_channel.send(
            f"{croupier_role.mention} 🎰 Le joueur **{member.display_name}** souhaite jouer à **{game_name}** !"
        )

        embed = discord.Embed(
            title=f"🎲 ROYAL Casino – {game_name}",
            description="Un croupier va arriver sous peu.\nTu peux commencer une partie pendant que tu attends.",
            color=discord.Color.gold()
        )

        await private_channel.send(content=member.mention, embed=embed, view=StartGameView())
        await interaction.response.send_message(f"✅ Un salon privé a été créé ici : {private_channel.mention}", ephemeral=True)

    @discord.ui.button(label="Blackjack", emoji="🃏", style=discord.ButtonStyle.primary)
    async def blackjack(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_private_game_channel(interaction, "Blackjack")

    @discord.ui.button(label="Roulette", emoji="🎯", style=discord.ButtonStyle.success)
    async def roulette(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_private_game_channel(interaction, "Roulette")

    @discord.ui.button(label="Roue de la fortune", emoji="🎡", style=discord.ButtonStyle.secondary)
    async def roue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_private_game_channel(interaction, "Roue de la fortune")

    @discord.ui.button(label="Autre demande", emoji="💬", style=discord.ButtonStyle.danger)
    async def autre(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_private_game_channel(interaction, "Autre demande")

# ========== Commande /sonnette ==========
@bot.tree.command(name="sonnette", description="Appelle un croupier pour lancer un jeu", guild=discord.Object(id=GUILD_ID))
async def sonnette(interaction: discord.Interaction):
    if interaction.channel.id != SALON_CLIENTS_ID:
        return await interaction.response.send_message("❌ Cette commande ne peut être utilisée que dans le salon clients.", ephemeral=True)

    embed = discord.Embed(
        title="🎲 ROYAL Casino – Besoin d’un croupier ?",
        description=(
            "Vous voulez jouer, mais personne n’est là ?\n"
            "**Clique sur un jeu** et **attends**, un croupier arrive ! 🧑‍⚖️\n"
            "_Tu peux aussi faire une autre demande si nécessaire._"
        ),
        color=discord.Color.gold()
    )

    await interaction.response.send_message(embed=embed, view=CasinoView())

# ========== Gère les replays ==========
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component and interaction.data.get("custom_id") == "replay_blackjack":
        player = [random.choice(cards), random.choice(cards)]
        dealer = [random.choice(cards), random.choice(cards)]

        embed = discord.Embed(
            title="🃏 Partie de Blackjack",
            description=(
                f"**Vos cartes :** {' '.join(player)}\n"
                f"**Total :** {BlackjackView(player, dealer, None, interaction.user).calculate_total(player)}\n\n"
                f"**Cartes du croupier :** {' '.join(dealer[:1])} ❓"
            ),
            color=discord.Color.gold()
        )

        await interaction.message.channel.send(
            embed=embed,
            view=BlackjackView(player, dealer, interaction.message, interaction.user)
        )
        await interaction.response.defer()


# ==== REWARDS ====
rewards = [
    ("1000€ de mise", 15),
    ("250€ Cash", 20),
    ("2000€ de mise", 15),
    ("500€ de mise", 20),
    ("Rien", 20),
    ("*2 sur la prochaine mise", 5),
    ("1000€ de mise", 3),
    ("Une photo avec le PDG", 1),
    ("Une visite du casino", 1),
]

def tirer_gain():
    pool = []
    for reward, chance in rewards:
        pool.extend([reward] * chance)
    return random.choice(pool)

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
            await log_channel.send(f"🎡 {interaction.user.display_name} a tourné la roue et a gagné : **{gain}**")



# ==== COMMANDES ====

@bot.tree.command(name="casino", description="Affiche les boutons de gestion du ROYALE Casino", guild=discord.Object(id=GUILD_ID))
async def casino(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Tu dois être administrateur pour utiliser cette commande.", ephemeral=True)
        return
    await interaction.response.send_message("🎰 Contrôle du ROYAL Casino :", view=CasinoControlView())

@bot.tree.command(name="resetroue", description="Remet la roue à zéro", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(administrator=True)
async def resetroue(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="🎡 Roue journalière", description="Clique sur le bouton ci-dessous pour tenter ta chance !", color=discord.Color.blue())
    embed.set_image(url=GIF_URL)
    channel = bot.get_channel(SALON_ROUE_ID)
    if channel:
        await channel.send(embed=embed, view=VueRoue())
        await interaction.followup.send("✅ Roue relancée dans 🌡｜tourner-la-roue.", ephemeral=True)
    else:
        await interaction.followup.send("❌ Salon introuvable.", ephemeral=True)


@bot.tree.command(name="service", description="Envoyer le bouton de prise de service")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def service(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Clique sur le bouton pour prendre ton service :", view=PriseDeServiceView())

# ==== VIEWS pour prise et fin de service ====

class FinServiceModal(ui.Modal, title="📋 Rapport de fin de service"):
    nb_clients = ui.TextInput(label="👥 Nombre de clients", required=True)
    argent_depart = ui.TextInput(label="💸 Argent au départ", required=True)
    argent_fin = ui.TextInput(label="💰 Argent à la fin", required=True)
    temps_service = ui.TextInput(label="⏱️ Temps de service (HH:MM)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = bot.get_channel(SALON_LOGS_SERVICE_ID)
        embed = discord.Embed(title="📝 Fin de service", color=discord.Color.green())
        embed.add_field(name="👤 Nom", value=interaction.user.display_name, inline=False)
        embed.add_field(name="👥 Nombre de clients", value=self.nb_clients.value, inline=True)
        embed.add_field(name="💸 Argent départ", value=self.argent_depart.value, inline=True)
        embed.add_field(name="💰 Argent fin", value=self.argent_fin.value, inline=True)
        embed.add_field(name="⏱️ Temps de service", value=self.temps_service.value, inline=True)
        await interaction.response.send_message("✅ Ton rapport a bien été envoyé !", ephemeral=True)
        await log_channel.send(embed=embed)

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
        nom = interaction.user.display_name
        await log_channel.send(f"✅ Le joueur **{nom}** a pris son service.")
        await interaction.response.send_message(
            "🟢 Tu es maintenant en service.\nQuand tu veux terminer, clique sur le bouton ci-dessous.",
            view=FinDeServiceView(),
            ephemeral=True)
sessions = {}  # Dictionnaire temporaire pour stocker l'état d'une session par croupier

class ClientModal(discord.ui.Modal, title="Nom des clients"):
    clients = discord.ui.TextInput(label="Nom(s) du/des client(s)", placeholder="Ex: Alice, Bob", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        sessions[interaction.user.id] = {
            "clients": self.clients.value,
            "total_gain": 0,
            "total_perte": 0
        }

        view = ActionView()
        await interaction.response.send_message(
            f"🎲 Session démarrée avec : **{self.clients.value}**",
            view=view,
            ephemeral=True
        )

class GainPerteModal(discord.ui.Modal, title="Gains / Pertes"):
    gain = discord.ui.TextInput(label="Montant gagné", placeholder="Laisse vide si aucun", required=False)
    perte = discord.ui.TextInput(label="Montant perdu", placeholder="Laisse vide si aucun", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        session = sessions.get(interaction.user.id)
        if not session:
            await interaction.response.send_message("Aucune session active.", ephemeral=True)
            return

        try:
            gain = int(self.gain.value) if self.gain.value else 0
            perte = int(self.perte.value) if self.perte.value else 0
        except ValueError:
            await interaction.response.send_message("❌ Veuillez entrer des nombres valides.", ephemeral=True)
            return

        session["total_gain"] += gain
        session["total_perte"] += perte

        await interaction.response.send_message(
            f"✅ Montants ajoutés ! Gain: **{gain}**, Perte: **{perte}**",
            view=ActionView(),
            ephemeral=True
        )

class ActionView(discord.ui.View):
    @discord.ui.button(label="Gains / Perte", style=discord.ButtonStyle.green)
    async def gains_perte(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GainPerteModal())

    @discord.ui.button(label="Fin des clients", style=discord.ButtonStyle.red)
    async def fin_session(self, interaction: discord.Interaction, button: discord.ui.Button):
        session = sessions.pop(interaction.user.id, None)
        if not session:
            await interaction.response.send_message("Aucune session active.", ephemeral=True)
            return

        total = session["total_gain"] - session["total_perte"]
        couleur = discord.Color.green() if total >= 0 else discord.Color.red()

        embed = discord.Embed(
            title="🎰 Fin de session casino",
            color=couleur
        )
        embed.add_field(name="Croupier", value=interaction.user.display_name, inline=True)
        embed.add_field(name="Client(s)", value=session["clients"], inline=True)
        embed.add_field(
            name="Bilan",
            value=f"**{'+ ' if total >= 0 else '- '}{abs(total)}**",
            inline=False
        )

        salon = bot.get_channel(SALON_LOGS_gains_ID)
        await salon.send(embed=embed)
        await interaction.response.send_message("✅ Session terminée et enregistrée.", ephemeral=True)

@bot.tree.command(name="money", description="Lancer une session client casino")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def money(interaction: discord.Interaction):
    salon = bot.get_channel(SALON_BOUTON_ID)
    if not salon:
        await interaction.response.send_message("❌ Salon introuvable.", ephemeral=True)
        return

    class StartView(discord.ui.View):
        @discord.ui.button(label="Commencer une session", style=discord.ButtonStyle.primary)
        async def commencer(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(ClientModal())

    await salon.send("🎰 Cliquez ci-dessous pour commencer une session client casino :", view=StartView())
    await interaction.response.send_message("✅ Bouton envoyé dans le salon.", ephemeral=True)
# ==== Gestion des erreurs sur resetroue ====
@resetroue.error
async def permission_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("🚫 Tu n'as pas les permissions administrateur.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Une erreur est survenue.", ephemeral=True)

# ==== Event on_ready ====
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        print(f"❌ Erreur de synchronisation : {e}")
    print(f"🤖 Connecté en tant que {bot.user}")

# ==== LANCEMENT FINAL ====
keep_alive()
bot.run(TOKEN)
