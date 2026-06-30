
@client.tree.command(name="say", description="Make the bot say something.")
@app_commands.describe(say="The message you want the bot to say.")
async def pardonCommand(interaction: discord.Interaction, say: str):#TODO add a filter so people don't make it saying slurs or executing further commands.
    if not await isInteractionAuthorised(interaction):
        return

    if not isinstance(say, str) and say.startswith("/"):
        await interaction.response.send_message("I can't say that.")
        logger.warning(f"Attempted admin command called by: {interaction.user.name} Tried to say a blocked term or attempted to execute commands as a bot.")
        return

    if len(say) >= MSG_LEN_LIMIT - 1:
        await interaction.response.send_message("The message is too long.")
        logger.warning(f"Attempted admin command called by: {interaction.user.name} The message is too long.")
        return

    await interaction.response.send_message(say)
    logger.info(f"Say command executed by: {interaction.user.name} With message of: {say}")
    return