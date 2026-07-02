
@client.tree.command(name="purgemsg", description="Deletes all messages sent from the bot in the channel.")
@app_commands.describe(scanrange="How deep into message history will be purged.")
async def scanCommand(interaction: discord.Interaction, scanrange: int):
    if not await isInteractionAuthorised(interaction):
        return

    messages = await getBotMessageHistory(interaction.channel, scanrange)

    scanNeeded = False
    if len(messages) <= 0:
        msg = "Found no messages with image attachments." 
    else:
        msg = f"The channel purge has been started...\nCount:{len(messages)}"
        scanNeeded = True

    logger.info(f"Bot Message purge called by: {interaction.user.name} {msg}")
    responseMSG = await interaction.response.send_message(msg)

    if responseMSG in purgeQueues.keys():
        logger.warning("Purge already queued...")
        return

    if scanNeeded:
        purgeQueues[responseMSG.message_id] = messages
        
    if not purgeLoop.is_running():
        purgeLoop.start()
    return