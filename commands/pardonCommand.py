
@client.tree.command(name="pardonimg", description="Remove a image from the banned list using the SHA256.")
@app_commands.describe(pardonsha="The SHA256 to remove the image from the database.")
async def pardonCommand(interaction: discord.Interaction, pardonsha: str):
    if not isInteractionAuthorised(interaction):
        return

    expectedLength = len(pardonsha) == SHA256_CHAR_LEN

    if not expectedLength:
        errMsg = "The provided SHA256 didn't meet expected length requirements."
        await interaction.response.send_message(errMsg, ephemeral=True)
        logger.info(f"Attempted admin command called by: {interaction.user.name} MSG: {errMsg}.")
        return

    if not databaseManager.exists(pardonsha):
        errMsg = "The provided SHA256 isn't within the database."
        await interaction.response.send_message(errMsg, ephemeral=True)
        logger.info(f"Attempted admin command called by: {interaction.user.name} MSG: {errMsg}.")
        return 

    sizeChanges = databaseManager.deleteEntry(pardonsha)
    msg = f"Delete sent to database. Response size changes Before: {sizeChanges["before"]} After: {sizeChanges["after"]}"
    logger.info(f"Image has been pardoned by: {interaction.user.name} {msg}")
    await interaction.response.send_message(msg)
    return

        


        
