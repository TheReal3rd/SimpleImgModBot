
@client.tree.command(name="logs", description="Provides the most recent logger reports.")
async def logsCommand(interaction: discord.Interaction):
    if not await isInteractionAuthorised(interaction):
        return

    logMSG = fetchLogs()

    embedLimit = globals.EMBED_LEN_LIMIT
    if len(logMSG) >= embedLimit:
        pages = pageString(logMSG, embedLimit)
        logMSG = pages[len(pages) - 1]

    if len(logMSG) >= embedLimit:
        logMSG = limitString(logMSG, embedLimit)

    embed = discord.Embed (
        title = "Latest Logs",
        description = logMSG,
        color=discord.Color.red()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)
    logger.info(f"{interaction.user.name} Has executed the log command.")
