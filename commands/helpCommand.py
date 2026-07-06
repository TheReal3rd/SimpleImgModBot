
@client.tree.command(name="help", description="Provides details about the bot and commands.")
@app_commands.describe(page="The page number to display to the user.")
async def helpCommand(interaction: discord.Interaction, page : int = 1):
    if not await isInteractionAuthorised(interaction):
        return

    FORMAT_TEMPLATE = "{name} - {description}\n"

    commandList = ""
    for cmd in client.tree.get_commands():
        commandList += FORMAT_TEMPLATE.format(name = cmd.name, description = cmd.description)

    if globals.configDict["JokesMemes"]:
        commandList += FORMAT_TEMPLATE.format(name="tickleballs", description="Activates remote ball tickler that's attached to 3rd.")

    embed = None
    embedLimit = globals.EMBED_LEN_LIMIT
    if len(commandList) >= embedLimit:
        pages = pageString(commandList, embedLimit)

        embed = discord.Embed (
            title = f"Help {page + 1}",
            description = pages[page - 1],
            color=discord.Color.red()
        )

    else:
        embed = discord.Embed (
            title = "Help",
            description = commandList,
            color=discord.Color.red()
        )

    await interaction.response.send_message(embed=embed)
    logger.info(f"{interaction.user.name} Has executed the help command.")

        


        
