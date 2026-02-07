import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive

# Load environment variables
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
STUDENT_ROLE_ID = os.getenv('STUDENT_ROLE_ID')

if not TOKEN or not STUDENT_ROLE_ID:
    print("Error: DISCORD_TOKEN or STUDENT_ROLE_ID not found in .env file.")
    exit(1)

try:
    STUDENT_ROLE_ID = int(STUDENT_ROLE_ID)
except ValueError:
    print("Error: STUDENT_ROLE_ID must be an integer.")
    exit(1)

# Define the Verification View
class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent view

    @discord.ui.button(label="Verificati", style=discord.ButtonStyle.green, custom_id="persistent_view:verify")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Read allowed users
        allowed_users = []
        try:
            with open('allowed_users.txt', 'r', encoding='utf-8') as f:
                allowed_users = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            print("Warning: allowed_users.txt not found. No one can verify.")

        user_id = str(interaction.user.id)
        username = interaction.user.name

        if user_id not in allowed_users and username not in allowed_users:
            await interaction.response.send_message("❌ **Accesso Negato**: Non sei nella lista degli studenti autorizzati.", ephemeral=True)
            return


        role = interaction.guild.get_role(STUDENT_ROLE_ID)
        if role:
            if role in interaction.user.roles:
                await interaction.response.send_message("Hai già il ruolo Student!", ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"✅ Verifica completata! Ti è stato assegnato il ruolo **{role.name}**!", ephemeral=True)
        else:
            await interaction.response.send_message("Errore: Ruolo 'Student' non trovato nel server. Contatta un amministratore.", ephemeral=True)

class VerifyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True # Needed to assign roles
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        # Register the persistent view logic
        self.add_view(VerificationView())

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        print(f'Connected to {len(self.guilds)} guilds:')
        for guild in self.guilds:
            print(f' - {guild.name} (ID: {guild.id})')

bot = VerifyBot()

@bot.command()
@commands.has_permissions(administrator=True)
async def spawn_verify(ctx):
    """Spawns the verification message with the button."""
    embed = discord.Embed(title="Verifica", description="Clicca sul pulsante qui sotto per ottenere l'accesso come Student.", color=discord.Color.blue())
    await ctx.send(embed=embed, view=VerificationView())

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
