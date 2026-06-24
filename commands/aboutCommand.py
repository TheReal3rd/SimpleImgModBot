
@client.tree.command(name="about", description="Status information of the bot and its current state.")
async def aboutCommand(interaction: discord.Interaction):
    if not str(interaction.guild.id) == SERVER_ID:
        await interaction.response.send_message("This is not the guild i serve.", ephemeral=True)
        logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
        return

    embed = discord.Embed (
        title = "About",
        description = "This bot is dedicated to prevent spam posting of scam and unwanted images.",
        color=discord.Color.red()
    )

    embed.add_field(
        name="DB Size",
        value = f"{databaseManager.count()}",
        inline = True
    )

    embed.add_field(
        name="Performance",
        value = "Not implemented yet.",
        inline = True
    )

    embed.add_field(
        name="Images Checked",
        value = "Not implemented yet.",
        inline = True
    )

    embed.add_field(
        name="L's given to Resenfor",
        value = "Not implemented yet.",
        inline = True
    )

    await interaction.response.send_message(embed=embed)
    logger.info(f"{interaction.user.name} Has executed the about command.")

        


        


        
