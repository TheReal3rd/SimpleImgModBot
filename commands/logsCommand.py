
@client.tree.command(name="logs", description="Provides the most recent logger reports")
async def logsCommand(interaction: discord.Interaction):
        if not str(interaction.guild.id) == SERVER_ID:
            await interaction.response.send_message("This is not the guild i serve.", ephemeral=True)
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You're not an administrator.", ephemeral=True)
            logger.warning(f"Attempted admin command called by: {interaction.user.name} no action where performed.")
            return

        logMsg = fetchLogs()

        if len(logMsg) >= EMBED_LEN_LIMIT:
            logMsg = logMsg[:EMBED_LEN_LIMIT].rsplit(" ", 1)[0] + "..."

        embed = discord.Embed (
            title = "Latest Logs",
            description = logMsg
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
