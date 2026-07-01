
@client.tree.command(name="scan", description="Scans the current channel for images that are banned.")
@app_commands.describe(scanrange="How deep into message history that will be scanned.")
async def scanCommand(interaction: discord.Interaction, scanrange: int):
    if not await isInteractionAuthorised(interaction, SERVER_ID):
        return

    messages = await getHistory(interaction.channel, scanrange)

    scanNeeded = False
    if len(messages) <= 0:
        msg = "Found no messages with image attachments." 
    else:
        msg = f"The channel scan has been started...\nCount:{len(messages)}"
        scanNeeded = True

    logger.info(f"History scan called by: {interaction.user.name} {msg}")
    responseMSG = await interaction.response.send_message(msg)

    if scanNeeded:
        scanQueues[responseMSG.message_id] = messages
        
    if not scanLoop.is_running():
        scanLoop.start()
    return