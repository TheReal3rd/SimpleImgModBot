
@client.tree.command(name="react", description="Toggles on and off the react.")
async def reactToggleCommand(interaction: discord.Interaction):
    if not await isInteractionAuthorised(interaction):
        return

    if not globals.configDict["JokesMemes"]:
        await interaction.response.send_message("Jokes and Meme have been disabled.", ephemeral=True)
        logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
        return

    hitTable = globals.hitTable

    hitTable["L_Halt"] = not hitTable["L_Halt"]
    writeJson("hits.json", hitTable)

    msg = f"Resenfor L reaction toggled to: {hitTable["L_Halt"]}"
    await interaction.response.send_message(msg)
    logger.info(f"React toggle command executed by: {interaction.user.name} With message of: {msg}")
    return