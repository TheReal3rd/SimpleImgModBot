
@client.tree.command(name="logs", description="Provides the most recent logger reports")
async def logsCommand(interaction: discord.Interaction):
    if not await isInteractionAuthorised(interaction, SERVER_ID):
        return

    logMsg = limitString(fetchLogs(), EMBED_LEN_LIMIT)

    if len(logMsg) > EMBED_LEN_LIMIT:
        await interaction.response.send_message("Ran into an issue.", ephemeral=True)
        logger.error(f"Failed to limit message log within log command.")
        return

    embed = discord.Embed (
        title = "Latest Logs",
        description = logMsg,
        color=discord.Color.red()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)
    logger.info(f"{interaction.user.name} Has executed the log command.")
