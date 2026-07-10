
@client.tree.command(name="about", description="Status information of the bot and its current state.")
async def aboutCommand(interaction: discord.Interaction):
    if not await isInteractionAuthServer(interaction):
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

    if globals.configDict["Debug"]:
        embed.set_footer(text="In tested mode!!! Certain function will do nothing!")
    else:
        if globals.configDict["JokesMemes"]:
            embed.add_field(
                name="L's given to Resenfor",
                value = f"Today: {resLHits}\nTotal: {hitTable["L_Res"]}",
                inline = False
            )

            embed.set_footer(text=choice(globals.ABT_MSG))
        else:
            embed.set_footer(text="Made by 3rd")

    await interaction.response.send_message(embed=embed)
    logger.info(f"{interaction.user.name} Has executed the about command.")

        


        


        
