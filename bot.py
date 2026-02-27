import discord
import os
import traceback
import logging
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive

# Setup logging to see all errors
logging.basicConfig(level=logging.INFO)

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

# Define the Modal for Name Input
class VerificationModal(discord.ui.Modal, title='Verifica Studente'):
    name_input = discord.ui.TextInput(
        label='Nome e Cognome',
        placeholder='Es. Mario Rossi',
        min_length=2,
        max_length=50,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # 1. Get the input name
        input_name = self.name_input.value.strip()
        
        # 2. Read allowed users (Real Names)
        allowed_names = []
        try:
            with open('allowed_users.txt', 'r', encoding='utf-8') as f:
                allowed_names = [line.strip().lower() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            print("Warning: allowed_users.txt not found.")

        # 3. Check if input name is allowed
        if input_name.lower() not in allowed_names:
            await interaction.response.send_message(
                f"❌ **Accesso Negato**\nIl nome `{input_name}` non è nella lista autorizzata.\n"
                "Assicurati di aver scritto **Nome e Cognome** esattamente come comunicato.",
                ephemeral=True
            )
            return

        # 4. Assign Role & Rename
        role = interaction.guild.get_role(STUDENT_ROLE_ID)
        if role:
            if role in interaction.user.roles:
                await interaction.response.send_message("Hai già il ruolo Student!", ephemeral=True)
            else:
                try:
                    # Assign Role
                    await interaction.user.add_roles(role)
                    
                    # Rename User (Change Nickname)
                    # Note: Bot cannot rename Server Owner or Roles higher than itself
                    try:
                        await interaction.user.edit(nick=input_name)
                        rename_msg = f"e rinominato in **{input_name}**"
                    except discord.Forbidden:
                        rename_msg = "(non ho il permesso di rinominarti, ma il ruolo è stato dato)"
                    
                    await interaction.response.send_message(f"✅ **Verifica Completata!**\nSei stato identificato come `{input_name}` {rename_msg}.", ephemeral=True)
                
                except discord.Forbidden:
                    await interaction.response.send_message("❌ Errore: Il bot non ha i permessi per darti il ruolo. Contatta un admin.", ephemeral=True)
        else:
            await interaction.response.send_message("Errore: Ruolo 'Student' non trovato.", ephemeral=True)

# Define the Verification View (Button only opens the Modal)
class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent view

    @discord.ui.button(label="Verificati", style=discord.ButtonStyle.green, custom_id="persistent_view:verify_v2")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("DEBUG: Button clicked! Opening Modal...")
        try:
            await interaction.response.send_modal(VerificationModal())
        except Exception as e:
            print(f"ERROR in button handler: {e}")
            try:
                await interaction.response.send_message(f"❌ Errore interno: {e}", ephemeral=True)
            except:
                pass

    async def on_error(self, interaction: discord.Interaction, error: Exception, item):
        print(f"ERROR in view: {error}")
        try:
            await interaction.response.send_message(f"❌ Errore: {error}", ephemeral=True)
        except:
            pass

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
    try:
        print("Starting bot...")
        bot.run(TOKEN, log_handler=None)
    except discord.errors.LoginFailure as e:
        print(f"ERRORE LOGIN: Token non valido! {e}")
    except Exception as e:
        print(f"ERRORE AVVIO BOT: {type(e).__name__}: {e}")
        traceback.print_exc()
