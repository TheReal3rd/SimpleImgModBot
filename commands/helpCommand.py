
@client.tree.command(name="help", description="Provides details about the bot and commands.")
async def helpCommand(interaction: discord.Interaction):
    if not str(interaction.guild.id) == SERVER_ID:
        await interaction.response.send_message("This is not the guild i serve.", ephemeral=True)
        logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You're not an administrator.", ephemeral=True)
        logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
        return

    FORMAT_TEMPLATE = "{name} - {description}\n"

    commandList = ""
    for cmd in client.tree.get_commands():
        commandList += FORMAT_TEMPLATE.format(name = cmd.name, description = cmd.description)

    commandList += FORMAT_TEMPLATE.format(name="tickleballs", description="Activates remote ball tickler that's attached to 3rd.")

    embed = discord.Embed (
        title = "Help",
        description = commandList,
        color=discord.Color.red()
    )

    await interaction.response.send_message(embed=embed)
    logger.info(f"{interaction.user.name} Has executed the help command.")

        


        
