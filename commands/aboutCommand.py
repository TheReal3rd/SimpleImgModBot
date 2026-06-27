
@client.tree.command(name="about", description="Status information of the bot and its current state.")
async def aboutCommand(interaction: discord.Interaction):
    if not str(interaction.guild.id) == SERVER_ID:
        await interaction.response.send_message("This is not the guild i serve.", ephemeral=True)
        logger.warning(f"Attempted admin command called by: {interaction.user.name} no actions where performed.")
        return

    embed = discord.Embed (
        title = "About",
        description = "This bot is dedicated to stopping spam posting of unwanted and scam images.",
        color=discord.Color.red()
    )

    embed.add_field(
        name="DB Size's",
        value = f"HashDB: {databaseManager.count()}\nPending:\n * ChecksDB: {pendingDatabaseManager.count(Tables.CHECKS)}\n * BanDB: {pendingDatabaseManager.count(Tables.BANS)}",
        inline = False
    )

    embed.add_field(
        name="Performance",
        value = f"{perfManager.summary()}",
        inline = False
    )

    embed.add_field(
        name="Images Checked",
        value = f"{hitTable["Img_Scans"]}",
        inline = False
    )

    if configDict["Jokes_Memes"]:
        embed.add_field(
            name="L's given to Resenfor",
            value = f"Today: {resLHits}\nTotal: {hitTable["L_Res"]}",
            inline = False
        )

    embed.set_footer(text="4d61646520627920337264")

    await interaction.response.send_message(embed=embed)
    logger.info(f"{interaction.user.name} Has executed the about command.")

        


        


        
