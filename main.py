import discord
from discord.ext import commands, tasks
from discord import app_commands
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import logging
from discord.ui import View, Select
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve sensitive info from environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# Set up logging
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

def sync_commands():
    @bot.event
    async def on_ready():
        await bot.tree.sync()
        print(f"Bot connected as {bot.user}")
        auto_kick_task.start()

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client["discord_bot"]
guild_settings_collection = db["guild_settings"]  # To store guild-specific settings
whitelist_collection = db["whitelist"]  # To store whitelisted users

# Function to check if user is an admin
async def is_admin(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

# Command to set the account age limit for auto-kick
@bot.tree.command(name="setaccountagelimit", description="Set the account age limit for auto-kick.")
async def set_account_age_limit(interaction: discord.Interaction, age_limit: int):
    if not await is_admin(interaction):
        await interaction.response.send_message("You need administrator permissions to use this command.", ephemeral=True)
        return

    if age_limit <= 0:
        await interaction.response.send_message("Age limit must be greater than 0 days.", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    guild_settings = guild_settings_collection.find_one({"guild_id": guild_id})

    if guild_settings is None:
        guild_settings_collection.insert_one({"guild_id": guild_id, "account_age_limit": age_limit, "autokick_enabled": True})
    else:
        guild_settings_collection.update_one({"guild_id": guild_id}, {"$set": {"account_age_limit": age_limit}})
    
    await interaction.response.send_message(f"Account age limit for auto-kick set to {age_limit} days.", ephemeral=True)

# Command to add a user to the whitelist
@bot.tree.command(name="whitelist", description="Add a user to the whitelist to bypass age limit kick.")
async def whitelist(interaction: discord.Interaction, user: discord.User):
    if not await is_admin(interaction):
        await interaction.response.send_message("You need administrator permissions to use this command.", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    if whitelist_collection.find_one({"guild_id": guild_id, "user_id": user.id}):
        await interaction.response.send_message(f"{user.name} is already in the whitelist.", ephemeral=True)
        return
    
    whitelist_collection.insert_one({"guild_id": guild_id, "user_id": user.id})
    await interaction.response.send_message(f"{user.name} has been added to the whitelist.", ephemeral=True)

# Command to remove a user from the whitelist
@bot.tree.command(name="removefromwhitelist", description="Remove a user from the whitelist.")
async def remove_from_whitelist(interaction: discord.Interaction, user: discord.User):
    if not await is_admin(interaction):
        await interaction.response.send_message("You need administrator permissions to use this command.", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    if not whitelist_collection.find_one({"guild_id": guild_id, "user_id": user.id}):
        await interaction.response.send_message(f"{user.name} is not in the whitelist.", ephemeral=True)
        return
    
    whitelist_collection.delete_one({"guild_id": guild_id, "user_id": user.id})
    await interaction.response.send_message(f"{user.name} has been removed from the whitelist.", ephemeral=True)

# Auto-kick alt accounts with the configured account age limit
@bot.tree.command(name="autokickalt", description="Automatically kick accounts younger than the configured age limit.")
async def autokickalt(interaction: discord.Interaction):
    if not await is_admin(interaction):
        await interaction.response.send_message("You need administrator permissions to use this command.", ephemeral=True)
        return

    guild_id = interaction.guild.id
    guild_settings = guild_settings_collection.find_one({"guild_id": guild_id})

    if guild_settings is None:
        guild_settings_collection.insert_one({"guild_id": guild_id, "autokick_enabled": True})
        guild_settings = {"autokick_enabled": True}
    
    class AutoKickSelect(Select):
        def __init__(self):
            options = [
                discord.SelectOption(label="Enable Auto-Kick", value="enable"),
                discord.SelectOption(label="Disable Auto-Kick", value="disable")
            ]
            super().__init__(placeholder="Select an option", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            if not await is_admin(interaction):
                await interaction.response.send_message("You need administrator permissions to use this option.", ephemeral=True)
                return

            selected_option = self.values[0]
            if selected_option == "enable":
                if guild_settings["autokick_enabled"]:
                    await interaction.response.send_message("Auto-kick is already enabled.", ephemeral=True)
                else:
                    guild_settings_collection.update_one({"guild_id": guild_id}, {"$set": {"autokick_enabled": True}})
                    await interaction.response.send_message("Auto-kick has been enabled.", ephemeral=True)
            elif selected_option == "disable":
                if not guild_settings["autokick_enabled"]:
                    await interaction.response.send_message("Auto-kick is already disabled.", ephemeral=True)
                else:
                    guild_settings_collection.update_one({"guild_id": guild_id}, {"$set": {"autokick_enabled": False}})
                    await interaction.response.send_message("Auto-kick has been disabled.", ephemeral=True)

    view = discord.ui.View()
    view.add_item(AutoKickSelect())
    await interaction.response.send_message("Select an option:", view=view, ephemeral=True)

# Function to check and kick members under the configured account age limit, ignoring boosters
async def process_members(guild):
    guild_settings = guild_settings_collection.find_one({"guild_id": guild.id})
    if guild_settings and guild_settings.get("autokick_enabled", False):
        account_age_limit = guild_settings.get("account_age_limit", 7)  
        for member in guild.members:
            if member.premium_since is not None:
                logging.info(f"Skipping {member.name} (ID: {member.id}) as they are a server booster.")
                continue

            if whitelist_collection.find_one({"guild_id": guild.id, "user_id": member.id}):
                logging.info(f"Skipping {member.name} (ID: {member.id}) as they are whitelisted.")
                continue
            
            account_age = datetime.now(timezone.utc) - member.created_at
            logging.info(f"Checking user: {member.name} (ID: {member.id}) | Account created at: {member.created_at} | Account age: {account_age}")

            if timedelta(days=0) <= account_age < timedelta(days=account_age_limit):
                try:
                    logging.info(f"User {member.name} (ID: {member.id}) has been kicked. Account age: {account_age}")
                    await member.kick(reason=f"Account too new (under {account_age_limit} days)")
                except discord.Forbidden:
                    logging.error(f"Permission error: Could not kick {member.name} (ID: {member.id}).")
                except discord.HTTPException as e:
                    logging.error(f"HTTP error: {e}")
                except Exception as e:
                    logging.error(f"Error: {e}")

# Background task to check members every 10 seconds
@tasks.loop(seconds=10)
async def auto_kick_task():
    for guild in bot.guilds:
        await process_members(guild)

sync_commands()
bot.run(DISCORD_TOKEN)
