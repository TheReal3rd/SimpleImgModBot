
@client.tree.command(name="help", description="Provides details about the bot and commands.")
async def helpCommand(interaction: discord.Interaction):
    if not await isInteractionAuthorised(interaction, SERVER_ID):
        return

    FORMAT_TEMPLATE = "{name} - {description}\n"

    commandList = ""
    for cmd in client.tree.get_commands():
        commandList += FORMAT_TEMPLATE.format(name = cmd.name, description = cmd.description)

    if configDict["Jokes_Memes"]:
        commandList += FORMAT_TEMPLATE.format(name="tickleballs", description="Activates remote ball tickler that's attached to 3rd.")

    embed = discord.Embed (
        title = "Help",
        description = commandList,
        color=discord.Color.red()
    )

    await interaction.response.send_message(embed=embed)
    logger.info(f"{interaction.user.name} Has executed the help command.")

        


        
