
@client.tree.command(name="graph", description="Creates and send a performance graph")
async def graphCommand(interaction: discord.Interaction):
    if not await isInteractionAuthorised(interaction):
        return

    result = globals.perfManager.createGraph()

    if result == None:
        await interaction.response.send_message("Not enough performance data collected.")
        logger.info(f"{interaction.user.name} has executed the graph command.")
        return

    await interaction.response.send_message(content="Bot Performance.", file = discord.File(result, filename="benchmark.png"))
    logger.info(f"{interaction.user.name} Has executed the graph command.")
