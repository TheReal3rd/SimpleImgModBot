
@client.tree.command(name="logs", description="Provides the most recent logger reports")
async def logsCommand(interaction: discord.Interaction):
        if not str(interaction.guild.id) == SERVER_ID:
            await interaction.response.send_message("This is not the guild i serve.", ephemeral=True)
            logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You're not an administrator.", ephemeral=True)
            logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
            return

        logMsg = limitString(fetchLogs(), EMBED_LEN_LIMIT)

        if len(logMsg) > EMBED_LEN_LIMIT:
            await interaction.response.send_message("Ran into an issue.", ephemeral=True)
            logger.error(f"Failed to limit message log within log command.")
            return

        embed = discord.Embed (
            title = "Latest Logs",
            description = logMsg
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"{interaction.user.name} Has used the log command.")
