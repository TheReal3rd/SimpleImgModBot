
@client.tree.command(name="react", description="Toggles on and off the react.")
async def reactToggleCommand(interaction: discord.Interaction):
    if not str(interaction.guild.id) == SERVER_ID:
        await interaction.response.send_message("This is not the guild i serve.", ephemeral=True)
        logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You're not an administrator.", ephemeral=True)
        logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
        return

    hitTable["L_Halt"] = not hitTable["L_Halt"]

    msg = f"Resenfor L reaction toggled to: {hitTable["L_Halt"]}"
    await interaction.response.send_message(msg)
    logger.info(f"React toggle command executed by: {interaction.user.name} With message of: {msg}")
    return