
@client.tree.command(name="about", description="Status information of the bot and its current state.")
async def aboutCommand(interaction: discord.Interaction):
    if not str(interaction.guild.id) == globals.SERVER_ID:
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
        value = f"{globals.perfManager.summary()}",
        inline = False
    )
    hitTable = globals.hitTable
    embed.add_field(
        name="Stats",
        value = f"Images Scans:{hitTable["Img_Scans"]}\nBans:{hitTable["BanCount"]}",
        inline = False
    )

    if globals.configDict["Jokes_Memes"]:
        embed.add_field(
            name="L's given to Resenfor",
            value = f"Today: {resLHits}\nTotal: {hitTable["L_Res"]}",
            inline = False
        )

        embed.set_footer(text=globals.ABT_MSG[random.randint(0, len(globals.ABT_MSG) - 1)])
    else:
        embed.set_footer(text="Made by 3rd")

    await interaction.response.send_message(embed=embed)
    logger.info(f"{interaction.user.name} Has executed the about command.")

        


        


        
